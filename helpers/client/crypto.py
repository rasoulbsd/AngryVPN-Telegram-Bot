"""
Crypto/manual purchase functions for client flows.
"""

import telegram
import telegram.ext as telext
import datetime
from helpers.initial import get_secrets_config, connect_to_database, set_lang
from helpers.bot_functions import check_subscription
from helpers.states import NEWUSER_PURCHASE_FINAL, CHECK_TRANS_MANUALLY
from helpers.utils import normalize_transaction_id, validate_transaction, verfiy_transaction
import helpers.xuiAPI as xAPI

(secrets, Config) = get_secrets_config()

# --- Begin moved crypto functions ---

# (Function bodies pasted here)

async def newuser_purchase_receipt_crypto(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    try:
        db_client = connect_to_database(secrets['DBConString'])
    except Exception:
        print("Failed to connect to the database!")

    user_id = update.effective_user.id
    user_dict = db_client[secrets['DBName']].users.find_one({'user_id': user_id})
    user_lang = user_dict.get('lang', Config['default_language']) if user_dict else Config['default_language']
    client_functions_texts = set_lang(user_lang, 'client_functions')

    query = update.callback_query
    # await query.answer()
    if query.data == 'Cancel':
        db_client.close()
        return telext.ConversationHandler.END
    if 'plan' not in context.user_data:
        context.user_data['plan'] = query.data['plan']

    if not await check_subscription(update):
        main_channel = db_client[secrets['DBName']].orgs.find_one(
            {'name': 'main'}
        )['channel']['link']
        reply_text = client_functions_texts('join_channel') + f"\n\n{main_channel}"
        await context.user_data['menu'].edit_text(reply_text)
        db_client.close()
        return telext.ConversationHandler.END

    org_name = context.user_data['org']
    org_obj = db_client[secrets['DBName']].orgs.find_one({'name': org_name})
    context.user_data['wallet'] = org_obj['payment_options']['currencies']['tron']['wallet']
    context.user_data['currency'] = org_obj['payment_options']['currencies']['tron']['currency']
    context.user_data['amount'] = org_obj['payment_options']['currencies']['tron']['plans'][context.user_data['plan']]
    context.user_data['payment_url'] = (
        f"https://weswap.digital/quick/?amount={context.user_data['amount']}&currency="
        f"{context.user_data['currency']}&address={context.user_data['wallet']}"
    )

    print(context.user_data['payment_url'])

    reply_text = client_functions_texts("selected_plan") + f': *{context.user_data["plan"]} Pack*\n\n'
    reply_text += client_functions_texts("send_token") + f' *{context.user_data["amount"]} '
    reply_text += client_functions_texts("tron") + f'({context.user_data["currency"]})* '
    reply_text += client_functions_texts("to_our_wallet") + ' '
    reply_text += f'(`{context.user_data["wallet"]}`) '
    reply_text += client_functions_texts("crypto_wallet_link") + f': \n\n{context.user_data["payment_url"]}\n\n⚠️ '
    reply_text += client_functions_texts("send_transaction_id") + ':\n\n'
    reply_text += client_functions_texts("cancel_to_abort")

    keyboard = [
        [telegram.InlineKeyboardButton(client_functions_texts("general_cancel"), callback_data='Cancel')]
    ]
    reply_markup = telegram.InlineKeyboardMarkup(keyboard)
    await context.user_data['menu'].edit_text(
        reply_text,
        reply_markup=reply_markup,
        parse_mode=telegram.constants.ParseMode.MARKDOWN
    )

    db_client.close()
    return NEWUSER_PURCHASE_FINAL


async def newuser_purchase_receipt_crypto_inputed(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    print("in newuser_purchase_receipt_crypto_inputed")
    try:
        db_client = connect_to_database(secrets['DBConString'])
    except Exception:
        print("Failed to connect to the database!")

    user_id = update.effective_user.id
    user_dict = db_client[secrets['DBName']].users.find_one({'user_id': user_id})
    user_lang = user_dict.get('lang', Config['default_language']) if user_dict else Config['default_language']
    client_functions_texts = set_lang(user_lang, 'client_functions')

    if not await check_subscription(update):
        main_channel = db_client[secrets['DBName']].orgs.find_one(
            {'name': 'main'}
        )['channel']['link']
        reply_text = client_functions_texts('join_channel') + f"\n\n{main_channel}"
        await context.user_data['menu'].reply_text(reply_text)
        db_client.close()
        return telext.ConversationHandler.END
    else:
        user_dict = db_client[secrets['DBName']].users.find_one(
            {'user_id': int(update.effective_chat.id)}
        )
        if user_dict is None:
            reply_text = client_functions_texts("user_not_found")
            await context.user_data['menu'].reply_text(reply_text)
        else:
            org_name = context.user_data['org']
            org_obj = db_client[secrets['DBName']].orgs.find_one({'name': org_name})
            org_ticketing_channel_id = org_obj['ticketing_group_id']
            support_account = org_obj['support_account']

            transaction_id = normalize_transaction_id(update.effective_message.text)
            context.user_data['transaction_id'] = transaction_id

            (tr_isValid, tr_validation_message) = validate_transaction(
                context.user_data['payment_url'],
                transaction_id,
                org_name,
                context.user_data['plan']
            )

            if (transaction_id is False) or (not tr_isValid):
                await context.bot.send_message(
                    chat_id=context.user_data['user_id'],
                    text=tr_validation_message
                )
                db_client.close()
                return telext.ConversationHandler.END

            if context.user_data['currency'] != "rial":
                payment_type = "crypto"
            else:
                payment_type = "rial"

            tr_verification_data = {
                "user_id": context.user_data['user_id'],
                "org": context.user_data['org'],
                "plan": context.user_data['plan'],
                "payment_type": payment_type,
                "currency": context.user_data['currency'],
                "amount": context.user_data['amount'] * context.user_data['discount'],
                "discount": context.user_data['discount'],
                "transactionID": transaction_id,
                "payment_url": context.user_data['payment_url'],
                "date": datetime.datetime.now().isoformat(),
                "verified": False,
                "failed": False
            }

            db_client[secrets['DBName']].payments.insert_one(tr_verification_data)

        await context.bot.send_message(
            chat_id=context.user_data['chat'].id,
            text=client_functions_texts("verify_crypto_manually")
        )

        reply_text = client_functions_texts("verify_crypto_manually2") + ":"
        keyboard = [
            [telegram.InlineKeyboardButton(client_functions_texts("check_crypto_button"), callback_data='Check Manually')]
        ]
        reply_markup = telegram.InlineKeyboardMarkup(keyboard)
        await context.user_data['menu'].edit_text(
            reply_text,
            reply_markup=reply_markup,
            parse_mode=telegram.constants.ParseMode.MARKDOWN
        )

        db_client.close()
        context.user_data['menu'] = update.message
        return CHECK_TRANS_MANUALLY


async def newuser_purchase_crypto_check_manually(update, context):
    try:
        db_client = connect_to_database(secrets['DBConString'])
    except Exception:
        print("Failed to connect to the database!")

    user_id = update.effective_user.id
    user_dict = db_client[secrets['DBName']].users.find_one({'user_id': user_id})
    user_lang = user_dict.get('lang', Config['default_language']) if user_dict else Config['default_language']
    client_functions_texts = set_lang(user_lang, 'client_functions')

    org_name = context.user_data['org']
    org_obj = db_client[secrets['DBName']].orgs.find_one({'name': org_name})
    org_ticketing_channel_id = org_obj['ticketing_group_id']
    tr_obj = db_client[secrets['DBName']].payments.find_one(
        {'transactionID': context.user_data['transaction_id']}
    )
    support_account = org_obj['support_account']

    if tr_obj['verified'] is True:
        await context.bot.send_message(
            chat_id=context.user_data['user_id'],
            text=client_functions_texts("already_verified_crypto_payment")
        )
        db_client.close()
        return telext.ConversationHandler.END

    user_dict = db_client[secrets['DBName']].users.find_one(
        {'user_id': context.user_data['user_id']}
    )

    (tr_isVerfy, tr_verification_message) = await verfiy_transaction(
        context.user_data['transaction_id'],
        context.user_data['amount'],
        context.user_data['wallet'],
        context.user_data['user_id'],
        context.user_data['plan'],
        context.user_data['payment_url']
    )

    if tr_isVerfy is False:
        if tr_verification_message is not None:
            reply_text = client_functions_texts("failed_crypto_transaction") + " \n"
            reply_text += (
                client_functions_texts("error_wrong_trans_id") + '\n'
                if tr_verification_message == "Failed"
                else client_functions_texts("error_wrong_amount") + client_functions_texts("selected_plan") + '.\n'
            )
            reply_text += (
                client_functions_texts("check_trans_manually_2") + f': \nhttps://tronscan.org/#/transaction/{context.user_data["transaction_id"]}\n\n'
            )
            reply_text += client_functions_texts("contact_us_in_advance") + f': {support_account}'

            await context.bot.send_message(
                chat_id=context.user_data['chat'].id,
                text=reply_text,
                disable_web_page_preview=True,
            )
        await context.bot.send_message(
            chat_id=org_ticketing_channel_id,
            text=(
                "❌ Failed Payment from user: \n\n" +
                (f"@{context.user_data['username']} - " if(context.user_data['username'] is not None) else "") +
                f"{context.user_data['user_id']} - {context.user_data['full_name']}" +
                f"\nPlan: {context.user_data['plan']} Pack" +
                "\n-------------------------" +
                (
                    "\nPossibility of wrong transaction ID.\n"
                    if tr_verification_message == "Failed"
                    else "\nPossibility of incorrect amount or destination wallet on this transaction ID and selected plan.\n"
                ) +
                f"\nhttps://tronscan.org/#/transaction/{context.user_data['transaction_id']}"
            ),
            disable_web_page_preview=True,
            reply_to_message_id=secrets['test_topic_id'] if secrets["DBName"].lower() == "rhvp-test" else secrets['payments_topic_id']
        )
        db_client[secrets['DBName']].payments.update_one(
            {'transactionID': context.user_data['transaction_id']},
            {"$set": {"failed": True}}
        )
        db_client.close()
        return telext.ConversationHandler.END
    else:
        server_dict = db_client[secrets['DBName']].servers.find_one({"org": org_name})
        charge_amount = int(org_obj['payment_options']['plans'][context.user_data['plan']])
        user_client = xAPI.get_clients(
            server_dict, select=[f"{user_dict['user_id']}@{server_dict['rowRemark']}"]
        )
        if user_client is None:
            result = xAPI.add_client(
                server_dict, user_dict['user_id'], charge_amount, user_dict['uuid']
            )
        total = xAPI.xui_charge_account(
            server_dict, context.user_data['user_id'], charge_amount, new=True
        )
        db_client[secrets['DBName']].payments.update_one(
            {'transactionID': context.user_data['transaction_id']},
            {"$set": {"verified": True}}
        )
        org_channel = db_client[secrets['DBName']].orgs.find_one(
            {'name': context.user_data['org']}
        )['channel']['link']
        text = (
            client_functions_texts("verified_account") + f' {charge_amount} ' + client_functions_texts("GB") + '!\n'
        )
        text += (
            client_functions_texts("added_to_org") + f': \n\n{org_channel}\n\n *{secrets["DBName"]}* ' + client_functions_texts("group") + ' ️'
        )
        await context.bot.send_message(
            chat_id=context.user_data['user_id'],
            text=text,
            disable_web_page_preview=True
        )
        context.user_data['paymeny_method'] = "crypto"
        context.user_data['payment_receipt'] = (
            f"\nhttps://tronscan.org/#/transaction/`{context.user_data['transaction_id']}`"
        )
        await context.bot.send_message(
            chat_id=org_ticketing_channel_id,
            text=(
                "✅ Verfied Payment from user: \n\n" +
                (f"@{context.user_data['username']} - " if(context.user_data['username'] is not None) else "") +
                f"{context.user_data['user_id']} - {context.user_data['full_name']}" +
                f"\nPlan: {context.user_data['plan']} Pack" +
                "\n-------------------------" +
                f"\nhttps://tronscan.org/#/transaction/`{context.user_data['transaction_id']}`"
            ),
            disable_web_page_preview=True,
            reply_to_message_id=secrets['test_topic_id'] if secrets["DBName"].lower() == "rhvp-test" else secrets['payments_topic_id']
        )
        db_client[secrets['DBName']].users.update_one(
            {'user_id': context.user_data['user_id']},
            {"$set": {f"orgs.{org_name}": {"expires": (datetime.datetime.now()+datetime.timedelta(days=62)).isoformat()}}}
        )
        db_client.close()
        return telext.ApplicationHandlerStop(telext.ConversationHandler.END)
