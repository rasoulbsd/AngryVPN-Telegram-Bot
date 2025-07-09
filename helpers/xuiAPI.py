import requests
import json
import pandas as pd
import numpy as np
import urllib
import string
import base64
import datetime
import pymongo
# from urllib.parse import urlencode, quote

from helpers.initial import get_secrets_config

(secrets, Config) = get_secrets_config()

def _login(panel_url, panel_username, panel_password, httpAuth=None):
    with requests.session() as c:
        login_response = c.post(
            f'{panel_url}/login',
            data={
                'username': panel_username,
                'password': panel_password
            },
            headers={
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'Authorization': httpAuth
            }
        )

    # Check the new cookie name 'x-ui'
    try:
        return login_response.cookies['x-ui']
    except KeyError:
        print('Could not get session cookie')
        return ""


def get_cookie(server_dict: dict):
    # Test the current session or token
    with requests.session() as c:
        headers = {
            'Cookie': f"x-ui={server_dict.get('cookie', '')}",
            'Authorization': server_dict.get('httpAuth', None)
        }

        response = c.get(
            f"{server_dict['url']}/xui/",
            headers=headers
        )

    if response.status_code == 200 and len(response.history) == 0:
        print("Session or token is valid")
        return server_dict['cookie']
    else:
        print("Session or token is invalid, logging in again")
        new_cookie = _login(
            server_dict['url'],
            server_dict['username'],
            server_dict['password'],
            server_dict.get('httpAuth', None)
        )
        if new_cookie == "":
            raise ConnectionError


        # with open(Config.secret_file, 'r') as fp:
        #     secrets = json.load(fp)

        db_client = pymongo.MongoClient(secrets['DBConString'])
        db_client[secrets['DBName']].servers.update_one(
            {'name': server_dict['name']},
            {'$set': {'cookie': new_cookie}}
        )
        db_client.close()
        return new_cookie


def get_remark(server_dict: dict) -> dict:
    with requests.session() as c:
        # Use the correct cookie name 'x-ui' instead of 'session'
        response = c.post(
            f"{server_dict['url']}/xui/inbound/list",
            headers={
                'Cookie': f"x-ui={get_cookie(server_dict)}",  # Updated cookie name
                'Authorization': server_dict.get('httpAuth', None)
            }
        )

    # Debugging prints
    # print("Response Status Code:", response.status_code)
    # print("Response Text:", response.text)

    # Parse the JSON response
    try:
        df = pd.DataFrame(json.loads(response.text)['obj'])
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Failed to decode JSON or find 'obj' key: {e}")
        return {}

    # print("Remarks in DataFrame:", df['remark'].tolist())
    # print("Target Remark:", server_dict['rowRemark'])

    # Find the row with the matching 'remark'
    try:
        df = df.loc[df['remark'] == server_dict['rowRemark']].iloc[0]
        return df.to_dict()
    except IndexError:
        print("No matching remark found.")
        return {}

def get_client(server_dict, email):
    headers = {
        'Accept': "application/json, text/plain, */*",
        'Accept-Language': "en-US,en;q=0.9",
        'Content-Type': "application/x-www-form-urlencoded; charset=UTF-8",
        'Cookie': f'x-ui={get_cookie(server_dict)}',
        'Authorization': server_dict.get('httpAuth', None),
        'X-Requested-With': "XMLHttpRequest"
    }

    res = requests.get(
        f"{server_dict['url']}/xui/API/inbounds/getClientTraffics/{email}",
        headers=headers
    )

    result = json.loads(res.text)
    if not result['success']:
        return (-1, result['msg'])
    if 'obj' not in result:
        return (-1, 'Unhandled Error')
    return (1, result['obj']) #user_uuid, port

def get_clients(server_dict, select=None):
    row = get_remark(server_dict)
    clients_dict = row['clientStats']

    client_settings = json.loads(row['settings'])['clients']
    client_settings = pd.DataFrame(client_settings).set_index('email', drop=True).rename(columns={'id': 'uuid'})

    clients = pd.DataFrame(clients_dict).set_index('email', drop=True)
    clients = clients.join(client_settings[['uuid']])
    if select is not None:
        clients = clients.loc[np.isin(clients.index, select)]
    if len(clients) == 0:
        return None
    return clients


