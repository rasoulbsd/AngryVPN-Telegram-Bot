"""
Account charging functions for client flows.
"""

import telegram
import telegram.ext as telext
from helpers.initial import get_secrets_config, connect_to_database, set_lang
from helpers.bot_functions import check_subscription
from helpers.states import (
    USER_RECHARGE_ACCOUNT_SELECT_PLAN, USER_RECHARGE_ACCOUNT
)
import secrets as sc
import requests

(secrets, Config) = get_secrets_config()
client_functions_texts = set_lang(Config['default_language'], 'client_functions')

# --- Begin moved charge/account functions ---

async def user_charge_account(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    try:
        db_client = connect_to_database(secrets['DBConString'])
    except Exception:
        print("Failed to connect to the database!")

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
    reply_text = client_functions_texts("choose_plan2") + ':\n\n' + client_functions_texts("cancel_to_abort")
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
    keyboard = [
        [telegram.InlineKeyboardButton(f"{plan}: {round(int(org_obj['payment_options']['currencies']['rial']['plans'][plan]) * discount)} T" + (f" ({100-100*discount}% off)" if (100-100*discount != 0) else "")
                                       , callback_data={'plan': plan})] for plan in org_obj['payment_options']['currencies']['rial']['plans']
    ]
    keyboard.extend([[telegram.InlineKeyboardButton(client_functions_texts("general_cancel"), callback_data='Cancel')]])
    reply_markup = telegram.InlineKeyboardMarkup(keyboard)
    await update.effective_message.edit_text(reply_text, reply_markup=reply_markup, parse_mode=telegram.constants.ParseMode.MARKDOWN)
    db_client.close()
    return USER_RECHARGE_ACCOUNT_SELECT_PLAN

async def user_charge_account_with_plan(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    try:
        db_client = connect_to_database(secrets['DBConString'])
    except Exception:
        print("Failed to connect to the database!")

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
    context.user_data['payment_method'] = org_obj['payment_options']['currencies']['rial']['method']
    if context.user_data['payment_method'] == 'e-transfer':
        reply_text = client_functions_texts("selected_plan") + f': {query.data["plan"]} Pack\n' + client_functions_texts("send_crypto_transaction_receipt") + ':'
        if "card_number" in org_obj['payment_options']['currencies']['rial'] and org_obj['payment_options']['currencies']['rial']['card_number'] != "":
            reply_text += '\n\n' + client_functions_texts("card_number") + f': `{org_obj["payment_options"]["currencies"]["rial"]["card_number"]}`'
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
        description = u'خرید پلن'+query.data['plan']
        email=''
        mobile=''
        secret_url=sc.token_urlsafe()
        context.user_data['pay_amount'] = org_obj['payment_options']['currencies']['rial']['plans'][query.data['plan']]
        context.user_data['payment_type'] = 'rial'
        url = "https://api.zarinpal.com/pg/v4/payment/request.json"
        payload = {
            "merchant_id": context.user_data['merchant_id'],
            "amount": int(context.user_data['pay_amount'])*10000,
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

async def user_charge_acc_inputed(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    print("in user_charge_acc_inputed")
    try:
        db_client = connect_to_database(secrets['DBConString'])
    except Exception:
        print("Failed to connect to the database!")

    if not await check_subscription(update):
        main_channel = db_client[secrets['DBName']].orgs.find_one({'name': 'main'})['channel']['link']
        reply_text = client_functions_texts('join_channel') + f"\n\n{main_channel}"
        await update.effective_message.reply_text(reply_text)
        db_client.close()
        return telext.ConversationHandler.END
    else:
            user_dict = db_client[secrets['DBName']].users.find_one({'user_id': int(update.effective_chat.id)})
            if user_dict is None:
                reply_text = client_functions_texts("user_not_found")
                await update.effective_message.reply_text(reply_text)
            else:
                user_obj = db_client[secrets['DBName']].users.find_one({'user_id': update.effective_user.id}, {"orgs": { "$slice": 1 }})
                org_name = list(user_obj["orgs"].keys())[0]
                org_obj = db_client[secrets['DBName']].orgs.find_one({'name': org_name})
                keyboard = [
                        [telegram.InlineKeyboardButton('❌ Reject', callback_data='Reject'),telegram.InlineKeyboardButton('✅ Accept', callback_data='Accept')]
                    ]
                context.user_data["payment_receipt"] = update.effective_message.text
                reply_markup = telegram.InlineKeyboardMarkup(keyboard)
                context.user_data['payment_receipt'] = f"\n{update.effective_message.text}"
                context.user_data['full_name'] = update.effective_chat.full_name
                context.user_data['username'] = update.effective_chat.username
                context.user_data['user_id'] = update.effective_chat.id
                context.user_data['org'] = org_name
                context.user_data['pay_amount'] = org_obj['payment_options']['currencies']['rial']['plans'][context.user_data['plan']]
                await context.bot.send_message(
                    chat_id=org_obj['ticketing_group_id'],
                    text=
                        f"Recharg\n"+
                        f"payment_method:{context.user_data['payment_method']}\n" +
                        (f"username:@{context.user_data['username']}\n" if(context.user_data['username'] is not None) else "") +
                        f"user_id:{context.user_data['user_id']}\nfull_name:{context.user_data['full_name']}\n" +
                        f"Plan:{context.user_data['plan']}\n" +
                        f"org:{context.user_data['org']}\n"+
                        f"pay_amount:{context.user_data['pay_amount']}, included {100-100*context.user_data['discount']}% discount\n" +
                        f"currency:rial\n"+
                        "-------------------------\n" +
                        context.user_data['payment_receipt'],
                    reply_to_message_id=secrets['test_topic_id'] if secrets["DBName"].lower() == "rhvp-test" else secrets['payments_topic_id'],
                    reply_markup=reply_markup
                    )
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=client_functions_texts("thanks_for_payment")
                    )
            db_client.close()
            return telext.ConversationHandler.END

async def user_charge_acc_inputed_image(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    print("in user_charge_acc_inputed")
    try:
        db_client = connect_to_database(secrets['DBConString'])
    except Exception:
        print("Failed to connect to the database!")

    if not await check_subscription(update):
        main_channel = db_client[secrets['DBName']].orgs.find_one({'name': 'main'})['channel']['link']
        reply_text = client_functions_texts('join_channel') + f"\n\n{main_channel}"
        await update.effective_message.reply_text(reply_text)
        db_client.close()
        return telext.ConversationHandler.END
    else:
            user_dict = db_client[secrets['DBName']].users.find_one({'user_id': int(update.effective_chat.id)})
            if user_dict is None:
                reply_text = client_functions_texts("user_not_found")
                await update.effective_message.reply_text(reply_text)
            else:
                user_obj = db_client[secrets['DBName']].users.find_one({'user_id': update.effective_user.id}, {"orgs": { "$slice": 1 }})
                org_name = list(user_obj["orgs"].keys())[0]
                org_obj = db_client[secrets['DBName']].orgs.find_one({'name': org_name})
                keyboard = [
                        [telegram.InlineKeyboardButton('❌ Reject', callback_data='Reject'),telegram.InlineKeyboardButton('✅ Accept', callback_data='Accept')]
                    ]
                context.user_data["payment_receipt"] = update.effective_message.text
                reply_markup = telegram.InlineKeyboardMarkup(keyboard)
                context.user_data['payment_receipt'] = f"\n{update.effective_message.text}"
                context.user_data['full_name'] = update.effective_chat.full_name
                context.user_data['username'] = update.effective_chat.username
                context.user_data['user_id'] = update.effective_chat.id
                context.user_data['org']=org_name
                context.user_data['pay_amount'] = org_obj['payment_options']['currencies']['rial']['plans'][context.user_data['plan']]
                await context.bot.send_photo(
                    chat_id=org_obj['ticketing_group_id'],
                    photo=update.message.photo[0].file_id,
                    caption=
                        f"Recharg\n"+
                        f"payment_method:{context.user_data['payment_method']}\n" +
                        (f"username:@{context.user_data['username']}\n" if(context.user_data['username'] is not None) else "") +
                        f"user_id:{context.user_data['user_id']}\nfull_name:{context.user_data['full_name']}\n" +
                        f"Plan:{context.user_data['plan']}\n" +
                        f"org:{context.user_data['org']}\n"+
                        f"pay_amount:{context.user_data['pay_amount']}, included {100-100*context.user_data['discount']}% discount\n"
                        f"currency:rial\n",
                    reply_to_message_id= secrets['test_topic_id'] if secrets["DBName"].lower() == "rhvp-test" else secrets['payments_topic_id'],
                    reply_markup=reply_markup
                )
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=client_functions_texts("thanks_for_payment")
                    )
            db_client.close()
            return telext.ConversationHandler.END

async def user_charge_rial_inputed_document(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    print("in user_charge_rial_inputed_document")
    try:
        db_client = connect_to_database(secrets['DBConString'])
    except Exception:
        print("Failed to connect to the database!")

    if not await check_subscription(update):
        main_channel = db_client[secrets['DBName']].orgs.find_one(
            {'name': 'main'}
        )['channel']['link']
        reply_text = client_functions_texts('join_channel') + f"\n\n{main_channel}"
        await update.effective_message.reply_text(reply_text)
        db_client.close()
        return telext.ConversationHandler.END
    else:
        user_dict = db_client[secrets['DBName']].users.find_one(
            {'user_id': int(update.effective_chat.id)}
        )
        if user_dict is None:
            reply_text = client_functions_texts("user_not_found")
            await update.effective_message.reply_text(reply_text)
        else:
            user_obj = db_client[secrets['DBName']].users.find_one(
                {'user_id': update.effective_user.id}, {"orgs": {"$slice": 1}}
            )
            org_name = list(user_obj["orgs"].keys())[0]
            org_obj = db_client[secrets['DBName']].orgs.find_one(
                {'name': org_name}
            )
            keyboard = [
                [
                    telegram.InlineKeyboardButton('❌ Reject', callback_data='Reject'),
                    telegram.InlineKeyboardButton('✅ Accept', callback_data='Accept')
                ]
            ]
            context.user_data["payment_receipt"] = update.effective_message.text
            reply_markup = telegram.InlineKeyboardMarkup(keyboard)
            context.user_data['payment_receipt'] = f"\n{update.effective_message.text}"
            context.user_data['full_name'] = update.effective_chat.full_name
            context.user_data['username'] = update.effective_chat.username
            context.user_data['user_id'] = update.effective_chat.id
            context.user_data['org'] = org_name
            context.user_data['pay_amount'] = (
                org_obj['payment_options']['currencies']['rial']['plans'][
                    context.user_data['plan']
                ]
            )
            white_listed = [
                432080595, 97994343, 60256430, 92294065, 94307276,
                734823458, 128188905, 1403568736
            ]
            white_message = (
                "\n⚠️⚠️⚠️⚠️ WHITE LISTED ID⚠️⚠️⚠️⚠️"
                if context.user_data['user_id'] in white_listed else ""
            )
            await context.bot.send_document(
                chat_id=org_obj['ticketing_group_id'],
                document=update.message.document.file_id,
                caption=(
                    f"Recharg\n"
                    f"payment_method:{context.user_data['payment_method']}\n"
                    + (
                        f"username:@{context.user_data['username']}\n"
                        if context.user_data['username'] is not None else ""
                    )
                    + f"user_id:{context.user_data['user_id']}\n"
                    + f"full_name:{context.user_data['full_name']}\n"
                    + f"Plan:{context.user_data['plan']}\n"
                    + f"org:{context.user_data['org']}\n"
                    + (
                        f"pay_amount:{context.user_data['pay_amount']}, included "
                        f"{100-100*context.user_data['discount']}% discount\n"
                    )
                    + f"currency:rial\n"
                    + f"{white_message}"
                ),
                reply_to_message_id=(
                    secrets['test_topic_id']
                    if secrets["DBName"].lower() == "rhvp-test"
                    else secrets['payments_topic_id']
                ),
                reply_markup=reply_markup
            )
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=client_functions_texts("thanks_for_payment")
            )
        db_client.close()
        return telext.ConversationHandler.END
