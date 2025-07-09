import telegram
import telegram.ext as telext
import datetime
from .initial import get_secrets_config, connect_to_database, set_lang
from .bot_functions import check_subscription, check_newuser
import helpers.xuiAPI as xAPI
from helpers.states import *
import pandas as pd
import uuid

############################# GLOBALS #############################
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
    CHANGING_SERVER_TRAFFIC,
    ADMIN_DIRECT_MESSAGE_USERID,
    ADMIN_DIRECT_MESSAGE_TEXT
) = range(16)

(secrets, Config) = get_secrets_config()
org_admin_texts = set_lang(Config['default_language'], 'org_admin')

############################# Functions #############################

async def manage_my_org(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
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
        reply_text = org_admin_texts('join_channel') + f'\n\n{main_channel}'
        await update.effective_message.edit_text(reply_text)
        # application.add_handler(menu_handler)

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
                # [telegram.InlineKeyboardButton('Add Memeber', callback_data={'Exceed Users: Hard Coded': 'Exceed Users: Hard Coded'})],
                [telegram.InlineKeyboardButton('🖥 List Org Servers', callback_data={'task': 'List Org Servers', 'org': selected_org})],
                [telegram.InlineKeyboardButton('🔌 Charge a Account', callback_data={'task':'Admin Charge Account', 'org': selected_org})],
                [telegram.InlineKeyboardButton('🔋 Charge All Accounts', callback_data={'task':'Admin Charge All Accounts', 'org': selected_org})],
                [telegram.InlineKeyboardButton('🎯 Direct Message', callback_data={'task':'Direct Message', 'org': selected_org})],
                [telegram.InlineKeyboardButton('Cancel', callback_data='Cancel')]
            ]
            reply_markup = telegram.InlineKeyboardMarkup(keyboard)
            # Send message with text and appended InlineKeyboard
            reply_text = f"Managing: {selected_org}"
            await update.effective_message.edit_text(reply_text, reply_markup=reply_markup, parse_mode=telegram.constants.ParseMode.MARKDOWN)

            db_client.close()

            return MY_ORG_MNGMNT_SELECT_OPTION

