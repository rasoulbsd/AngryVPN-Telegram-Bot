"""
Account charging functions for client flows.
"""

import telegram
import telegram.ext as telext
from helpers.initial import get_secrets_config, connect_to_database, set_lang
from helpers.bot_functions import check_subscription
from helpers.states import (
    USER_RECHARGE_ACCOUNT_SELECT_PLAN, USER_RECHARGE_ACCOUNT,
    NEWUSER_PURCHASE_RIAL_ZARIN
)
import secrets as sc
import requests

(secrets, Config) = get_secrets_config()
# Removed global client_functions_texts

# --- Begin moved charge/account functions ---

async def user_charge_account(
    update: telegram.Update,
    context: telext.ContextTypes.DEFAULT_TYPE
):
    """Handle user account charging."""
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
    reply_text = client_functions_texts("choose_plan_simple") + ' :\n\n' + client_functions_texts("cancel_to_abort")
    user_obj = db_client[secrets['DBName']].users.find_one({'user_id': update.effective_user.id}, {"orgs": { "$slice": 1 }})
    org_name = list(user_obj["orgs"].keys())[0]
    org_obj = db_client[secrets['DBName']].orgs.find_one({'name': org_name})
    context.user_data['org_obj'] = org_obj
    user_dict = db_client[secrets['DBName']].users.find_one({'user_id': int(update.effective_chat.id)})
    context.user_data['user_dict'] = user_dict
    if ('discount' in user_dict and user_dict['discount']):
        discount = (100-user_dict['discount']) / 100
    else:
        discount = 1
    context.user_data['discount'] = discount
    if 'rial' in org_obj['payment_options']['currencies']:
        context.user_data['currency'] = 'rial'
        currency_icon = 'T'
    else:
        context.user_data['currency'] = 'cad'
        currency_icon = 'CAD'
    keyboard = [
        [telegram.InlineKeyboardButton(
            f"{plan}: {round(int(org_obj['payment_options']['currencies'][context.user_data['currency']]['plans'][plan]) * discount)} {currency_icon}" +
            (f" ({100-100*discount}% off)" if (100-100*discount != 0) else ""),
            callback_data={"plan": plan}
        )]
        for plan in org_obj['payment_options']['currencies'][
            context.user_data['currency']
        ]['plans']
    ]
    keyboard.extend([
        [telegram.InlineKeyboardButton(
            client_functions_texts("general_cancel"), callback_data='Cancel')]
    ])
    reply_markup = telegram.InlineKeyboardMarkup(keyboard)
    await update.effective_message.edit_text(
        reply_text,
        reply_markup=reply_markup,
        parse_mode=telegram.constants.ParseMode.MARKDOWN
    )
    db_client.close()
    return USER_RECHARGE_ACCOUNT_SELECT_PLAN


