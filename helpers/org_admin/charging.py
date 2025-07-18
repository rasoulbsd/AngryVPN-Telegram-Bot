import telegram
import telegram.ext as telext
import datetime
import uuid
import pandas as pd
from ..initial import connect_to_database, get_secrets_config, set_lang
from ..bot_functions import check_subscription
import helpers.xuiAPI as xAPI
from helpers.states import (
    ADMIN_CHARGE_ACCOUNT_USERID, ADMIN_CHARGE_ACCOUNT_FINAL,
    ADMIN_CHARGE_ALL_ACCOUNTS, ADMIN_CHARGE_ALL_ACCOUNTS_AMOUNT,
    ACCEPT, REJECT_CHECK, RESUBMMIT
)
import numpy as np
import time
import re

(secrets, Config) = get_secrets_config()


# async def admin_charge_account(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
#     try:
#         db_client = connect_to_database(secrets['DBConString'])
#     except Exception:
#         print("Failed to connect to the database!")

#     # Dynamic language for admin
#     user_dict = db_client[secrets['DBName']].users.find_one({'user_id': update.effective_user.id})
#     user_lang = user_dict.get('lang', Config['default_language']) if user_dict else Config['default_language']
#     org_admin_texts = set_lang(user_lang, 'org_admin')

#     query = update.callback_query
#     await query.answer()
#     if query.data == 'Cancel':
#         db_client.close()
#         return telext.ConversationHandler.END

#     if not await check_subscription(update):
#         main_channel = db_client[secrets['DBName']].orgs.find_one({'name': 'main'})['channel']['link']
#         reply_text = org_admin_texts('join_channel') + f'\n\n{main_channel}'
#         await update.effective_message.edit_text(reply_text)
#         db_client.close()
#         return telext.ConversationHandler.END

#     selected_org = query.data['org']

#     if selected_org not in db_client[secrets['DBName']].admins.find_one({'user_id': update.effective_user.id})['orgs']:
#         reply_text = "Unathorized! Also, How are you here?"
#         await update.effective_message.edit_text(reply_text)
#         db_client.close()
#         return telext.ConversationHandler.END
#     else:
#         reply_text = "Please select the server with:\n\nClick cancel to abort."
#         context.user_data['org'] = selected_org
#         server_names = db_client[secrets['DBName']].servers.find(
#             filter={
#                 'org': selected_org, 
#                 "$or": [
#                     {'isActive': {"$exists": True, "$eq": True}},
#                     {"isActive": {"$exists": False}}
#                 ]
#             },
#             projection={'name': True}
#         )
#         keyboard = [
#             [telegram.InlineKeyboardButton(s['name'], callback_data=s['name'])] for s in server_names
#         ] + [
#             [telegram.InlineKeyboardButton('❌ Cancel', callback_data='Cancel')]
#         ]
#         reply_markup = telegram.InlineKeyboardMarkup(keyboard)
#         await update.effective_message.edit_text(reply_text, reply_markup=reply_markup, parse_mode=telegram.constants.ParseMode.MARKDOWN)
#         db_client.close()
#         return ADMIN_CHARGE_ACCOUNT_USERID


