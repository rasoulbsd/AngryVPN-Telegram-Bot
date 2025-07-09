import telegram
import telegram.ext as telext
from ..initial import connect_to_database, get_secrets_config, set_lang
from ..bot_functions import check_subscription
from helpers.states import ADMIN_ANNOUNCEMENT, ADMIN_DIRECT_MESSAGE_USERID, ADMIN_DIRECT_MESSAGE_TEXT

(secrets, Config) = get_secrets_config()
org_admin_texts = set_lang(Config['default_language'], 'org_admin')


async def admin_announcement(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
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
        reply_text = org_admin_texts('join_channel') + f'\n\n{main_channel}'
        await update.effective_message.edit_text(reply_text)
        db_client.close()
        return telext.ConversationHandler.END
    selected_org = query.data['org']
    if selected_org not in db_client[secrets['DBName']].admins.find_one({'user_id': update.effective_user.id})['orgs']:
        reply_text = "Unathorized! Also, How are you here?"
        await update.effective_message.edit_text(reply_text)
        db_client.close()
        return telext.ConversationHandler.END
    else:
        reply_text = "Please send your announcement\n⚠️ Consider that it will be sent to everyone in your organization through bot\n\nClick cancel to abort."
        context.user_data['org'] = selected_org
        keyboard = [
            [telegram.InlineKeyboardButton('❌ Cancel', callback_data='Cancel')]
        ]
        reply_markup = telegram.InlineKeyboardMarkup(keyboard)
        await update.effective_message.edit_text(reply_text, reply_markup=reply_markup, parse_mode=telegram.constants.ParseMode.MARKDOWN)
        db_client.close()
        return ADMIN_ANNOUNCEMENT


async def admin_announcement_inputed(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    try: 
        db_client = connect_to_database(secrets['DBConString'])
    except Exception:
        print("Failed to connect to the database!")

    if not await check_subscription(update):
        main_channel = db_client[secrets['DBName']].orgs.find_one({'name': 'main'})['channel']['link']
        reply_text = org_admin_texts('join_channel') + f'\n\n{main_channel}'
        await update.effective_message.reply_text(reply_text)
        db_client.close()
        return telext.ConversationHandler.END
    selected_org = context.user_data['org']
    if selected_org not in db_client[secrets['DBName']].admins.find_one({'user_id': update.effective_user.id})['orgs']:
        reply_text = "Unathorized! Also, How are you here?"
        await update.effective_message.reply_text(reply_text)
        db_client.close()
        return telext.ConversationHandler.END
    else:
        user_dicts = db_client[secrets['DBName']].users.find({
            'orgs.' + selected_org: {'$exists': True}
        })
        for user_dict in user_dicts:
            try:
                await context.bot.send_message(
                    chat_id=user_dict['user_id'],
                    text=org_admin_texts("admin_announcement") + f'\n\n{update.effective_message.text}'
                )
            except:
                print("Failed to send message to user: " + str(user_dict['user_id']))
        db_client.close()
        return telext.ConversationHandler.END


async def direct_message(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
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
        reply_text = org_admin_texts('join_channel') + f'\n\n{main_channel}'
        await update.effective_message.edit_text(reply_text)
        db_client.close()
        return telext.ConversationHandler.END
    selected_org = query.data['org']
    if selected_org not in db_client[secrets['DBName']].admins.find_one({'user_id': update.effective_user.id})['orgs']:
        reply_text = "Unathorized! Also, How are you here?"
        await update.effective_message.reply_text(reply_text)
        db_client.close()
        return telext.ConversationHandler.END
    else:
        reply_text = "Please send your user_id in your organization\n\nClick cancel to abort."
        context.user_data['org'] = selected_org
        context.user_data['message_id_get_userid'] = update.effective_message.message_id
        keyboard = [
            [telegram.InlineKeyboardButton('❌ Cancel', callback_data='Cancel')]
        ]
        reply_markup = telegram.InlineKeyboardMarkup(keyboard)
        print("direct_message")
        await update.effective_message.edit_text(reply_text, reply_markup=reply_markup)
        db_client.close()
        return ADMIN_DIRECT_MESSAGE_USERID


async def direct_message_userid_inputed(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    try:
        db_client = connect_to_database(secrets['DBConString'])
    except Exception:
        print("Failed to connect to the database!")

    if not await check_subscription(update):
        main_channel = db_client[secrets['DBName']].orgs.find_one({'name': 'main'})['channel']['link']
        reply_text = org_admin_texts('join_channel') + f'\n\n{main_channel}'
        await update.effective_message.reply_text(reply_text)
        db_client.close()
        return telext.ConversationHandler.END
    selected_org = context.user_data['org']
    if selected_org not in db_client[secrets['DBName']].admins.find_one({'user_id': update.effective_user.id})['orgs']:
        reply_text = "Unathorized! Also, How are you here?"
        await update.effective_message.reply_text(reply_text)
        db_client.close()
        return telext.ConversationHandler.END
    else:
        user_dicts = db_client[secrets['DBName']].users.find({
            'orgs.' + selected_org: {'$exists': True},
            'user_id': int(update.effective_message.text)
        })
        if user_dicts is None:
            reply_text = "User is not a member of your organization or bot.\n"
            await update.effective_message.reply_text(reply_text)
            db_client.close()
            return telext.ConversationHandler.END
        else:
            context.user_data['selected_user'] = int(update.effective_message.text)
            reply_text = "Please send your message\n\nClick cancel to abort."
            keyboard = [
                [telegram.InlineKeyboardButton('❌ Cancel', callback_data='Cancel')]
            ]
            reply_markup = telegram.InlineKeyboardMarkup(keyboard)
            await update.effective_message.reply_text(reply_text, reply_markup=reply_markup)
            db_client.close()
            return ADMIN_DIRECT_MESSAGE_TEXT


async def direct_message_text_inputed(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    try:
        db_client = connect_to_database(secrets['DBConString'])
    except Exception:
        print("Failed to connect to the database!")
    if not await check_subscription(update):
        main_channel = db_client[secrets['DBName']].orgs.find_one({'name': 'main'})['channel']['link']
        reply_text = org_admin_texts("join_channel") + f'\n\n{main_channel}'
        await update.effective_message.reply_text(reply_text)
        db_client.close()
        return telext.ConversationHandler.END
    selected_org = context.user_data['org']
    selected_user = context.user_data['selected_user']
    if selected_org not in db_client[secrets['DBName']].admins.find_one({'user_id': update.effective_user.id})['orgs']:
        reply_text = "Unathorized! Also, How are you here?"
        await update.effective_message.reply_text(reply_text)
        db_client.close()
        return telext.ConversationHandler.END
    else:
        try:
            await context.bot.send_message(
                chat_id=selected_user,
                text=update.effective_message.text
            )
            await update.effective_message.reply_text(f"Message Sent to {selected_user}!")
        except:
            await update.effective_message.reply_text(f"Failed to send message to {selected_user}!")
        db_client.close()
        return telext.ConversationHandler.END 