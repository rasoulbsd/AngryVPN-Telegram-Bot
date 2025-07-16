"""
Purchase orchestration functions - handles the main purchase flow and routing.
"""

import telegram
import telegram.ext as telext
from helpers.initial import get_secrets_config, set_lang, connect_to_database
from helpers.bot_functions import check_subscription
from helpers.states import (
    NEWUSER_PURCHASE_SELECT_PLAN, NEWUSER_PURCHASE_RIAL,
    NUEWUSER_PURCHASE_RECEIPT_CRYPTO, NEWUSER_PURCHASE_INTERCEPTOR,
    NEWUSER_PURCHASE_INTERCEPTOR_INPUTED,
    NEWUSER_PURCHASE_CAD
)

(secrets, Config) = get_secrets_config()
# Removed global client_functions_texts


async def newuser_purchase(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    """Main entry point for new user purchase flow."""
    try:
        db_client = connect_to_database(secrets['DBConString'])
    except Exception:
        print("Failed to connect to the database!")

    user_id = update.effective_user.id
    user_dict = db_client[secrets['DBName']].users.find_one({'user_id': user_id})
    user_lang = user_dict.get('lang', Config['default_language']) if user_dict else Config['default_language']
    client_functions_texts = set_lang(user_lang, 'client_functions')

    query = update.callback_query
    await query.answer()
    if query.data == 'Cancel':
        db_client.close()
        return telext.ConversationHandler.END
    if not await check_subscription(update):
        main_channel = db_client[secrets['DBName']].orgs.find_one({'name': 'main'})['channel']['link']
        reply_text = client_functions_texts('join_channel') + f"\n\n{main_channel}"
        await update.effective_message.edit_text(reply_text)

        db_client.close()
        return telext.ConversationHandler.END

    context.user_data['menu'] = update.effective_message
    context.user_data['chat'] = update.effective_chat
    context.user_data['full_name'] = update.effective_chat.full_name
    context.user_data['username'] = update.effective_chat.username
    context.user_data['user_id'] = update.effective_chat.id
    
    reply_text = client_functions_texts("referal_code") + "\n\n" + client_functions_texts("cancel_to_abort") 
    keyboard = [
        [telegram.InlineKeyboardButton(client_functions_texts("general_cancel"), callback_data='Cancel')]
    ]
    reply_markup = telegram.InlineKeyboardMarkup(keyboard)
    await update.effective_message.edit_text(reply_text, reply_markup=reply_markup, parse_mode=telegram.constants.ParseMode.MARKDOWN)

    db_client.close()
    return NEWUSER_PURCHASE_SELECT_PLAN


async def newuser_purchase_select_plan(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    """Handle plan selection and determine payment method routing."""
    try:
        db_client = connect_to_database(secrets['DBConString'])
    except Exception:
        print("Failed to connect to the database!")

    print("me")
    user_id = update.effective_user.id
    user_dict = db_client[secrets['DBName']].users.find_one({'user_id': user_id})
    user_lang = user_dict.get('lang', Config['default_language']) if user_dict else Config['default_language']
    client_functions_texts = set_lang(user_lang, 'client_functions')

    if not await check_subscription(update):
        main_channel = db_client[secrets['DBName']].orgs.find_one({'name': 'main'})['channel']['link']
        reply_text = client_functions_texts('join_channel') + f"\n\n{main_channel}"
        await update.effective_message.edit_text(reply_text)

        db_client.close()
        return telext.ConversationHandler.END

    org = db_client[secrets['DBName']].orgs.find_one({'referral_code': update.effective_message.text})
    if org is None:
        reply_text = "The referral code is not valid!"
        await context.user_data['menu'].edit_text(reply_text)

        db_client.close()
        return telext.ConversationHandler.END
    
    context.user_data['org'] = org['name']

    if 'rial' in org['payment_options']['currencies']:
        currency_icon = 'T'
        context.user_data['currency'] = 'rial'
    else:
        currency_icon = 'CAD'
        context.user_data['currency'] = 'cad'
        context.user_data['method'] = 'cad'

    # Find the server with the lowest price
    lowest_price_server = db_client[secrets['DBName']].servers.find_one(
        {"price": {"$exists": True}},
        sort=[("price", 1)]
    )

    # if context.user_data['method'] == 'cad':
    reply_text = client_functions_texts("choose_plan_simple")
    reply_text += "\n\n"
    reply_text += client_functions_texts("choose_plan_cad")
    reply_text += "\n\n"
    reply_text += client_functions_texts("choose_plan_cad_extra")
    if lowest_price_server:
        reply_text += "\n\n"
        reply_text += client_functions_texts("lowest_price") + \
                    f" {lowest_price_server['price']} {currency_icon}"
    # else:
    #     reply_text = client_functions_texts("choose_plan_simple")

    reply_text += "\n\n" + client_functions_texts("cancel_to_abort")

    user_dict = db_client[secrets['DBName']].users.find_one({'user_id': int(update.effective_chat.id)})
    context.user_data['user_dict'] = user_dict
    if ('discount' in user_dict and user_dict['discount']):
        discount = (100-user_dict['discount']) / 100
    else:
        discount = 1
    context.user_data['discount'] = discount

    keyboard = [
        [telegram.InlineKeyboardButton(f"{plan}: {round(int(org['payment_options']['currencies'][context.user_data['currency']]['plans'][plan]) * discount)} {currency_icon}" + (f" ({100-100*discount}% off)" if (100-100*discount != 0) else ""), callback_data=f"plan_{plan}")] for plan in org['payment_options']['currencies'][context.user_data['currency']]['plans']
    ]
    keyboard.extend([[telegram.InlineKeyboardButton(client_functions_texts("general_cancel"), callback_data='Cancel')]])

    reply_markup = telegram.InlineKeyboardMarkup(keyboard)
    await context.user_data['menu'].edit_text(reply_text, reply_markup=reply_markup, parse_mode=telegram.constants.ParseMode.MARKDOWN)

    pay_methods = org['payment_options']['currencies']

    active_methods = []
    for currency, details in pay_methods.items():
        if details.get("active"):
            active_methods.append(currency)
    if len(active_methods) == 0:
        db_client.close()
        return telext.ConversationHandler.END
    elif len(active_methods) == 1:
        db_client.close()
        if active_methods[0] == 'rial':
            return NEWUSER_PURCHASE_RIAL
        elif active_methods[0] == 'tron':
            return NUEWUSER_PURCHASE_RECEIPT_CRYPTO
        elif active_methods[0] == 'cad':
            print("Select")
            return NEWUSER_PURCHASE_CAD
    else:
        db_client.close()
        return NEWUSER_PURCHASE_INTERCEPTOR


async def newuser_purchase_interceptor(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    """Handle payment method selection when multiple methods are available."""
    try:
        db_client = connect_to_database(secrets['DBConString'])
    except Exception:
        print("Failed to connect to the database!")

    user_id = update.effective_user.id
    user_dict = db_client[secrets['DBName']].users.find_one({'user_id': user_id})
    user_lang = user_dict.get('lang', Config['default_language']) if user_dict else Config['default_language']
    client_functions_texts = set_lang(user_lang, 'client_functions')

    if not await check_subscription(update):
        main_channel = db_client[secrets['DBName']].orgs.find_one({'name': 'main'})['channel']['link']
        reply_text = client_functions_texts('join_channel') + f"\n\n{main_channel}"
        await update.effective_message.edit_text(reply_text)

        db_client.close()
        return telext.ConversationHandler.END

    query = update.callback_query
    await query.answer()
    if query.data == 'Cancel':
        return telext.ConversationHandler.END
    if 'plan' not in context.user_data:
        context.user_data['plan'] = query.data['plan']

    org_obj = db_client[secrets['DBName']].orgs.find_one({'name': context.user_data['org']})

    pay_methods = org_obj['payment_options']['currencies']

    active_methods = []
    for currency, details in pay_methods.items():
        if details.get("active"):
            active_methods.append(currency)

    reply_text = "choose_payment_method"

    keyboard = [
            [telegram.InlineKeyboardButton(f"{method}", callback_data={'method': method})] for method in active_methods
    ] + [[telegram.InlineKeyboardButton(client_functions_texts("general_cancel"), callback_data='Cancel')]]

    reply_markup = telegram.InlineKeyboardMarkup(keyboard)
    await context.user_data['menu'].edit_text(reply_text, reply_markup=reply_markup, parse_mode=telegram.constants.ParseMode.MARKDOWN)

    db_client.close()
    return NEWUSER_PURCHASE_INTERCEPTOR_INPUTED


async def newuser_purchase_interceptor_inputed(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    """Route to the appropriate payment method based on user selection."""
    query = update.callback_query
    await query.answer()
    if query.data == 'Cancel':
        return telext.ConversationHandler.END

    if query.data['method'] == 'rial':
        return NEWUSER_PURCHASE_RIAL
    elif query.data['method'] == 'tron':
        return NUEWUSER_PURCHASE_RECEIPT_CRYPTO 
