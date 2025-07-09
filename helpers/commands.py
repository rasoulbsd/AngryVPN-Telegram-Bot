import telegram
import telegram.ext as telext
from .initial import get_secrets_config, connect_to_database, set_lang
import uuid
from .bot_functions import check_subscription, check_newuser, reset
from .states import ADMIN_MENU

############################# GLOBALS #############################
# Remove all local state definitions for states (ADMIN_MENU, etc.)

(secrets, Config) = get_secrets_config()
commands_texts = set_lang(Config['default_language'], 'commands')
# general_texts = set_lang(Config['default_language'], 'general')

############################# Functions #############################

async def start(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    try: 
        db_client = connect_to_database(secrets['DBConString'])
    except Exception:
        print("Failed to connect to the database!")

    if not await check_subscription(update):
        main_channel = db_client[secrets['DBName']].orgs.find_one({'name': 'main'})['channel']['link']
        reply_text = commands_texts("join_channel") + f'\n\n{main_channel}'
    else:
        # client = pymongo.MongoClient(secrets['DBConString'])

        user_dict = db_client[secrets['DBName']].users.find_one({'user_id': update.message.from_user.id})
        support_account = db_client[secrets['DBName']].orgs.find_one({'name': "main"})['support_account']

        if user_dict is None: 
            # New User
            db_client[secrets['DBName']].users.insert_one({
                'user_id': update.message.from_user.id,
                'uuid': str(uuid.uuid4()),
                'user_profile': update.message.from_user.full_name,
                'join_date': update.message.date,
                'orgs': dict(),
                'server_names': [],
                'discount': 0,
                'wallet': float(0)
            })

            reply_text = commands_texts("welcome") + f' {update.message.from_user.full_name}.\n'
            reply_text += commands_texts("unique_id")+ f' {update.effective_user.id}.\n'
            reply_text += commands_texts("pop_menu") + "\n"
            reply_text += commands_texts("contact_support") + f': {support_account}'
        else: # Existing User
            reply_text = commands_texts("welcome_back") + f' {update.message.from_user.full_name}.\n'
            reply_text += commands_texts("unique_id") + f' {update.effective_user.id}.\n'
            reply_text += commands_texts("pop_menu") + "\n"
            reply_text += commands_texts("contact_support") + f': {support_account}'

        # client.close()

    db_client.close()

    await update.message.reply_text(reply_text, reply_markup=telegram.ReplyKeyboardRemove())

async def menu(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    reset(update, context)
    try: 
        db_client = connect_to_database(secrets['DBConString'])
    except Exception:
        print("Failed to connect to the database!")

    user_dict = db_client[secrets['DBName']].users.find_one({'user_id': update.effective_chat.id})

    if user_dict is None:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text= commands_texts("user_not_found")
        )
        db_client.close()
        return telext.ConversationHandler.END

    keyboard = []

    if not await check_subscription(update):
        main_channel = db_client[secrets['DBName']].orgs.find_one({'name': 'main'})['channel']['link']
        reply_text = commands_texts("join_channel") + f'\n\n{main_channel}'
        await update.message.reply_text(reply_text)

    elif await check_newuser(update, context):
        reply_text = commands_texts("what_do_you_want")
        keyboard = [
            [telegram.InlineKeyboardButton(commands_texts("menu_purchase_account"), callback_data="Purchase Account")],
            [telegram.InlineKeyboardButton(commands_texts("menu_userinfo"), callback_data="Get User Info")],
            [telegram.InlineKeyboardButton(commands_texts("menu_support"), callback_data="Receive Ticket")],
            [telegram.InlineKeyboardButton(commands_texts("general_cancel"), callback_data="Cancel")]
        ]

    else:
        reply_text = commands_texts("what_do_you_want")
        keyboard = [
            [telegram.InlineKeyboardButton(commands_texts("menu_get_new_vmess"), callback_data="Get New Vmess")],
            [telegram.InlineKeyboardButton(commands_texts("menu_refresh_vmess"), callback_data="Refresh Vmess")],
            [telegram.InlineKeyboardButton(commands_texts("menu_recharge"), callback_data="Charge Account")],
            [telegram.InlineKeyboardButton(commands_texts("menu_userinfo"), callback_data="Get User Info")],
            [telegram.InlineKeyboardButton(commands_texts("menu_support"), callback_data="Receive Ticket")],
            [telegram.InlineKeyboardButton(commands_texts("general_cancel"), callback_data="Cancel")]
        ]

    db_client.close()

    reply_markup = telegram.InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(reply_text, reply_markup=reply_markup)

async def admin(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    try: 
        db_client = connect_to_database(secrets['DBConString'])
    except Exception:
        print("Failed to connect to the database!")

    if not await check_subscription(update):
        main_channel = db_client[secrets['DBName']].orgs.find_one({'name': 'main'})['channel']['link']
        reply_text = commands_texts("join_channel") + f'\n\n{main_channel}'
        await update.message.reply_text(reply_text)

        db_client.close()

        return telext.ConversationHandler.END
    else:
        # Admin's Greeting Message and Info
        auth_msg = ""
        keyboard = []
        if update.effective_user.id in secrets['MainAdmins']:
            auth_msg += "You are a Main Admin\n"
            keyboard.extend([
                [telegram.InlineKeyboardButton("Manage Organizations", callback_data="Manage Organizations")],
            ])
        admin_dict = db_client[secrets['DBName']].admins.find_one({'user_id': update.effective_user.id})
        admins_orgs = admin_dict['orgs'] if admin_dict is not None else []
        auth_msg += "Your Orgs: " + (", ".join(admins_orgs) if len(admins_orgs) != 0 else "None") + "\n"
        reply_text = commands_texts("what_do_you_want")
        keyboard.extend([
            [telegram.InlineKeyboardButton(f"{org}", callback_data=f"Manage: {org}") for org in admins_orgs]
        ] + [
            [telegram.InlineKeyboardButton("❌ Cancel", callback_data="Cancel")]
        ])
        reply_markup = telegram.InlineKeyboardMarkup(keyboard)
        
        if update.effective_user.id not in secrets['MainAdmins'] and len(admins_orgs) == 0:
            await update.message.reply_text("Unauthorized!")

            db_client.close()

            return telext.ConversationHandler.END
        
        await update.message.reply_text(auth_msg)
        await update.message.reply_text(reply_text, reply_markup=reply_markup)

        db_client.close()

        return ADMIN_MENU

async def cancel(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data.clear()

    # # application.add_handler(menu_handler)
    await query.edit_message_text(text='Canceled!')
    raise telext.ApplicationHandlerStop(telext.ConversationHandler.END)

async def cancel_command(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()

    # # application.add_handler(menu_handler)
    await update.effective_message.reply_text('Canceled!')
    raise telext.ApplicationHandlerStop(telext.ConversationHandler.END)