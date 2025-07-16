"""
Ticketing functions for client flows.
"""

import telegram
import telegram.ext as telext
from helpers.initial import get_secrets_config, connect_to_database, set_lang
from helpers.bot_functions import check_subscription
from helpers.states import RECEIVE_TICKET

(secrets, Config) = get_secrets_config()
# Removed global client_functions_texts


async def receive_ticket(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    try:
        db_client = connect_to_database(secrets['DBConString'])
    except Exception:
        print("Failed to connect to the database!")
        return

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
        main_channel = db_client[secrets['DBName']].orgs.find_one(
            {'name': 'main'}
        )['channel']['link']
        reply_text = client_functions_texts('join_channel') + \
            f"\n\n{main_channel}"
        await update.effective_message.edit_text(reply_text)
        db_client.close()
        return telext.ConversationHandler.END
    reply_text = (
        client_functions_texts("send_ticket") +
        "\n\n" + client_functions_texts("cancel_to_abort")
    )
    keyboard = [
        [telegram.InlineKeyboardButton(
            client_functions_texts("general_cancel"), callback_data='Cancel')]
    ]
    reply_markup = telegram.InlineKeyboardMarkup(keyboard)
    await update.effective_message.edit_text(
        reply_text, reply_markup=reply_markup,
        parse_mode=telegram.constants.ParseMode.MARKDOWN
    )
    db_client.close()
    return RECEIVE_TICKET


async def receive_ticket_inputed(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    try:
        db_client = connect_to_database(secrets['DBConString'])
    except Exception:
        print("Failed to connect to the database!")
        return

    user_id = update.effective_user.id
    user_dict = db_client[secrets['DBName']].users.find_one({'user_id': user_id})
    user_lang = user_dict.get('lang', Config['default_language']) if user_dict else Config['default_language']
    client_functions_texts = set_lang(user_lang, 'client_functions')

    if not await check_subscription(update):
        main_channel = db_client[secrets['DBName']].orgs.find_one(
            {'name': 'main'}
        )['channel']['link']
        reply_text = client_functions_texts('join_channel') + \
            f"\n\n{main_channel}"
        await update.effective_message.reply_text(reply_text)
        db_client.close()
        return telext.ConversationHandler.END
    print("In ticketing")
    user_dict = db_client[secrets['DBName']].users.find_one(
        {'user_id': int(update.effective_chat.id)}
    )
    if user_dict is None:
        reply_text = client_functions_texts("user_not_found")
        await update.effective_message.reply_text(reply_text)
    else:
        if bool(user_dict['orgs']):
            for user_org in user_dict['orgs'].keys():
                chat_id = db_client[secrets['DBName']].orgs.find_one(
                    {'name': user_org}
                )['ticketing_group_id']
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=(
                        "Ticket from user: \n\n" +
                        (f"@{update.effective_chat.username} - "
                         if (update.effective_chat.username is not None) else "") +
                        f"{update.effective_chat.id} - "
                        f"{update.effective_chat.full_name}" +
                        f"\nOrg: {user_org}" +
                        "\n-------------------------" +
                        f"\n{update.effective_message.text}"
                    ),
                    reply_to_message_id=secrets['ticket_topic_id']
                )
        else:
            chat_id = db_client[secrets['DBName']].orgs.find_one(
                {'name': 'main'}
            )['ticketing_group_id']
            await context.bot.send_message(
                chat_id=chat_id,
                text=(
                    "Ticket from user: \n\n" +
                    (f"@{update.effective_chat.username} - "
                     if (update.effective_chat.username is not None) else "") +
                    f"{update.effective_chat.id} - "
                    f"{update.effective_chat.full_name}" +
                    "\n-------------------------" +
                    f"\n{update.effective_message.text}"
                ),
                reply_to_message_id=secrets['ticket_topic_id']
            )
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=client_functions_texts("thanks_ticket")
        )
    db_client.close()
    return telext.ConversationHandler.END
