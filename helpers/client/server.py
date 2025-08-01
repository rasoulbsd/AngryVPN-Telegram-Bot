"""
Server/Vmess management functions for client flows.
"""

import telegram
import telegram.ext as telext
import uuid
import helpers.xuiAPI as xAPI
from helpers.initial import get_secrets_config, connect_to_database, set_lang
from helpers.bot_functions import check_subscription
from helpers.states import (
    DELIVER_SERVER,
    DELIVER_USER_VMESS_STATUS,
    DELIVER_REFRESH_VMESS,
    REVOKE_SERVERS
)
import html
import re

(secrets, Config) = get_secrets_config()
# Removed global client_functions_texts


def escape_markdown_v2(text):
    # Escape all special characters for MarkdownV2
    return re.sub(r'([_\*\[\]()~`>#+\-=|{}.!])', r'\\\1', str(text))

# --- Unified Server Selection ---


async def check_lang(user_obj, db_client):
    user_lang = user_obj.get('lang', Config['default_language'])
    client_functions_texts = set_lang(user_lang, 'client_functions')
    if user_obj['lang'] != Config['default_language']:
        return True
    return False


async def get_unified_servers(update: telegram.Update,
                              context: telext.ContextTypes.DEFAULT_TYPE):
    """
    Unified server selection that shows both new and existing servers with
    visual indicators.
    - Shows "🔴 NEW" tag for servers user hasn't received yet
    - Shows "⭐ RECOMMENDED" for recommended servers
    - Shows existing servers without special tags
    - Shows "📱 YOUR SERVERS" for servers user already has
    """
    try:
        db_client = connect_to_database(secrets['DBConString'])
    except Exception:
        print("Failed to connect to the database!")

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
            {'name': 'main'})['channel']['link']
        reply_text = (client_functions_texts('join_channel') +
                     f"\n\n{main_channel}")
        await update.effective_message.edit_text(reply_text)
        db_client.close()
        return telext.ConversationHandler.END

    if user_dict is None:
        reply_text = client_functions_texts("user_not_found")
        await update.effective_message.edit_text(reply_text)
        db_client.close()
        return telext.ConversationHandler.END

    # Get user's existing servers
    user_servers = user_dict.get("server_names", [])
    org_names = list(user_dict.get('orgs', {}).keys())

    # Get all available servers for the user
    server_list = list(db_client[secrets['DBName']].servers.find({
        '$or': [
            {
                'AcceptingNew': True,
                "$or": [
                    {'isActive': {"$exists": True, "$eq": True}},
                    {"isActive": {"$exists": False}}
                ],
                "role": {'$in': list(set((user_dict.get('role', []) or []) +
                                     ['normal']))},
            },
            {
                'AcceptingNew': False,
                'org': {'$in': org_names},
                "$or": [
                    {'isActive': {"$exists": True, "$eq": True}},
                    {"isActive": {"$exists": False}}
                ],
                "role": {'$in': list(set((user_dict.get('role', []) or []) +
                                     ['normal']))},
            }
        ],
    }))

    if len(server_list) == 0:
        print("Here")
        reply_text = client_functions_texts("no_server_available")
        await update.effective_message.edit_text(reply_text)
        db_client.close()
        return telext.ConversationHandler.END

    # Create keyboard with visual indicators
    keyboard = []
    reply_text = f"{client_functions_texts('select_server')}\n\n"

    # Group servers by status
    new_servers = []
    existing_servers = []
    recommended_servers = []

    for server in server_list:
        server_name = server['name']
        is_new = server_name not in user_servers
        is_recommended = server.get('isRecommended', False)

        if is_new:
            new_servers.append(server)
        elif is_recommended:
            recommended_servers.append(server)
        else:
            existing_servers.append(server)

    existing_server_names = {server['name'] for server in existing_servers}
    new_servers = [server for server in new_servers if server['name'] not in existing_server_names]

    # Add recommended servers first (if any)
    if recommended_servers:
        reply_text += f"<b>{client_functions_texts('recommended_servers')}</b>\n"
        for server in recommended_servers:
            if server.get('isNew', False):
                display_name = f"🔴 {html.escape(server['name'])} ({html.escape(client_functions_texts('new'))})"
            else:
                display_name = f"⭐ {html.escape(server['name'])} ({html.escape(client_functions_texts('recommended'))})"
            keyboard.append([telegram.InlineKeyboardButton(
                display_name, callback_data=server['name'])])
            reply_text += f"- {html.escape(server['name'])}\n"
        reply_text += "---------------------\n\n"

    # Add new servers
    if new_servers:
        reply_text += f"<b>{client_functions_texts('new_servers')}</b>\n"
        for server in new_servers:
            display_name = f"🔴 {html.escape(server['name'])} ({html.escape(client_functions_texts('new'))})"
            keyboard.append([telegram.InlineKeyboardButton(
                display_name, callback_data=server['name'])])
            reply_text += f"- {html.escape(server['name'])}\n"
        reply_text += "---------------------\n\n"

    # Add existing servers
    if existing_servers:
        reply_text += f"<b>{client_functions_texts('your_servers')}</b>\n"
        for server in existing_servers:
            display_name = f"📱 {html.escape(server['name'])}"
            keyboard.append([telegram.InlineKeyboardButton(
                display_name, callback_data=server['name'])])
            reply_text += f"- {html.escape(server['name'])}\n"
        reply_text += "---------------------\n\n"

    # Add cancel button
    keyboard.append([telegram.InlineKeyboardButton(
        client_functions_texts("general_cancel"), callback_data='Cancel')])

    reply_markup = telegram.InlineKeyboardMarkup(keyboard)
    await update.effective_message.edit_text(
        reply_text, reply_markup=reply_markup,
        parse_mode=telegram.constants.ParseMode.HTML)
    db_client.close()
    return DELIVER_SERVER