def add_client_request(server_dict, payload):
    # print(f"payload:{payload}")
    headers = {
        'Accept': "application/json, text/plain, */*",
        'Accept-Language': "en-US,en;q=0.9",
        'Content-Type': "application/x-www-form-urlencoded; charset=UTF-8",
        'Cookie': f'x-ui={get_cookie(server_dict)}',
        'Authorization': server_dict.get('httpAuth', None),
        'X-Requested-With': "XMLHttpRequest"
    }
    # print(f"get_cookie(server_dict):{get_cookie(server_dict)}")
    # print(f"server_dict.get('httpAuth', None):{server_dict.get('httpAuth', None)}")
    # print(f"server_dict['url']:{server_dict['url']}")
    res = requests.post(
        f"{server_dict['url']}/xui/inbound/addClient",
        headers=headers,
        data=urllib.parse.urlencode(payload)
    )

    result = json.loads(res.text)
    if not result['success']:
        return -1, result['msg']
    return (1,) #user_uuid, port


def add_client(server_dict, username, traffic, uuid, expires:datetime.datetime=None):
    print(f"uuid:{uuid}")
    row = get_remark(server_dict)

    client = {
        'id': uuid,
        'alterId': 0,
        'email': f"{username}@{server_dict['rowRemark']}",
        'totalGB': int(traffic * 1024**3),
        # 'expiryTime': expires.timestamp() * 1000,
        'enable': True,
        'tgId': '',
        'subId': ''
    }

    # row_settings = json.loads(row['settings'])
    # row_settings['clients'] = clients_list
    # row['settings'] = json.dumps(row_settings)

    row_id = row.pop('id', None)

    # row.pop('clientStats', None)
    # row.pop('tag', None)

    payload = {
        "id": row_id,
        "settings": json.dumps({
            "clients": [client]
        }),
        "disableInsecureEncryption": json.dumps(True)
    }


    return add_client_request(server_dict, payload)


def delete_client_request(server_dict, rowID, user_uuid):
    headers = {
        'Accept': "application/json, text/plain, */*",
        'Accept-Language': "en-US,en;q=0.9",
        'Content-Type': "application/x-www-form-urlencoded; charset=UTF-8",
        'Cookie': f'x-ui={get_cookie(server_dict)}',
        'Authorization': server_dict.get('httpAuth', None),
        'X-Requested-With': "XMLHttpRequest"
    }

    res = requests.post(
        f"{server_dict['url']}/xui/inbound/{rowID}/delClient/{user_uuid}",
        headers=headers,
        # data=urllib.parse.urlencode(payload)
    )

    print(res.text)

    result = json.loads(res.text)
    if not result['success']:
        return -1, result['msg']
    return (1,) #user_uuid, port


def delete_client(server_dict, user_uuid):
    row = get_remark(server_dict)
    # clients_list = json.loads(row['settings'])['clients']

    # clients_list = [c for c in clients_list if c['email'] != f'{username}@{server_dict["rowRemark"]}']

    # row_settings = json.loads(row['settings'])
    # row_settings['clients'] = clients_list
    # row['settings'] = json.dumps(row_settings)

    row_id = row.pop('id', None)
    # row.pop('clientStats', None)
    # row.pop('tag', None)

    # payload = {
    #     "id": row_id,
    #     "settings": json.dumps(row_settings),
    #     "disableInsecureEncryption": json.dumps(True)
    # }

    return delete_client_request(server_dict, rowID=row_id, user_uuid=user_uuid)


