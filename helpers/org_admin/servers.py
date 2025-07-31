import telegram
import telegram.ext as telext
import requests
from ..initial import connect_to_database, get_secrets_config, set_lang
from ..bot_functions import check_subscription
from helpers.states import (
    LISTING_ORG_SERVERS, CHOSING_SERVER_EDIT_ACTION, 
    CHANGING_SERVER_TRAFFIC, MY_ORG_MNGMNT_SELECT_OPTION, 
    VMESS_TEST_SELECT_ENDPOINT, VMESS_TEST_INPUT_CONFIG
)

(secrets, Config) = get_secrets_config()
org_admin_texts = set_lang(Config['default_language'], 'org_admin')


async def vmess_test(update: telegram.Update, 
                    context: telext.ContextTypes.DEFAULT_TYPE):
    """Handle the initial vmess test selection - show available endpoints"""
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
            {'name': 'main'})['channel']['link']
        reply_text = org_admin_texts('join_channel') + f'\n\n{main_channel}'
        await update.effective_message.edit_text(reply_text)
        db_client.close()
        return telext.ConversationHandler.END

    selected_org = query.data['org']
    admin_dict = db_client[secrets['DBName']].admins.find_one(
        {'user_id': update.effective_user.id})
    if selected_org not in admin_dict['orgs']:
        reply_text = "Unauthorized! Also, How are you here?"
        await update.effective_message.edit_text(reply_text)
        db_client.close()
        return telext.ConversationHandler.END

    # Get the org's vmess test servers
    org_data = db_client[secrets['DBName']].orgs.find_one({'name': selected_org})
    vmess_test_servers = org_data.get('vmess_test_servers', [])

    if not vmess_test_servers:
        reply_text = "No vmess test endpoints configured for this organization."
        keyboard = [
            [telegram.InlineKeyboardButton('❌ Cancel', callback_data='Cancel')]
        ]
        reply_markup = telegram.InlineKeyboardMarkup(keyboard)
        await update.effective_message.edit_text(reply_text, reply_markup=reply_markup)
        db_client.close()
        return telext.ConversationHandler.END

    # Create buttons for each endpoint
    keyboard = []
    for i, server in enumerate(vmess_test_servers):
        country = server.get('country', 'Unknown').upper()
        datacenter = server.get('datacenter', 'Unknown')
        button_text = f"🌍 {country} - {datacenter}"
        callback_data = {
            'task': 'Select VMess Test Endpoint',
            'org': selected_org,
            'endpoint_index': i
        }
        keyboard.append([telegram.InlineKeyboardButton(button_text, 
                                                    callback_data=callback_data)])

    keyboard.append([telegram.InlineKeyboardButton('❌ Cancel', callback_data='Cancel')])
    reply_markup = telegram.InlineKeyboardMarkup(keyboard)
    reply_text = f"Select a VMess test endpoint for {selected_org}:"

    await update.effective_message.edit_text(reply_text, reply_markup=reply_markup)
    db_client.close()
    return VMESS_TEST_SELECT_ENDPOINT


async def vmess_test_select_endpoint(update: telegram.Update, 
                                   context: telext.ContextTypes.DEFAULT_TYPE):
    """Handle endpoint selection and prompt for vmess config"""
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
            {'name': 'main'})['channel']['link']
        reply_text = org_admin_texts('join_channel') + f'\n\n{main_channel}'
        await update.effective_message.edit_text(reply_text)
        db_client.close()
        return telext.ConversationHandler.END

    selected_org = query.data['org']
    endpoint_index = query.data['endpoint_index']

    admin_dict = db_client[secrets['DBName']].admins.find_one(
        {'user_id': update.effective_user.id})
    if selected_org not in admin_dict['orgs']:
        reply_text = "Unauthorized! Also, How are you here?"
        await update.effective_message.edit_text(reply_text)
        db_client.close()
        return telext.ConversationHandler.END

    # Get the selected endpoint
    org_data = db_client[secrets['DBName']].orgs.find_one({'name': selected_org})
    vmess_test_servers = org_data.get('vmess_test_servers', [])

    if endpoint_index >= len(vmess_test_servers):
        reply_text = "Invalid endpoint selected."
        await update.effective_message.edit_text(reply_text)
        db_client.close()
        return telext.ConversationHandler.END

    selected_endpoint = vmess_test_servers[endpoint_index]

    # Store endpoint info in context for later use
    context.user_data['vmess_test_endpoint'] = selected_endpoint
    context.user_data['vmess_test_org'] = selected_org

    country = selected_endpoint.get('country', 'Unknown').upper()
    datacenter = selected_endpoint.get('datacenter', 'Unknown')

    reply_text = f"🌍 Testing endpoint: {country} - {datacenter}\n\n"
    reply_text += "Please send your VMess configuration to test:"

    keyboard = [
        [telegram.InlineKeyboardButton('❌ Cancel', callback_data='Cancel')]
    ]
    reply_markup = telegram.InlineKeyboardMarkup(keyboard)

    await update.effective_message.edit_text(reply_text, reply_markup=reply_markup)
    db_client.close()
    return VMESS_TEST_INPUT_CONFIG