async def add_member_to_my_org(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
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
        reply_text = org_admin_texts('join_channel') + f'\n\n{main_channel}'
        await update.effective_message.edit_text(reply_text)
        # application.add_handler(menu_handler)

        db_client.close()

        return telext.ConversationHandler.END
    selected_org = query.data['org']

    if (update.effective_user.id not in secrets["MainAdmins"]) or (selected_org in db_client[secrets['DBName']].admins.find_one({'user_id': update.effective_user.id})['orgs']):
            reply_text = "Please send the new member's NUMERICAL ID\nClick cancel to abort."
            context.user_data['org'] = selected_org
            keyboard = [
                [telegram.InlineKeyboardButton('❌ Cancel', callback_data='Cancel')]
            ]
            reply_markup = telegram.InlineKeyboardMarkup(keyboard)
            # Send message with text and appended InlineKeyboard
            await update.effective_message.edit_text(reply_text, reply_markup=reply_markup, parse_mode=telegram.constants.ParseMode.MARKDOWN)

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
    except Exception as e:
        print("Failed to connect to the database!")

    if not await check_subscription(update):
        main_channel = db_client[secrets['DBName']].orgs.find_one({'name': 'main'})['channel']['link']
        reply_text = org_admin_texts('join_channel') + f'\n\n{main_channel}'
        await update.effective_message.reply_text(reply_text)
        # application.add_handler(menu_handler)
        
        db_client.close()

        return telext.ConversationHandler.END
    selected_org = context.user_data['org']
    if selected_org not in db_client[secrets['DBName']].admins.find_one({'user_id': update.effective_user.id})['orgs']:
        reply_text = "Unathorized! Also, How are you here?"
        await update.effective_message.reply_text(reply_text)

        db_client.close()

        return telext.ConversationHandler.END
    else:
            user_dict = db_client[secrets['DBName']].users.find_one({'user_id': int(update.effective_message.text)})
            if user_dict is None:
                reply_text = "User is not a member of the bot.\nUser should start the bot first."
                await update.effective_message.reply_text(reply_text)

                db_client.close()

                return telext.ConversationHandler.END
            elif selected_org in user_dict['orgs'].keys():
                reply_text = f"User {user_dict['user_id']} is Already a member of {selected_org}."
                # until {user_dict['orgs'][selected_org]['expires'].strftime('%Y-%m-%d %H:%M UTC')}."
                await update.effective_message.reply_text(reply_text)

                db_client.close()

                return telext.ConversationHandler.END
            else: # Add the user to org directly, TODO: ask for confirmation with the user info
                expires = datetime.datetime.now() + datetime.timedelta(days=30)
                db_client[secrets['DBName']].users.update_one({'user_id': user_dict['user_id']}, 
                                                              [{'$set': {'orgs': {selected_org: {'expires': expires}}}}])
                reply_text = f"User {user_dict['user_id']} Added to {selected_org}.\nExpiration: {expires.strftime('%Y-%m-%d %H:%M UTC')}"
                org_channel = db_client[secrets['DBName']].orgs.find_one({'name': selected_org})['channel']['link']
                await context.bot.send_message(
                    chat_id=user_dict['user_id'],
                    text=org_admin_texts("after_adding_to_org") + f': \n\n{org_channel}',
                    disable_web_page_preview=True
                    # text=f"You are now added to the organization. Please follow the following channel for announcements about server connectivities: \n[https://t.me/+fpMXFyhEYD1jZDM8](لینک کانال)"
                )

                await update.effective_message.reply_text(reply_text, parse_mode=telegram.constants.ParseMode.MARKDOWN)

                db_client.close()

                return telext.ConversationHandler.END

async def ban_member(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
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
        reply_text = org_admin_texts('join_channel') + f'\n\n{main_channel}'
        await update.effective_message.edit_text(reply_text)
        # application.add_handler(menu_handler)

        db_client.close()

        return telext.ConversationHandler.END
    selected_org = query.data['org']
    if selected_org not in db_client[secrets['DBName']].admins.find_one({'user_id': update.effective_user.id})['orgs']:
        reply_text = "Unathorized! Also, How are you here?"
        await update.effective_message.edit_text(reply_text)

        db_client.close()

        return telext.ConversationHandler.END
    else:
            reply_text = "Please send the member's NUMERICAL ID\nClick cancel to abort."
            context.user_data['org'] = selected_org
            keyboard = [
                [telegram.InlineKeyboardButton('❌ Cancel', callback_data='Cancel')]
            ]
            reply_markup = telegram.InlineKeyboardMarkup(keyboard)
            # Send message with text and appended InlineKeyboard
            await update.effective_message.edit_text(reply_text, reply_markup=reply_markup, parse_mode=telegram.constants.ParseMode.MARKDOWN)

            db_client.close()

            return BAN_MEMBER

async def ban_member_inputed(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    try: 
        db_client = connect_to_database(secrets['DBConString'])
    except Exception as e:
        print("Failed to connect to the database!")

    if not await check_subscription(update):
        main_channel = db_client[secrets['DBName']].orgs.find_one({'name': 'main'})['channel']['link']
        reply_text = org_admin_texts('join_channel') + f'\n\n{main_channel}'
        await update.effective_message.reply_text(reply_text)
        # application.add_handler(menu_handler)
        
        db_client.close()

        return telext.ConversationHandler.END
    selected_org = context.user_data['org']
    if selected_org not in db_client[secrets['DBName']].admins.find_one({'user_id': update.effective_user.id})['orgs']:
        reply_text = "Unathorized! Also, How are you here?"
        await update.effective_message.reply_text(reply_text)

        db_client.close()

        return telext.ConversationHandler.END
    if selected_org not in db_client[secrets['DBName']].users.find_one({'user_id': int(update.effective_message.text)})['orgs']:
        reply_text = "User does not exist in this organization!"
        await update.effective_message.reply_text(reply_text)

        db_client.close()

        return telext.ConversationHandler.END
    else:
            user_dict = db_client[secrets['DBName']].users.find({
                    'user_id': int(update.effective_message.text),
                    'orgs.' + selected_org: {'$exists': True}
                 })
            if user_dict is None:
                reply_text = "User is not a member of the bot.\nUser should start the bot first."
                await update.effective_message.reply_text(reply_text)
            else:
                user_servers = user_dict["server_names"]
                server_dicts = db_client[secrets['DBName']].servers.find({
                    'name': {'$in': user_servers}
                })

                org_support_account = db_client[secrets['DBName']].orgs.find({'name': selected_org})['support_account']

                xAPI.restrict_user(server_dicts, str(update.effective_message.text))
                await context.bot.send_message(
                        chat_id=update.effective_message.text,
                        text=org_admin_texts("after_banned") + '\n' + org_admin_texts("contact_support") + f': {org_support_account}'
                        )
                await context.bot.send_message(
                        chat_id=update.effective_userf.id,
                        text=f"Account with userid {update.effective_message.text} has been banned!"
                        )

            db_client.close()
            return telext.ConversationHandler.END

async def list_my_org_servers(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
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
        reply_text = org_admin_texts('join_channel') + f'\n\n{main_channel}'
        await update.effective_message.edit_text(reply_text)
        # application.add_handler(menu_handler)

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
            # Send message with text and appended InlineKeyboard
            await update.effective_message.edit_text(reply_text, reply_markup=reply_markup, parse_mode=telegram.constants.ParseMode.MARKDOWN)

            db_client.close()

            return LISTING_ORG_SERVERS

async def manage_my_org_server(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
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
        reply_text = org_admin_texts('join_channel') + f'\n\n{main_channel}'
        await update.effective_message.edit_text(reply_text)
        # application.add_handler(menu_handler)
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
            # Send message with text and appended InlineKeyboard
            await update.effective_message.edit_text(reply_text, reply_markup=reply_markup, parse_mode=telegram.constants.ParseMode.MARKDOWN)

            db_client.close()

            return CHOSING_SERVER_EDIT_ACTION

async def switch_server_active_join(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    try: 
        db_client = connect_to_database(secrets['DBConString'])
    except Exception as e:
        print("Failed to connect to the database!")

    query = update.callback_query
    # await query.answer()
    if not await check_subscription(update):
        main_channel = db_client[secrets['DBName']].orgs.find_one({'name': 'main'})['channel']['link']
        reply_text = org_admin_texts('join_channel') + f'\n\n{main_channel}'
        await update.effective_message.edit_text(reply_text)
        # application.add_handler(menu_handler)

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
            # Send message with text and appended InlineKeyboard
            await update.effective_message.edit_text(reply_text, reply_markup=reply_markup, parse_mode=telegram.constants.ParseMode.MARKDOWN)
            
            db_client.close()

            return CHOSING_SERVER_EDIT_ACTION

async def change_server_traffic(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    try: 
        db_client = connect_to_database(secrets['DBConString'])
    except Exception as e:
        print("Failed to connect to the database!")

    query = update.callback_query
    # await query.answer()
    if not await check_subscription(update):
        main_channel = db_client[secrets['DBName']].orgs.find_one({'name': 'main'})['channel']['link']
        reply_text = org_admin_texts('join_channel') + f'\n\n{main_channel}'
        await update.effective_message.edit_text(reply_text)
        # application.add_handler(menu_handler)
        
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
            # Send message with text and appended InlineKeyboard
            await update.effective_message.edit_text(reply_text, reply_markup=reply_markup, parse_mode=telegram.constants.ParseMode.MARKDOWN)
            
            db_client.close()

            return CHANGING_SERVER_TRAFFIC

async def change_server_traffic_inputed(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    try: 
        db_client = connect_to_database(secrets['DBConString'])
    except Exception as e:
        print("Failed to connect to the database!")

    if not await check_subscription(update):
        main_channel = db_client[secrets['DBName']].orgs.find_one({'name': 'main'})['channel']['link']
        reply_text = org_admin_texts('join_channel') + f'\n\n{main_channel}'
        await update.effective_message.reply_text(reply_text)
        # application.add_handler(menu_handler)
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
            
            # Send message with text and appended InlineKeyboard
            await update.effective_message.reply_text(reply_text, parse_mode=telegram.constants.ParseMode.MARKDOWN)
            
            db_client.close()

            return telext.ConversationHandler.END

async def admin_announcement(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
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
        reply_text = org_admin_texts('join_channel') + f'\n\n{main_channel}'
        await update.effective_message.edit_text(reply_text)
        # application.add_handler(menu_handler)

        db_client.close()

        return telext.ConversationHandler.END
    selected_org = query.data['org']
    if selected_org not in db_client[secrets['DBName']].admins.find_one({'user_id': update.effective_user.id})['orgs']:
        reply_text = "Unathorized! Also, How are you here?"
        await update.effective_message.edit_text(reply_text)

        db_client.close()

        return telext.ConversationHandler.END
    else:
            reply_text = "Please send your announcement\n⚠️ Consider that it will be sent to everyone in your organization through bot\n\nClick cancel to abort."
            context.user_data['org'] = selected_org
            keyboard = [
                [telegram.InlineKeyboardButton('❌ Cancel', callback_data='Cancel')]
            ]
            reply_markup = telegram.InlineKeyboardMarkup(keyboard)
            # Send message with text and appended InlineKeyboard
            await update.effective_message.edit_text(reply_text, reply_markup=reply_markup, parse_mode=telegram.constants.ParseMode.MARKDOWN)

            db_client.close()

            return ADMIN_ANNOUNCEMENT

async def admin_announcement_inputed(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    try: 
        db_client = connect_to_database(secrets['DBConString'])
    except Exception as e:
        print("Failed to connect to the database!")

    if not await check_subscription(update):
        main_channel = db_client[secrets['DBName']].orgs.find_one({'name': 'main'})['channel']['link']
        reply_text = org_admin_texts('join_channel') + f'\n\n{main_channel}'
        await update.effective_message.reply_text(reply_text)
        # application.add_handler(menu_handler)
        
        db_client.close()

        return telext.ConversationHandler.END
    selected_org = context.user_data['org']
    if selected_org not in db_client[secrets['DBName']].admins.find_one({'user_id': update.effective_user.id})['orgs']:
        reply_text = "Unathorized! Also, How are you here?"
        await update.effective_message.reply_text(reply_text)

        db_client.close()

        return telext.ConversationHandler.END
    else:
            # user_dicts = db_client[secrets['DBName']].users.find({
            #     'orgs': {selected_org: {"$exists": True}}
            # })
            user_dicts = db_client[secrets['DBName']].users.find({
                'orgs.' + selected_org: {'$exists': True}
                # 'orgs': {selected_org: {"$exists": True}}
            })
            for user_dict in user_dicts:
                try:
                    await context.bot.send_message(
                            chat_id=user_dict['user_id'],
                            text=org_admin_texts("admin_announcement") + f'\n\n{update.effective_message.text}'
                            )
                except:
                    print("Failed to send message to user: " + str(user_dict['user_id']))

            db_client.close()
            return telext.ConversationHandler.END

async def direct_message_userid_inputed(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    try:
        db_client = connect_to_database(secrets['DBConString'])
    except Exception as e:
        print("Failed to connect to the database!")

    if not await check_subscription(update):
        main_channel = db_client[secrets['DBName']].orgs.find_one({'name': 'main'})['channel']['link']
        reply_text = org_admin_texts('join_channel') + f'\n\n{main_channel}'
        await update.effective_message.reply_text(reply_text)
        # application.add_handler(menu_handler)

        db_client.close()

        return telext.ConversationHandler.END
    selected_org = context.user_data['org']
    if selected_org not in db_client[secrets['DBName']].admins.find_one({'user_id': update.effective_user.id})['orgs']:
        reply_text = "Unathorized! Also, How are you here?"
        await update.effective_message.reply_text(reply_text)

        db_client.close()

        return telext.ConversationHandler.END
    else:
            user_dicts = db_client[secrets['DBName']].users.find({
                'orgs.' + selected_org: {'$exists': True},
                'user_id': int(update.effective_message.text)
                # 'orgs': {selected_org: {"$exists": True}}
            })
            if user_dicts is None:
                reply_text = "User is not a member of your organization or bot.\n"
                await update.effective_message.reply_text(reply_text)

                db_client.close()

                return telext.ConversationHandler.END
            else:
                context.user_data['selected_user'] = int(update.effective_message.text)
                reply_text = "Please send your message\n\nClick cancel to abort."
                keyboard = [
                    [telegram.InlineKeyboardButton('❌ Cancel', callback_data='Cancel')]
                ]
                reply_markup = telegram.InlineKeyboardMarkup(keyboard)
                # Send message with text and appended InlineKeyboard
                await update.effective_message.reply_text(reply_text, reply_markup=reply_markup)
                db_client.close()
                return ADMIN_DIRECT_MESSAGE_TEXT

async def direct_message_text_inputed(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    try:
        db_client = connect_to_database(secrets['DBConString'])
    except Exception as e:
        print("Failed to connect to the database!")
    if not await check_subscription(update):
        main_channel = db_client[secrets['DBName']].orgs.find_one({'name': 'main'})['channel']['link']
        reply_text = org_admin_texts("join_channel") + f'\n\n{main_channel}'
        await update.effective_message.reply_text(reply_text)
        # application.add_handler(menu_handler)

        db_client.close()

        return telext.ConversationHandler.END
    selected_org = context.user_data['org']
    selected_user = context.user_data['selected_user']
    if selected_org not in db_client[secrets['DBName']].admins.find_one({'user_id': update.effective_user.id})['orgs']:
        reply_text = "Unathorized! Also, How are you here?"
        await update.effective_message.reply_text(reply_text)

        db_client.close()

        return telext.ConversationHandler.END
    else:
            try:
                await context.bot.send_message(
                        chat_id=selected_user,
                        text=update.effective_message.text
                        )
                await update.effective_message.reply_text(f"Message Sent to {selected_user}!")
            except:
                await update.effective_message.reply_text(f"Failed to send message to {selected_user}!")
            db_client.close()
            return telext.ConversationHandler.END

async def direct_message(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
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
        reply_text = org_admin_texts('join_channel') + f'\n\n{main_channel}'
        await update.effective_message.edit_text(reply_text)
        # application.add_handler(menu_handler)

        db_client.close()

        return telext.ConversationHandler.END
    selected_org = query.data['org']
    if selected_org not in db_client[secrets['DBName']].admins.find_one({'user_id': update.effective_user.id})['orgs']:
        reply_text = "Unathorized! Also, How are you here?"
        await update.effective_message.reply_text(reply_text)

        db_client.close()

        return telext.ConversationHandler.END
    else:
            reply_text = "Please send your user_id in your organization\n\nClick cancel to abort."
            context.user_data['org'] = selected_org
            context.user_data['message_id_get_userid'] = update.effective_message.message_id
            keyboard = [
                [telegram.InlineKeyboardButton('❌ Cancel', callback_data='Cancel')]
            ]
            reply_markup = telegram.InlineKeyboardMarkup(keyboard)
            # Send message with text and appended InlineKeyboard
            print("direct_message")
            await update.effective_message.edit_text(reply_text, reply_markup=reply_markup)

            db_client.close()

            return ADMIN_DIRECT_MESSAGE_USERID



async def admin_charge_account(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
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
        reply_text = org_admin_texts('join_channel') + f'\n\n{main_channel}'
        await update.effective_message.edit_text(reply_text)
        # application.add_handler(menu_handler)

        db_client.close()

        return telext.ConversationHandler.END

    selected_org = query.data['org']

    if selected_org not in db_client[secrets['DBName']].admins.find_one({'user_id': update.effective_user.id})['orgs']:
        reply_text = "Unathorized! Also, How are you here?"
        await update.effective_message.edit_text(reply_text)

        db_client.close()

        return telext.ConversationHandler.END
    else:
        reply_text = "Please select the server:\n\nClick cancel to abort."
        context.user_data['org'] = selected_org
        server_names = db_client[secrets['DBName']].servers.find(
            filter={
                    'org': selected_org, 
                    "$or": [
                            {'isActive': {"$exists": True, "$eq": True}},
                            {"isActive": {"$exists": False}}
                        ]
                    }, 
            projection={'name': True}
        )
        keyboard = [
                [telegram.InlineKeyboardButton(s['name'], callback_data=s['name'])] for s in server_names
            ] + [
                [telegram.InlineKeyboardButton('❌ Cancel', callback_data='Cancel')]
            ]
        reply_markup = telegram.InlineKeyboardMarkup(keyboard)
        # Send message with text and appended InlineKeyboard
        await update.effective_message.edit_text(reply_text, reply_markup=reply_markup, parse_mode=telegram.constants.ParseMode.MARKDOWN)

        db_client.close()

        return ADMIN_CHARGE_ACCOUNT_USERID

async def admin_charge_account_with_server(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == 'Cancel':
        return telext.ConversationHandler.END

    server_name = query.data

    if(server_name == None and server_name == ""):
        await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"You must at first select server!"
            )
        return telext.ConversationHandler.END

    context.user_data['server_name'] = server_name
    # selected_org = context.user_data['org']

    reply_text = "Please send the unique user id account you want to charge and the amount. Example:\n\n8475837: 5\n\nClick cancel to abort."

    keyboard = [
            [telegram.InlineKeyboardButton('❌ Cancel', callback_data='Cancel')]
        ]
    reply_markup = telegram.InlineKeyboardMarkup(keyboard)
    # Send message with text and appended InlineKeyboard
    await update.effective_message.edit_text(reply_text, reply_markup=reply_markup, parse_mode=telegram.constants.ParseMode.MARKDOWN)

    return ADMIN_CHARGE_ACCOUNT_FINAL

async def admin_charge_account_with_server_and_userid(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    pass
#     context.user_data['user_id'] = update.effective_message.text
#     server_name = context.user_data['server_name']

#     if(server_name == None and server_name == ""):
#         await context.bot.send_message(
#                 chat_id=update.effective_chat.id,
#                 text=f"You must at first select server!"
#             )
#         return telext.ConversationHandler.END

#     context.user_data['server_name'] = server_name

#     reply_text = "Please send the amount you want to charge in GB:\nExample: 5\n\nClick cancel to abort."

#     keyboard = [
#             [telegram.InlineKeyboardButton('❌ Cancel', callback_data='Cancel')]
#         ]
#     reply_markup = telegram.InlineKeyboardMarkup(keyboard)
#     # Send message with text and appended InlineKeyboard
#     await update.effective_message.edit_text(reply_text, reply_markup=reply_markup, parse_mode=telegram.constants.ParseMode.MARKDOWN)

#     return ADMIN_CHARGE_ACCOUNT_FINAL

async def admin_charge_account_with_server_and_userid_and_amount(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    try: 
        db_client = connect_to_database(secrets['DBConString'])
    except Exception as e:
        print("Failed to connect to the database!")

    if not await check_subscription(update):
        main_channel = db_client[secrets['DBName']].orgs.find_one({'name': 'main'})['channel']['link']
        reply_text = org_admin_texts('join_channel') + f'\n\n{main_channel}'
        await update.effective_message.reply_text(reply_text)
        
        db_client.close()

        return telext.ConversationHandler.END

    server_name = context.user_data['server_name']

    selected_org = context.user_data['org']

    user_id = int(update.effective_message.text.split(":")[0])

    charge_amount = int(update.effective_message.text.split(":")[1])

    # print("user_id")
    # print(user_id)
    # print(charge_amount)
    if selected_org not in db_client[secrets['DBName']].admins.find_one({'user_id': update.effective_user.id})['orgs']:
        reply_text = "Unathorized! Also, How are you here?"
        await update.effective_message.reply_text(reply_text)

        db_client.close()

        return telext.ConversationHandler.END

    if selected_org not in db_client[secrets['DBName']].users.find_one({'user_id': user_id})['orgs']:
        reply_text = "User does not exist in this organization!"
        await update.effective_message.reply_text(reply_text)

        db_client.close()

        return telext.ConversationHandler.END
    else:
        server_dict = db_client[secrets['DBName']].servers.find_one({'name': server_name})
        user_dict = db_client[secrets['DBName']].users.find_one({'user_id': user_id})

        user_client = xAPI.get_clients(server_dict, select=[f"{user_dict['user_id']}@{server_dict['rowRemark']}"])

        if isinstance(user_client, pd.DataFrame) and user_client.empty:
            print("user is new")
            result = xAPI.add_client(server_dict, user_dict['user_id'], charge_amount, user_dict['uuid'], 
                            # expires:datetime.datetime=None
                    )
            total = charge_amount
        else:
            total = xAPI.xui_charge_account(server_dict, user_id, charge_amount)

        # prev_amount = xAPI.xui_charge_account(server_dict, user_xid, 0)

        # del_res = xAPI.delete_client(server_dict, user_dict['user_id']) # This may be redundant??
        # # prev_amount = user_client['totalGB']/1024**3

        # result = xAPI.add_client(server_dict, user_dict['user_id'], charge_amount, user_dict['uuid'], 
        #                     # expires:datetime.datetime=None
        #             )

        # total = xAPI.xui_charge_account(server_dict, user_id, charge_amount+int(prev_amount), new=True)
        await context.bot.send_message(
            chat_id=user_dict['user_id'],
            text=org_admin_texts("account_charged_for") + f' {charge_amount} ' + org_admin_texts("GB") + '!\n\n' + org_admin_texts("new_limit") + f': {total} ' + org_admin_texts("GB")
        )

        await context.bot.send_message(
            chat_id=update.effective_user.id,
            text=f"The account with userid {user_id} has been charged for {charge_amount} " + org_admin_texts("GB") + "!"
        )

        db_client.close()
        return telext.ConversationHandler.END


async def admin_charge_all_accounts(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
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
        reply_text = org_admin_texts('join_channel') + f'\n\n{main_channel}'
        await update.effective_message.edit_text(reply_text)
        # application.add_handler(menu_handler)

        db_client.close()

        return telext.ConversationHandler.END
    selected_org = query.data['org']
    if selected_org not in db_client[secrets['DBName']].admins.find_one({'user_id': update.effective_user.id})['orgs']:
        reply_text = "Unathorized! Also, How are you here?"
        await update.effective_message.edit_text(reply_text)

        db_client.close()

        return telext.ConversationHandler.END
    else:
        reply_text = "Please select the server:\n\nClick cancel to abort."
        context.user_data['org'] = selected_org
        server_names = db_client[secrets['DBName']].servers.find(filter={'org': selected_org, "$or": [
                            {'isActive': {"$exists": True, "$eq": True}},
                            {"isActive": {"$exists": False}}
                        ]}, projection={'name': True})
        keyboard = [
                [telegram.InlineKeyboardButton(s['name'], callback_data=s['name'])] for s in server_names
            ] + [
                [telegram.InlineKeyboardButton('❌ Cancel', callback_data='Cancel')]
            ]
        reply_markup = telegram.InlineKeyboardMarkup(keyboard)
        # Send message with text and appended InlineKeyboard
        await update.effective_message.edit_text(reply_text, reply_markup=reply_markup, parse_mode=telegram.constants.ParseMode.MARKDOWN)

        db_client.close()

        return ADMIN_CHARGE_ALL_ACCOUNTS

async def admin_charge_all_accounts_with_server(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == 'Cancel':
        return telext.ConversationHandler.END

    server_name = query.data

    if(server_name == None and server_name == ""):
        await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"You must at first select server!"
            )
        return telext.ConversationHandler.END

    context.user_data['server_name'] = server_name
    selected_org = context.user_data['org']

    reply_text = "Please send the amount you want to charge in " + org_admin_texts("GB") + ":\nExample: 5\n\nClick cancel to abort."
    context.user_data['org'] = selected_org

    keyboard = [
            [telegram.InlineKeyboardButton('❌ Cancel', callback_data='Cancel')]
        ]
    reply_markup = telegram.InlineKeyboardMarkup(keyboard)
    # Send message with text and appended InlineKeyboard
    await update.effective_message.edit_text(reply_text, reply_markup=reply_markup, parse_mode=telegram.constants.ParseMode.MARKDOWN)

    return ADMIN_CHARGE_ALL_ACCOUNTS_AMOUNT

async def admin_charge_all_accounts_inputed(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    try: 
        db_client = connect_to_database(secrets['DBConString'])
    except Exception as e:
        print("Failed to connect to the database!")

    if not await check_subscription(update):
        main_channel = db_client[secrets['DBName']].orgs.find_one({'name': 'main'})['channel']['link']
        reply_text = org_admin_texts('join_channel') + f'\n\n{main_channel}'
        await update.effective_message.reply_text(reply_text)
        
        db_client.close()

        return telext.ConversationHandler.END

    server_name = context.user_data['server_name']

    selected_org = context.user_data['org']
    if selected_org not in db_client[secrets['DBName']].admins.find_one({'user_id': update.effective_user.id})['orgs']:
        reply_text = "Unathorized! Also, How are you here?"
        await update.effective_message.reply_text(reply_text)

        db_client.close()

        return telext.ConversationHandler.END
    else:
        user_ids = db_client[secrets['DBName']].users.find(
                projection={'user_id': True}, 
                filter={'server_names': {'$in': [server_name]}, 
                        # 'orgs': {'$in': selected_org}
                        f"orgs.{selected_org}": { '$exists': True }
                    }
            )
        server_dict = db_client[secrets['DBName']].servers.find_one({'name': server_name})

        count = 0
        for user_obj in user_ids:
            count += 1
            print(user_obj['user_id'])
            charge_amount = int(update.effective_message.text)

            total = xAPI.xui_charge_account(server_dict, user_obj['user_id'], charge_amount)
            await context.bot.send_message(
                    chat_id=user_obj['user_id'],
                    text=org_admin_texts("account_charged_for") + f' {charge_amount} ' + org_admin_texts("GB") + '!\n\n' + org_admin_texts("new_limit") + f': {total} ' + org_admin_texts("GB")
                )
        if(count == 0):
            await context.bot.send_message(
                chat_id=update.effective_user.id,
                text=f"No user found in this organization"
            )
        else:
            await context.bot.send_message(
                    chat_id=update.effective_user.id,
                    text=f"All account have been charged for {int(update.effective_message.text)} " + org_admin_texts("GB") + f"!\nNumber of accounts were updadted: {count}"
                )
        db_client.close()
        return telext.ConversationHandler.END




async def accept_receipt(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    # print(update.callback_query.from_user.full_name)
    keyboard = [
        [telegram.InlineKeyboardButton('Manualy', callback_data='Manualy'),telegram.InlineKeyboardButton('Automatic', callback_data='Automatic')]
    ]
    reply_markup = telegram.InlineKeyboardMarkup(keyboard)
    # print(update.effective_message)
    # print(update.effective_message.caption)
    # print(update.effective_message.text)

    if update.effective_message.text:
        await update.effective_message.edit_text(
            update.effective_message.text,
            reply_markup=reply_markup
            )
    elif update.effective_message.caption:
        await update.effective_message.edit_caption(
            update.effective_message.caption,
            reply_markup=reply_markup
            )
    # await update.effective_message.edit_text(
    #     update.effective_message.text+
    #     "\n-------------------------"+
    #     "\nAdmin accepted : "+
    #     f"{update.callback_query.from_user.full_name}"
    #     )
    return ACCEPT

async def reject_receipt(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    keyboard = [
    [telegram.InlineKeyboardButton('❌ Reject', callback_data='Reject_sure'),telegram.InlineKeyboardButton('🔙Back', callback_data='Back')]
    ]
    reply_markup = telegram.InlineKeyboardMarkup(keyboard)
    if update.effective_message.text:
        await update.effective_message.edit_text(
        update.effective_message.text+
        "\n*-------------------------*"+
        "\nAre you sure that you want to reject this?"
        ,
        reply_markup=reply_markup
        )
    elif update.effective_message.caption:
        await update.effective_message.edit_caption(
        update.effective_message.caption+
        "\n*-------------------------*"+
        "\nAre you sure that you want to reject this?"
        ,
        reply_markup=reply_markup
        )

    return REJECT_CHECK

async def receipt_back(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    pass


async def receipt_rejected(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    # TODO_Rsool
    credentials = get_user_credentials(update.effective_message)
    text = org_admin_texts('reject_payment')+'\n'+org_admin_texts('contact_support')
    await context.bot.send_message(
        chat_id=credentials['user_id'],
        text=text,
        disable_web_page_preview=True
    )

    await update.effective_message.edit_text(
        update.effective_message.text+
        "\n-------------------------"+
        "\nAdmin rejected : "+
        f"{update.callback_query.from_user.full_name}"
        )
    return telext.ApplicationHandlerStop(telext.ConversationHandler.END)


async def accept_manualy_receipt(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    # TODO
    await update.effective_message.edit_text(
        update.effective_message.text+
        "\n-------------------------"+
        "\nAdmin Accept manualy : "+
        f"{update.callback_query.from_user.full_name}"
        )


def get_user_credentials(effective_message):
    lines = []
    payment_receipt = None
    credentials = {}
    if effective_message.text:
        payment_receipt = effective_message.text.split('-------------------------')[1]
        lines = effective_message.text.splitlines()  # Split the string into lines

    elif effective_message.caption:
        print(f"update.effective_message:{type(effective_message)}")

        if effective_message.document:
            payment_receipt = effective_message.document.file_id
        elif effective_message.photo:
            payment_receipt = effective_message.photo[0].file_id
        print(f"payment_receipt:{payment_receipt}")
        lines = effective_message.caption.splitlines()  # Split the string into lines
    credentials['payment_receipt'] = payment_receipt
    if lines[0] == 'Payment':
        is_new_user = True
    else:
        is_new_user = False
    credentials['is_new_user'] = is_new_user
    for line in lines:
        if 'user_id' in line:
            credentials['user_id'] = int(line.split(':')[1])
        elif 'org' in line:
            credentials['org_name'] = line.split(':')[1]
        elif 'currency' in line:
            credentials['currency'] = line.split(':')[1]
        elif 'Plan' in line:
            credentials['plan'] = line.split(':')[1]
        elif 'pay_amount' in line:
            credentials['pay_amount'] = line.split(':')[1]
        elif 'discount' in line: 
            credentials['discount'] = line.split(':')[1]
    return credentials



async def accept_automatic_receipt(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    try: 
        db_client = connect_to_database(secrets['DBConString'])
    except Exception as e:
        print("Failed to connect to the database!")
    credentials = get_user_credentials(update.effective_message)

    # line_of_user_id=update.effective_message.text.split('\n')[2].split('-')
    # if len(line_of_user_id)==3:
    #     user_id=int(line_of_user_id[1])
    # elif len(line_of_user_id)==2:
    #     user_id=int(line_of_user_id[0])
    # print(f"user_data:{user_id}")
    # print(context.user_data)
    # print(context.chat_data)
    user_dict = db_client[secrets['DBName']].users.find_one({'user_id': credentials["user_id"]})
    # print(float(user_dict['wallet']) + float(credentials['pay_amount'].split(',')[0]))
    # Moved wallet update to the end to prevent crediting wallet if payment processing fails

    org_obj = db_client[secrets['DBName']].orgs.find_one({'name': credentials["org_name"]})

    # org_ticketing_channel_id = org_obj['ticketing_group_id']
    # tr_obj = db_client[secrets['DBName']].payments.find_one({'transactionID': context.user_data['transaction_id']})
    # support_account = org_obj['support_account']
    server_dicts = list(db_client[secrets['DBName']].servers.find({"org": credentials["org_name"]}))

    if credentials['currency'] != "rial":
        payment_type = "crypto"
    else:
        payment_type = "rial"

    tr_verification_data = {
        "user_id": credentials['user_id'],
        "org": credentials["org_name"],
        "plan": credentials['plan'],
        "payment_type": payment_type,
        "payment_method": 'e-transfer',
        "amount": int(credentials['pay_amount'].split(',')[0]),
        "discount": user_dict['discount'] if 'discount' in user_dict else 0,
        # "transactionID": ,
        # "payment_url": context.user_data['payment_url'],
        "payment_receipt": credentials['payment_receipt'],
        "date": datetime.datetime.now().isoformat(),
        "verified": False,
        "failed": False
    }

    tr_db_id = (db_client[secrets['DBName']].payments.insert_one(tr_verification_data)).inserted_id

    db_client[secrets['DBName']].users.update_one({'user_id':  credentials['user_id']}, {"$set": {f"orgs.{credentials['org_name']}": {"expires": (datetime.datetime.now()+datetime.timedelta(days=62)).isoformat()}}})

    charge_amount = int(org_obj['payment_options']['plans'][credentials['plan']])
    for server_dict in server_dicts:
        user_client = xAPI.get_clients(server_dict, select=[f"{user_dict['user_id']}-{server_dict['name']}@{server_dict['rowRemark']}"])
        if user_client is None:
            result = xAPI.add_client(server_dict, f"{user_dict['user_id']}-{server_dict['name']}", 0, str(uuid.uuid4()),
                            # expires:datetime.datetime=None
                            )
    for server_dict in server_dicts:
        user_client = xAPI.get_clients(server_dict, select=[f"{user_dict['user_id']}-{server_dict['name']}@{server_dict['rowRemark']}"])
        if user_client is None:
            result = xAPI.add_client(server_dict, f"{user_dict['user_id']}-{server_dict['name']}", 0, str(uuid.uuid4()),
                                     # expires:datetime.datetime=None
                                     )
        elif credentials['is_new_user']:
            add_result = xAPI.add_client(server_dict, f"{user_dict['user_id']}-{server_dict['name']}", 0, str(uuid.uuid4()),
                            # expires:datetime.datetime=None
                            )

    db_client[secrets['DBName']].payments.update_one({'_id': tr_db_id}, { "$set": {"verified": True}})

    xAPI.unrestrict_user(server_dicts, f"{user_dict['user_id']}")

    # Update wallet only after all operations are successful
    db_client[secrets['DBName']].users.update_one({'user_id': credentials["user_id"]}, {"$set": {"wallet": float(user_dict['wallet']) + float(credentials['pay_amount'].split(',')[0])}})

    org_channel = db_client[secrets['DBName']].orgs.find_one({'name': credentials["org_name"]})['channel']['link']
    text = org_admin_texts("verified_payment") + '\n' + org_admin_texts("account_charged_for") + f' {float(credentials["pay_amount"].split(",")[0]) * 1000} ' + 'تومان' + '!\n'
    text += org_admin_texts("after_added_to_org") + f': \n\n{org_channel}\n\n' + org_admin_texts("thanks_joining") + f' *{secrets["DBName"]}* ' + org_admin_texts("group") + ' 🤍️'

    await context.bot.send_message(
        chat_id=credentials['user_id'],
        text=text,
        disable_web_page_preview=True
    )
    if update.effective_message.text:
        await update.effective_message.edit_text(
            update.effective_message.text+
            "\n-------------------------"+
            "\nAdmin Accept automatically : "+
            f"{update.callback_query.from_user.full_name}"
            )
    elif update.effective_message.caption:
        await update.effective_message.edit_caption(
            update.effective_message.caption+
            "\n-------------------------"+
            "\nAdmin Accept automatically : "+
            f"{update.callback_query.from_user.full_name}"
            )

    db_client.close()

    return telext.ApplicationHandlerStop(telext.ConversationHandler.END)