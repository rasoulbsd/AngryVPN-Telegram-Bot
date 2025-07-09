import helpers.xuiAPI as xAPI
from helpers.initial import get_secrets_config, connect_to_database
from bson import Int64
from scripts.check85 import send_warning_message
import asyncio
def update_db():
    (secrets, Config) = get_secrets_config()
    try:
        db_client = connect_to_database(secrets['DBConString'])
    except Exception as e:
        print("Failed to connect to the database!")
        return

    # server_dict = list(db_client[secrets['DBName']].servers.find())
    # for server in server_dict:
    #     db_client[secrets['DBName']].servers.update_one(
    #         {'_id': server['_id']},
    #         {'$set': {'role': 'normal', 'price': 2.}}
    #     )
    user_dict = list(db_client[secrets['DBName']].users.find())
    for user in user_dict:
        # # if user['user_id'] != 75788887:
        # #     continue
        # total = 0.
        # usage = 0.
        # row_remarks = []
        # for server in server_dict:
        #     if server['rowRemark'] in row_remarks:
        #         continue
        #     row_remarks.append(server['rowRemark'])
        #     print(f"{server['name']} {user['user_id']}@{server['rowRemark']}")

        #     (res, user_client) = xAPI.get_client(server, f"{user['user_id']}@{server['rowRemark']}")
        #     if res == -1 or type(user_client) == type(None):
        #         continue
        #     print(f"usage{(float(user_client['down']) + float(user_client['up'])) / 1024**3}/ {float(user_client['total']) / 1024**3}")
        #     total += float(user_client['total']) / 1024**3
        #     usage += (float(user_client['down']) + float(user_client['up'])) / 1024**3
        # print(f"{user['user_id']}: {usage}/{total}")
        db_client[secrets['DBName']].users.update_one(
            {'_id': user['_id']},
            {'$set': {'wallet': user['wallet'] * 3/2}}
        )
        print(f'{user["_id"]} - {user["wallet"]}')

update_db()