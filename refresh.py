import helpers.xuiAPI as xAPI
from helpers.initial import get_secrets_config, connect_to_database
from bson import Int64
from scripts.check85 import send_warning_message
import asyncio
import datetime


async def update_wallets():
    (secrets, Config) = get_secrets_config()
    try:
        db_client = connect_to_database(secrets['DBConString'])
    except Exception:
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
    xui_server = {}
    user_dicts = list(db_client[secrets['DBName']].users.find())
    number_of_updates = 0
    number_of_message = 0
    for user_dict in user_dicts:
        updated_user_dict = db_client[secrets['DBName']].users.find_one({'user_id': user_dict["user_id"]})
        for server_name in user_dict["server_names"]:
            server_tmp = db_client[secrets['DBName']].servers.find_one({'name': server_name})
            if server_tmp:
                if server_tmp['rowRemark'] not in xui_server:
                    xui_server[server_tmp['rowRemark']] = xAPI.get_clients(server_tmp)
                xui_data = xui_server[server_tmp['rowRemark']][xui_server[server_tmp['rowRemark']].index == f'{user_dict["user_id"]}-{server_name}@{server_tmp["rowRemark"]}']
                for index, row in xui_data.iterrows():
                    # print(index)
                    try:
                            # id_server, server_remark = index.split("@")
                            # id = id_server.split("-")[0]
                        id = user_dict["user_id"]
                        # server_name = "-".join(id_server.split("-")[1:])
                        # server_name = id_server[len(id)+1:]
                        server = server_tmp

                        prev_usage = 0
                        if 'server_usage' in updated_user_dict:
                            if server['name'] in updated_user_dict['server_usage']:
                                prev_usage = updated_user_dict['server_usage'][server['name']]
                            updated_user_dict['server_usage'][server['name']] = Int64(row['up'] + row['down'])
                        else:
                            updated_user_dict['server_usage'] = {}
                            updated_user_dict['server_usage'][server['name']] = Int64(row['up'] + row['down'])

                        usage = (row['up'] + row['down'] - prev_usage) / (1024*1024*1024)
                        discount = 0
                        if  'server_discount' in updated_user_dict:
                            if server['name'] in updated_user_dict['server_discount']:
                                discount = updated_user_dict['server_discount'][server['name']]
                        cost = usage * server['price'] * (100 - discount) / 100
                        if  'wallet' in updated_user_dict:
                            updated_user_dict['wallet'] = updated_user_dict['wallet'] - cost
                        else:
                            updated_user_dict['wallet'] = - cost

                        db_client[secrets['DBName']].users.update_one({'user_id': int(id)}, {"$set": {"wallet": updated_user_dict['wallet'], "server_usage": updated_user_dict['server_usage']}})


                        if updated_user_dict['wallet'] < 0:
                            temp = await send_warning_message(db_client[secrets['DBName']], updated_user_dict, -1)
                            if temp:
                                number_of_message += 1
                            try:
                                if temp:
                                    user_servers = []
                                    for server_name2 in updated_user_dict["server_names"]:
                                        user_servers.append(db_client[secrets['DBName']].servers.find_one({'name': server_name2}))
                                    # print(user_dict)
                                    # print(user_servers)
                                    xAPI.restrict_user(user_servers, f"{id}")
                            except Exception as e2:
                                print(e2)
                                # exit()

                        elif updated_user_dict['wallet'] < 5 * mean_server_price:
                            # print(user_dict['wallet']< 5 * mean_server_price)
                            temp = await send_warning_message(db_client[secrets['DBName']], updated_user_dict, 0)
                            if temp:
                                number_of_message += 1
                        else:
                            await send_warning_message(db_client[secrets['DBName']], updated_user_dict, 1)

                    # print(f"{index} updated successfully!!")
                    except Exception as e:
                        # print("Here")
                        print(e)
                        # exit()
                    #     pass
            else:
                continue
        number_of_updates += 1
    print(f"{number_of_updates} users updated successfully and {number_of_message} have been sent! {str(datetime.datetime.now())}")

asyncio.run(update_wallets())