async def admin_charge_account(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == 'Cancel':
        return telext.ConversationHandler.END

    context.user_data['selected_org'] = query.data['org']

    reply_text = "Please send the unique user id account you want to charge and the amount. Example:\n\n8475837: 5\n\nClick cancel to abort."

    keyboard = [
        [telegram.InlineKeyboardButton('❌ Cancel', callback_data='Cancel')]
    ]
    reply_markup = telegram.InlineKeyboardMarkup(keyboard)
    await update.effective_message.edit_text(reply_text, reply_markup=reply_markup, parse_mode=telegram.constants.ParseMode.MARKDOWN)
    return ADMIN_CHARGE_ACCOUNT_FINAL


async def admin_charge_account_with_userid_and_amount(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    try:
        db_client = connect_to_database(secrets['DBConString'])
    except Exception:
        print("Failed to connect to the database!")

    # Dynamic language for admin
    user_dict = db_client[secrets['DBName']].users.find_one({'user_id': update.effective_user.id})
    user_lang = user_dict.get('lang', Config['default_language']) if user_dict else Config['default_language']
    org_admin_texts = set_lang(user_lang, 'org_admin')
    selected_org = context.user_data['selected_org']

    user_org = db_client[secrets['DBName']].orgs.find_one({'name': selected_org})
    if 'rial' in user_org['payment_options']['currencies']:
        currency = 'rial'
        currency_symbol = 'T'
    elif 'cad' in user_org['payment_options']['currencies']:
        currency = 'cad'
        currency_symbol = 'CAD'
    else:
        print("Not Implemented")
        raise EOFError

    if not await check_subscription(update):
        main_channel = db_client[secrets['DBName']].orgs.find_one({'name': 'main'})['channel']['link']
        reply_text = org_admin_texts('join_channel') + f'\n\n{main_channel}'
        await update.effective_message.reply_text(reply_text)
        db_client.close()
        return telext.ConversationHandler.END

    user_id = int(update.effective_message.text.split(":")[0])
    charge_amount = int(update.effective_message.text.split(":")[1])

    if selected_org not in db_client[secrets['DBName']].admins.find_one({'user_id': update.effective_user.id})['orgs']:
        reply_text = "Unathorized! Also, How are you here?"
        await update.effective_message.reply_text(reply_text)
        db_client.close()
        return telext.ConversationHandler.END

    if selected_org not in db_client[secrets['DBName']].users.find_one({'user_id': user_id})['orgs']:
        reply_text = "User does not exist in this organization!"
        await update.effective_message.reply_text(reply_text)
        db_client.close()
        return telext.ConversationHandler.END
    else:
        user_user_dict = db_client[secrets['DBName']].users.find_one({'user_id': update.effective_user.id})

        user_user_dict['wallet'] += float(charge_amount)

        tr_verification_data = {
            "user_id": user_id,
            "org": selected_org,
            "plan": '',
            "payment_type": 'Manual',
            "payment_method": 'Manual',
            "amount": charge_amount,
            "payment_receipt": f"Manual by admin: {update.effective_chat.id}",
            "admin": update.effective_chat.id,
            "prev_wallet": user_user_dict['wallet'],
            "new_wallet": user_user_dict['wallet'] + float(charge_amount),
            "date": datetime.datetime.now().isoformat(),
            "verified": True,
            "failed": False
        }

        _ = (db_client[secrets['DBName']].payments.insert_one(tr_verification_data)).inserted_id

        user_org_admin_texts = set_lang(user_user_dict.get('lang', Config['default_language']), 'org_admin')
        try:
            await context.bot.send_message(
                chat_id=user_dict['user_id'],
                text=user_org_admin_texts("account_charged_for") +
                    f' {charge_amount} ' + user_org_admin_texts(currency_symbol) +
                    '!\n\n' + user_org_admin_texts("new_limit") +
                    f': {tr_verification_data["new_wallet"]} ' +
                    user_org_admin_texts(currency_symbol)
            )

            await context.bot.send_message(
                chat_id=update.effective_user.id,
                text=f"The account with userid {user_id} has been charged for {charge_amount} " + org_admin_texts(currency_symbol) + "!"
            )
        except Exception as err:
            await context.bot.send_message(
                chat_id=update.effective_user.id,
                text=f"An error occured: {err.message}"
            )

        db_client.close()
        return telext.ConversationHandler.END


# async def admin_charge_all_accounts(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
#     try:
#         db_client = connect_to_database(secrets['DBConString'])
#     except Exception:
#         print("Failed to connect to the database!")

#     # Dynamic language for admin
#     user_dict = db_client[secrets['DBName']].users.find_one({'user_id': update.effective_user.id})
#     user_lang = user_dict.get('lang', Config['default_language']) if user_dict else Config['default_language']
#     org_admin_texts = set_lang(user_lang, 'org_admin')

#     query = update.callback_query
#     await query.answer()
#     if query.data == 'Cancel':
#         db_client.close()
#         return telext.ConversationHandler.END

#     if not await check_subscription(update):
#         main_channel = db_client[secrets['DBName']].orgs.find_one({'name': 'main'})['channel']['link']
#         reply_text = org_admin_texts('join_channel') + f'\n\n{main_channel}'
#         await update.effective_message.edit_text(reply_text)
#         db_client.close()
#         return telext.ConversationHandler.END
#     selected_org = query.data['org']
#     if selected_org not in db_client[secrets['DBName']].admins.find_one({'user_id': update.effective_user.id})['orgs']:
#         reply_text = "Unathorized! Also, How are you here?"
#         await update.effective_message.edit_text(reply_text)
#         db_client.close()
#         return telext.ConversationHandler.END
#     else:
#         reply_text = "Please select the server:\n\nClick cancel to abort."
#         context.user_data['org'] = selected_org
#         server_names = db_client[secrets['DBName']].servers.find(
#             filter={'org': selected_org, "$or": [
#                 {'isActive': {"$exists": True, "$eq": True}},
#                 {"isActive": {"$exists": False}}
#             ]}, 
#             projection={'name': True}
#         )
#         keyboard = [
#             [telegram.InlineKeyboardButton(s['name'], callback_data=s['name'])] for s in server_names
#         ] + [
#             [telegram.InlineKeyboardButton('❌ Cancel', callback_data='Cancel')]
#         ]
#         reply_markup = telegram.InlineKeyboardMarkup(keyboard)
#         await update.effective_message.edit_text(reply_text, reply_markup=reply_markup, parse_mode=telegram.constants.ParseMode.MARKDOWN)
#         db_client.close()
#         return ADMIN_CHARGE_ALL_ACCOUNTS


async def admin_charge_all_accounts(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == 'Cancel':
        return telext.ConversationHandler.END

    query = update.callback_query
    context.user_data['org'] = query.data['org']

    reply_text = "Please send the amount you want to charge:\nExample: 5\n\nClick cancel to abort."

    keyboard = [
        [telegram.InlineKeyboardButton('❌ Cancel', callback_data='Cancel')]
    ]
    reply_markup = telegram.InlineKeyboardMarkup(keyboard)
    await update.effective_message.edit_text(reply_text, reply_markup=reply_markup, parse_mode=telegram.constants.ParseMode.MARKDOWN)
    return ADMIN_CHARGE_ALL_ACCOUNTS_AMOUNT


async def admin_charge_all_accounts_inputed(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    try:
        db_client = connect_to_database(secrets['DBConString'])
    except Exception:
        print("Failed to connect to the database!")

    # Dynamic language for admin
    user_dict = db_client[secrets['DBName']].users.find_one({'user_id': update.effective_user.id})
    user_lang = user_dict.get('lang', Config['default_language']) if user_dict else Config['default_language']
    org_admin_texts = set_lang(user_lang, 'org_admin')

    selected_org = context.user_data['org']

    user_org = db_client[secrets['DBName']].orgs.find_one({'name': selected_org})
    if 'rial' in user_org['payment_options']['currencies']:
        currency = 'rial'
        currency_symbol = 'T'
    elif 'cad' in user_org['payment_options']['currencies']:
        currency = 'cad'
        currency_symbol = 'CAD'
    else:
        print("Not Implemented")
        raise EOFError

    if not await check_subscription(update):
        main_channel = db_client[secrets['DBName']].orgs.find_one({'name': 'main'})['channel']['link']
        reply_text = org_admin_texts('join_channel') + f'\n\n{main_channel}'
        await update.effective_message.reply_text(reply_text)
        db_client.close()
        return telext.ConversationHandler.END

    if selected_org not in db_client[secrets['DBName']].admins.find_one({'user_id': update.effective_user.id})['orgs']:
        reply_text = "Unathorized! Also, How are you here?"
        await update.effective_message.reply_text(reply_text)
        db_client.close()
        return telext.ConversationHandler.END
    else:
        user_ids = db_client[secrets['DBName']].users.find(
            filter={
                f"orgs.{selected_org}": {'$exists': True}
            }
        )

        count = 0
        failed_users = []
        for user_obj in user_ids:
            count += 1
            charge_amount = int(update.effective_message.text)
            user_obj['wallet'] += float(charge_amount)

            tr_verification_data = {
                "user_id": user_obj['user_id'],
                "org": selected_org,
                "plan": '',
                "payment_type": 'Charge All',
                "payment_method": 'Charge All',
                "amount": charge_amount,
                "payment_receipt": f"Charge All by admin: {update.effective_chat.id}",
                "admin": update.effective_chat.id,
                "prev_wallet": user_obj['wallet'],
                "new_wallet": user_obj['wallet'] + float(charge_amount),
                "date": datetime.datetime.now().isoformat(),
                "verified": True,
                "failed": False
            }

            _ = (db_client[secrets['DBName']].payments.insert_one(tr_verification_data)).inserted_id

            user_org_admin_texts = set_lang(user_obj.get('lang', Config['default_language']), 'org_admin')
            try:
                await context.bot.send_message(
                    chat_id=user_obj['user_id'],
                    text=user_org_admin_texts("account_charged_for") +
                        f' {charge_amount} ' + user_org_admin_texts(currency_symbol) +
                        '!\n\n' + user_org_admin_texts("new_limit") +
                        f': {tr_verification_data["new_wallet"]} ' +
                        user_org_admin_texts(currency_symbol)
                )
            except Exception as err:
                failed_users.append(user_obj['user_id'])
                print(err)

        if count == 0:
            await context.bot.send_message(
                chat_id=update.effective_user.id,
                text="No user found in this organization"
            )
        else:
            await context.bot.send_message(
                chat_id=update.effective_user.id,
                text=f"All account have been charged for {int(update.effective_message.text)} " + org_admin_texts(currency_symbol) + f"!\nNumber of accounts were updadted: {count}"
            )
            if len(failed_users) != 0:
                await context.bot.send_message(
                    chat_id=update.effective_user.id,
                    text=f"Failed Users: {failed_users}"
                )
        db_client.close()
        return telext.ConversationHandler.END


async def accept_receipt(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            # telegram.InlineKeyboardButton('Manualy', callback_data='Manualy'),
            telegram.InlineKeyboardButton('Automatic', callback_data='Automatic')]
    ]
    reply_markup = telegram.InlineKeyboardMarkup(keyboard)

    if update.effective_message.text:
        await update.effective_message.edit_text(
            update.effective_message.text,
            reply_markup=reply_markup
        )
    elif update.effective_message.caption:
        await update.effective_message.edit_caption(
            update.effective_message.caption,
            reply_markup=reply_markup
        )
    return ACCEPT


async def reject_receipt(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    # Dynamic language for admin
    db_client = connect_to_database(secrets['DBConString'])
    user_dict = db_client[secrets['DBName']].users.find_one({'user_id': update.effective_user.id})
    user_lang = user_dict.get('lang', Config['default_language']) if user_dict else Config['default_language']
    org_admin_texts = set_lang(user_lang, 'org_admin')

    keyboard = [
        [telegram.InlineKeyboardButton('❌ Reject', callback_data='Reject_sure'),telegram.InlineKeyboardButton('🔙Back', callback_data='Back')]
    ]
    reply_markup = telegram.InlineKeyboardMarkup(keyboard)
    if update.effective_message.text:
        await update.effective_message.edit_text(
            update.effective_message.text +
            "\n*-------------------------*" +
            "\nAre you sure that you want to reject this? ",
            reply_markup=reply_markup
        )
    elif update.effective_message.caption:
        await update.effective_message.edit_caption(
            update.effective_message.caption +
            "\n*-------------------------*" +
            "\nAre you sure that you want to reject this?",
            reply_markup=reply_markup
        )
    return REJECT_CHECK


async def receipt_back(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    pass


async def receipt_rejected(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    # Dynamic language for admin
    db_client = connect_to_database(secrets['DBConString'])
    user_dict = db_client[secrets['DBName']].users.find_one({'user_id': update.effective_user.id})
    user_lang = user_dict.get('lang', Config['default_language']) if user_dict else Config['default_language']
    org_admin_texts = set_lang(user_lang, 'org_admin')

    credentials = get_user_credentials(update.effective_message)
    text = org_admin_texts('reject_payment')+'\n'+org_admin_texts('contact_support')
    await context.bot.send_message(
        chat_id=credentials['user_id'],
        text=text,
        disable_web_page_preview=True
    )

    await update.effective_message.edit_text(
        update.effective_message.text +
        "\n-------------------------" +
        "\nAdmin rejected : " +
        f"{update.callback_query.from_user.full_name}"
        )
    return telext.ApplicationHandlerStop(telext.ConversationHandler.END)


async def accept_manualy_receipt(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    await update.effective_message.edit_text(
        update.effective_message.text +
        "\n-------------------------" +
        "\nAdmin Accept manualy : " +
        f"{update.callback_query.from_user.full_name}"
    )


def get_user_credentials(effective_message):
    lines = []
    payment_receipt = None
    credentials = {}
    if effective_message.text:
        payment_receipt = effective_message.text.split('-------------------------')[1]
        lines = effective_message.text.splitlines()

    elif effective_message.caption:
        print(f"update.effective_message:{type(effective_message)}")

        if effective_message.document:
            payment_receipt = effective_message.document.file_id
        elif effective_message.photo:
            payment_receipt = effective_message.photo[0].file_id
        print(f"payment_receipt:{payment_receipt}")
        lines = effective_message.caption.splitlines()
    credentials['payment_receipt'] = payment_receipt
    if lines[0] == 'Payment':
        is_new_user = True
    else:
        is_new_user = False
    credentials['is_new_user'] = is_new_user
    for line in lines:
        if 'user_id' in line:
            credentials['user_id'] = int(line.split(':')[1])
        elif 'org' in line:
            credentials['org_name'] = line.split(':')[1]
        elif 'currency' in line:
            credentials['currency'] = line.split(':')[1]
        elif 'Plan' in line:
            credentials['plan'] = line.split(':')[1]
        elif 'pay_amount' in line:
            credentials['pay_amount'] = line.split(':')[1]
        elif 'discount' in line: 
            credentials['discount'] = line.split(':')[1]
    return credentials


async def accept_automatic_receipt(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    try:
        db_client = connect_to_database(secrets['DBConString'])
    except Exception:
        print("Failed to connect to the database!")

    # Dynamic language for admin
    user_dict = db_client[secrets['DBName']].users.find_one({'user_id': update.effective_user.id})
    user_lang = user_dict.get('lang', Config['default_language']) if user_dict else Config['default_language']
    org_admin_texts = set_lang(user_lang, 'org_admin')

    credentials = get_user_credentials(update.effective_message)

    user_dict = db_client[secrets['DBName']].users.find_one({'user_id': credentials["user_id"]})
    server_dicts = list(db_client[secrets['DBName']].servers.find({"org": credentials["org_name"]}))

    if credentials['currency'] == "rial":
        payment_type = "rial"
    elif credentials['currency'] == "cad":
        payment_type = "cad"
    else:
        payment_type = "crypto"

    tr_verification_data = {
        "user_id": credentials['user_id'],
        "org": credentials["org_name"],
        "plan": credentials['plan'],
        "payment_type": payment_type,
        "payment_method": 'e-transfer',
        "amount": int(credentials['pay_amount'].split(',')[0]),
        "discount": user_dict['discount'] if 'discount' in user_dict else 0,
        "payment_receipt": credentials['payment_receipt'],
        "date": datetime.datetime.now().isoformat(),
        "verified": False,
        "failed": False
    }

    tr_db_id = (db_client[secrets['DBName']].payments.insert_one(tr_verification_data)).inserted_id
    context.user_data['tr_db_id'] = tr_db_id

    db_client[secrets['DBName']].users.update_one(
        {
            'user_id': credentials['user_id']
        },
        {
            "$set": {
                f"orgs.{credentials['org_name']}": {"expires": (datetime.datetime.now()+datetime.timedelta(days=62)).isoformat()}
            }
        }
    )

    initial_wallet_amount = user_dict['wallet']

    # Charge wallet
    db_client[secrets['DBName']].users.update_one(
        {
            'user_id': credentials["user_id"]
        },
        {
            "$set": {
                "wallet": float(user_dict['wallet']) + float(credentials['pay_amount'].split(',')[0])
            }
        }
    )
    # Update transaction in DB
    db_client[secrets['DBName']].payments.update_one({'_id': tr_db_id}, { "$set": {"verified": True}})

    hasError = False
    error_message = ''
    keyboard = None
    try:
        if len(server_dicts) > 0:
            user_clients = xAPI.get_clients(server_dicts[0])
            for server_dict in server_dicts:
                select = [f"{user_dict['user_id']}-{server_dict['name']}@{server_dict['rowRemark']}"]
                user_client = user_clients.loc[np.isin(user_clients.index, select)]
                if user_client is None:
                    xAPI.add_client(server_dict, f"{user_dict['user_id']}-{server_dict['name']}", 0, str(uuid.uuid4()))
    except Exception as err:
        hasError = True

        url_match = re.search(r"Max retries exceeded with url: (.+?)\s", str(err))
        failed_url = url_match.group(1) if url_match else "unknown URL"
        host_match = re.search(r"host='([^']+)'", str(err))
        host = host_match.group(1) if host_match else "unknown host"
        error_message = (
            f"\n\nError in checking user's server ({time.strftime('%Y-%m-%d %H:%M:%S')}): "
            f"\nConnection failed to {host}{failed_url}"
        )
        keyboard = [
            [telegram.InlineKeyboardButton('Resubmit ER1', callback_data='Resubmit')]
        ]

    if hasError is False:
        try:
            if initial_wallet_amount < 0 and len(server_dicts) > 0:
                xAPI.unrestrict_user(server_dicts, f"{user_dict['user_id']}")
        except Exception as err:
            hasError = True

            url_match = re.search(r"Max retries exceeded with url: (.+?)\s", str(err))
            failed_url = url_match.group(1) if url_match else "unknown URL"
            host_match = re.search(r"host='([^']+)'", str(err))
            host = host_match.group(1) if host_match else "unknown host"
            error_message = (
                f"\n\nError in unresticting user's server ({time.strftime('%Y-%m-%d %H:%M:%S')}): "
                f"\nConnection failed to {host}{failed_url}"
            )
            keyboard = [
                [telegram.InlineKeyboardButton('Resubmit ER2', callback_data='Resubmit')]
            ]

    if update.effective_message.text:
        await update.effective_message.edit_text(
            update.effective_message.text +
            "\n-------------------------" +
            f"\nAdmin Accept automatically : {update.callback_query.from_user.full_name}" +
            error_message,
            reply_markup=telegram.InlineKeyboardMarkup(keyboard) if hasError else None
        )
    elif update.effective_message.caption:
        await update.effective_message.edit_caption(
            update.effective_message.caption +
            "\n-------------------------" +
            f"\nAdmin Accept automatically : {update.callback_query.from_user.full_name}" +
            error_message,
            reply_markup=telegram.InlineKeyboardMarkup(keyboard) if hasError else None
        )
    if hasError is True:
        db_client[secrets['DBName']].payments.update_one({'_id': tr_db_id}, { "$set": {"failed": True}})
        db_client.close()
        return RESUBMMIT

    org_channel = db_client[secrets['DBName']].orgs.find_one({'name': credentials["org_name"]})['channel']['link']
    if context.user_data['currency'] == 'cad':
        currency_text = f' {float(credentials["pay_amount"].split(",")[0])} ' + org_admin_texts('CAD')
    else:
        currency_text = f' {float(credentials["pay_amount"].split(",")[0]) * 1000} ' + org_admin_texts('T')

    text = org_admin_texts("verified_payment") + '\n' + org_admin_texts("account_charged_for") + currency_text + '!\n'
    if credentials['is_new_user']:
        text += org_admin_texts("after_added_to_org") + f': \n\n{org_channel}\n\n' + org_admin_texts("thanks_joining") + f' *{secrets["DBName"]}* ' + org_admin_texts("group") + ' 🤍️'

    await context.bot.send_message(
        chat_id=credentials['user_id'],
        text=text,
        disable_web_page_preview=True
    )

    db_client.close()
    return telext.ApplicationHandlerStop(telext.ConversationHandler.END)


async def resubmission(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    try:
        db_client = connect_to_database(secrets['DBConString'])
    except Exception:
        print("Failed to connect to the database!")
    credentials = get_user_credentials(update.effective_message)

    # Dynamic language for admin
    user_dict = db_client[secrets['DBName']].users.find_one({'user_id': update.effective_user.id})
    user_lang = user_dict.get('lang', Config['default_language']) if user_dict else Config['default_language']
    org_admin_texts = set_lang(user_lang, 'org_admin')

    user_dict = db_client[secrets['DBName']].users.find_one({'user_id': credentials["user_id"]})
    server_dicts = list(db_client[secrets['DBName']].servers.find({"org": credentials["org_name"]}))

    hasError = False
    error_message = ''
    keyboard = None
    try:
        if len(server_dicts) > 0:
            user_clients = xAPI.get_clients(server_dicts[0])
            for server_dict in server_dicts:
                select = [f"{user_dict['user_id']}-{server_dict['name']}@{server_dict['rowRemark']}"]
                user_client = user_clients.loc[np.isin(user_clients.index, select)]
                if user_client is None:
                    xAPI.add_client(server_dict, f"{user_dict['user_id']}-{server_dict['name']}", 0, str(uuid.uuid4()))
    except Exception as err:
        hasError = True

        url_match = re.search(r"Max retries exceeded with url: (.+?)\s", str(err))
        failed_url = url_match.group(1) if url_match else "unknown URL"
        host_match = re.search(r"host='([^']+)'", str(err))
        host = host_match.group(1) if host_match else "unknown host"
        error_message = (
            f"\n\nError in checking user's server (Resubmited at {time.strftime('%Y-%m-%d %H:%M:%S')})"
            f"\nConnection failed to {host}{failed_url}"
        )
        keyboard = [
            [telegram.InlineKeyboardButton('Resubmit ER1', callback_data='Resubmit')]
        ]

    if hasError is False:
        try:
            xAPI.unrestrict_user(server_dicts, f"{user_dict['user_id']}")
        except Exception as err:
            hasError = True

            url_match = re.search(r"Max retries exceeded with url: (.+?)\s", str(err))
            failed_url = url_match.group(1) if url_match else "unknown URL"
            host_match = re.search(r"host='([^']+)'", str(err))
            host = host_match.group(1) if host_match else "unknown host"
            error_message = (
                f"\n\nError in unresticting user's server (Resubmited at {time.strftime('%Y-%m-%d %H:%M:%S')}): "
                f"\nConnection failed to {host}{failed_url}"
            )
            keyboard = [
                [telegram.InlineKeyboardButton('Resubmit ER2', callback_data='Resubmit')]
            ]

    if keyboard is not None:
        reply_markup = telegram.InlineKeyboardMarkup(keyboard)
    new_block = f"\nAdmin Accept automatically : {update.callback_query.from_user.full_name}" + error_message

    if update.effective_message.text:
        updated_text = replace_last_section(update.effective_message.text, new_block)
        await update.effective_message.edit_text(
            updated_text,
            reply_markup=reply_markup if hasError else None
        )
    elif update.effective_message.caption:
        updated_caption = replace_last_section(update.effective_message.caption, new_block)
        await update.effective_message.edit_caption(
            updated_caption,
            reply_markup=reply_markup if hasError else None
        )

    if hasError is True:
        db_client.close()
        return RESUBMMIT

    db_client[secrets['DBName']].payments.update_one({'_id': context.user_data['tr_db_id']}, { "$set": {"falied": False}})

    org_channel = db_client[secrets['DBName']].orgs.find_one({'name': credentials["org_name"]})['channel']['link']
    if context.user_data['currency'] == 'cad':
        currency_text = f' {float(credentials["pay_amount"].split(",")[0])} ' + org_admin_texts('CAD')
    else:
        currency_text = f' {float(credentials["pay_amount"].split(",")[0]) * 1000} ' + org_admin_texts('T')

    text = org_admin_texts("verified_payment") + '\n' + org_admin_texts("account_charged_for") + currency_text + '!\n'
    if credentials['is_new_user']:
        text += org_admin_texts("after_added_to_org") + f': \n\n{org_channel}\n\n' + org_admin_texts("thanks_joining") + f' *{secrets["DBName"]}* ' + org_admin_texts("group") + ' 🤍️'

    await context.bot.send_message(
        chat_id=credentials['user_id'],
        text=text,
        disable_web_page_preview=True
    )

    db_client.close()
    return telext.ApplicationHandlerStop(telext.ConversationHandler.END)


def replace_last_section(original_text: str, new_block: str) -> str:
    delimiter = "-------------------------"
    parts = original_text.rsplit(delimiter, 1)
    if len(parts) == 2:
        return parts[0] + delimiter + new_block
    else:
        # Delimiter not found; append instead
        return original_text + "\n" + delimiter + new_block
