import telegram
import telegram.ext as telext
import datetime
from ..initial import connect_to_database, get_secrets_config, set_lang
from ..bot_functions import check_subscription
from helpers.states import ADDING_MEMEBER_TO_ORG, BAN_MEMBER

(secrets, Config) = get_secrets_config()
org_admin_texts = set_lang(Config['default_language'], 'org_admin')


def split_long_text(text, max_length=79):
    if len(text) <= max_length:
        return [text]
    lines = []
    while len(text) > max_length:
        split_at = text.rfind(' ', 0, max_length)
        if split_at == -1:
            split_at = max_length
        lines.append(text[:split_at])
        text = text[split_at:].lstrip()
    lines.append(text)
    return lines


async def add_member_to_my_org(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
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
        main_channel = db_client[secrets['DBName']].orgs.find_one(
            {'name': 'main'}
        )['channel']['link']
        reply_text = (
            org_admin_texts('join_channel') +
            f'\n\n{main_channel}'
        )
        await update.effective_message.edit_text(reply_text)
        db_client.close()
        return telext.ConversationHandler.END
    selected_org = query.data['org'] if isinstance(query.data, dict) else query.data

    if (
        update.effective_user.id not in secrets["MainAdmins"]
    ) or (
        selected_org in db_client[secrets['DBName']].admins.find_one(
            {'user_id': update.effective_user.id}
        )['orgs']
    ):
        reply_text = (
            "Please send the new member's NUMERICAL ID\nClick cancel to abort."
        )
        context.user_data['org'] = selected_org
        keyboard = [
            [telegram.InlineKeyboardButton('❌ Cancel', callback_data='Cancel')]
        ]
        reply_markup = telegram.InlineKeyboardMarkup(keyboard)
        await update.effective_message.edit_text(
            reply_text,
            reply_markup=reply_markup,
            parse_mode=telegram.constants.ParseMode.MARKDOWN,
        )
        db_client.close()
        return ADDING_MEMEBER_TO_ORG
    else:
        reply_text = "Unathorized! Also, How are you here?"
        await update.effective_message.edit_text(reply_text)
        db_client.close()
        return telext.ConversationHandler.END


async def add_member_to_my_org_inputed(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    try:
        db_client = connect_to_database(secrets['DBConString'])
    except Exception:
        print("Failed to connect to the database!")

    if not await check_subscription(update):
        main_channel = db_client[secrets['DBName']].orgs.find_one(
            {'name': 'main'}
        )['channel']['link']
        reply_text = (
            org_admin_texts('join_channel') +
            f'\n\n{main_channel}'
        )
        await update.effective_message.reply_text(reply_text)
        db_client.close()
        return telext.ConversationHandler.END
    selected_org = context.user_data['org']
    if selected_org not in db_client[secrets['DBName']].admins.find_one(
        {'user_id': update.effective_user.id}
    )['orgs']:
        reply_text = "Unathorized! Also, How are you here?"
        await update.effective_message.reply_text(reply_text)
        db_client.close()
        return telext.ConversationHandler.END
    else:
        user_dict = db_client[secrets['DBName']].users.find_one(
            {'user_id': int(update.effective_message.text)}
        )
        if user_dict is None:
            reply_text = (
                "User is not a member of the bot.\nUser should start the bot first."
            )
            await update.effective_message.reply_text(reply_text)
            db_client.close()
            return telext.ConversationHandler.END
        elif selected_org in user_dict['orgs'].keys():
            reply_text = (
                f"User {user_dict['user_id']} is Already a member of {selected_org}."
            )
            await update.effective_message.reply_text(reply_text)
            db_client.close()
            return telext.ConversationHandler.END
        else:
            expires = datetime.datetime.now() + datetime.timedelta(days=30)
            db_client[secrets['DBName']].users.update_one(
                {'user_id': user_dict['user_id']},
                [{'$set': {'orgs': {selected_org: {'expires': expires}}}}],
            )
            reply_text = (
                f"User {user_dict['user_id']} Added to {selected_org}.\nExpiration: "
                f"{expires.strftime('%Y-%m-%d %H:%M UTC')}"
            )
            org_channel = db_client[secrets['DBName']].orgs.find_one(
                {'name': selected_org}
            )['channel']['link']
            await context.bot.send_message(
                chat_id=user_dict['user_id'],
                text=(
                    org_admin_texts("after_adding_to_org") +
                    f': \n\n{org_channel}'
                ),
                disable_web_page_preview=True,
            )
            await update.effective_message.reply_text(
                reply_text, parse_mode=telegram.constants.ParseMode.MARKDOWN
            )
            db_client.close()
            return telext.ConversationHandler.END


async def ban_member(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
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
        main_channel = db_client[secrets['DBName']].orgs.find_one(
            {'name': 'main'}
        )['channel']['link']
        reply_text = (
            org_admin_texts('join_channel') +
            f'\n\n{main_channel}'
        )
        await update.effective_message.edit_text(reply_text)
        db_client.close()
        return telext.ConversationHandler.END
    selected_org = query.data['org'] if isinstance(query.data, dict) else query.data
    if selected_org not in db_client[secrets['DBName']].admins.find_one(
        {'user_id': update.effective_user.id}
    )['orgs']:
        reply_text = "Unathorized! Also, How are you here?"
        await update.effective_message.edit_text(reply_text)
        db_client.close()
        return telext.ConversationHandler.END
    else:
        reply_text = (
            "Please send the member's NUMERICAL ID\nClick cancel to abort."
        )
        context.user_data['org'] = selected_org
        keyboard = [
            [telegram.InlineKeyboardButton('❌ Cancel', callback_data='Cancel')]
        ]
        reply_markup = telegram.InlineKeyboardMarkup(keyboard)
        await update.effective_message.edit_text(
            reply_text,
            reply_markup=reply_markup,
            parse_mode=telegram.constants.ParseMode.MARKDOWN,
        )
        db_client.close()
        return BAN_MEMBER


async def ban_member_inputed(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    try:
        db_client = connect_to_database(secrets['DBConString'])
    except Exception:
        print("Failed to connect to the database!")

    if not await check_subscription(update):
        main_channel = db_client[secrets['DBName']].orgs.find_one(
            {'name': 'main'}
        )['channel']['link']
        reply_text = (
            org_admin_texts('join_channel') +
            f'\n\n{main_channel}'
        )
        await update.effective_message.reply_text(reply_text)
        db_client.close()
        return telext.ConversationHandler.END
    selected_org = context.user_data['org']
    user_id = int(update.effective_message.text)
    if selected_org not in db_client[secrets['DBName']].admins.find_one(
        {'user_id': update.effective_user.id}
    )['orgs']:
        reply_text = "Unathorized! Also, How are you here?"
        await update.effective_message.reply_text(reply_text)
        db_client.close()
        return telext.ConversationHandler.END
    if selected_org not in db_client[secrets['DBName']].users.find_one(
        {'user_id': user_id}
    )['orgs']:
        reply_text = "User does not exist in this organization!"
        await update.effective_message.reply_text(reply_text)
        db_client.close()
        return telext.ConversationHandler.END
    else:
        user_dict = db_client[secrets['DBName']].users.find_one({'user_id': user_id})
        user_servers = user_dict["server_names"]
        server_dicts = db_client[secrets['DBName']].servers.find(
            {'name': {'$in': user_servers}}
        )
        org_support_account = db_client[secrets['DBName']].orgs.find_one(
            {'name': selected_org}
        )['support_account']
        import helpers.xuiAPI as xAPI
        xAPI.restrict_user(server_dicts, str(user_id))
        await context.bot.send_message(
            chat_id=user_id,
            text=(
                org_admin_texts("after_banned") +
                '\n' +
                org_admin_texts("contact_support") +
                f': {org_support_account}'
            ),
        )
        await context.bot.send_message(
            chat_id=update.effective_user.id,
            text=(
                f"Account with userid {user_id} has been banned!"
            ),
        )
        db_client.close()
        return telext.ConversationHandler.END

