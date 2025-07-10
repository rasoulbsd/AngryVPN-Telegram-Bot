import telegram
import telegram.ext as telext
from helpers.initial import get_secrets_config, set_lang, connect_to_database
from helpers.bot_functions import check_subscription
from helpers.states import (
    NEWUSER_PURCHASE_CAD_INPUTED,
)

(secrets, Config) = get_secrets_config()
client_functions_texts = set_lang(Config['default_language'], 'client_functions')


async def newuser_purchase_cad(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
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
    context.user_data['pay_amount'] = org_obj['payment_options']['currencies']['cad']['plans'][context.user_data['plan']]
    context.user_data['is_new_user'] = True
    context.user_data['payment_type'] = 'cad'

    if not await check_subscription(update):
        main_channel = db_client[secrets['DBName']].orgs.find_one({'name': 'main'})['channel']['link']
        reply_text = client_functions_texts('join_channel') + f"\n\n{main_channel}"
        await update.effective_message.edit_text(reply_text)
        db_client.close()
        return telext.ConversationHandler.END

    context.user_data['payment_method'] = org_obj['payment_options']['currencies']['cad']['method']

    if context.user_data['payment_method'] == 'e-transfer':
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
        return NEWUSER_PURCHASE_CAD_INPUTED


async def newuser_purchase_cad_inputed_any(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    try:
        db_client = connect_to_database(secrets['DBConString'])
    except Exception:
        print("Failed to connect to the database!")
        return telext.ConversationHandler.END

    if not await check_subscription(update):
        main_channel = db_client[secrets['DBName']].orgs.find_one({'name': 'main'})['channel']['link']
        reply_text = client_functions_texts('join_channel') + f"\n\n{main_channel}"
        await update.effective_message.reply_text(reply_text)
        db_client.close()
        return telext.ConversationHandler.END

    user_dict = db_client[secrets['DBName']].users.find_one({'user_id': int(update.effective_chat.id)})
    if user_dict is None:
        reply_text = client_functions_texts("user_not_found")
        await update.effective_message.reply_text(reply_text)
        db_client.close()
        return telext.ConversationHandler.END

    org_obj = db_client[secrets['DBName']].orgs.find_one({'name': context.user_data['org']})
    keyboard = [
        [telegram.InlineKeyboardButton('❌ Reject', callback_data='Reject'), telegram.InlineKeyboardButton('✅ Accept', callback_data='Accept')]
    ]
    reply_markup = telegram.InlineKeyboardMarkup(keyboard)
    context.user_data["payment_receipt"] = None

    # Handle text, photo, or document
    if update.message and update.message.text:
        context.user_data["payment_receipt"] = update.message.text
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
                "currency:cad\n" +
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
    elif update.message and update.message.photo:
        context.user_data["payment_receipt"] = update.effective_message.text if update.effective_message.text else ""
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
                "currency:cad\n"
            ),
            reply_to_message_id=secrets['test_topic_id'] if secrets["DBName"].lower() == "rhvp-test" else secrets['payments_topic_id'],
            reply_markup=reply_markup
        )
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=client_functions_texts("thanks_for_payment")
        )
    elif update.message and update.message.document:
        context.user_data["payment_receipt"] = update.effective_message.text if update.effective_message.text else ""
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
                "currency:cad\n"
            ),
            reply_to_message_id=secrets['test_topic_id'] if secrets["DBName"].lower() == "rhvp-test" else secrets['payments_topic_id'],
            reply_markup=reply_markup
        )
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=client_functions_texts("thanks_for_payment")
        )
    else:
        await update.effective_message.reply_text(client_functions_texts("user_not_found"))
    db_client.close()
    return telext.ConversationHandler.END
