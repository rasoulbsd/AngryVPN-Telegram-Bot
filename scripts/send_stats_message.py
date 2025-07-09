import json
import requests
from datetime import datetime

# Load bot token and chat_id from secrets
with open('secrets.json', 'r') as fp:
    secrets = json.load(fp)

bot_token = secrets['BotAPI']
chat_id = secrets['OnlineUsersGroupID']  # Read chat_id from secrets
# If you want to send to a specific topic (forum), set message_thread_id
message_thread_id = secrets['OnlineUsersTopicID']  # Set to a number if using topics, else None

# Compose the message
current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
message = (
    "🟢 **Online Users Statistics**\n"
    f"📅 Last Updated: {current_time}\n"
    "👥 Total Unique Users: **0**\n\n"
    "**Server Breakdown:**\n"
    "• Example-Server:    0 users\n"
)

url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
data = {
    'chat_id': chat_id,
    'text': message,
    'parse_mode': 'Markdown'
}
if message_thread_id is not None:
    data['message_thread_id'] = message_thread_id

response = requests.post(url, data=data)
result = response.json()
print(json.dumps(result, indent=2, ensure_ascii=False))
if result.get('ok'):
    print(f"Message sent! message_id: {result['result']['message_id']}")
else:
    print(f"Failed to send message: {result}")