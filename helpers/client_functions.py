import telegram
import telegram.ext as telext
import helpers.xuiAPI as xAPI
import datetime
from .initial import get_secrets_config, connect_to_database, set_lang
from .bot_functions import check_subscription, check_newuser, validate_transaction, verfiy_transaction, normalize_transaction_id, after_automatic_payment
import requests
import secrets as sc
import uuid

############################# GLOBALS #############################

# Stages
DELIVER_SERVER = range(1)
DELIVER_USER_VMESS_STATUS = range(1)
DELIVER_REFRESH_VMESS = range(1)

(
    RECEIVE_TICKET,
    USER_RECHARGE_ACCOUNT_SELECT_PLAN,
    USER_RECHARGE_ACCOUNT,
    USER_RECHARGE_ACCOUNT_RIAL_ZARIN,
    USER_RECHARGE_ACCOUNT_RIAL_ZARIN_PAID
) = range(5)

( 
    NEWUSER_PURCHASE_SELECT_PLAN,
    NEWUSER_PURCHASE_INTERCEPTOR,
    NEWUSER_PURCHASE_INTERCEPTOR_INPUTED,
    NEWUSER_PURCHASE_RIAL,
    NEWUSER_PURCHASE_RIAL_INPUTED,
    NEWUSER_PURCHASE_RIAL_ZARIN,
    NUEWUSER_PURCHASE_RECEIPT_CRYPTO,
    NEWUSER_PURCHASE_FINAL,
    CHECK_TRANS_MANUALLY,
    PAID
) = range(10)

(
    ADMIN_MENU, 
    ORG_MNGMNT_SELECT_OPTION, 
    MY_ORG_MNGMNT_SELECT_OPTION,
    ADDING_MEMEBER_TO_ORG,
    BAN_MEMBER,
    ADMIN_ANNOUNCEMENT,
    ADMIN_CHARGE_ACCOUNT_USERID,
    ADMIN_CHARGE_ACCOUNT_AMOUNT,
    ADMIN_CHARGE_ACCOUNT_FINAL,
    ADMIN_CHARGE_ALL_ACCOUNTS,
    ADMIN_CHARGE_ALL_ACCOUNTS_AMOUNT,
    LISTING_ORG_SERVERS,
    CHOSING_SERVER_EDIT_ACTION,
    CHANGING_SERVER_TRAFFIC
) = range(14)

(secrets, Config) = get_secrets_config()
client_functions_texts = set_lang(Config['default_language'], 'client_functions')

############################# Functions #############################


