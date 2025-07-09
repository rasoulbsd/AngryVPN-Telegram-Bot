import helpers.xuiAPI as xAPI
from helpers.initial import get_secrets_config, connect_to_database
from bson import Int64
from check85 import send_warning_message
import asyncio
async def update_wallets():
    (secrets, Config) = get_secrets_config()
    try:
        db_client = connect_to_database(secrets['DBConString'])
    except Exception as e:
        print("Failed to connect to the database!")
        return
    server_dict = list(db_client[secrets['DBName']].servers.find({
        "$or": [
            {'isActive': {"$exists": True, "$eq": True}},
            {"isActive": {"$exists": False}}
        ],
    }))
    mean_server_price = 0
    number_server = 0
    for i in server_dict:
        mean_server_price += i['price']
        number_server += 1
    mean_server_price /= number_server

    row_remarks = []
    for server_tmp in server_dict:
        if server_tmp['rowRemark'] in row_remarks:
            continue
        row_remarks.append(server_tmp['rowRemark'])
        clients = xAPI.get_clients(server_tmp)
        for index, row in clients.iterrows():
            try:
                id_server, server_remark = index.split("@")
                id = id_server.split("-")[0]
                # server_name = "-".join(id_server.split("-")[1:])
                server_name = id_server[len(id)+1:]
                server = db_client[secrets['DBName']].servers.find_one({'name': server_name})
                user_dict = db_client[secrets['DBName']].users.find_one({'user_id': int(id)})

                prev_usage = 0
                if 'server_usage' in user_dict:
                    if server['name'] in user_dict['server_usage']:
                        prev_usage = user_dict['server_usage'][server['name']]
                    user_dict['server_usage'][server['name']] = Int64(row['up'] + row['down'])
                else:
                    user_dict['server_usage'] = {}
                    user_dict['server_usage'][server['name']] = Int64(row['up'] + row['down'])

                usage = (row['up'] + row['down'] - prev_usage) / (1024*1024*1024)
                discount = 0
                if  'server_discount' in user_dict:
                    if server['name'] in user_dict['server_discount']:
                        discount = user_dict['server_discount'][server['name']]
                cost = usage * server['price'] * (1 - discount)
                if  'wallet' in user_dict:
                    user_dict['wallet'] = user_dict['wallet'] - cost
                else:
                    user_dict['wallet'] = - cost

                if user_dict['wallet'] < 0:
                    await send_warning_message(user_dict, -1)
                    xAPI.restrict_user(server_dict, f"{id}")
                elif user_dict['wallet'] < 5 * mean_server_price:
                    # print(user_dict['wallet']< 5 * mean_server_price)
                    await send_warning_message(user_dict, 0)
                else:
                    await send_warning_message(user_dict, 1)
                db_client[secrets['DBName']].users.update_one({'user_id': int(id)}, {"$set": {"wallet": user_dict['wallet'], "server_usage": user_dict['server_usage']}})
                print(f"{index} updated successfully!!")
            except Exception as e:
                # print(e)
                pass




asyncio.run(update_wallets())