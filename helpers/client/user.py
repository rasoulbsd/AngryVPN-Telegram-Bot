"""
User info functions for client flows.
"""

import telegram
import telegram.ext as telext
import helpers.xuiAPI as xAPI
from helpers.initial import get_secrets_config, connect_to_database, set_lang
from helpers.bot_functions import check_subscription

(secrets, Config) = get_secrets_config()
# Removed global client_functions_texts


async def get_userinfo(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    try:
        db_client = connect_to_database(secrets['DBConString'])
    except Exception:
        print("Failed to connect to the database!")
        return

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
            {'name': 'main'}
        )['channel']['link']
        reply_text = client_functions_texts("join_channel") + \
            f'\n\n{main_channel}'
        await update.effective_message.edit_text(reply_text)
        db_client.close()
        return telext.ConversationHandler.END
    else:
        if user_dict is None:
            reply_text = client_functions_texts("user_not_found")
            await update.effective_message.edit_text(reply_text)
            db_client.close()
            return telext.ConversationHandler.END
        else:
            if len(user_dict['server_names']) == 0:
                reply_text = client_functions_texts("your_user_id") + \
                    f' `{update.effective_user.id}`'
                reply_text += "\n" + client_functions_texts("get_an_account")
                await update.effective_message.edit_text(
                    reply_text,
                    parse_mode=telegram.constants.ParseMode.MARKDOWN
                )
                db_client.close()
                return telext.ConversationHandler.END

            reply_text = client_functions_texts("your_user_id") + \
                f' `{update.effective_user.id}`'
            servers_rowRemarks = {}
            for server_name in user_dict['server_names']:
                if len(list(user_dict["orgs"].keys())) == 0:
                    reply_text = client_functions_texts("your_user_id") + \
                        f' `{update.effective_user.id}`'
                    reply_text += "\n" + client_functions_texts("join_org")
                    await update.effective_message.edit_text(
                        reply_text,
                        parse_mode=telegram.constants.ParseMode.MARKDOWN
                    )
                    db_client.close()
                    return telext.ConversationHandler.END
                server_dict = db_client[secrets['DBName']].servers.find_one(
                    {
                        'name': server_name,
                        'org': list(user_dict["orgs"].keys())[0],
                        "$or": [
                            {'isActive': {"$exists": True, "$eq": True}},
                            {"isActive": {"$exists": False}}
                        ]
                    }
                )
                print(server_dict)
                if server_dict is None:
                    continue

                (res, user_client) = xAPI.get_client(
                    server_dict,
                    f"{user_dict['user_id']}-{server_dict['name']}@{server_dict['rowRemark']}"
                )
                if res == -1:
                    reply_text = client_functions_texts("your_user_id") + \
                        f' `{update.effective_user.id}`'
                    reply_text += (
                        "\n\n" + client_functions_texts("error_code") + " 11" +
                        "\n\n" + client_functions_texts("contact_support")
                    )
                    await update.effective_message.edit_text(
                        reply_text,
                        parse_mode=telegram.constants.ParseMode.MARKDOWN
                    )
                    db_client.close()
                    return telext.ConversationHandler.END

                if server_dict['rowRemark'] not in servers_rowRemarks:
                    servers_rowRemarks[server_dict['rowRemark']] = {}
                    servers_rowRemarks[server_dict['rowRemark']]['servers'] = []

                servers_rowRemarks[server_dict['rowRemark']]['servers'].append(
                    {'name': server_dict['name'], 'price': server_dict['price']}
                )

            max_dash = 0
            reply_text += "\n\n"
            for row in servers_rowRemarks:
                for server in servers_rowRemarks[row]['servers']:
                    temp = (
                        f'*{server["name"]}*: ' +
                        f'{server["price"]} ' +
                        client_functions_texts('price_per_gb_rial') + ' \n'
                    )
                    reply_text += temp
                    if len(temp) > max_dash:
                        max_dash = len(temp)
            reply_text += (
                f'{"-"*max_dash}\n' +
                client_functions_texts('wallet_balance') +
                ":\t" + f'{int(user_dict["wallet"])} ' +
                client_functions_texts('price_rial')
            )

            await update.effective_message.edit_text(
                reply_text,
                parse_mode=telegram.constants.ParseMode.MARKDOWN
            )
            db_client.close()
            return telext.ConversationHandler.END