async def user_charge_account_with_plan(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    try:
        db_client = connect_to_database(secrets['DBConString'])
    except Exception:
        print("Failed to connect to the database!")

    user_id = update.effective_user.id
    user_dict = db_client[secrets['DBName']].users.find_one({'user_id': user_id})
    user_lang = user_dict.get('lang', Config['default_language']) if user_dict else Config['default_language']
    client_functions_texts = set_lang(user_lang, 'client_functions')

    user_org = db_client[secrets['DBName']].orgs.find_one({'name': list(user_dict['orgs'].keys())[0]})
    if 'rial' in user_org['payment_options']['currencies']:
        context.user_data['currency'] = 'rial'
    elif 'cad' in user_org['payment_options']['currencies']:
        context.user_data['currency'] = 'cad'
    else:
        print("Not Implemented")
        raise EOFError

    query = update.callback_query
    await query.answer()
    if query.data == 'Cancel':
        db_client.close()
        return telext.ConversationHandler.END
    if 'plan' not in context.user_data:
        context.user_data['plan'] = query.data['plan']
    if not await check_subscription(update):
        main_channel = db_client[secrets['DBName']].orgs.find_one({'name': 'main'})['channel']['link']
        reply_text = client_functions_texts('join_channel') + f"\n\n{main_channel}"
        await update.effective_message.edit_text(reply_text)
        db_client.close()
        return telext.ConversationHandler.END
    org_obj = context.user_data['org_obj']
    context.user_data['is_new_user'] = False

    context.user_data['payment_method'] = org_obj['payment_options']['currencies'][context.user_data['currency']]['method']
    if context.user_data['payment_method'] == 'e-transfer':
        if context.user_data['currency'] == 'rial':
            reply_text = client_functions_texts("selected_plan") + f': {query.data["plan"]} Pack\n' + client_functions_texts("send_crypto_transaction_receipt") + ':'
            if "card_number" in org_obj['payment_options']['currencies'][context.user_data['currency']] and org_obj['payment_options']['currencies'][context.user_data['currency']]['card_number'] != "":
                reply_text += '\n\n' + client_functions_texts("card_number") + f': `{org_obj["payment_options"]["currencies"][context.user_data["currency"]]["card_number"]}`'
        else:
            reply_text = client_functions_texts("selected_plan") + f': {query.data["plan"]} Pack\n' + client_functions_texts("etransfer_instruction") + ":"
            if "email" in org_obj['payment_options']['currencies']['cad'] and org_obj['payment_options']['currencies']['cad']['email'] != "":
                reply_text += '\n\n' + client_functions_texts("email") + f': `{org_obj["payment_options"]["currencies"]["cad"]["email"]}`'
            elif "phone_number" in org_obj['payment_options']['currencies']['cad'] and org_obj['payment_options']['currencies']['cad']['phone_number'] != "":
                reply_text += '\n\n' + client_functions_texts("phone_number") + f': `{org_obj["payment_options"]["currencies"]["cad"]["phone_number"]}`'

        reply_text += '\n\n' + client_functions_texts("cancel_to_abort")
        keyboard = [
            [telegram.InlineKeyboardButton(client_functions_texts("general_cancel"), callback_data='Cancel')]
        ]
        reply_markup = telegram.InlineKeyboardMarkup(keyboard)
        await update.effective_message.edit_text(reply_text, reply_markup=reply_markup, parse_mode=telegram.constants.ParseMode.MARKDOWN)
        db_client.close()
        return USER_RECHARGE_ACCOUNT
    else:
        reply_text = client_functions_texts("selected_plan") + f': {query.data["plan"]} Pack\n' + client_functions_texts("zarinpal_message") + ':\n\n' + client_functions_texts('cancel_to_abort')
        context.user_data['merchant_id'] = org_obj['payment_options']['currencies']['rial']['merchant_id']
        secret_url = sc.token_urlsafe()
        context.user_data['pay_amount'] = org_obj['payment_options']['currencies']['rial']['plans'][query.data['plan']]
        context.user_data['payment_type'] = 'rial'
        url = "https://api.zarinpal.com/pg/v4/payment/request.json"
        if context.user_data['payment_type'] == 'rial':
            multiply_factor = 10000
        else:
            multiply_factor = 1
        payload = {
            "merchant_id": context.user_data['merchant_id'],
            "amount": int(context.user_data['pay_amount'])*multiply_factor,
            "callback_url": "http://t.me/"+secrets["BOT_USERNAME"],
            "description": "خرید پلن"+query.data['plan'],
        }
        print(payload)
        headers = {
            "accept": "application/json",
            "content-type": "application/json"
        }
        response = requests.request("POST", url, json=payload, headers=headers).json()
        print(context.user_data)
        print(response['data'])
        context.user_data['authority']=response['data']['authority']
        context.user_data['secret_url']=secret_url
        keyboard = [
            [telegram.InlineKeyboardButton(client_functions_texts("pay_now"), callback_data='Pay now')],
            [telegram.InlineKeyboardButton(client_functions_texts("general_cancel"), callback_data='Cancel')]
        ]
        reply_markup = telegram.InlineKeyboardMarkup(keyboard)
        await update.effective_message.edit_text(reply_text, reply_markup=reply_markup, parse_mode=telegram.constants.ParseMode.MARKDOWN)
        db_client.close()
        return NEWUSER_PURCHASE_RIAL_ZARIN


async def user_charge_acc_unified(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    print("in user_charge_acc_unified")
    try:
        db_client = connect_to_database(secrets['DBConString'])
    except Exception:
        print("Failed to connect to the database!")
        return

    user_id = update.effective_user.id
    user_dict = db_client[secrets['DBName']].users.find_one({'user_id': user_id})
    user_lang = user_dict.get('lang', Config['default_language']) if user_dict else Config['default_language']
    client_functions_texts = set_lang(user_lang, 'client_functions')

    # Defensive check for required context
    if 'currency' not in context.user_data or 'plan' not in context.user_data:
        await update.effective_message.reply_text(
            "Payment flow error: missing currency or plan. Please start again."
        )
        db_client.close()
        return telext.ConversationHandler.END

    # Get org info
    user_obj = db_client[secrets['DBName']].users.find_one(
        {'user_id': update.effective_user.id}, {"orgs": {"$slice": 1}}
    )
    org_name = list(user_obj["orgs"].keys())[0]
    org_obj = db_client[secrets['DBName']].orgs.find_one({'name': org_name})

    # Common context
    context.user_data['full_name'] = update.effective_chat.full_name
    context.user_data['username'] = update.effective_chat.username
    context.user_data['user_id'] = update.effective_chat.id
    context.user_data['org'] = org_name
    context.user_data['pay_amount'] = org_obj['payment_options']['currencies'][context.user_data['currency']]['plans'][context.user_data['plan']]

    # Build keyboard
    keyboard = [
        [
            telegram.InlineKeyboardButton('❌ Reject', callback_data='Reject'),
            telegram.InlineKeyboardButton('✅ Accept', callback_data='Accept')
        ]
    ]
    reply_markup = telegram.InlineKeyboardMarkup(keyboard)

    # Handle input type
    if update.message.text:
        context.user_data["payment_receipt"] = f"{update.effective_message.text}"
        await context.bot.send_message(
            chat_id=org_obj['ticketing_group_id'],
            text=(
                "Recharg\n"
                f"payment_method:{context.user_data.get('payment_method', '')}\n"
                + (f"username:@{context.user_data['username']}\n" if context.user_data['username'] else "")
                + f"user_id:{context.user_data['user_id']}\n"
                + f"full_name:{context.user_data['full_name']}\n"
                + f"Plan:{context.user_data['plan']}\n"
                + f"org:{context.user_data['org']}\n"
                + f"pay_amount:{context.user_data['pay_amount']}, included {100-context.user_data.get('discount',1)*100}% discount\n"
                + f"currency:{context.user_data['currency']}\n"
                "-------------------------\n"
                + context.user_data["payment_receipt"]
            ),
            reply_to_message_id=secrets['test_topic_id'] if secrets["DBName"].lower() == "rhvp-test" else secrets['payments_topic_id'],
            reply_markup=reply_markup
        )
    elif update.message.photo:
        context.user_data["payment_receipt"] = "Photo payment receipt"
        await context.bot.send_photo(
            chat_id=org_obj['ticketing_group_id'],
            photo=update.message.photo[0].file_id,
            caption=(
                "Recharg\n"
                f"payment_method:{context.user_data.get('payment_method', '')}\n"
                + (f"username:@{context.user_data['username']}\n" if context.user_data['username'] else "")
                + f"user_id:{context.user_data['user_id']}\n"
                + f"full_name:{context.user_data['full_name']}\n"
                + f"Plan:{context.user_data['plan']}\n"
                + f"org:{context.user_data['org']}\n"
                + f"pay_amount:{context.user_data['pay_amount']}, included {100-context.user_data.get('discount',1)*100}% discount\n"
                + f"currency:{context.user_data['currency']}\n"
            ),
            reply_to_message_id=secrets['test_topic_id'] if secrets["DBName"].lower() == "rhvp-test" else secrets['payments_topic_id'],
            reply_markup=reply_markup
        )
    elif update.message.document:
        context.user_data["payment_receipt"] = "Document payment receipt"
        await context.bot.send_document(
            chat_id=org_obj['ticketing_group_id'],
            document=update.message.document.file_id,
            caption=(
                "Recharg\n"
                f"payment_method:{context.user_data.get('payment_method', '')}\n"
                + (f"username:@{context.user_data['username']}\n" if context.user_data['username'] else "")
                + f"user_id:{context.user_data['user_id']}\n"
                + f"full_name:{context.user_data['full_name']}\n"
                + f"Plan:{context.user_data['plan']}\n"
                + f"org:{context.user_data['org']}\n"
                + f"pay_amount:{context.user_data['pay_amount']}, included {100-context.user_data.get('discount',1)*100}% discount\n"
                + f"currency:{context.user_data['currency']}\n"
            ),
            reply_to_message_id=secrets['test_topic_id'] if secrets["DBName"].lower() == "rhvp-test" else secrets['payments_topic_id'],
            reply_markup=reply_markup
        )
    else:
        await update.effective_message.reply_text("Unsupported payment input. Please send text, photo, or document.")
        db_client.close()
        return telext.ConversationHandler.END

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=client_functions_texts("thanks_for_payment")
    )
    db_client.close()
    return telext.ConversationHandler.END
