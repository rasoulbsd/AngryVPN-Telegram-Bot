from initial import get_secrets_config, connect_to_database
import requests
import json
import logging
import pymongo
import json
import os
from dotenv import load_dotenv
import gettext
# (secrets, Config) = get_secrets_config()

# env_variables = {key: os.environ.get(key) for key in os.environ.keys()}
# json_string = json.dumps(env_variables)
# Config = json.loads(json_string)
# print(Config)
with open('../secrets.json', 'r') as fp:
    secrets = json.load(fp)

# Check if a specific user is a subscriber of a Telegram channel
def is_user_subscribed(channel_username, user_id, bot_token):
    """Check if a user is subscribed to a Telegram channel (bot must be admin)"""
    base_url = f"https://api.telegram.org/bot{bot_token}"
    url = f"{base_url}/getChatMember"
    params = {
        "chat_id": f"@{channel_username}",
        "user_id": user_id
    }
    try:
        response = requests.get(url, params=params)
        data = response.json()
        if not data.get('ok'):
            print(f"Error checking user subscription: {data}")
            return False
        status = data['result']['status']
        if status in ['member', 'administrator', 'creator']:
            print(f"User {user_id} is subscribed (status: {status})")
            return True
        else:
            print(f"User {user_id} is NOT subscribed (status: {status})")
            return False
    except Exception as e:
        print(f"Error: {e}")
        return False

# Example usage
bot_token = secrets.get('BotAPI')
if not bot_token:
    print("BotAPI token not found in secrets.json")
else:
    channel = "ir_network_incidents"
    user_id = 123456789  # Replace with the actual user ID you want to check
    print(f"Checking if user {user_id} is subscribed to @{channel}...")
    is_user_subscribed(channel, user_id, bot_token)


# userIDs = 
# db_client = connect_to_database(secrets['DBConString'])
# db_client[secrets['DBName']]
# payments = db_client[secrets['DBName']].payments.find({
#     "org": "rhvp-reis",
#     "user_id": {"$nin": excluded_user_ids}
# })


