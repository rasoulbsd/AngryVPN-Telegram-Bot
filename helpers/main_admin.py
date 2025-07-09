import telegram
import telegram.ext as telext
from .initial import get_secrets_config, connect_to_database
from .bot_functions import check_subscription, check_newuser

############################# GLOBALS #############################
(
    ADMIN_MENU, 
    ORG_MNGMNT_SELECT_OPTION, 
    MY_ORG_MNGMNT_SELECT_OPTION,
    ADDING_MEMEBER_TO_ORG,
    LISTING_ORG_SERVERS,
    CHOSING_SERVER_EDIT_ACTION,
    CHANGING_SERVER_TRAFFIC
) = range(7)

(secrets, Config) = get_secrets_config()


############################# Functions #############################

async def manage_orgs(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    try: 
        db_client = connect_to_database(secrets['DBConString'])
    except Exception as e:
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