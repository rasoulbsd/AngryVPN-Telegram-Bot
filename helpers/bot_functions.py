import telegram
import telegram.ext as telext
import helpers.xuiAPI as xAPI
import datetime
from .initial import get_secrets_config, connect_to_database, set_lang
import requests, json
import datetime
import time


MAX_RETRIES = 5
DELAY_IN_SECONDS = 60
############################# GLOBALS #############################

# Stages
DELIVER_SERVER = range(1)
DELIVER_USER_VMESS_STATUS = range(1)
DELIVER_REFRESH_VMESS = range(1)

(secrets, Config) = get_secrets_config()
bot_functions_texts = set_lang(Config['default_language'], 'bot_functions')

############################# Functions #############################
def reset(update, context):
    context.user_data.clear()
    context.chat_data.clear()
    return telext.ConversationHandler.END

async def check_subscription(update: telegram.Update):
    try:
        res = await update.get_bot().get_chat_member(secrets['ChannelID'], update.effective_user.id)
        # print(f"secrets['ChannelID']:\n{secrets['ChannelID']}")
        # print(f"result of check_subscription:\n{res}")
        if res.status in ['creator', 'administrator', 'member']: return True
    except NameError:
        print(f"error in check_subscription :\n{NameError}")

    return False

def normalize_transaction_id(tr_id):
    # EXP: https://tronscan.org/#/transaction/bf8249412c56ab861a154a55ee8757b75dfc8b77e04c156bd5058262a87c2f9e
    tr_id = tr_id.split("transaction/")
    if "tronscan.org" in tr_id:
        if len(tr_id) != 2:
            return False
        else:
            return tr_id[1]
    else:
        return tr_id[0]

def validate_transaction(payment_url, tr_id, org_name, plan):
    try: 
        db_client = connect_to_database(secrets['DBConString'])
    except Exception as e:
        print("Failed to connect to the database!")

    org_obj = db_client[secrets['DBName']].orgs.find_one({'name': org_name})
    # valid_payment_url = org_obj['payment_options'][plan]
    support_account = org_obj['support_account']

    # Check for duplicated payments
    if db_client[secrets['DBName']].payments.find_one({'transactionID': tr_id}) is not None:
        reply_text = bot_functions_texts("used_transaction_id")+ '\n'
        reply_text += bot_functions_texts("contact_support") + f': {support_account}'
        db_client.close()
        return (False, reply_text)

    db_client.close()

    # Check payment url based on user's org and selected plan
    # if valid_payment_url != payment_url:
    #     reply_text = f"Payment url is not valid or it is not same as the plan you have selected!\nPlease contact support: {support_account}"
    #     return (False, reply_text)
    # else:
    #     return (True, )
    return (True, None)

async def verfiy_transaction(transaction_id, amount, dest_wallet , user_id, plan, payment_url):
    url = f'https://apilist.tronscan.org/api/transaction-info?hash={transaction_id}'

    response = requests.get(url)
    if response.status_code != 200:
        return (False, None)

    data = response.json()

    if 'confirmed' not in data and ('riskTransaction' in data and data['riskTransaction'] == False):
        return (False, "Failed")
    elif float(amount) != float(data['contractData']['amount'])/10**6 or dest_wallet != data['toAddress']:
        return (False, "incorrect_data")
    elif data['confirmed'] and data['contractRet'] == 'SUCCESS':
        return (True, None)
    else:
        return (False, None)


