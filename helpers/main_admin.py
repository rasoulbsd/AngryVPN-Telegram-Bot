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