import telegram
import telegram.ext as telext
import secrets as sc
import requests
from helpers.initial import get_secrets_config, set_lang, connect_to_database
from helpers.bot_functions import after_automatic_payment, check_subscription
from helpers.states import (
    PAID, NEWUSER_PURCHASE_RIAL_INPUTED,
    NEWUSER_PURCHASE_RIAL_ZARIN
)

(secrets, Config) = get_secrets_config()
# Removed global client_functions_texts


async def check_payment(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    try:
        url = "https://api.zarinpal.com/pg/v4/payment/verify.json"
        payload = {
            "merchant_id": context.user_data['merchant_id'],
            "amount": int(context.user_data['pay_amount'])*10000,
            "authority": context.user_data['authority']
        }
        headers = {
            "accept": "application/json",
            "content-type": "application/json"
        }
        response = requests.request("POST", url, json=payload, headers=headers).json()
        if response['data']['code'] == 100 or response['data']['code'] == 101:
            context.user_data['payment_receipt'] = response['data']['ref_id']
            await after_automatic_payment(update, context)
        else:
            print('else payment error')
            await update.effective_message.reply_text(client_functions_texts("not_yet_verified_payment"))
    except Exception as e:
        print('else payment error', e)
        await update.effective_message.reply_text(client_functions_texts("not_yet_verified_payment"))
    return PAID


async def payment(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [telegram.InlineKeyboardButton('💰 Paid', callback_data='Paid')],
    ]
    reply_markup = telegram.InlineKeyboardMarkup(keyboard)
    url = 'https://www.zarinpal.com/pg/StartPay/' + context.user_data['authority']
    reply_text = f'{url}'
    await update.effective_message.edit_text(
        reply_text,
        reply_markup=reply_markup,
        parse_mode=telegram.constants.ParseMode.MARKDOWN
    )
    return PAID


async def newuser_purchase_rial(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
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
    if 'plan' not in context.user_data:
        context.user_data['plan'] = query.data['plan']
    user_dict = db_client[secrets['DBName']].users.find_one({'user_id': int(update.effective_chat.id)})
    context.user_data['user_dict'] = user_dict
    if ('discount' in user_dict and user_dict['discount']):
        discount = (100-user_dict['discount']) / 100
    else:
        discount = 1
    context.user_data['discount'] = discount

    org_obj = db_client[secrets['DBName']].orgs.find_one({'name': context.user_data['org']})
    context.user_data['pay_amount'] = org_obj['payment_options']['currencies']['rial']['plans'][context.user_data['plan']]
    context.user_data['is_new_user'] = True
    context.user_data['payment_type'] = 'rial'

    if not await check_subscription(update):
        main_channel = db_client[secrets['DBName']].orgs.find_one({'name': 'main'})['channel']['link']
        reply_text = client_functions_texts('join_channel') + f"\n\n{main_channel}"
        await update.effective_message.edit_text(reply_text)
        db_client.close()
        return telext.ConversationHandler.END

    context.user_data['payment_method'] = org_obj['payment_options']['currencies']['rial']['method']

    if context.user_data['payment_method'] == 'e-transfer':
        reply_text = client_functions_texts("selected_plan") + f': {query.data["plan"]} Pack\n' + client_functions_texts("transaction_receipt") + ":"
        if "card_number" in org_obj['payment_options']['currencies']['rial'] and org_obj['payment_options']['currencies']['rial']['card_number'] != "":
            reply_text += '\n\n' + client_functions_texts("card_number") + f': `{org_obj["payment_options"]["currencies"]["rial"]["card_number"]}`'
        reply_text += '\n\n' + client_functions_texts("cancel_to_abort")
        keyboard = [
            [telegram.InlineKeyboardButton(client_functions_texts("general_cancel"), callback_data='Cancel')]
        ]
        reply_markup = telegram.InlineKeyboardMarkup(keyboard)
        await update.effective_message.edit_text(reply_text, reply_markup=reply_markup, parse_mode=telegram.constants.ParseMode.MARKDOWN)
        db_client.close()
        return NEWUSER_PURCHASE_RIAL_INPUTED
    else:
        reply_text = client_functions_texts("selected_plan") + f': {query.data["plan"]} Pack\n' + client_functions_texts("zarinpal_message") + ':\n\n' + client_functions_texts('cancel_to_abort')
        context.user_data['merchant_id'] = org_obj['payment_options']['currencies']['rial']['merchant_id']
        secret_url = sc.token_urlsafe()
        url = "https://api.zarinpal.com/pg/v4/payment/request.json"
        payload = {
            "merchant_id": context.user_data['merchant_id'],
            "amount": int(context.user_data['pay_amount'])*10000,
            "callback_url": "http://t.me/"+secrets["BOT_USERNAME"],
            "description": "خرید پلن"+query.data['plan'],
        }
        headers = {
            "accept": "application/json",
            "content-type": "application/json"
        }
        response = requests.request("POST", url, json=payload, headers=headers).json()
        context.user_data['authority'] = response['data']['authority']
        context.user_data['secret_url'] = secret_url
        keyboard = [
            [telegram.InlineKeyboardButton(client_functions_texts("pay_now"), callback_data='Pay now')],
            [telegram.InlineKeyboardButton(client_functions_texts("general_cancel"), callback_data='Cancel')]
        ]
        reply_markup = telegram.InlineKeyboardMarkup(keyboard)
        await update.effective_message.edit_text(reply_text, reply_markup=reply_markup, parse_mode=telegram.constants.ParseMode.MARKDOWN)
        db_client.close()
        return NEWUSER_PURCHASE_RIAL_ZARIN


async def newuser_purchase_rial_inputed(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
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
            org_obj = db_client[secrets['DBName']].orgs.find_one({'name': context.user_data['org']})
            context.user_data["payment_receipt"] = update.effective_message.text
            keyboard = [
                [telegram.InlineKeyboardButton('❌ Reject', callback_data='Reject'), telegram.InlineKeyboardButton('✅ Accept', callback_data='Accept')]
            ]
            reply_markup = telegram.InlineKeyboardMarkup(keyboard)
            await context.bot.send_message(
                chat_id=org_obj['ticketing_group_id'],
                text=(
                    "Payment\n" +
                    f"payment_method:{context.user_data['payment_method']}\n" +
                    (f"username:@{context.user_data['username']}\n" if (context.user_data['username'] is not None) else "") +
                    f"user_id:{context.user_data['user_id']}\nfull_name:{context.user_data['full_name']}\n" +
                    f"Plan:{context.user_data['plan']}\n" +
                    f"org:{context.user_data['org']}\n" +
                    f"pay_amount:{context.user_data['pay_amount']}, included {100-100*context.user_data['discount']}% discount\n" +
                    "currency:rial\n" +
                    "-------------------------\n" +
                    context.user_data['payment_receipt']
                ),
                reply_to_message_id=secrets['test_topic_id'] if secrets["DBName"].lower() == "rhvp-test" else secrets['payments_topic_id'],
                reply_markup=reply_markup
            )
            try:
                await update.effective_message.edit_text(client_functions_texts("thanks_for_payment"))
            except Exception:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=client_functions_texts("thanks_for_payment")
                )
        db_client.close()
        return telext.ConversationHandler.END


async def newuser_purchase_rial_inputed_image(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
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
            org_obj = db_client[secrets['DBName']].orgs.find_one({'name': context.user_data['org']})
            keyboard = [
                [telegram.InlineKeyboardButton('❌ Reject', callback_data='Reject'), telegram.InlineKeyboardButton('✅ Accept', callback_data='Accept')]
            ]
            context.user_data["payment_receipt"] = update.effective_message.text
            reply_markup = telegram.InlineKeyboardMarkup(keyboard)
            await context.bot.send_photo(
                chat_id=org_obj['ticketing_group_id'],
                photo=update.message.photo[0].file_id,
                caption=(
                    "Payment\n" +
                    f"payment_method:{context.user_data['payment_method']}\n" +
                    (f"username:@{context.user_data['username']}\n" if (context.user_data['username'] is not None) else "") +
                    f"user_id:{context.user_data['user_id']}\nfull_name:{context.user_data['full_name']}\n" +
                    f"Plan:{context.user_data['plan']}\n" +
                    f"org:{context.user_data['org']}\n" +
                    f"pay_amount:{context.user_data['pay_amount']}, included {100-100*context.user_data['discount']}% discount\n" +
                    "currency:rial\n"
                ),
                reply_to_message_id=secrets['test_topic_id'] if secrets["DBName"].lower() == "rhvp-test" else secrets['payments_topic_id'],
                reply_markup=reply_markup
            )
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=client_functions_texts("thanks_for_payment")
            )
        db_client.close()
        return telext.ConversationHandler.END


async def newuser_purchase_rial_inputed_document(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
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
            org_obj = db_client[secrets['DBName']].orgs.find_one({'name': context.user_data['org']})
            keyboard = [
                [telegram.InlineKeyboardButton('❌ Reject', callback_data='Reject'), telegram.InlineKeyboardButton('✅ Accept', callback_data='Accept')]
            ]
            context.user_data["payment_receipt"] = update.effective_message.text
            reply_markup = telegram.InlineKeyboardMarkup(keyboard)
            await context.bot.send_document(
                chat_id=org_obj['ticketing_group_id'],
                document=update.message.document.file_id,
                caption=(
                    "Payment\n" +
                    f"payment_method:{context.user_data['payment_method']}\n" +
                    (f"username:@{context.user_data['username']}\n" if (context.user_data['username'] is not None) else "") +
                    f"user_id:{context.user_data['user_id']}\nfull_name:{context.user_data['full_name']}\n" +
                    f"Plan:{context.user_data['plan']}\n" +
                    f"org:{context.user_data['org']}\n" +
                    f"pay_amount:{context.user_data['pay_amount']}, included {100-100*context.user_data['discount']}% discount\n" +
                    "currency:rial\n"
                ),
                reply_to_message_id=secrets['test_topic_id'] if secrets["DBName"].lower() == "rhvp-test" else secrets['payments_topic_id'],
                reply_markup=reply_markup
            )
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=client_functions_texts("thanks_for_payment")
            )
        db_client.close()
        return telext.ConversationHandler.END 