def generate_vmess(server_dict, username, user_uuid):
    tls = 'tls'
    sni = ''
    host = ''
    if server_dict.get('SNIPattern', None) is not None:
        sni = f"{''.join(np.random.choice([*string.ascii_lowercase], size=np.random.randint(10, 20)))}.{server_dict['SNIPattern']}"

    if server_dict.get('hostHeader', None) is not None:
        host = server_dict['hostHeader']

    if server_dict.get('tls', None) is False:
        tls = ''

    if 'path' in server_dict and ((server_dict.get('path', None) is None) or (server_dict['path'] == '')):
        path = '/api'
    else:
        path = server_dict['path']

    template = {
        'add': server_dict['domain'],
        'aid': 0,
        'host': host,
        'id': user_uuid,
        'net': 'ws',
        'path': path,
        'port': server_dict['clientPort'],
        'ps': f'{username}@{server_dict["name"]}',
        'scy': 'auto',
        'sni': sni,
        'tls': tls,
        'type': 'none',
        'v': '2'
    }
    print(template)
    vmess = 'vmess://' + base64.encodebytes(json.dumps(template).replace(' ', '').encode()).decode().replace('\n', '')
    return vmess


def restrict_user(server_dicts, user_id):
    for server_dict in server_dicts:
        row = get_remark(server_dict)
        clients_list = json.loads(row['settings'])['clients']
        temp = None
        for client in clients_list:
            if client['email'] == f'{user_id}-{server_dict["name"]}@{server_dict["rowRemark"]}':
                temp = client
                temp['enable'] = False
        row_settings = json.loads(row['settings'])
        row_settings['clients'] = clients_list

        row_id = row.pop('id', None)

        payload = {
            "id": row_id,
            "settings": json.dumps({
                "clients": [temp]
            }),
            "disableInsecureEncryption": json.dumps(True)
        }
        update_client_request(server_dict, temp['id'], payload)

def get_client_by_email_or_id(server_dict, user_id):
    """
    Retrieves a client dictionary from XUI using the user's formatted email.
    """
    df = get_clients(server_dict)
    if df is None or df.empty:
        return None
    
    email = f"{user_id}-{server_dict['name']}@{server_dict['rowRemark']}"
    
    if email not in df.index:
        return None

    row = df.loc[email]
    return {
        'id': row['uuid'],
        'email': email
    }

def unrestrict_user(server_dicts, user_id):
    for server_dict in server_dicts:
        try:
            row = get_remark(server_dict)
            temp = get_client_by_email_or_id(server_dict, user_id)
            if not temp:
                print(f"[WARN] Client not found: {user_id}")
                continue

            row_id = row.pop('id', None)

            payload = {
                "id": row_id,
                "settings": json.dumps({
                    "clients": [dict(temp, enable=True)]
                }),
                "disableInsecureEncryption": json.dumps(True)
            }

            result = update_client_request(server_dict, temp['id'], payload)
            print(f"[INFO] Unrestricted user {user_id} on server {server_dict['name']}: {result}")

        except Exception as e:
            print(f"[ERROR] Failed to unrestrict user {user_id}: {e}")


def xui_charge_account(server_dict, user_id, charge_amount, new=False):
    row = get_remark(server_dict)
    clients_list = json.loads(row['settings'])['clients']
    for client in clients_list:
        print('xui_charge_account:',client,f'{user_id}@{server_dict["rowRemark"]}')
        if client['email'] == f'{user_id}@{server_dict["rowRemark"]}':
            client_uuid = client['id']
            if new is True:
                if float(charge_amount) < 0.01:
                    charge_amount = 0.01
                client['totalGB'] = float(charge_amount)*(1024**3)
            else:
                if float(charge_amount)+float(client['totalGB']) < 0.01:
                    charge_amount = 0.01
                client['totalGB'] = float(client['totalGB']) + float(charge_amount)*(1024**3)
            break

    # row_settings = json.loads(row['settings'])
    # row_settings['clients'] = clients_list

    row_id = row.pop('id', None)


    client['totalGB'] = int(client['totalGB'])
    payload = {
        "id": row_id,
        "settings": json.dumps({
            "clients": [client]
        }),
        "disableInsecureEncryption": json.dumps(True)
    }

    update_client_request(server_dict, client_uuid, payload)

    return round(float(client['totalGB'])/1024**3, 5)


