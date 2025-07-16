import socket
import contextlib 
import requests
from helpers.initial import get_secrets_config, connect_to_database, set_lang

(secrets, Config) = get_secrets_config()
bot_functions_texts = set_lang(Config['default_language'], 'bot_functions')


def is_port_open(port, host='127.0.0.1'):
    with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        if sock.connect_ex((host, port)) == 0:
            return False
        else:
            return True


def get_port():
    while True:
        sock = socket.socket()
        sock.bind(('', 0))
        port = sock.getsockname()[1]
        sock.close()
        if is_port_open(port):
            return port


def normalize_transaction_id(tr_id):
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
    except Exception:
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

    return (True, None)


async def verfiy_transaction(transaction_id, amount, dest_wallet , user_id, plan, payment_url):
    url = f'https://apilist.tronscan.org/api/transaction-info?hash={transaction_id}'

    response = requests.get(url)
    if response.status_code != 200:
        return (False, None)

    data = response.json()

    if 'confirmed' not in data and ('riskTransaction' in data and not data['riskTransaction']):
        return (False, "Failed")
    elif float(amount) != float(data['contractData']['amount'])/10**6 or dest_wallet != data['toAddress']:
        return (False, "incorrect_data")
    elif data['confirmed'] and data['contractRet'] == 'SUCCESS':
        return (True, None)
    else:
        return (False, None)


def get_user_lang(db_client, db_name, user_id, default_lang):
    user = db_client[db_name].users.find_one({'user_id': user_id})
    if user:
        if 'lang' not in user:
            db_client[db_name].users.update_one({'user_id': user_id}, {'$set': {'lang': default_lang}})
            return default_lang
        return user.get('lang', default_lang)
    return default_lang
