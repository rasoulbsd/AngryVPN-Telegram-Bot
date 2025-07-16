import telegram
import telegram.ext as telext
from ..initial import connect_to_database, get_secrets_config, set_lang
from ..bot_functions import check_subscription
from helpers.states import (
    LISTING_ORG_SERVERS, CHOSING_SERVER_EDIT_ACTION, CHANGING_SERVER_TRAFFIC,
    MY_ORG_MNGMNT_SELECT_OPTION
)

(secrets, Config) = get_secrets_config()
org_admin_texts = set_lang(Config['default_language'], 'org_admin')


async def manage_my_org(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
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
    selected_org = query.data.removeprefix('Manage: ')
    if selected_org not in db_client[secrets['DBName']].admins.find_one({'user_id': update.effective_user.id})['orgs']:
        reply_text = "Unathorized! Also, How are you here?"
        await update.effective_message.edit_text(reply_text)
        db_client.close()
        return telext.ConversationHandler.END
    else:
        keyboard = [
            [telegram.InlineKeyboardButton('📱 Add Memeber', callback_data={'task': 'Add Member to org', 'org': selected_org})],
            [telegram.InlineKeyboardButton('📵 Ban Memeber', callback_data={'task': 'Ban Member', 'org': selected_org})],
            [telegram.InlineKeyboardButton('📢 Send Announcement', callback_data={'task': 'Admin Announcement', 'org': selected_org})],
            [telegram.InlineKeyboardButton('🖥 List Org Servers', callback_data={'task': 'List Org Servers', 'org': selected_org})],
            [telegram.InlineKeyboardButton('🔌 Charge a Account', callback_data={'task':'Admin Charge Account', 'org': selected_org})],
            [telegram.InlineKeyboardButton('🔋 Charge All Accounts', callback_data={'task':'Admin Charge All Accounts', 'org': selected_org})],
            [telegram.InlineKeyboardButton('🎯 Direct Message', callback_data={'task':'Direct Message', 'org': selected_org})],
            [telegram.InlineKeyboardButton('Cancel', callback_data='Cancel')]
        ]
        reply_markup = telegram.InlineKeyboardMarkup(keyboard)
        reply_text = f"Managing: {selected_org}"
        await update.effective_message.edit_text(reply_text, reply_markup=reply_markup, parse_mode=telegram.constants.ParseMode.MARKDOWN)
        db_client.close()
        return MY_ORG_MNGMNT_SELECT_OPTION


async def list_my_org_servers(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
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
    admin_dict = db_client[secrets['DBName']].admins.find_one({'user_id': update.effective_user.id})
    if selected_org not in admin_dict['orgs']:
        reply_text = "Unathorized! Also, How are you here?"
        await update.effective_message.edit_text(reply_text)
        db_client.close()
        return telext.ConversationHandler.END
    else:
        admin_servers = list(db_client[secrets['DBName']].servers.find({'org': {'$in': admin_dict['orgs']}}))
        keyboard = [
            [telegram.InlineKeyboardButton(s['name'], callback_data={'task': 'Manage Server', 'org': selected_org, 'server': s['name']}) for s in admin_servers]
        ] + [
            [telegram.InlineKeyboardButton('❌ Cancel', callback_data='Cancel')]
        ]
        if len(admin_servers) == 0:
            reply_text = "You do not have any servers!"
            await update.effective_message.edit_text(reply_text, parse_mode=telegram.constants.ParseMode.MARKDOWN)
            return telext.ConversationHandler.END
        
        reply_text = "Choose Server to Manage:"
        reply_markup = telegram.InlineKeyboardMarkup(keyboard)
        await update.effective_message.edit_text(reply_text, reply_markup=reply_markup, parse_mode=telegram.constants.ParseMode.MARKDOWN)
        db_client.close()
        return LISTING_ORG_SERVERS


async def manage_my_org_server(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    try:
        db_client = connect_to_database(secrets['DBConString'])
    except Exception:
        print("Failed to connect to the database!")

    query = update.callback_query
    await query.answer()
    if query.data == 'Cancel':
        db_client.close()
        return telext.ConversationHandler.END

    # Fix: parse org and server from string callback_data
    if query.data.startswith('ManageServer:'):
        _, selected_org, selected_server = query.data.split(':', 2)
    else:
        selected_org = None
        selected_server = None
    admin_dict = db_client[secrets['DBName']].admins.find_one({'user_id': update.effective_user.id})
    server_dict = db_client[secrets['DBName']].servers.find_one({'name': selected_server})
    # Normalize org names for robust comparison
    selected_org_norm = selected_org.strip().lower() if selected_org else ''
    admin_orgs_norm = [org.strip().lower() for org in admin_dict.get('orgs', [])]
    server_org_norm = server_dict['org'].strip().lower() if server_dict and 'org' in server_dict else ''

    if selected_org_norm not in admin_orgs_norm or selected_org_norm != server_org_norm:
        reply_text = "Unathorized! Also, How are you here?"
        await update.effective_message.edit_text(reply_text)
        db_client.close()
        return telext.ConversationHandler.END
    else:
        reply_text = f"=== Server: *{selected_server}* ===\n"
        reply_text += f"  Organization: __{server_dict['org']}__\n"
        reply_text += f"  Active Join: __{'Yes' if server_dict['AcceptingNew'] else 'No'}__\n"
        reply_text += f"  Default Traffic: __{server_dict['traffic']}__\n"
        reply_text += "Chose an Action:"

        keyboard = [
            [telegram.InlineKeyboardButton('Switch Active Join', callback_data={'task': 'Switch Server Active Join', 'org': selected_org, 'server': selected_server})],
            [telegram.InlineKeyboardButton('Change Traffic', callback_data={'task': 'Change Server Traffic', 'org': selected_org, 'server': selected_server})],
            [telegram.InlineKeyboardButton('❌ Cancel', callback_data='Cancel')]
        ]
        
        reply_markup = telegram.InlineKeyboardMarkup(keyboard)
        await update.effective_message.edit_text(reply_text, reply_markup=reply_markup, parse_mode=telegram.constants.ParseMode.MARKDOWN)
        db_client.close()
        return CHOSING_SERVER_EDIT_ACTION


async def switch_server_active_join(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    try: 
        db_client = connect_to_database(secrets['DBConString'])
    except Exception:
        print("Failed to connect to the database!")

    query = update.callback_query
    if not await check_subscription(update):
        main_channel = db_client[secrets['DBName']].orgs.find_one({'name': 'main'})['channel']['link']
        reply_text = org_admin_texts('join_channel') + f'\n\n{main_channel}'
        await update.effective_message.edit_text(reply_text)
        db_client.close()
        return telext.ConversationHandler.END
    selected_org = query.data['org']
    selected_server = query.data['server']
    admin_dict = db_client[secrets['DBName']].admins.find_one({'user_id': update.effective_user.id})
    server_dict = db_client[secrets['DBName']].servers.find_one({'name': selected_server})
    if selected_org not in admin_dict['orgs'] or selected_org != server_dict['org']:
        reply_text = "Unathorized! Also, How are you here?"
        await update.effective_message.edit_text(reply_text)
        db_client.close()
        return telext.ConversationHandler.END
    else:
        db_client[secrets['DBName']].servers.update_one(
            {'name': selected_server},
            {'$set': {'AcceptingNew': False if server_dict['AcceptingNew'] else True}}
        )
        server_dict = db_client[secrets['DBName']].servers.find_one({'name': selected_server})
        await query.answer(text='Changed!')

        reply_text = f"=== Server: *{selected_server}* ===\n"
        reply_text += f"  Organization: __{server_dict['org']}__\n"
        reply_text += f"  Active Join: __{'Yes' if server_dict['AcceptingNew'] else 'No'}__\n"
        reply_text += f"  Default Traffic: __{server_dict['traffic']}__\n"
        reply_text += "Chose an Action:"

        keyboard = [
            [telegram.InlineKeyboardButton('Switch Active Join', callback_data={'task': 'Switch Server Active Join', 'org': selected_org, 'server': selected_server})],
            [telegram.InlineKeyboardButton('Change Traffic', callback_data={'task': 'Change Server Traffic', 'org': selected_org, 'server': selected_server})],
            [telegram.InlineKeyboardButton('❌ Cancel', callback_data='Cancel')]
        ]
        
        reply_markup = telegram.InlineKeyboardMarkup(keyboard)
        await update.effective_message.edit_text(reply_text, reply_markup=reply_markup, parse_mode=telegram.constants.ParseMode.MARKDOWN)
        db_client.close()
        return CHOSING_SERVER_EDIT_ACTION


async def change_server_traffic(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    try: 
        db_client = connect_to_database(secrets['DBConString'])
    except Exception:
        print("Failed to connect to the database!")

    query = update.callback_query
    if not await check_subscription(update):
        main_channel = db_client[secrets['DBName']].orgs.find_one({'name': 'main'})['channel']['link']
        reply_text = org_admin_texts('join_channel') + f'\n\n{main_channel}'
        await update.effective_message.edit_text(reply_text)
        db_client.close()
        return telext.ConversationHandler.END
    selected_org = query.data['org']
    selected_server = query.data['server']
    admin_dict = db_client[secrets['DBName']].admins.find_one({'user_id': update.effective_user.id})
    server_dict = db_client[secrets['DBName']].servers.find_one({'name': selected_server})
    if selected_org not in admin_dict['orgs'] or selected_org != server_dict['org']:
        reply_text = "Unathorized! Also, How are you here?"
        await update.effective_message.edit_text(reply_text)
        db_client.close()
        return telext.ConversationHandler.END
    else:
        reply_text = "Please send an INTEGER number.\nClick cancel to abort."
        context.user_data['org'] = selected_org
        context.user_data['server'] = selected_server
        keyboard = [
            [telegram.InlineKeyboardButton('❌ Cancel', callback_data='Cancel')]
        ] 
        reply_markup = telegram.InlineKeyboardMarkup(keyboard)
        await update.effective_message.edit_text(reply_text, reply_markup=reply_markup, parse_mode=telegram.constants.ParseMode.MARKDOWN)
        db_client.close()
        return CHANGING_SERVER_TRAFFIC


async def change_server_traffic_inputed(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    try: 
        db_client = connect_to_database(secrets['DBConString'])
    except Exception:
        print("Failed to connect to the database!")

    if not await check_subscription(update):
        main_channel = db_client[secrets['DBName']].orgs.find_one({'name': 'main'})['channel']['link']
        reply_text = org_admin_texts('join_channel') + f'\n\n{main_channel}'
        await update.effective_message.reply_text(reply_text)
        return telext.ConversationHandler.END
    selected_org = context.user_data['org']
    selected_server = context.user_data['server']
    admin_dict = db_client[secrets['DBName']].admins.find_one({'user_id': update.effective_user.id})
    server_dict = db_client[secrets['DBName']].servers.find_one({'name': selected_server})
    if selected_org not in admin_dict['orgs'] or selected_org != server_dict['org']:
        reply_text = "Unathorized! Also, How are you here?"
        await update.effective_message.reply_text(reply_text)
        db_client.close()
        return telext.ConversationHandler.END
    else:
        new_traffic = int(update.effective_message.text)
        db_client[secrets['DBName']].servers.update_one(
            {'name': selected_server},
            {'$set': {'traffic': new_traffic}}
        )
        reply_text = f"Server: {selected_server}'s Default Traffic Changed to " + (f'{new_traffic}' + org_admin_texts("GB")) if new_traffic != 0 else 'Unlimited' + '.'
        
        await update.effective_message.reply_text(reply_text, parse_mode=telegram.constants.ParseMode.MARKDOWN)
        db_client.close()
        return telext.ConversationHandler.END 