# --- Get New Server and Vmess ---
async def get_vmess_start(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    try:
        db_client = connect_to_database(secrets['DBConString'])
    except Exception:
        print("Failed to connect to the database!")

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
        main_channel = db_client[secrets['DBName']].orgs.find_one({'name': 'main'})['channel']['link']
        reply_text = client_functions_texts('join_channel') + f"\n\n{main_channel}"
        await update.effective_message.edit_text(reply_text)
        db_client.close()
        return telext.ConversationHandler.END
    else:
        user_dict = db_client[secrets['DBName']].users.find_one({'user_id': update.effective_user.id})
        if user_dict is None:
            reply_text = client_functions_texts("user_not_found")
            await update.effective_message.edit_text(reply_text)
            db_client.close()
            return telext.ConversationHandler.END
        elif len(user_dict["server_names"]) < 10:
            org_names = list(user_dict['orgs'].keys())
            user_servers = user_dict["server_names"]
            server_list = list(db_client[secrets['DBName']].servers.find({
                '$or': [
                    {
                        'AcceptingNew': True,
                        'name': {'$not': {'$in': user_servers}},
                        "$or": [
                            {'isActive': {"$exists": True, "$eq": True}},
                            {"isActive": {"$exists": False}}
                        ],
                        "role": {'$in': list(set((user_dict['role'] or [] if 'role' in user_dict else []) + ['normal']))},
                    },
                    {
                        'AcceptingNew': False,
                        'org': {'$in': org_names},
                        'name': {'$not': {'$in': user_servers}},
                        "$or": [
                            {'isActive': {"$exists": True, "$eq": True}},
                            {"isActive": {"$exists": False}}
                        ],
                        "role": {'$in': list(set((user_dict['role'] or [] if 'role' in user_dict else []) + ['normal']))},
                    }
                ],
            }))
            if len(server_list) == 0:
                reply_text = client_functions_texts("no_server_available")
                await update.effective_message.edit_text(reply_text)
                db_client.close()
                return telext.ConversationHandler.END
            keyboard = [
                [telegram.InlineKeyboardButton(s['name'], callback_data=s['name'])] for s in server_list
            ] + [
                [telegram.InlineKeyboardButton(client_functions_texts("general_cancel"), callback_data='Cancel')]
            ]
            reply_markup = telegram.InlineKeyboardMarkup(keyboard)
            reply_text = client_functions_texts("select_server") + '\n'
            reply_text += client_functions_texts("servers_list") +'\n\n'
            servers_rowRemarks = {}
            for s in server_list:
                if (s['rowRemark'] not in servers_rowRemarks):
                    servers_rowRemarks[s['rowRemark']] = {}
                    servers_rowRemarks[s['rowRemark']]['servers'] = []
                    servers_rowRemarks[s['rowRemark']]['traffic'] = s['traffic']
                servers_rowRemarks[s['rowRemark']]['servers'].append(s['name'])
            for row in servers_rowRemarks:
                for server in servers_rowRemarks[row]['servers']:
                    reply_text += f"{server}\n"
                reply_text += "---------------------\n"
            print("reply_text")
            print(reply_text)
            await update.effective_message.edit_text(reply_text, reply_markup=reply_markup, parse_mode=telegram.constants.ParseMode.MARKDOWN)
            db_client.close()
            return DELIVER_SERVER


async def deliver_vmess(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    try:
        db_client = connect_to_database(secrets['DBConString'])
    except Exception:
        print("Failed to connect to the database!")

    # Define client_functions_texts for localization
    user_id = update.effective_user.id
    user_dict = db_client[secrets['DBName']].users.find_one({'user_id': user_id})
    user_lang = user_dict.get('lang', Config['default_language']) if user_dict else Config['default_language']
    client_functions_texts = set_lang(user_lang, 'client_functions')

    query = update.callback_query
    await query.answer()
    if query.data == 'Cancel':
        db_client.close()
        return telext.ConversationHandler.END
    server_name = query.data
    user_dict = db_client[secrets['DBName']].users.find_one({'user_id': update.effective_user.id})
    server_dict = db_client[secrets['DBName']].servers.find_one({'name': server_name, 'org':list(user_dict["orgs"].keys())[0]})
    is_error = False
    user_client = xAPI.get_clients(server_dict, select=[f"{user_dict['user_id']}-{server_dict['name']}@{server_dict['rowRemark']}"])
    print(user_client)
    if user_client is None or user_client.shape[0] == 0:
        temp = str(uuid.uuid4())
        result = xAPI.add_client(
            server_dict=server_dict,
            username=f"{user_dict['user_id']}-{server_dict['name']}",
            traffic=0,
            uuid=temp,
        )
        if result[0] != 1:
            if "uplicate" not in result[1]:
                is_error = True
                vmess_str = client_functions_texts("error_failed_account_creations")
                print("Error - Failed to Create Account")
                print(result)
        if not is_error:
            user_client = xAPI.get_clients(server_dict, select=[f"{user_dict['user_id']}-{server_dict['name']}@{server_dict['rowRemark']}"])
            if user_client.shape[0] == 0:
                is_error = True
                vmess_str = client_functions_texts("error_get_config_api_conflict")
                print("Failed to get your config (API/Database Conflict)")
                print(user_client)
            else:
                reply_text = client_functions_texts("account_ready")
                reply_text += f"\nRemark: `{user_dict['user_id']}@{server_dict['name']}`"
                reply_text += f"\n{'-'*25}"
                user_client = user_client.iloc[0]
                vmess_str = xAPI.generate_vmess(
                    server_dict,
                    f"{user_dict['user_id']}",
                    temp
                )
    else:
        reply_text = client_functions_texts("account_ready")
        reply_text += f"\nRemark: `{user_dict['user_id']}@{server_dict['name']}`"
        reply_text += f"\n{'-'*25}"
        print()
        user_client = user_client.iloc[0]
        vmess_str = xAPI.generate_vmess(
            server_dict,
            f"{user_dict['user_id']}",
            user_client['uuid']
        )
    result_text = vmess_str if is_error else f"*{reply_text}*\n\n`{vmess_str}`"
    if (not is_error):
        db_client[secrets['DBName']].users.update_one({'user_id': user_dict['user_id']}, {'$push': {'server_names': server_name}})
    await query.edit_message_text(text=result_text, parse_mode=telegram.constants.ParseMode.MARKDOWN)
    db_client.close()
    return telext.ConversationHandler.END


async def get_status(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    try:
        db_client = connect_to_database(secrets['DBConString'])
    except Exception:
        print("Failed to connect to the database!")
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
        main_channel = db_client[secrets['DBName']].orgs.find_one({'name': 'main'})['channel']['link']
        reply_text = client_functions_texts('join_channel') + "\n\n{main_channel}"
        await update.effective_message.edit_text(reply_text)
        db_client.close()
        return telext.ConversationHandler.END
    else:
        user_dict = db_client[secrets['DBName']].users.find_one({'user_id': update.effective_user.id})
        if user_dict is None:
            reply_text = client_functions_texts("user_not_found")
            await update.effective_message.edit_text(reply_text)
            db_client.close()
            return telext.ConversationHandler.END
        elif len(user_dict['server_names']) == 0:
            reply_text = client_functions_texts("get_an_account")
            await update.effective_message.edit_text(reply_text)
            db_client.close()
            return telext.ConversationHandler.END
        else:
            keyboard = [
                [telegram.InlineKeyboardButton(s, callback_data=s)] for s in user_dict['server_names']
            ] + [
                [telegram.InlineKeyboardButton(client_functions_texts("general_cancel"), callback_data='Cancel')]
            ]
            reply_markup = telegram.InlineKeyboardMarkup(keyboard)
            reply_text = client_functions_texts('get_an_account') + '\n'
            await update.effective_message.edit_text(reply_text, reply_markup=reply_markup, parse_mode=telegram.constants.ParseMode.MARKDOWN)
            db_client.close()
            return DELIVER_USER_VMESS_STATUS


async def deliver_vmess_status(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    try:
        db_client = connect_to_database(secrets['DBConString'])
    except Exception:
        print("Failed to connect to the database!")
    query = update.callback_query
    await query.answer()
    if query.data == 'Cancel':
        db_client.close()
        return telext.ConversationHandler.END
    server_name = query.data
    user_dict = db_client[secrets['DBName']].users.find_one({'user_id': update.effective_user.id})
    if not user_dict:
        reply_text = client_functions_texts("error_get_account_status")
    else:
        reply_text = client_functions_texts("account_status") + '\n'
        reply_text += client_functions_texts("username") + f': _{user_dict["user_id"]}_\n'
        reply_text += client_functions_texts("server_name") + f': _{server_name}_\n'
        reply_text += client_functions_texts("active") + f': _{"Yes" if user_dict.get("enable", True) else "No"}_\n'
        reply_text += 'مانده کیف پول' + f': {user_dict["wallet"]} ' + 'تومان' + '_\n'
    await update.effective_message.edit_text(reply_text, parse_mode=telegram.constants.ParseMode.MARKDOWN)
    db_client.close()
    return telext.ConversationHandler.END


async def refresh_vmess(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    try:
        db_client = connect_to_database(secrets['DBConString'])
    except Exception:
        print("Failed to connect to the database!")

    user_id = update.effective_user.id
    user_dict = db_client[secrets['DBName']].users.find_one({'user_id': user_id})
    user_lang = user_dict.get('lang', Config['default_language']) if user_dict else Config['default_language']
    client_functions_texts = set_lang(user_lang, 'client_functions')

    user_org = db_client[secrets['DBName']].orgs.find_one({'name': list(user_dict['orgs'].keys())[0]})
    if 'rial' in user_org['payment_options']['currencies']:
        currency = 'rial'
    elif 'cad' in user_org['payment_options']['currencies']:
        currency = 'cad'
    else:
        print("Not Implemented")
        raise EOFError

    query = update.callback_query
    await query.answer()
    if query.data == 'Cancel':
        db_client.close()
        return telext.ConversationHandler.END
    if not await check_subscription(update):
        main_channel = db_client[secrets['DBName']].orgs.find_one({'name': 'main'})['channel']['link']
        reply_text = client_functions_texts('join_channel') + f"\n\n{main_channel}"
        await update.effective_message.edit_text(reply_text)
        db_client.close()
        return telext.ConversationHandler.END
    else:
        user_dict = db_client[secrets['DBName']].users.find_one({'user_id': update.effective_user.id})
        if user_dict is None:
            reply_text = client_functions_texts("user_not_found")
            await update.effective_message.edit_text(reply_text)
            db_client.close()
            return telext.ConversationHandler.END
        elif len(user_dict["server_names"]) == 0:
            reply_text = client_functions_texts("get_an_account")
            await update.effective_message.edit_text(reply_text)
            db_client.close()
            return telext.ConversationHandler.END
        else:
            reply_text = ''
            reply_text_header = client_functions_texts("servers_list").replace("=", '')
            servers_rowRemarks = {}
            server_list = list(db_client[secrets['DBName']].servers.find(
                filter={
                    'name': {'$in': user_dict["server_names"]},
                    'org': {'$in': list(user_dict['orgs'].keys())},
                    "$or": [
                        {'isActive': {"$exists": True, "$eq": True}},
                        {"isActive": {"$exists": False}}
                    ]
                },
            ))
            keyboard = [
                [telegram.InlineKeyboardButton(s['name'], callback_data=s['name'])] for s in server_list
            ] + [
                [telegram.InlineKeyboardButton(client_functions_texts("general_cancel"), callback_data='Cancel')]
            ]
            reply_markup = telegram.InlineKeyboardMarkup(keyboard)
            for s in server_list:
                if s['rowRemark'] not in servers_rowRemarks:
                    servers_rowRemarks[s['rowRemark']] = {}
                    servers_rowRemarks[s['rowRemark']]['servers'] = []
                    servers_rowRemarks[s['rowRemark']]['traffic'] = s['traffic']
                servers_rowRemarks[s['rowRemark']]['servers'].append({'name': s['name'], 'price': s['price']})
            max_dash = 0
            for row in servers_rowRemarks:
                for server in servers_rowRemarks[row]['servers']:
                    temp = f'*{server["name"]}*: ' + f'{server["price"]} ' + client_functions_texts('price_per_gb_rial' if currency == 'rial' else 'price_per_gb_cad') + ' \n'
                    reply_text += temp
                    if len(temp) > max_dash:
                        max_dash = len(temp)
                reply_text += f"{'-'*max_dash}\n"
            final_reply_text = '='*((max_dash-len(reply_text_header)-4)//2) + reply_text_header + '='*((max_dash-len(reply_text_header)-4)//2) + "\n\n" + reply_text
            await update.effective_message.edit_text(final_reply_text, reply_markup=reply_markup, parse_mode=telegram.constants.ParseMode.MARKDOWN)
            db_client.close()
            return DELIVER_REFRESH_VMESS


async def deliver_refresh_vmess(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    try:
        db_client = connect_to_database(secrets['DBConString'])
    except Exception:
        print("Failed to connect to the database!")
    query = update.callback_query
    await query.answer()
    if query.data == 'Cancel':
        db_client.close()
        return telext.ConversationHandler.END
    server_name = query.data
    user_dict = db_client[secrets['DBName']].users.find_one({'user_id': update.effective_user.id})
    server_dict = db_client[secrets['DBName']].servers.find_one({'name': server_name, 'org':list(user_dict["orgs"].keys())[0]})
    is_error = False
    reply_text = client_functions_texts("refreshed_vmess")
    reply_text += f"\nRemark: `{user_dict['user_id']}@{server_dict['name']}`"
    reply_text += f"\n{'-'*25}"
    vmess_str = ""
    user_client = xAPI.get_clients(server_dict, select=[f"{user_dict['user_id']}-{server_dict['name']}@{server_dict['rowRemark']}"])
    if user_client.shape[0] == 0:
        is_error = True
        reply_text = client_functions_texts("error_get_config_api_conflict")
    else:
        user_client = user_client.iloc[0]
        vmess_str = xAPI.generate_vmess(
            server_dict,
            f"{user_dict['user_id']}",
            user_client['uuid']
        )
    result_text = reply_text if is_error else f"*{reply_text}*\n\n`{vmess_str}`"
    await query.edit_message_text(text=result_text, parse_mode=telegram.constants.ParseMode.MARKDOWN)
    db_client.close()
    return telext.ConversationHandler.END


async def revoke_servers(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    """
    Shows initial revoke information and options to the user.
    """
    try:
        db_client = connect_to_database(secrets['DBConString'])
    except Exception:
        print("Failed to connect to the database!")

    # Define client_functions_texts for localization
    user_id = update.effective_user.id
    user_dict = db_client[secrets['DBName']].users.find_one({'user_id': user_id})
    user_lang = user_dict.get('lang', Config['default_language']) if user_dict else Config['default_language']
    client_functions_texts = set_lang(user_lang, 'client_functions')

    query = update.callback_query
    await query.answer()

    if query.data == 'Cancel':
        db_client.close()
        return telext.ConversationHandler.END

    # Check if user exists and has servers
    if user_dict is None:
        reply_text = client_functions_texts("user_not_found")
        await update.effective_message.edit_text(reply_text)
        db_client.close()
        return telext.ConversationHandler.END

    if len(user_dict["server_names"]) == 0:
        reply_text = client_functions_texts("get_an_account")
        await update.effective_message.edit_text(reply_text)
        db_client.close()
        return telext.ConversationHandler.END

        # Create informative message about revoke process
    reply_text = f"**{client_functions_texts('revoke_title')}**\n\n"
    reply_text += f"**{client_functions_texts('revoke_what_happens')}**\n"
    reply_text += f"{client_functions_texts('revoke_configs_invalid')}\n"
    # reply_text += f"{client_functions_texts('revoke_new_configs')}\n"
    reply_text += f"{client_functions_texts('revoke_preserve_data')}\n"
    reply_text += f"{client_functions_texts('revoke_immediate_configs')}\n\n"

    reply_text += f"**{client_functions_texts('revoke_important_notes')}**\n"
    reply_text += f"{client_functions_texts('revoke_cannot_undo')}\n"
    reply_text += f"{client_functions_texts('revoke_update_clients')}\n"
    reply_text += f"{client_functions_texts('revoke_terminate_connections')}\n\n"

    # reply_text += f"**{client_functions_texts('revoke_servers_affected')}** " + str(len(user_dict["server_names"])) + "\n\n"

    reply_text += client_functions_texts('revoke_proceed_question')

    # Create keyboard with options
    keyboard = [
        [telegram.InlineKeyboardButton(client_functions_texts('revoke_accept_button'), callback_data="Accept")],
        [telegram.InlineKeyboardButton(client_functions_texts("general_cancel"), callback_data="Cancel")]
    ]
    reply_markup = telegram.InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        text=reply_text,
        reply_markup=reply_markup,
        parse_mode=telegram.constants.ParseMode.MARKDOWN
    )

    db_client.close()
    return REVOKE_SERVERS


async def revoke_servers_accepted(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    try:
        db_client = connect_to_database(secrets['DBConString'])
    except Exception:
        print("Failed to connect to the database!")

    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    user_dict = db_client[secrets['DBName']].users.find_one({'user_id': user_id})
    user_lang = user_dict.get('lang', Config['default_language']) if user_dict else Config['default_language']
    client_functions_texts = set_lang(user_lang, 'client_functions')

    if query.data == 'Cancel':
        db_client.close()
        return telext.ConversationHandler.END

    user_dict = db_client[secrets['DBName']].users.find_one({'user_id': user_id})
    if user_dict is None:
        reply_text = client_functions_texts("user_not_found")
        await update.effective_message.edit_text(reply_text)
        db_client.close()
        return telext.ConversationHandler.END

    if len(user_dict["server_names"]) == 0:
        reply_text = client_functions_texts("get_an_account")
        await update.effective_message.edit_text(reply_text)
        db_client.close()
        return telext.ConversationHandler.END

    # Get all servers for the user
    server_list = list(db_client[secrets['DBName']].servers.find(
        filter={
            'name': {'$in': user_dict["server_names"]},
            'org': {'$in': list(user_dict['orgs'].keys())},
            "$or": [
                {'isActive': {"$exists": True, "$eq": True}},
                {"isActive": {"$exists": False}}
            ]
        },
    ))

    if not server_list:
        reply_text = client_functions_texts("no_servers_found")
        await update.effective_message.edit_text(reply_text)
        db_client.close()
        return telext.ConversationHandler.END

    # Revoke UUIDs from all servers
    revoked_count = 0
    failed_count = 0
    error_messages = []

    for server_dict in server_list:
        try:
            # Regenerate the client's UUID
            result = xAPI.regenerate_client_uuid(server_dict, user_dict['user_id'])
            if result[0] == 1:
                revoked_count += 1
                new_uuid = result[1]
                print(f"Successfully regenerated UUID for server {server_dict['name']}: {new_uuid}")
            else:
                failed_count += 1
                error_msg = f"Failed to revoke from {server_dict['name']}: {result[1]}"
                error_messages.append(error_msg)
                print(error_msg)
        except Exception as e:
            failed_count += 1
            error_msg = f"Error revoking from {server_dict['name']}: {str(e)}"
            error_messages.append(error_msg)
            print(error_msg)

        # Prepare response message
    if revoked_count > 0:
        reply_text = client_functions_texts("revoke_success") + str(revoked_count)

        # if failed_count > 0:
        #     reply_text += f"\n❌ Failed to revoke {failed_count} server(s)"
    else:
        reply_text = client_functions_texts("revoke_failed")

    # Add error details if any
    # if error_messages:
    #     reply_text += "\n\nError details:\n" + "\n".join(error_messages[:3])

    await query.edit_message_text(text=reply_text, parse_mode=telegram.constants.ParseMode.MARKDOWN)

    # Send a separate message with server selection
    await send_server_selection_message(update, context, user_dict, db_client)

    db_client.close()
    return telext.ConversationHandler.END


async def send_server_selection_message(update, context, user_dict, db_client):
    """
    Sends VMess configuration immediately in a new message after revoke operation.
    Shows recommended servers if available, otherwise shows the first active server.
    """
    user_lang = user_dict.get('lang', Config['default_language'])
    client_functions_texts = set_lang(user_lang, 'client_functions')
    
    # Get all available servers for the user
    server_list = list(db_client[secrets['DBName']].servers.find({
        '$or': [
            {
                'AcceptingNew': True,
                "$or": [
                    {'isActive': {"$exists": True, "$eq": True}},
                    {"isActive": {"$exists": False}}
                ],
                "role": {'$in': list(set((user_dict.get('role', []) or []) +
                                     ['normal']))},
            },
            {
                'AcceptingNew': False,
                'org': {'$in': list(user_dict['orgs'].keys())},
                "$or": [
                    {'isActive': {"$exists": True, "$eq": True}},
                    {"isActive": {"$exists": False}}
                ],
                "role": {'$in': list(set((user_dict.get('role', []) or []) +
                                     ['normal']))},
            }
        ],
    }))

    if not server_list:
        return

    # Find recommended and active servers
    recommended_servers = []
    active_servers = []

    for server in server_list:
        if server.get('isRecommended', False):
            recommended_servers.append(server)
        elif server.get('isActive', True):  # Default to True if not specified
            active_servers.append(server)

    # Select servers to show
    servers_to_show = []
    if recommended_servers:
        # Show all recommended servers
        servers_to_show = recommended_servers
    elif active_servers:
        # Show the first active server
        servers_to_show = [active_servers[0]]

    if not servers_to_show:
        return

    # Send configuration for each selected server
    for server_dict in servers_to_show:
        try:
            # Get or create client for this server
            user_client = xAPI.get_clients(server_dict, select=[f"{user_dict['user_id']}-{server_dict['name']}@{server_dict['rowRemark']}"])

            if user_client is None or user_client.empty:
                # Create new client if it doesn't exist
                import uuid
                temp = str(uuid.uuid4())
                result = xAPI.add_client(
                    server_dict=server_dict,
                    username=f"{user_dict['user_id']}-{server_dict['name']}",
                    traffic=0,
                    uuid=temp
                )
                if result[0] != 1:
                    continue
                user_uuid = temp
            else:
                user_client = user_client.iloc[0]
                user_uuid = user_client['uuid']

            # Generate VMess configuration
            vmess_str = xAPI.generate_vmess(
                server_dict,
                f"{user_dict['user_id']}",
                user_uuid
            )

            # Create message content
            server_name = server_dict['name']
            is_recommended = server_dict.get('isRecommended', False)
            is_new = server_dict.get('isNew', False)

            if is_recommended:
                header = f"⭐ **{server_name}** (Recommended)"
            elif is_new:
                header = f"🔴 **{server_name}** (New)"
            else:
                header = f"📱 **{server_name}**"

            reply_text = f"{header}\n"
            reply_text += f"Remark: `{user_dict['user_id']}-{server_dict['name']}@{server_dict['rowRemark']}`\n"
            reply_text += f"{'-'*25}\n\n"
            reply_text += f"`{vmess_str}`"

            # Send as a new message
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=reply_text,
                parse_mode=telegram.constants.ParseMode.MARKDOWN
            )

        except Exception as e:
            print(f"Error generating config for server {server_dict['name']}: {str(e)}")
            continue
