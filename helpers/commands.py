import telegram
import telegram.ext as telext
from .initial import get_secrets_config, connect_to_database, set_lang
import uuid
from .bot_functions import check_subscription, check_newuser, reset
from .states import ADMIN_MENU


## Remove all local state definitions for states (ADMIN_MENU, etc.)
(secrets, Config) = get_secrets_config()
# Removed global commands_texts
# general_texts = set_lang(Config['default_language'], 'general')


## Functions
async def start(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    try:
        db_client = connect_to_database(secrets['DBConString'])
    except Exception:
        print("Failed to connect to the database!")
        return

    # --- Development mode check ---
    org_main = db_client[secrets['DBName']].orgs.find_one({'name': 'main'})
    is_in_production = org_main.get('isInProduction', True)
    development_message = org_main.get('development_message', "Under Development!\nPlease be patient while we are fixing things.\n\n…")

    if not is_in_production:
        admin_usr = db_client[secrets['DBName']].admins.find_one({'user_id': update.message.from_user.id})
        await update.message.reply_text(development_message)
        if admin_usr is not None:
            await update.message.reply_text("Skipping for Admin")
        else:
            db_client.close()
            return
    # --- End development mode check ---

    user_dict = db_client[secrets['DBName']].users.find_one({'user_id': update.message.from_user.id})
    user_lang = user_dict.get('lang', Config['default_language']) if user_dict else Config['default_language']
    commands_texts = set_lang(user_lang, 'commands')

    if not await check_subscription(update):
        main_channel = db_client[secrets['DBName']].orgs.find_one({'name': 'main'})['channel']['link']
        reply_text = commands_texts("join_channel") + f'\n\n{main_channel}'
    else:
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

            reply_text = (
                commands_texts("welcome") + f' {update.message.from_user.full_name}.\n'
            )
            reply_text += commands_texts("unique_id") + f' {update.effective_user.id}.\n'
            reply_text += commands_texts("pop_menu") + "\n"
            reply_text += commands_texts("contact_support") + f': {support_account}'
        else:  # Existing User
            reply_text = (
                commands_texts("welcome_back") + f' {update.message.from_user.full_name}.\n'
            )
            reply_text += commands_texts("unique_id") + f' {update.effective_user.id}.\n'
            reply_text += commands_texts("pop_menu") + "\n"
            reply_text += commands_texts("contact_support") + f': {support_account}'

    db_client.close()
    await update.message.reply_text(
        reply_text, reply_markup=telegram.ReplyKeyboardRemove()
    )


async def menu(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    reset(update, context)
    try:
        db_client = connect_to_database(secrets['DBConString'])
    except Exception:
        print("Failed to connect to the database!")

    # --- Development mode check ---
    org_main = db_client[secrets['DBName']].orgs.find_one({'name': 'main'})
    is_in_production = org_main.get('isInProduction', True)
    development_message = org_main.get('development_message', "Under Development!\nPlease be patient while we are fixing things.\n\n…")
    if not is_in_production:
        admin_usr = db_client[secrets['DBName']].admins.find_one({'user_id': update.message.from_user.id})
        await update.message.reply_text(development_message)
        if admin_usr is not None:
            await update.message.reply_text("Skipping for Admin")
        else:
            db_client.close()
            return
    # --- End development mode check ---

    user_dict = db_client[secrets['DBName']].users.find_one({'user_id': update.effective_chat.id})

    if user_dict is None:
        user_lang = Config['default_language']
    else:
        user_lang = user_dict.get('lang', Config['default_language'])
    commands_texts = set_lang(user_lang, 'commands')

    if user_dict is None:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=commands_texts("user_not_found")
        )
        db_client.close()
        return telext.ConversationHandler.END

    if not await check_subscription(update):
        main_channel = db_client[secrets['DBName']].orgs.find_one({'name': 'main'})['channel']['link']
        reply_text = commands_texts("join_channel") + \
            f'\n\n{main_channel}'
        await update.message.reply_text(reply_text)
    elif await check_newuser(update, context):
        reply_text = commands_texts("what_do_you_want")
        keyboard = [
            [telegram.InlineKeyboardButton(
                commands_texts("menu_purchase_account"),
                callback_data="Purchase Account"
            )],
            [telegram.InlineKeyboardButton(
                commands_texts("menu_userinfo"),
                callback_data="Get User Info"
            )],
            [telegram.InlineKeyboardButton(
                commands_texts("menu_support"),
                callback_data="Receive Ticket"
            )],
            [telegram.InlineKeyboardButton(
                commands_texts("general_cancel"),
                callback_data="Cancel"
            )]
        ]
        reply_markup = telegram.InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            reply_text, reply_markup=reply_markup
        )
    else:
        reply_text = commands_texts("what_do_you_want")
        keyboard = [
            [telegram.InlineKeyboardButton(
                commands_texts("menu_servers"),
                callback_data="Get Servers"
            )],
            [telegram.InlineKeyboardButton(
                commands_texts("menu_recharge"),
                callback_data="Charge Account"
            )],
            [telegram.InlineKeyboardButton(
                commands_texts("menu_userinfo"),
                callback_data="Get User Info"
            )],
            [telegram.InlineKeyboardButton(
                commands_texts("menu_support"),
                callback_data="Receive Ticket"
            )],
            [telegram.InlineKeyboardButton(
                commands_texts("general_cancel"),
                callback_data="Cancel"
            )]
        ]
        reply_markup = telegram.InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            reply_text, reply_markup=reply_markup
        )
    db_client.close()
    return