def change_usage(user_id, server_dict, up, down):
    row = get_remark(server_dict)
    clients_list = json.loads(row['settings'])['clients']
    for client in clients_list:
        if client['email'] == f'{user_id}@{server_dict["rowRemark"]}':
            print(client)
            break
    # exit()

    row_settings = json.loads(row['settings'])
    row_settings['clients'] = clients_list

    row_id = row.pop('id', None)

    payload = {
        "id": row_id,
        "settings": json.dumps(row_settings),
        "disableInsecureEncryption": json.dumps(True)
    }

    # add_client_request(server_dict, payload)

    return round(float(client['totalGB'])/1024**3, 5)
    # user_client = get_clients(server_dict, select=[f"{user_id}"])

    # return (round(float(user_client.down.iloc[0])/1024**3+float(user_client.up.iloc[0])/1024**3, 5), round(float(user_client.total.iloc[0])/1024**3, 5))

# def update_client(server_dict, traffic, user_obj):
#     row = get_remark(server_dict)
#     clients_list = json.loads(row['settings'])['clients']
#     total = traffic * 1024**3
#     # print(clients_list)
#     # exit()
#     {"clients": [{  "id": "3f79f735-6ec0-4928-a7ec-88352efb66be",  "alterId": 0,  "email": "ds35jr",  "totalGB": 34424509440,  "expiryTime": 0,  "enable": true,  "tgId": "",  "subId": ""}]}

#     for c
#     clients_list.append({
#         'id': user_obj.uuid,
#         'alterId': 0,
#         'email': f"{user_obj.user_id}@{server_dict['rowRemark']}",
#         'totalGB': total,
#         # 'expiryTime': expires.timestamp() * 1000,
#         'enable': True,
#         'tgId': '',
#         'subId': ''
#     })

#     row_settings = json.loads(row['settings'])
#     row_settings['clients'] = clients_list
#     # row['settings'] = json.dumps(row_settings)

#     row_id = row.pop('id', None)

#     # row.pop('clientStats', None)
#     # row.pop('tag', None)

#     payload = {
#         "id": row_id,
#         "settings": json.dumps(row_settings),
#         "disableInsecureEncryption": json.dumps(True)
#     }

#     return add_client_request(server_dict, payload)

def update_client_request(server_dict, client_uuid, payload):
    # Example:
    # {"clients": [{  "id": "ac6cd21ba-766d-403a-bf17-72fdf5b8ab21",  "alterId": 0,  "email": "7jv22s1c",  "totalGB": 208447924224,  "expiryTime": 0,  "enable": false,  "tgId": "",  "subId": ""}]}

    headers = {
        'Accept': "application/json, text/plain, */*",
        'Accept-Language': "en-US,en;q=0.9",
        'Content-Type': "application/x-www-form-urlencoded; charset=UTF-8",
        'Cookie': f'x-ui={get_cookie(server_dict)}',
        'Authorization': server_dict.get('httpAuth', None),
        'X-Requested-With': "XMLHttpRequest"
    }

    res = requests.post(
        f"{server_dict['url']}/xui/inbound/updateClient/{client_uuid}",
        headers=headers,
        data=urllib.parse.urlencode(payload)
    )

    result = json.loads(res.text)
    if not result['success']:
        return -1, result['msg']
    return (1,) #user_uuid, port

def get_online_users(server_dict):
    """Fetch online users from the x-ui panel using the /onlines API endpoint (POST)."""
    url = f"{server_dict['url']}/xui/inbound/onlines"
    headers = {
        'Accept': "application/json, text/plain, */*",
        'Accept-Language': "en-US,en;q=0.9",
        'Content-Type': "application/x-www-form-urlencoded; charset=UTF-8",
        'Cookie': f'x-ui={get_cookie(server_dict)}',
        'Authorization': server_dict.get('httpAuth', None),
        'X-Requested-With': "XMLHttpRequest"
    }
    try:
        response = requests.post(url, headers=headers, data={})
        print("Status code:", response.status_code)
        print("Response text:", response.text)  # Debug print
        print("Response headers:", response.headers)
        response.raise_for_status()
        data = response.json()
        return data
    except Exception as e:
        print(f"Error fetching online users: {e}")
        return None