async def check_newuser(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    try: 
        db_client = connect_to_database(secrets['DBConString'])
    except Exception as e:
        print("Failed to connect to the database!")
    org_names = [i['name'] for i in db_client[secrets['DBName']].orgs.find(filter={'active': True}, projection={'name': True})]
    user_dict = db_client[secrets['DBName']].users.find_one({'user_id': update.effective_chat.id})

    # if len(user_dict['server_names']) == 0 and not bool(user_dict['orgs']):
    if not bool(user_dict['orgs']):
        db_client.close()
        return True
    else:
        for org in user_dict['orgs']:
            if org in org_names:
                db_client.close()
                return False
        db_client.close()

        return True

def update_all_users():
    try: 
        db_client = connect_to_database(secrets['DBConString'])
    except Exception as e:
        print("Failed to connect to the database!")
    
    db_client[secrets['DBName']].users.update_many({},
            {
                "$push": {"orgs": ["rahbazkon-vip"]}
            }
                # {'name': selected_server},
                # {'$set': {'AcceptingNew': False if server_dict['AcceptingNew'] else True}}
        )

async def usage_warning(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
            chat_id="5868735617",
            text="Hi \n"
            )

async def usage_exceed(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    try: 
        db_client = connect_to_database(secrets['DBConString'])
    except Exception as e:
        print("Failed to connect to the database!")

    exceed_users = []

    for user_id in exceed_users:
        user_dict = db_client[secrets['DBName']].users.find_one({'user_id': int(user_id)})
        if user_dict is None:
            reply_text = f"User ${user_id} is not a member of the bot.\nUser should start the bot first."
            await update.effective_message.reply_text(reply_text)
        user_servers = user_dict["server_names"]
        server_dicts = db_client[secrets['DBName']].servers.find({
            'name': {'$in': user_servers}
        })
        xAPI.restrict_user(server_dicts, user_id)
        await context.bot.send_message(
                chat_id=user_id,
                text=bot_functions_texts("exceed_usage") + '\n' + bot_functions_texts("after_exceed_usage") + ' \n'
                )
    db_client.close()
    return telext.ConversationHandler.END

def show_users():
    try: 
        db_client = connect_to_database(secrets['DBConString'])
    except Exception as e:
        print("Failed to connect to the database!")

    user_objs = db_client[secrets['DBName']].users.find()

    for user_obj in user_objs:
        user_obj['credit'] = 0
        user_obj['total'] = 0
        # user_objs = db_client[secrets['DBName']].users.find()
        db_client[secrets['DBName']].users.update_one({'_id': user_obj['_id']}, {'$push': {'credit': 0}})

async def after_automatic_payment(update, context):
    try: 
        db_client = connect_to_database(secrets['DBConString'])
    except Exception as e:
        print("Failed to connect to the database!")

    if context.user_data['is_new_user']:
        org_name = context.user_data['org']
        org_obj = db_client[secrets['DBName']].orgs.find_one({'name': org_name})
    else:
        org_obj = context.user_data['org_obj']
        org_name = org_obj['name']
    context.user_data['user_id'] = update.effective_chat.id

    org_ticketing_channel_id = org_obj['ticketing_group_id']

    user_dict = db_client[secrets['DBName']].users.find_one({'user_id': context.user_data['user_id']})

    server_dict = db_client[secrets['DBName']].servers.find_one({"org": org_name})

    tr_verification_data = {
        "user_id": context.user_data['user_id'],
        "org": org_name,
        "plan": context.user_data['plan'],
        "payment_type": context.user_data['payment_type'],
        "payment_method": context.user_data['payment_method'],
        "amount": context.user_data['pay_amount'] * context.user_data['discount'],
        "discount":  context.user_data['discount'],
        "payment_receipt": context.user_data['payment_receipt'],
        "date": datetime.datetime.now().isoformat(),
        "verified": False,
        "failed": False
    }
    tr_db_id = (db_client[secrets['DBName']].payments.insert_one(tr_verification_data)).inserted_id

    # Adding to organization
    db_client[secrets['DBName']].users.update_one({'user_id': context.user_data['user_id']}, {"$set": {f"orgs.{org_name}": {"expires": (datetime.datetime.now()+datetime.timedelta(days=62)).isoformat()}}})

    charge_amount = int(org_obj['payment_options']['plans'][context.user_data['plan']])

    user_client = xAPI.get_clients(server_dict, select=[f"{user_dict['user_id']}@{server_dict['rowRemark']}"])
    if user_client is None:
        result = xAPI.add_client(server_dict, user_dict['user_id'], charge_amount, user_dict['uuid'], 
                        # expires:datetime.datetime=None
                        )
    elif context.user_data['is_new_user']:
        delete_result = xAPI.delete_client(server_dict, user_dict['uuid'])
        add_result = xAPI.add_client(server_dict, user_dict['user_id'], charge_amount, user_dict['uuid'], 
                        # expires:datetime.datetime=None
                        )
        if (add_result[0] == -1):
            print("======ERROR======")
            print(add_result[1])
            print("======ERROR======")
            total = xAPI.xui_charge_account(server_dict, context.user_data['user_id'], charge_amount, new=True)
    else:
        total = xAPI.xui_charge_account(server_dict, context.user_data['user_id'], charge_amount, new=False)

    # total = xAPI.xui_charge_account(server_dict, context.user_data['user_id'], charge_amount, new=True)

    # db_client[secrets['DBName']].payments.update_one({'transactionID': context.user_data['transaction_id']}, { "$set": {"verified": True}})

    org_channel = db_client[secrets['DBName']].orgs.find_one({'name': org_name})['channel']['link']

    text = bot_functions_texts("verified_payment") 
    text += '\n'
    text += bot_functions_texts("account_charged_for")
    text += f' {charge_amount} ' + bot_functions_texts("GB") + '!\n'
    text += bot_functions_texts("after_added_to_org") 
    text += f': \n\n{org_channel}\n\n' 
    text += bot_functions_texts("thanks_joining") 
    text += f' *{secrets["DBName"]}* ' 
    text += bot_functions_texts("group")
    text += ' 🤍️'

    context.user_data['menu'] = update.effective_message
    context.user_data['chat'] = update.effective_chat
    context.user_data['full_name'] = update.effective_chat.full_name
    context.user_data['username'] = update.effective_chat.username
    context.user_data['user_id'] = update.effective_chat.id
    # Bot Message for Ticketing Admins
    await context.bot.send_message(
        chat_id=org_ticketing_channel_id,
        text=
            f"✅ Verified *{context.user_data['payment_method']}* Payment from user: \n\n" +
            (f"@{context.user_data['username']} - " if(context.user_data['username'] is not None) else "") + 
            f"{context.user_data['user_id']} - {context.user_data['full_name']}" + 
            f"\nPlan: {context.user_data['plan']} Pack" +
            f"\nOrg Name: {org_name}" +
            "\n-------------------------" +
            f"\nPayment Receipt: {context.user_data['payment_receipt']}",
        disable_web_page_preview=True,
        reply_to_message_id=secrets['test_topic_id'] if secrets["DBName"].lower() == "rhvp-test" else secrets['payments_topic_id']
    )

    # Bot Message for Ticketing Admins
    await context.bot.send_message(
        chat_id=context.user_data['user_id'],
        text=text,
        disable_web_page_preview=True
    )

    db_client.close()
    return telext.ApplicationHandlerStop(telext.ConversationHandler.END)
    # return telext.ConversationHandler.END

async def manual_charge(user_id, charge_amount):
        try: 
            db_client = connect_to_database(secrets['DBConString'])
        except Exception as e:
            print("Failed to connect to the database!")

        server_dict = db_client[secrets['DBName']].servers.find_one({'name': "Mahsa-Test"})
        user_dict = db_client[secrets['DBName']].users.find_one({'user_id': user_id})

        user_client = await xAPI.get_clients(server_dict, select=[f"{user_dict['user_id']}@{server_dict['rowRemark']}"])

        if user_client is None:
            result = await xAPI.add_client(server_dict, user_dict['user_id'], charge_amount, user_dict['uuid'], 
                            # expires:datetime.datetime=None
                    )
            return 0

        user_client = await xAPI.get_clients(server_dict, select=[f"{user_dict['user_id']}@{server_dict['rowRemark']}"])

        print("user_client")
        print(user_client)
        print("-----------------")

        await xAPI.change_usage(user_id, server_dict, user_client['up'], user_client['down'])


        # exit()
        prev_amount = await xAPI.xui_charge_account(server_dict, user_id, 0)
        print(f"prev_amount: {prev_amount} - type: {type(prev_amount)}")
        print("-----------------")
        del_res = await xAPI.delete_client(server_dict, user_id) # This may be redundant??
        # prev_amount = user_client['totalGB']/1024**3
        print("del_res")
        print(del_res)
        print("-----------------")

        result = await xAPI.add_client(server_dict, user_id, charge_amount, user_dict['uuid'], 
                            # expires:datetime.datetime=None
                    )
        print(f"charge_amount: {charge_amount} - type: {type(charge_amount)}")
        print("-----------------")

