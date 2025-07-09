"""
Purchase/payment functions for client flows.
"""

import telegram
import telegram.ext as telext
from helpers.initial import get_secrets_config, set_lang, connect_to_database
from helpers.bot_functions import after_automatic_payment, check_subscription
from helpers.states import (
    PAID, NEWUSER_PURCHASE_SELECT_PLAN, NEWUSER_PURCHASE_RIAL,
    NUEWUSER_PURCHASE_RECEIPT_CRYPTO, NEWUSER_PURCHASE_INTERCEPTOR,
    NEWUSER_PURCHASE_INTERCEPTOR_INPUTED, NEWUSER_PURCHASE_RIAL_INPUTED,
    NEWUSER_PURCHASE_RIAL_ZARIN
)
import secrets as sc
import requests

(secrets, Config) = get_secrets_config()
client_functions_texts = set_lang(Config['default_language'], 'client_functions')

# --- Begin moved purchase functions ---

# (Function bodies pasted here)

async def check_payment(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    # keyboard = [
    #     [telegram.InlineKeyboardButton('💰 Paid', callback_data='Paid')],
    #     [telegram.InlineKeyboardButton(client_functions_texts("general_cancel"), callback_data='Cancel')]
    # ]
    # reply_markup = telegram.InlineKeyboardMarkup(keyboard)
    # Send message with text and appended InlineKeyboard
    # url='https://www.zarinpal.com/pg/StartPay/'+context.user_data['authority']
    # reply_text='''
    # Pay from below link and click paid after that:\n
    # '''+url
    try :
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
        # charge_amount=context.user_data['charge_amount']
        # print(response)
        # if (response['errors']):
        #     # throw error
        #     raise Exception(response['errors'])
        if response['data']['code']==100 or response['data']['code']==101:
        # if True:
            # await update.effective_message.reply_text(f"✅ Your payment was verfied!\nThe account has been charged for {charge_amount} GB!\n")

            context.user_data['payment_receipt']=response['data']['ref_id']
            # context.user_data['payment_receipt']=''
            await after_automatic_payment(update, context)
        else:
            print('else payment error')
            await update.effective_message.reply_text(client_functions_texts("not_yet_verified_payment"))
    except Exception as e:
        print('else payment error' ,e)
        print(e)
        await update.effective_message.reply_text(client_functions_texts("not_yet_verified_payment"))
    # await update.effective_message.edit_text(reply_text, reply_markup=reply_markup, parse_mode=telegram.constants.ParseMode.MARKDOWN)

    # print(update.message.text)

    return PAID

async def payment(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [telegram.InlineKeyboardButton('💰 Paid', callback_data='Paid')],
        # [telegram.InlineKeyboardButton(client_functions_texts("general_cancel"), callback_data='Cancel')]
    ]
    reply_markup = telegram.InlineKeyboardMarkup(keyboard)
    # Send message with text and appended InlineKeyboard
    url = 'https://www.zarinpal.com/pg/StartPay/' + context.user_data['authority']
    reply_text = f'{url}'
    await update.effective_message.edit_text(
        reply_text,
        reply_markup=reply_markup,
        parse_mode=telegram.constants.ParseMode.MARKDOWN
    )
    return PAID

async def newuser_purchase(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
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
        # application.add_handler(menu_handler)

        db_client.close()

        return telext.ConversationHandler.END
    # selected_org = query.data['org']
    # if selected_org not in db_client[secrets['DBName']].admins.find_one({'user_id': update.effective_user.id})['orgs']:
    #     reply_text = "Unathorized! Also, How are you here?"
    #     await update.effective_message.edit_text(reply_text)

    #     db_client.close()

    #     return telext.ConversationHandler.END
    # else:
    context.user_data['menu'] = update.effective_message
    context.user_data['chat'] = update.effective_chat
    context.user_data['full_name'] = update.effective_chat.full_name
    context.user_data['username'] = update.effective_chat.username
    context.user_data['user_id'] = update.effective_chat.id
    
    reply_text = client_functions_texts("referal_code") + "\n\n" + client_functions_texts("cancel_to_abort") 
    # context.user_data['org'] = selected_org
    keyboard = [
        [telegram.InlineKeyboardButton(client_functions_texts("general_cancel"), callback_data='Cancel')]
    ]
    reply_markup = telegram.InlineKeyboardMarkup(keyboard)
    # Send message with text and appended InlineKeyboard
    await update.effective_message.edit_text(reply_text, reply_markup=reply_markup, parse_mode=telegram.constants.ParseMode.MARKDOWN)

    db_client.close()

    return NEWUSER_PURCHASE_SELECT_PLAN

async def newuser_purchase_select_plan(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    try:
        db_client = connect_to_database(secrets['DBConString'])
    except Exception:
        print("Failed to connect to the database!")

    if not await check_subscription(update):
        main_channel = db_client[secrets['DBName']].orgs.find_one({'name': 'main'})['channel']['link']
        reply_text = client_functions_texts('join_channel') + f"\n\n{main_channel}"
        await update.effective_message.edit_text(reply_text)
        # application.add_handler(menu_handler)

        db_client.close()

        return telext.ConversationHandler.END
    # selected_org = query.data['org']
    # if selected_org not in db_client[secrets['DBName']].admins.find_one({'user_id': update.effective_user.id})['orgs']:
    #     reply_text = "Unathorized! Also, How are you here?"
    #     await update.effective_message.edit_text(reply_text)

    #     db_client.close()

    #     return telext.ConversationHandler.END
    # else:

    org = db_client[secrets['DBName']].orgs.find_one({'referral_code': update.effective_message.text})
    if org is None:
        reply_text = "The referral code is not valid!"
        await context.user_data['menu'].edit_text(reply_text)

        db_client.close()

        return telext.ConversationHandler.END
    context.user_data['org'] = org['name']
    # user_dict = db_client[secrets['DBName']].users.find_one({'user_id': int(update.effective_chat.id)})

    reply_text = client_functions_texts("choose_plan") + "\n\n" + client_functions_texts("cancel_to_abort")
    
    user_dict = db_client[secrets['DBName']].users.find_one({'user_id': int(update.effective_chat.id)})
    context.user_data['user_dict'] = user_dict
    if ('discount' in user_dict and user_dict['discount']):
        discount = (100-user_dict['discount']) / 100
    else:
        discount = 1
    context.user_data['discount'] = discount

    keyboard = [
        [telegram.InlineKeyboardButton(f"{plan}: {round(int(org['payment_options']['currencies']['rial']['plans'][plan]) * discount)} T" + (f" ({100-100*discount}% off)" if (100-100*discount != 0) else "")
                                       , callback_data={'plan': plan})] for plan in org['payment_options']['currencies']['rial']['plans']
    ]
    keyboard.extend([[telegram.InlineKeyboardButton(client_functions_texts("general_cancel"), callback_data='Cancel')]])

    reply_markup = telegram.InlineKeyboardMarkup(keyboard)
    # Send message with text and appended InlineKeyboard
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
        if active_methods[0] == 'rial':
            db_client.close()
            return NEWUSER_PURCHASE_RIAL
        elif active_methods[0] == 'tron':
            db_client.close()
            return NUEWUSER_PURCHASE_RECEIPT_CRYPTO
    else:
        db_client.close()
        return NEWUSER_PURCHASE_INTERCEPTOR

async def newuser_purchase_interceptor(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    try:
        db_client = connect_to_database(secrets['DBConString'])
    except Exception:
        print("Failed to connect to the database!")

    if not await check_subscription(update):
        main_channel = db_client[secrets['DBName']].orgs.find_one({'name': 'main'})['channel']['link']
        reply_text = client_functions_texts('join_channel') + f"\n\n{main_channel}"
        await update.effective_message.edit_text(reply_text)
        # application.add_handler(menu_handler)

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
    query = update.callback_query
    await query.answer()
    if query.data == 'Cancel':
        return telext.ConversationHandler.END

    if query.data['method'] == 'rial':
        return NEWUSER_PURCHASE_RIAL
    elif query.data['method'] == 'tron':
        return NUEWUSER_PURCHASE_RECEIPT_CRYPTO

async def newuser_purchase_rial(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
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
        # application.add_handler(menu_handler)

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
        # await update.effective_message.edit_text(reply_text)

        db_client.close()

        return NEWUSER_PURCHASE_RIAL_INPUTED
    else:
        reply_text = client_functions_texts("selected_plan") + f': {query.data["plan"]} Pack\n' + client_functions_texts("zarinpal_message") + ':\n\n' + client_functions_texts('cancel_to_abort')
        context.user_data['merchant_id'] = org_obj['payment_options']['currencies']['rial']['merchant_id']

        # description = u'خرید پلن'+query.data['plan']
        # email=''
        # mobile=''
        secret_url=sc.token_urlsafe()

        url = "https://api.zarinpal.com/pg/v4/payment/request.json"
        payload = {
            "merchant_id": context.user_data['merchant_id'],
            "amount": int(context.user_data['pay_amount'])*10000,
            # "amount": 200000,
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
        # Send message with text and appended InlineKeyboard
        await update.effective_message.edit_text(reply_text, reply_markup=reply_markup, parse_mode=telegram.constants.ParseMode.MARKDOWN)

        db_client.close()

        return NEWUSER_PURCHASE_RIAL_ZARIN

async def newuser_purchase_rial_inputed(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
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
            org_obj = db_client[secrets['DBName']].orgs.find_one({'name': context.user_data['org']})

            context.user_data["payment_receipt"] = update.effective_message.text

            keyboard = [
                [telegram.InlineKeyboardButton('❌ Reject', callback_data='Reject'),telegram.InlineKeyboardButton('✅ Accept', callback_data='Accept')]
            ]

            reply_markup = telegram.InlineKeyboardMarkup(keyboard)

            await context.bot.send_message(
                chat_id=org_obj['ticketing_group_id'],
                text=
                    "Payment\n"+
                    f"payment_method:{context.user_data['payment_method']}\n" +
                    (f"username:@{context.user_data['username']}\n" if(context.user_data['username'] is not None) else "") + 
                    f"user_id:{context.user_data['user_id']}\nfull_name:{context.user_data['full_name']}\n" + 
                    f"Plan:{context.user_data['plan']}\n" +
                    f"org:{context.user_data['org']}\n"+
                    f"pay_amount:{context.user_data['pay_amount']}, included {100-100*context.user_data['discount']}% discount\n"
                    f"currency:rial\n"+
                    "-------------------------\n" +
                    context.user_data['payment_receipt'],
                reply_to_message_id= secrets['test_topic_id'] if secrets["DBName"].lower() == "rhvp-test" else secrets['payments_topic_id'],
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
    print("in user_charge_acc_inputed_image")
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
                [telegram.InlineKeyboardButton('❌ Reject', callback_data='Reject'),telegram.InlineKeyboardButton('✅ Accept', callback_data='Accept')]
            ]
            
            context.user_data["payment_receipt"] = update.effective_message.text

            reply_markup = telegram.InlineKeyboardMarkup(keyboard)

            await context.bot.send_photo(
                chat_id=org_obj['ticketing_group_id'],
                photo=update.message.photo[0].file_id,
                caption=
                    "Payment\n"+
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

async def newuser_purchase_rial_inputed_document(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    print("in user_charge_acc_inputed_document")
    print(f"update.message.document.file_id:{update.message.document.file_id}")
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
                [telegram.InlineKeyboardButton('❌ Reject', callback_data='Reject'),telegram.InlineKeyboardButton('✅ Accept', callback_data='Accept')]
            ]
            
            context.user_data["payment_receipt"] = update.effective_message.text

            reply_markup = telegram.InlineKeyboardMarkup(keyboard)

            await context.bot.send_document(
                chat_id=org_obj['ticketing_group_id'],
                document=update.message.document.file_id,
                caption=
                    "Payment\n"+
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