############## Get New Server and Vmess ##############
async def get_vmess_start(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    try: 
        db_client = connect_to_database(secrets['DBConString'])
    except Exception as e:
        print("Failed to connect to the database!")

    query = update.callback_query
    await query.answer()
    if query.data == 'Cancel':
        db_client.close()
        return telext.ConversationHandler.END

    if not await check_subscription(update):
        main_channel = db_client[secrets['DBName']].orgs.find_one({'name': 'main'})['channel']['link']
        reply_text = client_functions_texts('join_channel') + f"\n\n{main_channel}"
        await update.effective_message.edit_text(reply_text)
        # application.add_handler(menu_handler)

        db_client.close()

        return telext.ConversationHandler.END
    else:
        # client = pymongo.MongoClient(secrets['DBConString'])
        user_dict = db_client[secrets['DBName']].users.find_one({'user_id': update.effective_user.id})
        if user_dict is None:
            reply_text = client_functions_texts("user_not_found")
            await update.effective_message.edit_text(reply_text)
            # client.close()
            # application.add_handler(menu_handler)

            db_client.close()

            return telext.ConversationHandler.END
        elif len(user_dict["server_names"]) < 10: # TODO: add limit here 
            #New Vmess
            org_names = list(user_dict['orgs'].keys())
            user_servers = user_dict["server_names"]
            # server_list = []

            # Get servers in "AcceptingNew" state
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

            # servers_accepting_new = list(db_client[secrets['DBName']].servers.find({
            #     'AcceptingNew': True,
            #     'name': {'$not': {'$in': user_servers}}
            # }))

            # server_list.extend(servers_accepting_new)

            # # Get servers for user's orgs
            # org_servers = list(db_client[secrets['DBName']].servers.find({
            #     'org': {'$in': org_names},
            #     'name': {'$not': {'$in': user_servers}}
            # }))

            # for server in org_servers:
            #     if not server.get('AcceptingNew') and (server.get('org') in org_names):
            #         server_list.append(server)
            # server_list = list(db_client[secrets['DBName']].servers.find({
            #     '$and': [
            #         {'org': {'$in': list(user_dict['orgs'].keys())}},
            #         {'AcceptingNew': True},
            #         {'name': {'$not': {'$in': user_dict["server_names"]}}}
            #     ]
            # }))
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
            # Send message with text and appended InlineKeyboard
            reply_text = client_functions_texts("select_server") + '\n'
            reply_text += client_functions_texts("servers_list") +'\n\n'

            servers_rowRemarks = {}
            for s in server_list:
                if(s['rowRemark'] not in servers_rowRemarks):
                    servers_rowRemarks[s['rowRemark']] = {}
                    servers_rowRemarks[s['rowRemark']]['servers'] = []
                    servers_rowRemarks[s['rowRemark']]['traffic'] = s['traffic']

                servers_rowRemarks[s['rowRemark']]['servers'].append(s['name'])
                # server_traffic = s.get('traffic', Config['default_traffic'])
                # reply_text += f"{s['name']}\n"
            for row in servers_rowRemarks:
                # reply_text += f"\n{row}\n"
                for server in servers_rowRemarks[row]['servers']:
                    reply_text += f"{server}\n"
                reply_text += "---------------------\n"
                # reply_text += f"Traffic: 'Unlimited'" if servers_rowRemarks[row]['traffic'] == 0 else f"Limit: {servers_rowRemarks[row]['traffic']}GB" + "\n\n"

            print("reply_text")
            print(reply_text)
            await update.effective_message.edit_text(reply_text, reply_markup=reply_markup, parse_mode=telegram.constants.ParseMode.MARKDOWN)
            # client.close()

            db_client.close()

            return DELIVER_SERVER

async def deliver_vmess(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    try: 
        db_client = connect_to_database(secrets['DBConString'])
    except Exception as e:
        print("Failed to connect to the database!")

    query = update.callback_query
    await query.answer()
    if query.data == 'Cancel':
        db_client.close()
        return telext.ConversationHandler.END
    server_name = query.data

    # client = pymongo.MongoClient(secrets['DBConString'])
    user_dict = db_client[secrets['DBName']].users.find_one({'user_id': update.effective_user.id})
    server_dict = db_client[secrets['DBName']].servers.find_one({'name': server_name, 'org':list(user_dict["orgs"].keys())[0]})
    is_error = False

    #Create vmess
    user_client = xAPI.get_clients(server_dict, select=[f"{user_dict['user_id']}-{server_dict['name']}@{server_dict['rowRemark']}"])
    print(user_client)
    if type(user_client) == type(None) or user_client.shape[0] == 0:
        temp = str(uuid.uuid4())
        result = xAPI.add_client(
            server_dict=server_dict,
            username=f"{user_dict['user_id']}-{server_dict['name']}",
            traffic=0,
            uuid=temp,
            # expires=user_dict['orgs'][server_dict['org']]['expires'] + datetime.timedelta(days=1)
        )
        if result[0] != 1:
            if "uplicate" not in result[1]:
                is_error = True
                vmess_str = client_functions_texts("error_failed_account_creations")
                print("Error - Failed to Create Account")
                print(result)
        if is_error == False:
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
                # db_client[secrets['DBName']].users.update_one({'user_id': user_dict['user_id']}, {'$push': {'server_names': server_name}})
                # vmess_str = vmess_str.replace(f"{user_dict['user_id']}", f"{user_dict['user_id']}@{server_name}")
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

############## Get Vmess Status ##############
async def get_status(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    try: 
        db_client = connect_to_database(secrets['DBConString'])
    except Exception as e:
        print("Failed to connect to the database!")

    query = update.callback_query
    await query.answer()
    if query.data == 'Cancel':
        db_client.close()
        return telext.ConversationHandler.END    
    if not await check_subscription(update):
        main_channel = db_client[secrets['DBName']].orgs.find_one({'name': 'main'})['channel']['link']
        reply_text = client_functions_texts('join_channel') + "\n\n{main_channel}"
        await update.effective_message.edit_text(reply_text)
        # application.add_handler(menu_handler)

        db_client.close()

        return telext.ConversationHandler.END
    else:
        # client = pymongo.MongoClient(secrets['DBConString'])
        user_dict = db_client[secrets['DBName']].users.find_one({'user_id': update.effective_user.id})

        if user_dict is None:
            reply_text = client_functions_texts("user_not_found")
            await update.effective_message.edit_text(reply_text)
            # client.close()
            # application.add_handler(menu_handler)
            
            db_client.close()

            return telext.ConversationHandler.END
        elif len(user_dict['server_names']) == 0: 
            # No account yet
            reply_text = client_functions_texts("get_an_account")
            await update.effective_message.edit_text(reply_text)
            # client.close()
            # application.add_handler(menu_handler)

            db_client.close()

            return telext.ConversationHandler.END
        else: 
            keyboard = [
                [telegram.InlineKeyboardButton(s, callback_data=s)] for s in user_dict['server_names']
            ] + [
                [telegram.InlineKeyboardButton(client_functions_texts("general_cancel"), callback_data='Cancel')]
            ]
            reply_markup = telegram.InlineKeyboardMarkup(keyboard)
            # Send message with text and appended InlineKeyboard
            reply_text = client_functions_texts('get_an_account') + '\n'
            await update.effective_message.edit_text(reply_text, reply_markup=reply_markup, parse_mode=telegram.constants.ParseMode.MARKDOWN)
            # client.close()

            db_client.close()

            return DELIVER_USER_VMESS_STATUS

async def deliver_vmess_status(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    try: 
        db_client = connect_to_database(secrets['DBConString'])
    except Exception as e:
        print("Failed to connect to the database!")

    query = update.callback_query
    await query.answer()
    if query.data == 'Cancel':
        db_client.close()
        return telext.ConversationHandler.END
    server_name = query.data

    # client = pymongo.MongoClient(secrets['DBConString'])
    user_dict = db_client[secrets['DBName']].users.find_one({'user_id': update.effective_user.id})


    if not user_dict:
        reply_text = client_functions_texts("error_get_account_status")
    else:
        reply_text = client_functions_texts("account_status") + '\n'
        reply_text += client_functions_texts("username") + f': _{user_dict["user_id"]}_\n'
        reply_text += client_functions_texts("server_name") + f': _{server_name}_\n'
        reply_text += client_functions_texts("active") + f': _{"Yes" if row["enable"] else "No"}_\n'
        reply_text += 'مانده کیف پول' + f': {user_dict["wallet"]} ' + 'تومان' + '_\n'
    # client.close()
    
    await update.effective_message.edit_text(reply_text, parse_mode=telegram.constants.ParseMode.MARKDOWN)
    # application.add_handler(menu_handler)

    db_client.close()

    return telext.ConversationHandler.END

############## Refresh Vmess ##############
async def refresh_vmess(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    try: 
        db_client = connect_to_database(secrets['DBConString'])
    except Exception as e:
        print("Failed to connect to the database!")

    query = update.callback_query
    await query.answer()
    if query.data == 'Cancel':
        db_client.close()
        return telext.ConversationHandler.END
    if not await check_subscription(update):
        main_channel = db_client[secrets['DBName']].orgs.find_one({'name': 'main'})['channel']['link']
        reply_text = client_functions_texts('join_channel') + f"\n\n{main_channel}"
        await update.effective_message.edit_text(reply_text)
        # application.add_handler(menu_handler)

        db_client.close()

        return telext.ConversationHandler.END
    else: 
        # client = pymongo.MongoClient(secrets['DBConString'])
        user_dict = db_client[secrets['DBName']].users.find_one({'user_id': update.effective_user.id})
        if user_dict is None:
            reply_text = client_functions_texts("user_not_found")
            await update.effective_message.edit_text(reply_text)
            # client.close()
            # application.add_handler(menu_handler)

            db_client.close()

            return telext.ConversationHandler.END
        elif len(user_dict["server_names"]) == 0:
            # reply_text = 'You have no accounts to refresh, get a new vmess first!'
            reply_text = client_functions_texts("get_an_account")
            await update.effective_message.edit_text(reply_text)
            # client.close()
            # application.add_handler(menu_handler)

            db_client.close()

            return telext.ConversationHandler.END
        else:
            # Send message with text and appended InlineKeyboard
            # reply_text = '*Pick a server to refresh*\n'
            # reply_text += '*===== Server List =====*\n'
            # server_list = list(db_client[secrets['DBName']].servers.find({'name': {'$in': user_dict["server_names"]}}))
            # for s in server_list:
            #     server_traffic = s.get('traffic', Config['default_traffic'])
            #     reply_text += f"{s['name']}:\n\t"
            #     reply_text += f"Traffic: {'Unlimited' if server_traffic == 0 else f'{server_traffic}GB'}\n"
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
                # projection={
                #     'name': True
                # }
            ))

            # active_servers = [server for server in user_dict['server_names'] if server in server_list]
            
            keyboard = [
                [telegram.InlineKeyboardButton(s['name'], callback_data=s['name'])] for s in server_list
            ] + [
                [telegram.InlineKeyboardButton(client_functions_texts("general_cancel"), callback_data='Cancel')]
            ]
            reply_markup = telegram.InlineKeyboardMarkup(keyboard)

            for s in server_list:
                if(s['rowRemark'] not in servers_rowRemarks):
                    servers_rowRemarks[s['rowRemark']] = {}
                    servers_rowRemarks[s['rowRemark']]['servers'] = []
                    servers_rowRemarks[s['rowRemark']]['traffic'] = s['traffic']

                servers_rowRemarks[s['rowRemark']]['servers'].append({'name': s['name'], 'price': s['price']})
                # server_traffic = s.get('traffic', Config['default_traffic'])
                # reply_text += f"{s['name']}\n"
            max_dash = 0
            for row in servers_rowRemarks:
                # reply_text += f"\n{row}\n"
                for server in servers_rowRemarks[row]['servers']:
                    # reply_text += f'*{server["name"]}*: ' + f'{server["price"]} ' + 'هزار تومان بر گیگ ' + '\n'
                    temp = f'*{server["name"]}*: ' + f'{server["price"]} ' + 'هزار تومان بر گیگ ' + '\n'
                    reply_text += temp
                    if len(temp) > max_dash:
                        max_dash = len(temp)
                reply_text += f"{'-'*max_dash}\n"
                # reply_text += f"Traffic: 'Unlimited'" if servers_rowRemarks[row]['traffic'] == 0 else f"Limit: {servers_rowRemarks[row]['traffic']}GB" + "\n\n"
            
            final_reply_text = '='*((max_dash-len(reply_text_header)-4)//2) + reply_text_header + '='*((max_dash-len(reply_text_header)-4)//2) + "\n\n" + reply_text
            await update.effective_message.edit_text(final_reply_text, reply_markup=reply_markup, parse_mode=telegram.constants.ParseMode.MARKDOWN)

            db_client.close()

            return DELIVER_REFRESH_VMESS

async def deliver_refresh_vmess(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    try: 
        db_client = connect_to_database(secrets['DBConString'])
    except Exception as e:
        print("Failed to connect to the database!")

    query = update.callback_query
    await query.answer()
    if query.data == 'Cancel':
        db_client.close()
        return telext.ConversationHandler.END
    server_name = query.data

    # client = pymongo.MongoClient(secrets['DBConString'])
    user_dict = db_client[secrets['DBName']].users.find_one({'user_id': update.effective_user.id})
    server_dict = db_client[secrets['DBName']].servers.find_one({'name': server_name, 'org':list(user_dict["orgs"].keys())[0]})
    is_error = False

    # Return vmess str from db
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

############## Get UserInfo ##############
async def get_userinfo(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    try: 
        db_client = connect_to_database(secrets['DBConString'])
    except Exception as e:
        print("Failed to connect to the database!")

    query = update.callback_query
    await query.answer()
    if query.data == 'Cancel':
        db_client.close()
        return telext.ConversationHandler.END
    if not await check_subscription(update):
        main_channel = db_client[secrets['DBName']].orgs.find_one({'name': 'main'})['channel']['link']
        reply_text = client_functions_texts("join_channel") + f'\n\n{main_channel}'
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
        else:
            if(len(user_dict['server_names']) == 0):
                reply_text = client_functions_texts("your_user_id") + f' `{update.effective_user.id}`'
                reply_text += "\n" + client_functions_texts("get_an_account")
                await update.effective_message.edit_text(reply_text, parse_mode=telegram.constants.ParseMode.MARKDOWN)
                db_client.close()
                return telext.ConversationHandler.END

            reply_text = client_functions_texts("your_user_id") + f' `{update.effective_user.id}`'
            # server_remarks = []
            # for server_name in user_dict['server_names']:
            #     server_dict = db_client[secrets['DBName']].servers.find_one({'name': server_name, 'org':list(user_dict["orgs"].keys())[0]})
            #     user_client = xAPI.get_clients(server_dict, select=[f"{user_dict['user_id']}@{server_dict['rowRemark']}"])
            #     if (not server_dict['rowRemark'] in server_remarks):
            #         server_remarks.append(server_dict['rowRemark'])
            #         reply_text += f"\n\n*{server_dict['name']}*"
            #         reply_text += "\nUsage: {:.3f}%".format((float(user_client.down.iloc[0]) + float(user_client.up.iloc[0])) / float(user_client.total.iloc[0]) * 100)
            #         reply_text += f"\nLimit: {int(float(user_client.total.iloc[0])/1024**3)} GB"

            servers_rowRemarks = {}
            for server_name in user_dict['server_names']:
                if len(list(user_dict["orgs"].keys())) == 0:
                    reply_text = client_functions_texts("your_user_id") + f' `{update.effective_user.id}`'
                    reply_text += "\n" + client_functions_texts("join_org")
                    await update.effective_message.edit_text(reply_text, parse_mode=telegram.constants.ParseMode.MARKDOWN)
                    db_client.close()
                    return telext.ConversationHandler.END
                server_dict = db_client[secrets['DBName']].servers.find_one(
                    {
                        'name': server_name, 
                        'org':list(user_dict["orgs"].keys())[0],
                        "$or": [
                            {'isActive': {"$exists": True, "$eq": True}},
                            {"isActive": {"$exists": False}}
                        ]
                    }
                )
                if server_dict is None:
                    continue

                (res, user_client) = xAPI.get_client(server_dict, f"{user_dict['user_id']}-{server_dict['name']}@{server_dict['rowRemark']}")
                if res == -1:
                    reply_text = client_functions_texts("your_user_id") + f' `{update.effective_user.id}`'
                    reply_text += "\n\n" + client_functions_texts("error_code") + " 11" + "\n\n" + client_functions_texts("contact_support")
                    await update.effective_message.edit_text(reply_text, parse_mode=telegram.constants.ParseMode.MARKDOWN)

                    db_client.close()
                    return telext.ConversationHandler.END

                if(server_dict['rowRemark'] not in servers_rowRemarks):
                    servers_rowRemarks[server_dict['rowRemark']] = {}
                    servers_rowRemarks[server_dict['rowRemark']]['servers'] = []
                    # servers_rowRemarks[server_dict['rowRemark']]['usage'] = (float(user_client['down']) + float(user_client['up'])) / float(user_client['total'])
                    # servers_rowRemarks[server_dict['rowRemark']]['traffic'] = int(float(user_client['total'])/1024**3)

                servers_rowRemarks[server_dict['rowRemark']]['servers'].append({'name': server_dict['name'], 'price': server_dict['price']})

            max_dash = 0
            reply_text += "\n\n"
            for row in servers_rowRemarks:
                # reply_text += f"\n{row}\n"
                # reply_text += f"\n"
                for server in servers_rowRemarks[row]['servers']:
                    temp = f'*{server["name"]}*: ' + f'{server["price"]} ' + 'هزار تومان بر گیگ ' + '\n'
                    reply_text += temp
                    if len(temp) > max_dash:
                        max_dash = len(temp)
                # reply_text = reply_text[:-3]
            reply_text += f'{"-"*max_dash}\n' + 'مانده کیف پول' + ":\t" + f'{int(user_dict["wallet"])} ' + 'هزار تومان'

                # reply_text += "---------------------\n"
                # reply_text += f"Traffic: 'Unlimited'" if servers_rowRemarks[row]['traffic'] == 0 else f"Limit: {servers_rowRemarks[row]['traffic']}GB" + "\n\n"


            await update.effective_message.edit_text(reply_text, parse_mode=telegram.constants.ParseMode.MARKDOWN)

            db_client.close()
            return telext.ConversationHandler.END

############## Ticketing ##############
async def receive_ticket(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    try: 
        db_client = connect_to_database(secrets['DBConString'])
    except Exception as e:
        print("Failed to connect to the database!")

    query = update.callback_query
    await query.answer()
    if query.data == 'Cancel':
        db_client.close()
        return telext.ConversationHandler.END
    if not await check_subscription(update):
        main_channel = db_client[secrets['DBName']].orgs.find_one({'name': 'main'})['channel']['link']
        reply_text = client_functions_texts('join_channel') + f"\n\n{main_channel}"
        await update.effective_message.edit_text(reply_text)
        # application.add_handler(menu_handler)

        db_client.close()

        return telext.ConversationHandler.END
    # selected_org = query.data['org']
    # if selected_org not in db_client[secrets['DBName']].admins.find_one({'user_id': update.effective_user.id})['orgs']:
    #     reply_text = "Unathorized! Also, How are you here?"
    #     await update.effective_message.edit_text(reply_text)

    #     db_client.close()

    #     return telext.ConversationHandler.END
    # else:
    reply_text = client_functions_texts("send_ticket") + "\n\n" + client_functions_texts("cancel_to_abort")
    # context.user_data['org'] = selected_org
    keyboard = [
        [telegram.InlineKeyboardButton(client_functions_texts("general_cancel"), callback_data='Cancel')]
    ]
    reply_markup = telegram.InlineKeyboardMarkup(keyboard)
    # Send message with text and appended InlineKeyboard
    await update.effective_message.edit_text(reply_text, reply_markup=reply_markup, parse_mode=telegram.constants.ParseMode.MARKDOWN)

    db_client.close()

    return RECEIVE_TICKET


async def receive_ticket_inputed(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    try: 
        db_client = connect_to_database(secrets['DBConString'])
    except Exception as e:
        print("Failed to connect to the database!")

    if not await check_subscription(update):
        main_channel = db_client[secrets['DBName']].orgs.find_one({'name': 'main'})['channel']['link']
        reply_text = client_functions_texts('join_channel') + f"\n\n{main_channel}"
        await update.effective_message.reply_text(reply_text)
        
        db_client.close()

        return telext.ConversationHandler.END
    else:
            print("In ticketing")
            user_dict = db_client[secrets['DBName']].users.find_one({'user_id': int(update.effective_chat.id)})
            if user_dict is None:
                reply_text = client_functions_texts("user_not_found")
                await update.effective_message.reply_text(reply_text)
            else:
                if bool(user_dict['orgs']):
                    for user_org in user_dict['orgs'].keys():
                        chat_id = db_client[secrets['DBName']].orgs.find_one({'name': user_org})['ticketing_group_id']
                        await context.bot.send_message(
                            chat_id=chat_id,
                            # text=f"Ticket from user: {update.effective_chat.id}\n{update.effective_message.text}",
                            text=
                                f"Ticket from user: \n\n" + 
                                (f"@{update.effective_chat.username} - " if(update.effective_chat.username is not None) else "") + 
                                f"{update.effective_chat.id} - {update.effective_chat.full_name}" + 
                                f"\nOrg: {user_org}" + 
                                "\n-------------------------" +
                                f"\n{update.effective_message.text}",
                            reply_to_message_id=secrets['ticket_topic_id']
                        )
                else:
                    chat_id = db_client[secrets['DBName']].orgs.find_one({'name': 'main'})['ticketing_group_id']
                    await context.bot.send_message(
                            chat_id=chat_id,
                            # text=f"Ticket from user: {update.effective_chat.id}\n{update.effective_message.text}",
                            text=
                                f"Ticket from user: \n\n" + 
                                (f"@{update.effective_chat.username} - " if(update.effective_chat.username is not None) else "") + 
                                f"{update.effective_chat.id} - {update.effective_chat.full_name}" + 
                                "\n-------------------------" +
                                f"\n{update.effective_message.text}",
                            reply_to_message_id=secrets['ticket_topic_id']
                    )
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=client_functions_texts("thanks_ticket")
                    )

            db_client.close()
            return telext.ConversationHandler.END

############## New User Purchase Account ##############
async def newuser_purchase(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    try: 
        db_client = connect_to_database(secrets['DBConString'])
    except Exception as e:
        print("Failed to connect to the database!")

    query = update.callback_query
    await query.answer()
    if query.data == 'Cancel':
        db_client.close()
        return telext.ConversationHandler.END
    if not await check_subscription(update):
        main_channel = db_client[secrets['DBName']].orgs.find_one({'name': 'main'})['channel']['link']
        reply_text = client_functions_texts('join_channel') + f"\n\n{main_channel}"
        await update.effective_message.edit_text(reply_text)
        # application.add_handler(menu_handler)

        db_client.close()

        return telext.ConversationHandler.END
    # selected_org = query.data['org']
    # if selected_org not in db_client[secrets['DBName']].admins.find_one({'user_id': update.effective_user.id})['orgs']:
    #     reply_text = "Unathorized! Also, How are you here?"
    #     await update.effective_message.edit_text(reply_text)

    #     db_client.close()

    #     return telext.ConversationHandler.END
    # else:
    context.user_data['menu'] = update.effective_message
    context.user_data['chat'] = update.effective_chat
    context.user_data['full_name'] = update.effective_chat.full_name
    context.user_data['username'] = update.effective_chat.username
    context.user_data['user_id'] = update.effective_chat.id
    
    reply_text = client_functions_texts("referal_code") + "\n\n" + client_functions_texts("cancel_to_abort") 
    # context.user_data['org'] = selected_org
    keyboard = [
        [telegram.InlineKeyboardButton(client_functions_texts("general_cancel"), callback_data='Cancel')]
    ]
    reply_markup = telegram.InlineKeyboardMarkup(keyboard)
    # Send message with text and appended InlineKeyboard
    await update.effective_message.edit_text(reply_text, reply_markup=reply_markup, parse_mode=telegram.constants.ParseMode.MARKDOWN)

    db_client.close()

    return NEWUSER_PURCHASE_SELECT_PLAN

async def newuser_purchase_select_plan(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    try:
        db_client = connect_to_database(secrets['DBConString'])
    except Exception as e:
        print("Failed to connect to the database!")

    if not await check_subscription(update):
        main_channel = db_client[secrets['DBName']].orgs.find_one({'name': 'main'})['channel']['link']
        reply_text = client_functions_texts('join_channel') + f"\n\n{main_channel}"
        await update.effective_message.edit_text(reply_text)
        # application.add_handler(menu_handler)

        db_client.close()

        return telext.ConversationHandler.END
    # selected_org = query.data['org']
    # if selected_org not in db_client[secrets['DBName']].admins.find_one({'user_id': update.effective_user.id})['orgs']:
    #     reply_text = "Unathorized! Also, How are you here?"
    #     await update.effective_message.edit_text(reply_text)

    #     db_client.close()

    #     return telext.ConversationHandler.END
    # else:

    org = db_client[secrets['DBName']].orgs.find_one({'referral_code': update.effective_message.text})
    if org == None:
        reply_text = "The referral code is not valid!"
        await context.user_data['menu'].edit_text(reply_text)

        db_client.close()

        return telext.ConversationHandler.END
    context.user_data['org'] = org['name']
    # user_dict = db_client[secrets['DBName']].users.find_one({'user_id': int(update.effective_chat.id)})

    reply_text = client_functions_texts("choose_plan") + "\n\n" + client_functions_texts("cancel_to_abort")
    
    user_dict = db_client[secrets['DBName']].users.find_one({'user_id': int(update.effective_chat.id)})
    context.user_data['user_dict'] = user_dict
    if ('discount' in user_dict and user_dict['discount']):
        discount = (100-user_dict['discount']) / 100
    else:
        discount = 1
    context.user_data['discount'] = discount

    keyboard = [
        # [telegram.InlineKeyboardButton(f"{plan}: {org['payment_options']['plans'][plan]} " + client_functions_texts("GB") + f" -> {org['payment_options']['currencies']['rial']['plans'][plan]} " + client_functions_texts("T")
        #                                , callback_data={'plan': plan})] for plan in org['payment_options']['currencies']['rial']['plans']
        [telegram.InlineKeyboardButton(f"{plan}: {round(int(org['payment_options']['currencies']['rial']['plans'][plan]) * discount)} T" + (f" ({100-100*discount}% off)" if (100-100*discount != 0) else "")
                                       , callback_data={'plan': plan})] for plan in org['payment_options']['currencies']['rial']['plans']
    ]
    keyboard.extend([[telegram.InlineKeyboardButton(client_functions_texts("general_cancel"), callback_data='Cancel')]])

    reply_markup = telegram.InlineKeyboardMarkup(keyboard)
    # Send message with text and appended InlineKeyboard
    await context.user_data['menu'].edit_text(reply_text, reply_markup=reply_markup, parse_mode=telegram.constants.ParseMode.MARKDOWN)

    pay_methods = org['payment_options']['currencies']

    active_methods = []
    for currency, details in pay_methods.items():
        if details.get("active"):
            active_methods.append(currency)
    
    if len(active_methods) == 0:
        # await context.bot.send_message(
        #     chat_id=context.user_data['chat'].id,
        #     # text=f"You are now added to the organization. Please follow the following channel for announcements about server connectivities: \n[Channel Link](https://t.me/+fpMXFyhEYD1jZDM8)"
        #     text=f"I'm sorry, no payment method is available right now. Please try again later or contact us at: {org['support_account']}"
        # )
        db_client.close()
        return telext.ConversationHandler.END
    elif len(active_methods) == 1:
        if active_methods[0] == 'rial':
            db_client.close()
            return NEWUSER_PURCHASE_RIAL
        elif active_methods[0] == 'tron':
            db_client.close()
            return NUEWUSER_PURCHASE_RECEIPT_CRYPTO
    else:
        db_client.close()
        return NEWUSER_PURCHASE_INTERCEPTOR

async def newuser_purchase_interceptor(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    try: 
        db_client = connect_to_database(secrets['DBConString'])
    except Exception as e:
        print("Failed to connect to the database!")

    if not await check_subscription(update):
        main_channel = db_client[secrets['DBName']].orgs.find_one({'name': 'main'})['channel']['link']
        reply_text = client_functions_texts('join_channel') + f"\n\n{main_channel}"
        await update.effective_message.edit_text(reply_text)
        # application.add_handler(menu_handler)

        db_client.close()

        return telext.ConversationHandler.END

    query = update.callback_query
    await query.answer()
    if query.data == 'Cancel':
        return telext.ConversationHandler.END
    if 'plan' not in context.user_data:
        context.user_data['plan'] = query.data['plan']

    org_obj = db_client[secrets['DBName']].orgs.find_one({'name': context.user_data['org']})

    pay_methods = org_obj['payment_options']['currencies']

    active_methods = []
    for currency, details in pay_methods.items():
        if details.get("active"):
            active_methods.append(currency)

    reply_text = "choose_payment_method"

    keyboard = [
            [telegram.InlineKeyboardButton(f"{method}", callback_data={'method': method})] for method in active_methods
    ] + [[telegram.InlineKeyboardButton(client_functions_texts("general_cancel"), callback_data='Cancel')]]

    reply_markup = telegram.InlineKeyboardMarkup(keyboard)
    await context.user_data['menu'].edit_text(reply_text, reply_markup=reply_markup, parse_mode=telegram.constants.ParseMode.MARKDOWN)

    db_client.close()

    return NEWUSER_PURCHASE_INTERCEPTOR_INPUTED

async def newuser_purchase_interceptor_inputed(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == 'Cancel':
        return telext.ConversationHandler.END

    if query.data['method'] == 'rial':
        return NEWUSER_PURCHASE_RIAL
    elif query.data['method'] == 'tron':
        return NUEWUSER_PURCHASE_RECEIPT_CRYPTO

async def newuser_purchase_rial(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    try: 
        db_client = connect_to_database(secrets['DBConString'])
    except Exception as e:
        print("Failed to connect to the database!")

    query = update.callback_query
    await query.answer()
    if query.data == 'Cancel':
        db_client.close()
        return telext.ConversationHandler.END
    if 'plan' not in context.user_data:
        context.user_data['plan'] = query.data['plan']
    user_dict = db_client[secrets['DBName']].users.find_one({'user_id': int(update.effective_chat.id)})
    context.user_data['user_dict'] = user_dict
    if ('discount' in user_dict and user_dict['discount']):
        discount = (100-user_dict['discount']) / 100
    else:
        discount = 1
    context.user_data['discount'] = discount

    org_obj = db_client[secrets['DBName']].orgs.find_one({'name': context.user_data['org']})
    context.user_data['pay_amount'] = org_obj['payment_options']['currencies']['rial']['plans'][context.user_data['plan']]
    context.user_data['is_new_user'] = True
    context.user_data['payment_type'] = 'rial'

    if not await check_subscription(update):
        main_channel = db_client[secrets['DBName']].orgs.find_one({'name': 'main'})['channel']['link']
        reply_text = client_functions_texts('join_channel') + f"\n\n{main_channel}"
        await update.effective_message.edit_text(reply_text)
        # application.add_handler(menu_handler)

        db_client.close()

        return telext.ConversationHandler.END

    context.user_data['payment_method'] = org_obj['payment_options']['currencies']['rial']['method']

    if context.user_data['payment_method'] == 'e-transfer':
        reply_text = client_functions_texts("selected_plan") + f': {query.data["plan"]} Pack\n' + client_functions_texts("transaction_receipt") + ":"
        if "card_number" in org_obj['payment_options']['currencies']['rial'] and org_obj['payment_options']['currencies']['rial']['card_number'] != "":
            reply_text += '\n\n' + client_functions_texts("card_number") + f': `{org_obj["payment_options"]["currencies"]["rial"]["card_number"]}`'
        reply_text += '\n\n' + client_functions_texts("cancel_to_abort")
        keyboard = [
            [telegram.InlineKeyboardButton(client_functions_texts("general_cancel"), callback_data='Cancel')]
        ]
        reply_markup = telegram.InlineKeyboardMarkup(keyboard)

        await update.effective_message.edit_text(reply_text, reply_markup=reply_markup, parse_mode=telegram.constants.ParseMode.MARKDOWN)
        # await update.effective_message.edit_text(reply_text)

        db_client.close()

        return NEWUSER_PURCHASE_RIAL_INPUTED
    else:
        reply_text = client_functions_texts("selected_plan") + f': {query.data["plan"]} Pack\n' + client_functions_texts("zarinpal_message") + ':\n\n' + client_functions_texts('cancel_to_abort')
        context.user_data['merchant_id'] = org_obj['payment_options']['currencies']['rial']['merchant_id']

        description = u'خرید پلن'+query.data['plan']
        email=''
        mobile=''
        secret_url=sc.token_urlsafe()

        url = "https://api.zarinpal.com/pg/v4/payment/request.json"
        payload = {
            "merchant_id": context.user_data['merchant_id'],
            "amount": int(context.user_data['pay_amount'])*10000,
            # "amount": 200000,
            "callback_url": "http://t.me/"+secrets["BOT_USERNAME"],
            "description": "خرید پلن"+query.data['plan'],
            
        }
        print(payload)

        headers = {
            "accept": "application/json",
            "content-type": "application/json"
        }

        response = requests.request("POST", url, json=payload, headers=headers).json()
        print(context.user_data)
        print(response['data'])
        context.user_data['authority']=response['data']['authority']
        context.user_data['secret_url']=secret_url

    
        # result = client.service.PaymentRequest(secrets['MMERCHANT_ID'],
        #                                        context.user_data['pay_amount'],
        #                                        description,
        #                                        email,
        #                                        mobile,

        #                                        )
        keyboard = [
            [telegram.InlineKeyboardButton(client_functions_texts("pay_now"), callback_data='Pay now')],
            [telegram.InlineKeyboardButton(client_functions_texts("general_cancel"), callback_data='Cancel')]
        ]
        reply_markup = telegram.InlineKeyboardMarkup(keyboard)
        # Send message with text and appended InlineKeyboard
        await update.effective_message.edit_text(reply_text, reply_markup=reply_markup, parse_mode=telegram.constants.ParseMode.MARKDOWN)

        db_client.close()

        return NEWUSER_PURCHASE_RIAL_ZARIN

async def payment(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [telegram.InlineKeyboardButton('💰 Paid', callback_data='Paid')],
        # [telegram.InlineKeyboardButton(client_functions_texts("general_cancel"), callback_data='Cancel')]
    ]
    reply_markup = telegram.InlineKeyboardMarkup(keyboard)
    # Send message with text and appended InlineKeyboard
    url='https://www.zarinpal.com/pg/StartPay/'+context.user_data['authority']
    reply_text=f'{url}'
    await update.effective_message.edit_text(reply_text, reply_markup=reply_markup, parse_mode=telegram.constants.ParseMode.MARKDOWN)

    return PAID

async def check_payment(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    # keyboard = [
    #     [telegram.InlineKeyboardButton('💰 Paid', callback_data='Paid')],
    #     [telegram.InlineKeyboardButton(client_functions_texts("general_cancel"), callback_data='Cancel')]
    # ]
    # reply_markup = telegram.InlineKeyboardMarkup(keyboard)
    # Send message with text and appended InlineKeyboard
    # url='https://www.zarinpal.com/pg/StartPay/'+context.user_data['authority']
    # reply_text='''
    # Pay from below link and click paid after that:\n
    # '''+url
    try :
        url = "https://api.zarinpal.com/pg/v4/payment/verify.json"
        payload = {
            "merchant_id": context.user_data['merchant_id'],
            "amount": int(context.user_data['pay_amount'])*10000,
            "authority": context.user_data['authority']
        }
        headers = {
            "accept": "application/json",
            "content-type": "application/json"
        }
        response = requests.request("POST", url, json=payload, headers=headers).json()
        # charge_amount=context.user_data['charge_amount']
        # print(response)
        # if (response['errors']):
        #     # throw error
        #     raise Exception(response['errors'])
        if response['data']['code']==100 or response['data']['code']==101:
        # if True:
            # await update.effective_message.reply_text(f"✅ Your payment was verfied!\nThe account has been charged for {charge_amount} GB!\n")

            context.user_data['payment_receipt']=response['data']['ref_id']
            # context.user_data['payment_receipt']=''
            await after_automatic_payment(update, context)
        else:
            print('else payment error')
            await update.effective_message.reply_text(client_functions_texts("not_yet_verified_payment"))
    except Exception as e:
        print('else payment error' ,e)
        print(e)
        await update.effective_message.reply_text(client_functions_texts("not_yet_verified_payment"))
    # await update.effective_message.edit_text(reply_text, reply_markup=reply_markup, parse_mode=telegram.constants.ParseMode.MARKDOWN)

    # print(update.message.text)

    return PAID


# rial
async def newuser_purchase_rial_inputed(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    print("in user_charge_acc_inputed")
    try: 
        db_client = connect_to_database(secrets['DBConString'])
    except Exception as e:
        print("Failed to connect to the database!")

    if not await check_subscription(update):
        main_channel = db_client[secrets['DBName']].orgs.find_one({'name': 'main'})['channel']['link']
        reply_text = client_functions_texts('join_channel') + f"\n\n{main_channel}"
        await update.effective_message.reply_text(reply_text)
        
        db_client.close()

        return telext.ConversationHandler.END
    else:
            user_dict = db_client[secrets['DBName']].users.find_one({'user_id': int(update.effective_chat.id)})
            if user_dict is None:
                reply_text = client_functions_texts("user_not_found")
                await update.effective_message.reply_text(reply_text)
            else:
                org_obj = db_client[secrets['DBName']].orgs.find_one({'name': context.user_data['org']})

                context.user_data["payment_receipt"] = update.effective_message.text

                keyboard = [
                    [telegram.InlineKeyboardButton('❌ Reject', callback_data='Reject'),telegram.InlineKeyboardButton('✅ Accept', callback_data='Accept')]
                ]

                reply_markup = telegram.InlineKeyboardMarkup(keyboard)

                await context.bot.send_message(
                    chat_id=org_obj['ticketing_group_id'],
                    text=
                        f"Payment\n"+
                        f"payment_method:{context.user_data['payment_method']}\n" +
                        (f"username:@{context.user_data['username']}\n" if(context.user_data['username'] is not None) else "") + 
                        f"user_id:{context.user_data['user_id']}\nfull_name:{context.user_data['full_name']}\n" + 
                        f"Plan:{context.user_data['plan']}\n" +
                        f"org:{context.user_data['org']}\n"+
                        f"pay_amount:{context.user_data['pay_amount']}, included {100-100*context.user_data['discount']}% discount\n"
                        f"currency:rial\n"+
                        "-------------------------\n" +
                        context.user_data['payment_receipt'],
                    reply_to_message_id= secrets['test_topic_id'] if secrets["DBName"].lower() == "rhvp-test" else secrets['payments_topic_id'],
                    reply_markup=reply_markup
                    )

                try:
                    await update.effective_message.edit_text(client_functions_texts("thanks_for_payment"))
                except:
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=client_functions_texts("thanks_for_payment")
                    )

            db_client.close()
            return telext.ConversationHandler.END

async def newuser_purchase_rial_inputed_image(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    print("in user_charge_acc_inputed_image")
    # print(update.message.photo[0].file_id)
    try: 
        db_client = connect_to_database(secrets['DBConString'])
    except Exception as e:
        print("Failed to connect to the database!")

    if not await check_subscription(update):
        main_channel = db_client[secrets['DBName']].orgs.find_one({'name': 'main'})['channel']['link']
        reply_text = client_functions_texts('join_channel') + f"\n\n{main_channel}"
        await update.effective_message.reply_text(reply_text)
        
        db_client.close()

        return telext.ConversationHandler.END
    else:
            user_dict = db_client[secrets['DBName']].users.find_one({'user_id': int(update.effective_chat.id)})
            if user_dict is None:
                reply_text = client_functions_texts("user_not_found")
                await update.effective_message.reply_text(reply_text)
            else:
                org_obj = db_client[secrets['DBName']].orgs.find_one({'name': context.user_data['org']})

                keyboard = [
                        [telegram.InlineKeyboardButton('❌ Reject', callback_data='Reject'),telegram.InlineKeyboardButton('✅ Accept', callback_data='Accept')]
                    ]
                
                context.user_data["payment_receipt"] = update.effective_message.text

                reply_markup = telegram.InlineKeyboardMarkup(keyboard)

                await context.bot.send_photo(
                    chat_id=org_obj['ticketing_group_id'],
                    photo=update.message.photo[0].file_id,
                    caption=
                        f"Payment\n"+
                        f"payment_method:{context.user_data['payment_method']}\n" +
                        (f"username:@{context.user_data['username']}\n" if(context.user_data['username'] is not None) else "") + 
                        f"user_id:{context.user_data['user_id']}\nfull_name:{context.user_data['full_name']}\n" + 
                        f"Plan:{context.user_data['plan']}\n" +
                        f"org:{context.user_data['org']}\n"+
                        f"pay_amount:{context.user_data['pay_amount']}, included {100-100*context.user_data['discount']}% discount\n"
                        f"currency:rial\n",
                    reply_to_message_id= secrets['test_topic_id'] if secrets["DBName"].lower() == "rhvp-test" else secrets['payments_topic_id'],
                    reply_markup=reply_markup
                )
                # await context.bot.send_message(
                #     chat_id=org_obj['ticketing_group_id'],
                #     text=
                #         f"Payment\n"+
                #         f"payment_method:{context.user_data['payment_method']}\n" +
                #         (f"username:@{context.user_data['username']}\n" if(context.user_data['username'] is not None) else "") + 
                #         f"user_id:{context.user_data['user_id']}\nfull_name:{context.user_data['full_name']}\n" + 
                #         f"Plan:{context.user_data['plan']}\n" +
                #         f"org:{context.user_data['org']}\n"+
                #         f"pay_amount:{context.user_data['pay_amount']}\n"
                #         f"currency:rial\n"+
                #         "-------------------------\n" +
                #         context.user_data['payment_receipt'],
                #     reply_to_message_id= 753 if secrets["DBName"].lower() == "rhvp-test" else 3,
                #     reply_markup=reply_markup
                #     )
            #     await context.bot.send_message(
            #         chat_id=org_obj['ticketing_group_id'],
                    
            #         # text=f"Payment from user: {update.effective_chat.id} - {update.effective_chat.full_name} - @{update.effective_chat.username}\nPlan: {context.user_data['plan']} Pack\n\nReciept:\n{update.effective_message.text}",
            #         text=
            #             f"Payment from user: \n\n" +
            #             (f"@{context.user_data['username']} - " if(context.user_data['username'] is not None) else "") + 
            #             f"{context.user_data['user_id']} - {context.user_data['full_name']}" + 
            #             f"\nPlan: {context.user_data['plan']} Pack" +
            #             "\n-------------------------" +
            #             f"\n{update.effective_message.text}",
            #         reply_to_message_id= 753 if secrets["DBName"].lower() == "rhvp-test" else 3
            #         )

                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    # text=f"You are now added to the organization. Please follow the following channel for announcements about server connectivities: \n[Channel Link](https://t.me/+fpMXFyhEYD1jZDM8)"
                    text=client_functions_texts("thanks_for_payment")
                    )

            db_client.close()
            return telext.ConversationHandler.END

async def user_charge_rial_inputed_document(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    print("in user_charge_rial_inputed_document")
    try: 
        db_client = connect_to_database(secrets['DBConString'])
    except Exception as e:
        print("Failed to connect to the database!")

    if not await check_subscription(update):
        main_channel = db_client[secrets['DBName']].orgs.find_one({'name': 'main'})['channel']['link']
        reply_text = client_functions_texts('join_channel') + f"\n\n{main_channel}"
        await update.effective_message.reply_text(reply_text)
        
        db_client.close()

        return telext.ConversationHandler.END
    else:
            user_dict = db_client[secrets['DBName']].users.find_one({'user_id': int(update.effective_chat.id)})
            if user_dict is None:
                reply_text = client_functions_texts("user_not_found")
                await update.effective_message.reply_text(reply_text)
            else:
                user_obj = db_client[secrets['DBName']].users.find_one({'user_id': update.effective_user.id}, {"orgs": { "$slice": 1 }})
                org_name = list(user_obj["orgs"].keys())[0]
                org_obj = db_client[secrets['DBName']].orgs.find_one({'name': org_name})

                keyboard = [
                        [telegram.InlineKeyboardButton('❌ Reject', callback_data='Reject'),telegram.InlineKeyboardButton('✅ Accept', callback_data='Accept')]
                    ]
                
                context.user_data["payment_receipt"] = update.effective_message.text

                reply_markup = telegram.InlineKeyboardMarkup(keyboard)
                context.user_data['payment_receipt'] = f"\n{update.effective_message.text}"
                context.user_data['full_name'] = update.effective_chat.full_name
                context.user_data['username'] = update.effective_chat.username
                context.user_data['user_id'] = update.effective_chat.id
                context.user_data['org']=org_name
                context.user_data['pay_amount'] = org_obj['payment_options']['currencies']['rial']['plans'][context.user_data['plan']]
                white_listed = [432080595, 97994343, 60256430, 92294065, 94307276, 734823458, 128188905, 1403568736]
                white_message = "\n⚠️⚠️⚠️⚠️ WHITE LISTED ID⚠️⚠️⚠️⚠️" if context.user_data['user_id'] in white_listed else ""
                await context.bot.send_document(
                    chat_id=org_obj['ticketing_group_id'],
                    document=update.message.document.file_id,
                    caption=
                        f"Recharg\n"+
                        f"payment_method:{context.user_data['payment_method']}\n" +
                        (f"username:@{context.user_data['username']}\n" if(context.user_data['username'] is not None) else "") + 
                        f"user_id:{context.user_data['user_id']}\nfull_name:{context.user_data['full_name']}\n" + 
                        f"Plan:{context.user_data['plan']}\n" +
                        f"org:{context.user_data['org']}\n"+
                        f"pay_amount:{context.user_data['pay_amount']}, included {100-100*context.user_data['discount']}% discount\n"+
                        f"currency:rial\n" +
                        f"{white_message}",
                    reply_to_message_id= secrets['test_topic_id'] if secrets["DBName"].lower() == "rhvp-test" else secrets['payments_topic_id'],
                    reply_markup=reply_markup
                )
                # await context.bot.send_message(
                #     chat_id=org_obj['ticketing_group_id'],
                #     # text=f"Payment from user: {update.effective_chat.id} - {update.effective_chat.full_name} - @{update.effective_chat.username}\nPlan: {context.user_data['plan']} Pack\n\nReciept:\n{update.effective_message.text}",
                #     text=
                #         f"Payment from user: \n\n" +
                #         (f"@{update.effective_chat.username} - " if(update.effective_chat.username is not None) else "") + 
                #         f"{update.effective_chat.id} - {update.effective_chat.full_name}" + 
                #         f"\nPlan: {context.user_data['plan']} Pack" +
                #         "\n-------------------------" +
                #         f"\n{update.effective_message.text}",
                #     reply_to_message_id= 753 if secrets["DBName"].lower() == "rhvp-test" else 3
                #     )

                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    # text=f"You are now added to the organization. Please follow the following channel for announcements about server connectivities: \n[Channel Link](https://t.me/+fpMXFyhEYD1jZDM8)"
                    text=client_functions_texts("thanks_for_payment")
                    )

            db_client.close()
            return telext.ConversationHandler.END


async def newuser_purchase_rial_inputed_document(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    print("in user_charge_acc_inputed_document")
    print(f"update.message.document.file_id:{update.message.document.file_id}")
    # print(update.message.photo[0].file_id)
    try: 
        db_client = connect_to_database(secrets['DBConString'])
    except Exception as e:
        print("Failed to connect to the database!")

    if not await check_subscription(update):
        main_channel = db_client[secrets['DBName']].orgs.find_one({'name': 'main'})['channel']['link']
        reply_text = client_functions_texts('join_channel') + f"\n\n{main_channel}"
        await update.effective_message.reply_text(reply_text)
        
        db_client.close()

        return telext.ConversationHandler.END
    else:
            user_dict = db_client[secrets['DBName']].users.find_one({'user_id': int(update.effective_chat.id)})
            if user_dict is None:
                reply_text = client_functions_texts("user_not_found")
                await update.effective_message.reply_text(reply_text)
            else:
                org_obj = db_client[secrets['DBName']].orgs.find_one({'name': context.user_data['org']})

                keyboard = [
                        [telegram.InlineKeyboardButton('❌ Reject', callback_data='Reject'),telegram.InlineKeyboardButton('✅ Accept', callback_data='Accept')]
                    ]
                
                context.user_data["payment_receipt"] = update.effective_message.text

                reply_markup = telegram.InlineKeyboardMarkup(keyboard)

                await context.bot.send_document(
                    chat_id=org_obj['ticketing_group_id'],
                    document=update.message.document.file_id,
                    caption=
                        f"Payment\n"+
                        f"payment_method:{context.user_data['payment_method']}\n" +
                        (f"username:@{context.user_data['username']}\n" if(context.user_data['username'] is not None) else "") + 
                        f"user_id:{context.user_data['user_id']}\nfull_name:{context.user_data['full_name']}\n" + 
                        f"Plan:{context.user_data['plan']}\n" +
                        f"org:{context.user_data['org']}\n"+
                        f"pay_amount:{context.user_data['pay_amount']}, included {100-100*context.user_data['discount']}% discount\n"
                        f"currency:rial\n",
                    reply_to_message_id= secrets['test_topic_id'] if secrets["DBName"].lower() == "rhvp-test" else secrets['payments_topic_id'],
                    reply_markup=reply_markup
                )
                # await context.bot.send_message(
                #     chat_id=org_obj['ticketing_group_id'],
                #     text=
                #         f"Payment\n"+
                #         f"payment_method:{context.user_data['payment_method']}\n" +
                #         (f"username:@{context.user_data['username']}\n" if(context.user_data['username'] is not None) else "") + 
                #         f"user_id:{context.user_data['user_id']}\nfull_name:{context.user_data['full_name']}\n" + 
                #         f"Plan:{context.user_data['plan']}\n" +
                #         f"org:{context.user_data['org']}\n"+
                #         f"pay_amount:{context.user_data['pay_amount']}\n"
                #         f"currency:rial\n"+
                #         "-------------------------\n" +
                #         context.user_data['payment_receipt'],
                #     reply_to_message_id= 753 if secrets["DBName"].lower() == "rhvp-test" else 3,
                #     reply_markup=reply_markup
                #     )
            #     await context.bot.send_message(
            #         chat_id=org_obj['ticketing_group_id'],
                    
            #         # text=f"Payment from user: {update.effective_chat.id} - {update.effective_chat.full_name} - @{update.effective_chat.username}\nPlan: {context.user_data['plan']} Pack\n\nReciept:\n{update.effective_message.text}",
            #         text=
            #             f"Payment from user: \n\n" +
            #             (f"@{context.user_data['username']} - " if(context.user_data['username'] is not None) else "") + 
            #             f"{context.user_data['user_id']} - {context.user_data['full_name']}" + 
            #             f"\nPlan: {context.user_data['plan']} Pack" +
            #             "\n-------------------------" +
            #             f"\n{update.effective_message.text}",
            #         reply_to_message_id= 753 if secrets["DBName"].lower() == "rhvp-test" else 3
            #         )

                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    # text=f"You are now added to the organization. Please follow the following channel for announcements about server connectivities: \n[Channel Link](https://t.me/+fpMXFyhEYD1jZDM8)"
                    text=client_functions_texts("thanks_for_payment")
                    )

            db_client.close()
            return telext.ConversationHandler.END


# crypto
async def newuser_purchase_receipt_crypto(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    try: 
        db_client = connect_to_database(secrets['DBConString'])
    except Exception as e:
        print("Failed to connect to the database!")

    query = update.callback_query
    
    # await query.answer()
    if query.data == 'Cancel':
        db_client.close()
        return telext.ConversationHandler.END
    if 'plan' not in context.user_data:
        context.user_data['plan'] = query.data['plan']

    # context.user_data['plan'] = query.data['plan']

    if not await check_subscription(update):
        main_channel = db_client[secrets['DBName']].orgs.find_one({'name': 'main'})['channel']['link']
        reply_text = client_functions_texts('join_channel') + f"\n\n{main_channel}"
        await context.user_data['menu'].edit_text(reply_text)
        # application.add_handler(menu_handler)

        db_client.close()

        return telext.ConversationHandler.END
    # selected_org = query.data['org']
    # if selected_org not in db_client[secrets['DBName']].admins.find_one({'user_id': update.effective_user.id})['orgs']:
    #     reply_text = "Unathorized! Also, How are you here?"
    #     await update.effective_message.edit_text(reply_text)

    #     db_client.close()

    #     return telext.ConversationHandler.END
    # else:
    org_name = context.user_data['org']
    org_obj = db_client[secrets['DBName']].orgs.find_one({'name': org_name})
    context.user_data['wallet'] = org_obj['payment_options']['currencies']['tron']['wallet']
    context.user_data['currency'] = org_obj['payment_options']['currencies']['tron']['currency']
    context.user_data['amount'] = org_obj['payment_options']['currencies']['tron']['plans'][context.user_data['plan']]
    context.user_data['payment_url'] = f"https://weswap.digital/quick/?amount={context.user_data['amount']}&currency={context.user_data['currency']}&address={context.user_data['wallet']}"

    print(context.user_data['payment_url'])

    reply_text = client_functions_texts("selected_plan") + f': *{context.user_data["plan"]} Pack*\n\n'
    reply_text += client_functions_texts("send_token") + f' *{context.user_data["amount"]} ' + client_functions_texts("tron") + f'({context.user_data["currency"]})* ' + client_functions_texts("to_our_wallet") + ' '
    reply_text += f'(`{context.user_data["wallet"]}`) ' + client_functions_texts("crypto_wallet_link") + f': \n\n{context.user_data["payment_url"]}\n\n⚠️ '
    reply_text += client_functions_texts("send_transaction_id") + ':\n\n' + client_functions_texts("cancel_to_abort")

    # context.user_data['org'] = selected_org
    keyboard = [
        [telegram.InlineKeyboardButton(client_functions_texts("general_cancel"), callback_data='Cancel')]
    ]
    reply_markup = telegram.InlineKeyboardMarkup(keyboard)
    # Send message with text and appended InlineKeyboard
    await context.user_data['menu'].edit_text(reply_text, reply_markup=reply_markup, parse_mode=telegram.constants.ParseMode.MARKDOWN)

    db_client.close()

    return NEWUSER_PURCHASE_FINAL

async def newuser_purchase_receipt_crypto_inputed(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    print("in newuser_purchase_receipt_crypto_inputed")
    try: 
        db_client = connect_to_database(secrets['DBConString'])
    except Exception as e:
        print("Failed to connect to the database!")

    if not await check_subscription(update):
        main_channel = db_client[secrets['DBName']].orgs.find_one({'name': 'main'})['channel']['link']
        reply_text = client_functions_texts('join_channel') + f"\n\n{main_channel}"
        await context.user_data['menu'].reply_text(reply_text)
        
        db_client.close()

        return telext.ConversationHandler.END
    else:
            user_dict = db_client[secrets['DBName']].users.find_one({'user_id': int(update.effective_chat.id)})
            if user_dict is None:
                reply_text = client_functions_texts("user_not_found")
                await context.user_data['menu'].reply_text(reply_text)
            else:
                org_name = context.user_data['org']
                org_obj = db_client[secrets['DBName']].orgs.find_one({'name': org_name})
                org_ticketing_channel_id = org_obj['ticketing_group_id']
                support_account = org_obj['support_account']

                # context.user_data['transaction_id'] = transaction_id

                transaction_id = normalize_transaction_id(update.effective_message.text)
                context.user_data['transaction_id'] = transaction_id

                (tr_isValid, tr_validation_message) = validate_transaction(context.user_data['payment_url'], transaction_id, org_name, context.user_data['plan'])

                if (transaction_id == False) or (not tr_isValid):
                    await context.bot.send_message(
                        chat_id=context.user_data['user_id'],
                        text=tr_validation_message
                    )
                    db_client.close()

                    return telext.ConversationHandler.END

                if  context.user_data['currency'] != "rial":
                    payment_type = "crypto"
                else:
                    payment_type = "rial"

                tr_verification_data = {
                    "user_id": context.user_data['user_id'],
                    "org": context.user_data['org'],
                    "plan": context.user_data['plan'],
                    "payment_type": payment_type,
                    "currency": context.user_data['currency'],
                    "amount": context.user_data['amount'] * context.user_data['discount'],
                    "discount": context.user_data['discount'],
                    "transactionID": transaction_id,
                    "payment_url": context.user_data['payment_url'],
                    "date": datetime.datetime.now().isoformat(),
                    "verified": False,
                    "failed": False
                }

                db_client[secrets['DBName']].payments.insert_one(tr_verification_data)
                # ToDo Rasoul

            await context.bot.send_message(
                chat_id=context.user_data['chat'].id,
                # text=f"You are now added to the organization. Please follow the following channel for announcements about server connectivities: \n[Channel Link](https://t.me/+fpMXFyhEYD1jZDM8)"
                text=client_functions_texts("verify_crypto_manually")
                )


            reply_text = client_functions_texts("verify_crypto_manually2") + ":"

            # context.user_data['org'] = selected_org
            keyboard = [
                [telegram.InlineKeyboardButton(client_functions_texts("check_crypto_button"), callback_data='Check Manually')]
            ]
            reply_markup = telegram.InlineKeyboardMarkup(keyboard)
            # Send message with text and appended InlineKeyboard
            await context.user_data['menu'].edit_text(reply_text, reply_markup=reply_markup, parse_mode=telegram.constants.ParseMode.MARKDOWN)

            db_client.close()
            context.user_data['menu'] = update.message

            return CHECK_TRANS_MANUALLY
            # return telext.ConversationHandler.END

async def newuser_purchase_crypto_check_manually(update, context):
    try: 
        db_client = connect_to_database(secrets['DBConString'])
    except Exception as e:
        print("Failed to connect to the database!")

    org_name = context.user_data['org']
    org_obj = db_client[secrets['DBName']].orgs.find_one({'name': org_name})
    org_ticketing_channel_id = org_obj['ticketing_group_id']
    tr_obj = db_client[secrets['DBName']].payments.find_one({'transactionID': context.user_data['transaction_id']})
    support_account = org_obj['support_account']

    if tr_obj['verified'] is True:
        await context.bot.send_message(
            chat_id=context.user_data['user_id'],
            text=client_functions_texts("already_verified_crypto_payment")
        )
        db_client.close()

        return telext.ConversationHandler.END

    user_dict = db_client[secrets['DBName']].users.find_one({'user_id': context.user_data['user_id']})

    (tr_isVerfy, tr_verification_message) = await verfiy_transaction(context.user_data['transaction_id'], context.user_data['amount'], context.user_data['wallet'] , context.user_data['user_id'], context.user_data['plan'], context.user_data['payment_url'])

    if tr_isVerfy is False:
        if tr_verification_message != None:
            
            reply_text = client_functions_texts("failed_crypto_transaction") + f" \n" 
            reply_text += (client_functions_texts("error_wrong_trans_id") + '\n') if tr_verification_message == "Failed" else (client_functions_texts("error_wrong_amount") + client_functions_texts("selected_plan") + '.\n')
            reply_text += client_functions_texts("check_trans_manually_2") + f': \nhttps://tronscan.org/#/transaction/{context.user_data["transaction_id"]}\n\n'
            reply_text += client_functions_texts("contact_us_in_advance") + f': {support_account}'

            # User Message
            await context.bot.send_message(
                chat_id=context.user_data['chat'].id,
                # text=f"You are now added to the organization. Please follow the following channel for announcements about server connectivities: \n[Channel Link](https://t.me/+fpMXFyhEYD1jZDM8)"
                text=reply_text,
                disable_web_page_preview=True,
            )

            # Bot Message for Ticketing Admins
            await context.bot.send_message(
                chat_id=org_ticketing_channel_id,
                text=
                    f"❌ Failed Payment from user: \n\n" +
                    (f"@{context.user_data['username']} - " if(context.user_data['username'] is not None) else "") + 
                    f"{context.user_data['user_id']} - {context.user_data['full_name']}" + 
                    f"\nPlan: {context.user_data['plan']} Pack" +
                    "\n-------------------------" +
                    (f"\nPossibility of wrong transaction ID.\n" if tr_verification_message == "Failed" else f"\nPossibility of incorrect amount or destination wallet on this transaction ID and selected plan.\n") +
                    f"\nhttps://tronscan.org/#/transaction/{context.user_data['transaction_id']}",
                disable_web_page_preview=True,
                reply_to_message_id= secrets['test_topic_id'] if secrets["DBName"].lower() == "rhvp-test" else secrets['payments_topic_id']
            )

            db_client[secrets['DBName']].payments.update_one({'transactionID': context.user_data['transaction_id']}, { "$set": {"failed": True}})

            db_client.close()
            return telext.ConversationHandler.END

        reply_text = client_functions_texts("not_verified_payment")
        # f"\n\nIf there was a problem, at first please check if your transaction ID is sent correctly and then contact us at: {support_account}"

        await context.bot.send_message(
            chat_id=context.user_data['chat'].id,
            # text=f"You are now added to the organization. Please follow the following channel for announcements about server connectivities: \n[Channel Link](https://t.me/+fpMXFyhEYD1jZDM8)"
            text=reply_text
        )

        return CHECK_TRANS_MANUALLY
    else:
        server_dict = db_client[secrets['DBName']].servers.find_one({"org": org_name})
        # if context.user_data['plan'] == 'Family':
        #     charge_amount = 30 - int(server_dict['traffic'])
        # elif context.user_data['plan'] == 'Career':
        #     charge_amount = 50 - int(server_dict['traffic'])
        # else:
        #     charge_amount = 100 - int(server_dict['traffic'])
        charge_amount = int(org_obj['payment_options']['plans'][context.user_data['plan']])

        user_client = xAPI.get_clients(server_dict, select=[f"{user_dict['user_id']}@{server_dict['rowRemark']}"])
        if user_client is None:
            result = xAPI.add_client(server_dict, user_dict['user_id'], charge_amount, user_dict['uuid'], 
                            # expires:datetime.datetime=None
                            )
        total = xAPI.xui_charge_account(server_dict, context.user_data['user_id'], charge_amount, new=True)

        db_client[secrets['DBName']].payments.update_one({'transactionID': context.user_data['transaction_id']}, { "$set": {"verified": True}})

        org_channel = db_client[secrets['DBName']].orgs.find_one({'name': context.user_data['org']})['channel']['link']

        text = client_functions_texts("verified_account") + f' {charge_amount} ' + client_functions_texts("GB") + '!\n'
        text += client_functions_texts("added_to_org") + f': \n\n{org_channel}\n\n *{secrets["DBName"]}* ' + client_functions_texts("group") + ' 🤍️'

        await context.bot.send_message(
            chat_id=context.user_data['user_id'],
            text=text,
            disable_web_page_preview=True
        )

        context.user_data['paymeny_method'] = "crypto"
        context.user_data['payment_receipt'] = f"\nhttps://tronscan.org/#/transaction/`{context.user_data['transaction_id']}`"

        # Bot Message for Ticketing Admins
        await context.bot.send_message(
            chat_id=org_ticketing_channel_id,
            text=
                f"✅ Verfied Payment from user: \n\n" +
                (f"@{context.user_data['username']} - " if(context.user_data['username'] is not None) else "") + 
                f"{context.user_data['user_id']} - {context.user_data['full_name']}" + 
                f"\nPlan: {context.user_data['plan']} Pack" +
                "\n-------------------------" +
                f"\nhttps://tronscan.org/#/transaction/`{context.user_data['transaction_id']}`",
            disable_web_page_preview=True,
            reply_to_message_id=secrets['test_topic_id'] if secrets["DBName"].lower() == "rhvp-test" else secrets['payments_topic_id']
        )

        db_client[secrets['DBName']].users.update_one({'user_id': context.user_data['user_id']}, {"$set": {f"orgs.{org_name}": {"expires": (datetime.datetime.now()+datetime.timedelta(days=62)).isoformat()}}})
        db_client.close()

        return telext.ApplicationHandlerStop(telext.ConversationHandler.END)
        # return telext.ConversationHandler.END

############## User Recharge Account ##############
async def user_charge_account(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    try: 
        db_client = connect_to_database(secrets['DBConString'])
    except Exception as e:
        print("Failed to connect to the database!")

    query = update.callback_query
    await query.answer()
    if query.data == 'Cancel':
        db_client.close()
        return telext.ConversationHandler.END
    if not await check_subscription(update):
        main_channel = db_client[secrets['DBName']].orgs.find_one({'name': 'main'})['channel']['link']
        reply_text = client_functions_texts('join_channel') + f"\n\n{main_channel}"
        await update.effective_message.edit_text(reply_text)
        # application.add_handler(menu_handler)

        db_client.close()

        return telext.ConversationHandler.END
    # selected_org = query.data['org']
    # if selected_org not in db_client[secrets['DBName']].admins.find_one({'user_id': update.effective_user.id})['orgs']:
    #     reply_text = "Unathorized! Also, How are you here?"
    #     await update.effective_message.edit_text(reply_text)

    #     db_client.close()

    #     return telext.ConversationHandler.END
    # else:
    reply_text = client_functions_texts("choose_plan2") + ':\n\n' + client_functions_texts("cancel_to_abort")

    # context.user_data['org'] = selected_org
    user_obj = db_client[secrets['DBName']].users.find_one({'user_id': update.effective_user.id}, {"orgs": { "$slice": 1 }})
    org_name = list(user_obj["orgs"].keys())[0]
    org_obj = db_client[secrets['DBName']].orgs.find_one({'name': org_name})
    context.user_data['org_obj'] = org_obj

    user_dict = db_client[secrets['DBName']].users.find_one({'user_id': int(update.effective_chat.id)})
    context.user_data['user_dict'] = user_dict
    if ('discount' in user_dict and user_dict['discount']):
        discount = (100-user_dict['discount']) / 100
    else:
        discount = 1
    context.user_data['discount'] = discount

    keyboard = [
        # [telegram.InlineKeyboardButton(f"{plan}: {org_obj['payment_options']['plans'][plan]} " + client_functions_texts("GB") + f" -> {org_obj['payment_options']['currencies']['rial']['plans'][plan]} " + client_functions_texts("T")
        #                                , callback_data={'plan': plan})] for plan in org_obj['payment_options']['currencies']['rial']['plans']
        [telegram.InlineKeyboardButton(f"{plan}: {round(int(org_obj['payment_options']['currencies']['rial']['plans'][plan]) * discount)} T" + (f" ({100-100*discount}% off)" if (100-100*discount != 0) else "")
                                       , callback_data={'plan': plan})] for plan in org_obj['payment_options']['currencies']['rial']['plans']
    ]
    keyboard.extend([[telegram.InlineKeyboardButton(client_functions_texts("general_cancel"), callback_data='Cancel')]])

    reply_markup = telegram.InlineKeyboardMarkup(keyboard)
    # Send message with text and appended InlineKeyboard
    await update.effective_message.edit_text(reply_text, reply_markup=reply_markup, parse_mode=telegram.constants.ParseMode.MARKDOWN)

    db_client.close()

    return USER_RECHARGE_ACCOUNT_SELECT_PLAN

async def user_charge_account_with_plan(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    try: 
        db_client = connect_to_database(secrets['DBConString'])
    except Exception as e:
        print("Failed to connect to the database!")

    query = update.callback_query
    await query.answer()
    if query.data == 'Cancel':
        db_client.close()
        return telext.ConversationHandler.END
    if 'plan' not in context.user_data:
        context.user_data['plan'] = query.data['plan']


    if not await check_subscription(update):
        main_channel = db_client[secrets['DBName']].orgs.find_one({'name': 'main'})['channel']['link']
        reply_text = client_functions_texts('join_channel') + f"\n\n{main_channel}"
        await update.effective_message.edit_text(reply_text)
        # application.add_handler(menu_handler)

        db_client.close()

        return telext.ConversationHandler.END
    # selected_org = query.data['org']
    # if selected_org not in db_client[secrets['DBName']].admins.find_one({'user_id': update.effective_user.id})['orgs']:
    #     reply_text = "Unathorized! Also, How are you here?"
    #     await update.effective_message.edit_text(reply_text)

    #     db_client.close()

    #     return telext.ConversationHandler.END
    # else:

    org_obj = context.user_data['org_obj']
    context.user_data['is_new_user'] = False
    context.user_data['payment_method'] = org_obj['payment_options']['currencies']['rial']['method']

    if context.user_data['payment_method'] == 'e-transfer':
        reply_text = client_functions_texts("selected_plan") + f': {query.data["plan"]} Pack\n' + client_functions_texts("send_crypto_transaction_receipt") + ':'
        if "card_number" in org_obj['payment_options']['currencies']['rial'] and org_obj['payment_options']['currencies']['rial']['card_number'] != "":
            reply_text += '\n\n' + client_functions_texts("card_number") + f': `{org_obj["payment_options"]["currencies"]["rial"]["card_number"]}`'
        reply_text += '\n\n' + client_functions_texts("cancel_to_abort")

        # context.user_data['org'] = selected_org
        keyboard = [
            [telegram.InlineKeyboardButton(client_functions_texts("general_cancel"), callback_data='Cancel')]
        ]
        reply_markup = telegram.InlineKeyboardMarkup(keyboard)
        # Send message with text and appended InlineKeyboard
        await update.effective_message.edit_text(reply_text, reply_markup=reply_markup, parse_mode=telegram.constants.ParseMode.MARKDOWN)

        db_client.close()

        return USER_RECHARGE_ACCOUNT
    else:
        reply_text = client_functions_texts("selected_plan") + f': {query.data["plan"]} Pack\n' + client_functions_texts("zarinpal_message") + ':\n\n' + client_functions_texts('cancel_to_abort')
        context.user_data['merchant_id'] = org_obj['payment_options']['currencies']['rial']['merchant_id']

        description = u'خرید پلن'+query.data['plan']
        email=''
        mobile=''
        secret_url=sc.token_urlsafe()

        context.user_data['pay_amount'] = org_obj['payment_options']['currencies']['rial']['plans'][query.data['plan']]
        context.user_data['payment_type'] = 'rial'

        url = "https://api.zarinpal.com/pg/v4/payment/request.json"
        payload = {
            "merchant_id": context.user_data['merchant_id'],
            "amount": int(context.user_data['pay_amount'])*10000,
            # "amount": 200000,
            "callback_url": "http://t.me/"+secrets["BOT_USERNAME"],
            "description": "خرید پلن"+query.data['plan'],
            
        }
        print(payload)

        headers = {
            "accept": "application/json",
            "content-type": "application/json"
        }

        response = requests.request("POST", url, json=payload, headers=headers).json()
        print(context.user_data)
        print(response['data'])
        context.user_data['authority']=response['data']['authority']
        context.user_data['secret_url']=secret_url

    
        # result = client.service.PaymentRequest(secrets['MMERCHANT_ID'],
        #                                        context.user_data['pay_amount'],
        #                                        description,
        #                                        email,
        #                                        mobile,

        #                                        )
        keyboard = [
            [telegram.InlineKeyboardButton(client_functions_texts("pay_now"), callback_data='Pay now')],
            [telegram.InlineKeyboardButton(client_functions_texts("general_cancel"), callback_data='Cancel')]
        ]
        reply_markup = telegram.InlineKeyboardMarkup(keyboard)
        # Send message with text and appended InlineKeyboard
        await update.effective_message.edit_text(reply_text, reply_markup=reply_markup, parse_mode=telegram.constants.ParseMode.MARKDOWN)

        db_client.close()
        return NEWUSER_PURCHASE_RIAL_ZARIN

async def user_charge_acc_inputed(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    print("in user_charge_acc_inputed")
    try: 
        db_client = connect_to_database(secrets['DBConString'])
    except Exception as e:
        print("Failed to connect to the database!")

    if not await check_subscription(update):
        main_channel = db_client[secrets['DBName']].orgs.find_one({'name': 'main'})['channel']['link']
        reply_text = client_functions_texts('join_channel') + f"\n\n{main_channel}"
        await update.effective_message.reply_text(reply_text)
        
        db_client.close()

        return telext.ConversationHandler.END
    else:
            user_dict = db_client[secrets['DBName']].users.find_one({'user_id': int(update.effective_chat.id)})
            if user_dict is None:
                reply_text = client_functions_texts("user_not_found")
                await update.effective_message.reply_text(reply_text)
            else:
                user_obj = db_client[secrets['DBName']].users.find_one({'user_id': update.effective_user.id}, {"orgs": { "$slice": 1 }})
                org_name = list(user_obj["orgs"].keys())[0]
                org_obj = db_client[secrets['DBName']].orgs.find_one({'name': org_name})

                keyboard = [
                        [telegram.InlineKeyboardButton('❌ Reject', callback_data='Reject'),telegram.InlineKeyboardButton('✅ Accept', callback_data='Accept')]
                    ]
                
                context.user_data["payment_receipt"] = update.effective_message.text

                reply_markup = telegram.InlineKeyboardMarkup(keyboard)

                # await context.bot.send_message(
                #     chat_id=org_obj['ticketing_group_id'],
                #     text=
                #         f"*Recharging* - *{context.user_data['payment_method']}* Payment from user: \n\n" +
                #         (f"@{update.effective_chat.username} - " if(update.effective_chat.username is not None) else "") + 
                #         f"{update.effective_chat.id} - {update.effective_chat.full_name}" + 
                #         f"\nPlan: {context.user_data['plan']} Pack" +
                #         "\n-------------------------" +
                #         f"\n{update.effective_message.text}",
                #         reply_to_message_id= 753 if secrets["DBName"].lower() == "rhvp-test" else 3,
                #         reply_markup=reply_markup
                #     )
                context.user_data['payment_receipt'] = f"\n{update.effective_message.text}"
                context.user_data['full_name'] = update.effective_chat.full_name
                context.user_data['username'] = update.effective_chat.username
                context.user_data['user_id'] = update.effective_chat.id
                context.user_data['org'] = org_name
                context.user_data['pay_amount'] = org_obj['payment_options']['currencies']['rial']['plans'][context.user_data['plan']]
                await context.bot.send_message(
                    chat_id=org_obj['ticketing_group_id'],
                    text=
                        f"Recharg\n"+
                        f"payment_method:{context.user_data['payment_method']}\n" +
                        (f"username:@{context.user_data['username']}\n" if(context.user_data['username'] is not None) else "") + 
                        f"user_id:{context.user_data['user_id']}\nfull_name:{context.user_data['full_name']}\n" +
                        f"Plan:{context.user_data['plan']}\n" +
                        f"org:{context.user_data['org']}\n"+
                        f"pay_amount:{context.user_data['pay_amount']}, included {100-100*context.user_data['discount']}% discount\n" +
                        f"currency:rial\n"+
                        "-------------------------\n" +
                        context.user_data['payment_receipt'],
                    reply_to_message_id=secrets['test_topic_id'] if secrets["DBName"].lower() == "rhvp-test" else secrets['payments_topic_id'],
                    reply_markup=reply_markup
                    )
                

                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    # text=f"You are now added to the organization. Please follow the following channel for announcements about server connectivities: \n[Channel Link](https://t.me/+fpMXFyhEYD1jZDM8)"
                    text=client_functions_texts("thanks_for_payment")
                    )

            db_client.close()
            return telext.ConversationHandler.END

async def user_charge_acc_inputed_image(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    print("in user_charge_acc_inputed")
    try: 
        db_client = connect_to_database(secrets['DBConString'])
    except Exception as e:
        print("Failed to connect to the database!")

    if not await check_subscription(update):
        main_channel = db_client[secrets['DBName']].orgs.find_one({'name': 'main'})['channel']['link']
        reply_text = client_functions_texts('join_channel') + f"\n\n{main_channel}"
        await update.effective_message.reply_text(reply_text)
        
        db_client.close()

        return telext.ConversationHandler.END
    else:
            user_dict = db_client[secrets['DBName']].users.find_one({'user_id': int(update.effective_chat.id)})
            if user_dict is None:
                reply_text = client_functions_texts("user_not_found")
                await update.effective_message.reply_text(reply_text)
            else:
                user_obj = db_client[secrets['DBName']].users.find_one({'user_id': update.effective_user.id}, {"orgs": { "$slice": 1 }})
                org_name = list(user_obj["orgs"].keys())[0]
                org_obj = db_client[secrets['DBName']].orgs.find_one({'name': org_name})

                keyboard = [
                        [telegram.InlineKeyboardButton('❌ Reject', callback_data='Reject'),telegram.InlineKeyboardButton('✅ Accept', callback_data='Accept')]
                    ]
                
                context.user_data["payment_receipt"] = update.effective_message.text

                reply_markup = telegram.InlineKeyboardMarkup(keyboard)
                context.user_data['payment_receipt'] = f"\n{update.effective_message.text}"
                context.user_data['full_name'] = update.effective_chat.full_name
                context.user_data['username'] = update.effective_chat.username
                context.user_data['user_id'] = update.effective_chat.id
                context.user_data['org']=org_name
                context.user_data['pay_amount'] = org_obj['payment_options']['currencies']['rial']['plans'][context.user_data['plan']]

                await context.bot.send_photo(
                    chat_id=org_obj['ticketing_group_id'],
                    photo=update.message.photo[0].file_id,
                    caption=
                        f"Recharg\n"+
                        f"payment_method:{context.user_data['payment_method']}\n" +
                        (f"username:@{context.user_data['username']}\n" if(context.user_data['username'] is not None) else "") + 
                        f"user_id:{context.user_data['user_id']}\nfull_name:{context.user_data['full_name']}\n" + 
                        f"Plan:{context.user_data['plan']}\n" +
                        f"org:{context.user_data['org']}\n"+
                        f"pay_amount:{context.user_data['pay_amount']}, included {100-100*context.user_data['discount']}% discount\n"
                        f"currency:rial\n",
                    reply_to_message_id= secrets['test_topic_id'] if secrets["DBName"].lower() == "rhvp-test" else secrets['payments_topic_id'],
                    reply_markup=reply_markup
                )
                # await context.bot.send_message(
                #     chat_id=org_obj['ticketing_group_id'],
                #     # text=f"Payment from user: {update.effective_chat.id} - {update.effective_chat.full_name} - @{update.effective_chat.username}\nPlan: {context.user_data['plan']} Pack\n\nReciept:\n{update.effective_message.text}",
                #     text=
                #         f"Payment from user: \n\n" +
                #         (f"@{update.effective_chat.username} - " if(update.effective_chat.username is not None) else "") + 
                #         f"{update.effective_chat.id} - {update.effective_chat.full_name}" + 
                #         f"\nPlan: {context.user_data['plan']} Pack" +
                #         "\n-------------------------" +
                #         f"\n{update.effective_message.text}",
                #     reply_to_message_id= 753 if secrets["DBName"].lower() == "rhvp-test" else 3
                #     )

                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    # text=f"You are now added to the organization. Please follow the following channel for announcements about server connectivities: \n[Channel Link](https://t.me/+fpMXFyhEYD1jZDM8)"
                    text=client_functions_texts("thanks_for_payment")
                    )

            db_client.close()
            return telext.ConversationHandler.END