async def admin(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    try:
        db_client = connect_to_database(secrets['DBConString'])
    except Exception:
        print("Failed to connect to the database!")

    # Define commands_texts for localization
    user_dict = db_client[secrets['DBName']].users.find_one({'user_id': update.effective_user.id})
    user_lang = user_dict.get('lang', Config['default_language']) if user_dict else Config['default_language']
    commands_texts = set_lang(user_lang, 'commands')

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
                [telegram.InlineKeyboardButton("Bot Settings", callback_data="Bot Settings")]
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


async def change_lang(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    try:
        db_client = connect_to_database(secrets['DBConString'])
    except Exception:
        print("Failed to connect to the database!")
        return

    # --- Development mode check ---
    org_main = db_client[secrets['DBName']].orgs.find_one({'name': 'main'})
    is_in_production = org_main.get('isInProduction', True)
    development_message = org_main.get('development_message', "Under Development!\nPlease be patient while we are fixing things.\n\n…")
    if not is_in_production:
        admin_usr = db_client[secrets['DBName']].admins.find_one({'user_id': update.message.from_user.id})
        await update.message.reply_text(development_message)
        if admin_usr is not None:
            await update.message.reply_text("Skipping for Admin")
        else:
            db_client.close()
            return
    # --- End development mode check ---

    user_id = update.effective_user.id
    user_dict = db_client[secrets['DBName']].users.find_one({'user_id': user_id})
    user_lang = user_dict.get('lang', Config['default_language']) if user_dict else Config['default_language']
    commands_texts = set_lang(user_lang, 'commands')

    main_org = db_client[secrets['DBName']].orgs.find_one({'name': 'main'})
    available_langs = main_org.get('langs', ['fa', 'en'])

    # Fallback texts if not present in translation files
    choose_language_text = None
    language_changed_text = None
    try:
        choose_language_text = commands_texts("choose_language")
    except Exception:
        choose_language_text = "Please choose your language:"
    try:
        language_changed_text = commands_texts("language_changed")
    except Exception:
        language_changed_text = "Language changed successfully!"

    # If user sent a language code as argument, update it
    if context.args and context.args[0] in available_langs:
        new_lang = context.args[0]
        db_client[secrets['DBName']].users.update_one({'user_id': user_id}, {'$set': {'lang': new_lang}})
        commands_texts = set_lang(new_lang, 'commands')
        try:
            language_changed_text = commands_texts("language_changed")
        except Exception:
            language_changed_text = "Language changed successfully!"
        await update.message.reply_text(language_changed_text + f" ({new_lang})")
        db_client.close()
        return

    # Otherwise, show language options
    keyboard = [
        [telegram.InlineKeyboardButton(lang, callback_data=f"setlang_{lang}")] for lang in available_langs
    ]
    reply_markup = telegram.InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(choose_language_text, reply_markup=reply_markup)
    db_client.close()


# Add a CallbackQueryHandler for language selection
async def set_lang_callback(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang_code = query.data.replace('setlang_', '')
    try:
        db_client = connect_to_database(secrets['DBConString'])
    except Exception:
        print("Failed to connect to the database!")
        return
    user_id = update.effective_user.id
    db_client[secrets['DBName']].users.update_one(
        {'user_id': user_id}, {'$set': {'lang': lang_code}}
    )
    commands_texts = set_lang(lang_code, 'commands')
    try:
        language_changed_text = commands_texts("language_changed")
    except Exception:
        language_changed_text = "Language changed successfully!"
    await query.edit_message_text(language_changed_text + f" ({lang_code})")
    db_client.close()


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