async def vmess_test_input_config(update: telegram.Update, 
                                context: telext.ContextTypes.DEFAULT_TYPE):
    """Handle vmess config input and send to test endpoint"""
    try:
        db_client = connect_to_database(secrets['DBConString'])
    except Exception:
        print("Failed to connect to the database!")

    if not await check_subscription(update):
        main_channel = db_client[secrets['DBName']].orgs.find_one(
            {'name': 'main'})['channel']['link']
        reply_text = org_admin_texts('join_channel') + f'\n\n{main_channel}'
        await update.effective_message.reply_text(reply_text)
        return telext.ConversationHandler.END

    endpoint = context.user_data.get('vmess_test_endpoint')
    org_name = context.user_data.get('vmess_test_org')
    
    if not endpoint or not org_name:
        reply_text = "Session expired. Please try again."
        await update.effective_message.reply_text(reply_text)
        return telext.ConversationHandler.END

    admin_dict = db_client[secrets['DBName']].admins.find_one(
        {'user_id': update.effective_message.from_user.id})
    if org_name not in admin_dict['orgs']:
        reply_text = "Unauthorized! Also, How are you here?"
        await update.effective_message.reply_text(reply_text)
        db_client.close()
        return telext.ConversationHandler.END

    vmess_config = update.effective_message.text
    
    # Send loading message
    loading_message = await update.effective_message.reply_text(
        "🔄 Testing VMess configuration...\nThis may take up to 30 seconds.",
        parse_mode=telegram.constants.ParseMode.MARKDOWN
    )
    
    # Send the vmess config to the test endpoint
    try:
        test_url = endpoint['url']
        api_key = endpoint['apikey']
        
        headers = {
            'Content-Type': 'application/json',
            'X-API-Key': api_key
        }
        
        payload = {
            'vmess_link': vmess_config,
            'dest': endpoint.get('dest', ''),
            'country': endpoint.get('country', ''),
            'datacenter': endpoint.get('datacenter', '')
        }
        
        response = requests.post(test_url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            success = result.get('success', False)
            summary = result.get('summary', {})
            
            if success:
                reply_text = f"✅ **Test Successful!**\n\n"
                reply_text += f"🌍 **Endpoint:** {endpoint.get('country', 'Unknown').upper()} - {endpoint.get('datacenter', 'Unknown')}\n\n"
                
                # Add summary information
                if summary:
                    reply_text += "📊 **Test Summary:**\n"
                    avg_ping = summary.get('average_ping_ms', 'N/A')
                    packets_sent = summary.get('packets_sent', 'N/A')
                    packets_received = summary.get('packets_received', 'N/A')
                    packet_loss = summary.get('packet_loss_percent', 'N/A')
                    duration = summary.get('test_duration_seconds', 'N/A')
                    destination = summary.get('destination_url', 'N/A')
                    
                    reply_text += f"• **Average Ping:** {avg_ping} ms\n"
                    reply_text += f"• **Packets Sent/Received:** {packets_sent}/{packets_received}\n"
                    reply_text += f"• **Packet Loss:** {packet_loss}%\n"
                    reply_text += f"• **Test Duration:** {duration}s\n"
                    reply_text += f"• **Destination:** `{destination}`\n"
            else:
                reply_text = f"❌ **Test Failed!**\n\n"
                reply_text += f"🌍 **Endpoint:** {endpoint.get('country', 'Unknown').upper()} - {endpoint.get('datacenter', 'Unknown')}\n"
                reply_text += f"📡 **Error:** Test returned failure status"
        else:
            reply_text = f"❌ **Test Failed!**\n\n"
            reply_text += f"🌍 **Endpoint:** {endpoint.get('country', 'Unknown').upper()} - {endpoint.get('datacenter', 'Unknown')}\n"
            reply_text += f"📡 **HTTP Error:** {response.status_code}\n"
            reply_text += f"📄 **Response:** {response.text[:200]}"
            
    except requests.exceptions.Timeout:
        reply_text = f"❌ **Test Failed!**\n\n"
        reply_text += f"🌍 **Endpoint:** {endpoint.get('country', 'Unknown').upper()} - {endpoint.get('datacenter', 'Unknown')}\n"
        reply_text += f"📡 **Error:** Request timeout (30s)"
    except requests.exceptions.RequestException as e:
        reply_text = f"❌ **Test Failed!**\n\n"
        reply_text += f"🌍 **Endpoint:** {endpoint.get('country', 'Unknown').upper()} - {endpoint.get('datacenter', 'Unknown')}\n"
        reply_text += f"📡 **Error:** {str(e)}"
    except Exception as e:
        reply_text = f"❌ **Test Failed!**\n\n"
        reply_text += f"🌍 **Endpoint:** {endpoint.get('country', 'Unknown').upper()} - {endpoint.get('datacenter', 'Unknown')}\n"
        reply_text += f"📡 **Error:** Unexpected error - {str(e)}"

    # Clear the stored data
    context.user_data.pop('vmess_test_endpoint', None)
    context.user_data.pop('vmess_test_org', None)

    # Edit the loading message with the result
    try:
        await loading_message.edit_text(reply_text, 
                                      parse_mode=telegram.constants.ParseMode.MARKDOWN)
    except telegram.error.BadRequest as e:
        # If markdown parsing fails, send without markdown
        await loading_message.edit_text(reply_text)
    db_client.close()
    return telext.ConversationHandler.END


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
        main_channel = db_client[secrets['DBName']].orgs.find_one(
            {'name': 'main'})['channel']['link']
        reply_text = org_admin_texts('join_channel') + f'\n\n{main_channel}'
        await update.effective_message.edit_text(reply_text)
        db_client.close()
        return telext.ConversationHandler.END
    selected_org = query.data.removeprefix('Manage: ')
    if selected_org not in db_client[secrets['DBName']].admins.find_one(
        {'user_id': update.effective_user.id})['orgs']:
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
            [telegram.InlineKeyboardButton('🧪 Test a Connection', callback_data={'task':'Test Connection', 'org': selected_org})],
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
        main_channel = db_client[secrets['DBName']].orgs.find_one(
            {'name': 'main'})['channel']['link']
        reply_text = org_admin_texts('join_channel') + f'\n\n{main_channel}'
        await update.effective_message.edit_text(reply_text)
        db_client.close()
        return telext.ConversationHandler.END
    selected_org = query.data['org']
    admin_dict = db_client[secrets['DBName']].admins.find_one(
        {'user_id': update.effective_user.id})
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
    admin_dict = db_client[secrets['DBName']].admins.find_one(
        {'user_id': update.effective_user.id})
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
            [telegram.InlineKeyboardButton('Disable Server', callback_data=f'disable_server:{selected_server}')],
            [telegram.InlineKeyboardButton('Enable Server', callback_data=f'enable_server:{selected_server}')],
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
        main_channel = db_client[secrets['DBName']].orgs.find_one(
            {'name': 'main'})['channel']['link']
        reply_text = org_admin_texts('join_channel') + f'\n\n{main_channel}'
        await update.effective_message.edit_text(reply_text)
        db_client.close()
        return telext.ConversationHandler.END
    selected_org = query.data['org']
    selected_server = query.data['server']
    admin_dict = db_client[secrets['DBName']].admins.find_one(
        {'user_id': update.effective_user.id})
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
            [telegram.InlineKeyboardButton('Disable Server', callback_data=f'disable_server:{selected_server}')],
            [telegram.InlineKeyboardButton('Enable Server', callback_data=f'enable_server:{selected_server}')],
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
        main_channel = db_client[secrets['DBName']].orgs.find_one(
            {'name': 'main'})['channel']['link']
        reply_text = org_admin_texts('join_channel') + f'\n\n{main_channel}'
        await update.effective_message.edit_text(reply_text)
        db_client.close()
        return telext.ConversationHandler.END
    selected_org = query.data['org']
    selected_server = query.data['server']
    admin_dict = db_client[secrets['DBName']].admins.find_one(
        {'user_id': update.effective_user.id})
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
        main_channel = db_client[secrets['DBName']].orgs.find_one(
            {'name': 'main'})['channel']['link']
        reply_text = org_admin_texts('join_channel') + f'\n\n{main_channel}'
        await update.effective_message.reply_text(reply_text)
        return telext.ConversationHandler.END
    selected_org = context.user_data['org']
    selected_server = context.user_data['server']
    admin_dict = db_client[secrets['DBName']].admins.find_one(
        {'user_id': update.effective_user.id})
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

# Handler to disable a server and all user accounts for that server
async def disable_server_callback(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    server_name = query.data.split(":", 1)[1]
    db_client = connect_to_database(secrets['DBConString'])
    # Set server inactive
    db_client[secrets['DBName']].servers.update_one({'name': server_name}, {'$set': {'isActive': False}})
    # Disable all user accounts for this server
    db_client[secrets['DBName']].users.update_many(
        {'server_names': server_name},
        {'$set': {f'server_enabled.{server_name}': False}}
    )
    await query.edit_message_text(f"Server {server_name} has been disabled. All user accounts for this server are now disabled.")
    db_client.close()

# Handler to enable a server and all user accounts with positive wallet
async def enable_server_callback(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    server_name = query.data.split(":", 1)[1]
    db_client = connect_to_database(secrets['DBConString'])
    # Set server active
    db_client[secrets['DBName']].servers.update_one({'name': server_name}, {'$set': {'isActive': True}})
    # Enable user accounts with positive wallet
    users = db_client[secrets['DBName']].users.find({'server_names': server_name, 'wallet': {'$gt': 0}})
    for user in users:
        db_client[secrets['DBName']].users.update_one(
            {'user_id': user['user_id']},
            {'$set': {f'server_enabled.{server_name}': True}}
        )
    await query.edit_message_text(f"Server {server_name} has been enabled. All user accounts with positive wallet are now enabled.")
    db_client.close() 