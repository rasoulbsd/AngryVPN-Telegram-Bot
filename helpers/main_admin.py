import telegram
import telegram.ext as telext
from .initial import connect_to_database, get_secrets_config, set_lang
from .bot_functions import check_subscription
from .states import ORG_MNGMNT_SELECT_OPTION

(secrets, Config) = get_secrets_config()
_ = set_lang(Config['default_language'], 'org_admin')


############################# Functions #############################
async def manage_orgs(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    try:
        db_client = connect_to_database(secrets['DBConString'])
    except Exception:
        print("Failed to connect to the database!")

    query = update.callback_query
    await query.answer()
    if not await check_subscription(update):
        main_channel = db_client[secrets['DBName']].orgs.find_one({'name': 'main'})['channel']['link']
        reply_text = f"{_('join_channel')}\n\n{main_channel}"
        await update.effective_message.edit_text(reply_text)
        # application.add_handler(menu_handler)
        return telext.ConversationHandler.END
    elif update.effective_user.id not in secrets["MainAdmins"]:
        print("asdwedsd")
        reply_text = "Unathorized! Also, How are you here?"
        await update.effective_message.edit_text(reply_text)
        return telext.ConversationHandler.END
    else:
        keyboard = [
            [telegram.InlineKeyboardButton('Add Organization', callback_data='Add Organization')],
            [telegram.InlineKeyboardButton('List Organizations', callback_data='List Organizations')],
            # [telegram.InlineKeyboardButton('Exceed Users: Hard Coded', callback_data='Exceed Users: Hard Coded')],
            [telegram.InlineKeyboardButton('❌ Cancel', callback_data='Cancel')]
        ]
        reply_markup = telegram.InlineKeyboardMarkup(keyboard)
        # Send message with text and appended InlineKeyboard
        reply_text = "Managing Organizations"
        await update.effective_message.edit_text(reply_text, reply_markup=reply_markup, parse_mode=telegram.constants.ParseMode.MARKDOWN)
        return ORG_MNGMNT_SELECT_OPTION


# --- Bot Settings Menu for Main Admins ---
async def bot_settings_callback(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    if user_id not in secrets['MainAdmins']:
        await query.edit_message_text("Unauthorized!")
        return

    keyboard = [
        [telegram.InlineKeyboardButton("Toggle Production/Development", callback_data="toggle_bot_status")],
        [telegram.InlineKeyboardButton("Change Development Message", callback_data="change_dev_message")],
        [telegram.InlineKeyboardButton("❌ Cancel", callback_data="Cancel")]
    ]
    reply_markup = telegram.InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Bot Settings:", reply_markup=reply_markup)


async def toggle_bot_status_callback(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    if user_id not in secrets['MainAdmins']:
        await query.edit_message_text("Unauthorized!")
        return

    try:
        db_client = connect_to_database(secrets['DBConString'])
    except Exception:
        await query.edit_message_text("Failed to connect to the database!")
        return

    org_main = db_client[secrets['DBName']].orgs.find_one({'name': 'main'})
    is_in_production = org_main.get('isInProduction', True)
    new_status = not is_in_production
    db_client[secrets['DBName']].orgs.update_one(
        {'name': 'main'},
        {'$set': {'isInProduction': new_status}}
    )
    status_text = "Production" if new_status else "Development"
    await query.edit_message_text(f"Bot status changed to: {status_text}")
    db_client.close()

async def change_dev_message_callback(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    if user_id not in secrets['MainAdmins']:
        await query.edit_message_text("Unauthorized!")
        return

    await query.edit_message_text("Please send the new development message.")
    context.user_data['awaiting_dev_message'] = True

async def set_dev_message(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('awaiting_dev_message'):
        new_message = update.message.text
        try:
            db_client = connect_to_database(secrets['DBConString'])
        except Exception:
            await update.message.reply_text("Failed to connect to the database!")
            return

        db_client[secrets['DBName']].orgs.update_one(
            {'name': 'main'},
            {'$set': {'development_message': new_message}}
        )
        await update.message.reply_text("Development message updated.")
        context.user_data['awaiting_dev_message'] = False
        db_client.close()