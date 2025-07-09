#!/usr/bin/env python3
"""
Script to update Telegram message with online user statistics every 15 minutes.
This script fetches online users from all active servers, counts unique users,
and updates a specified Telegram message with the statistics.
"""

import json
import requests
import logging
from datetime import datetime
from helpers.initial import connect_to_database
from helpers.xuiAPI import get_online_users

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('online_stats.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def load_secrets():
    """Load secrets configuration"""
    try:
        with open('secrets.json', 'r') as fp:
            return json.load(fp)
    except FileNotFoundError:
        logger.error("secrets.json not found")
        return None


def get_active_servers(db_client, db_name):
    """Get all active servers from database"""
    try:
        servers = list(db_client[db_name].servers.find({
            "$or": [
                {'isActive': {"$exists": True, "$eq": True}},
                {"isActive": {"$exists": False}}
            ],
        }))
        logger.info(f"Found {len(servers)} active servers")
        return servers
    except Exception as e:
        logger.error(f"Error fetching servers: {e}")
        return []


def parse_online_user(user_string):
    """
    Parse online user string to extract user ID and server name.
    Format: "UserID-ServerName@protocol"
    Example: "465839432-Nika-teh-pars@https"
    """
    try:
        # Remove the @protocol part
        user_part = user_string.split('@')[0]
        
        # Split by the first dash to separate user ID from server name
        parts = user_part.split('-', 1)  # Split only on first dash
        if len(parts) == 2:
            user_id = parts[0]
            server_name = parts[1]  # This will be the complete server name
            return user_id, server_name
        else:
            logger.warning(f"Could not parse user string: {user_string}")
            return None, None
    except Exception as e:
        logger.error(f"Error parsing user string '{user_string}': {e}")
        return None, None


def get_online_statistics(servers):
    """
    Get online statistics from all servers
    Returns:
        - server_stats: dict with server names as keys and unique user counts as values
        - total_unique_users: int
        - all_unique_users: set of all user IDs
        - server_users: dict of server_name -> list of user_ids
        - user_servers: dict of user_id -> list of server_names
    """
    server_stats = {}
    all_unique_users = set()
    server_users = {}
    user_servers = {}
    
    for server in servers:
        try:
            logger.info(f"Fetching online users from server: {server['name']}")
            result = get_online_users(server)
            
            if result and 'obj' in result:
                online_users = result['obj']
                logger.info(
                    f"Server {server['name']}: {len(online_users)} "
                    f"online users"
                )
                # Parse each online user and group by server name from response
                for user_string in online_users:
                    user_id, server_name = parse_online_user(user_string)
                    if user_id and server_name:
                        # For server_stats and server_users
                        if server_name not in server_stats:
                            server_stats[server_name] = set()
                            server_users[server_name] = set()
                        server_stats[server_name].add(user_id)
                        server_users[server_name].add(user_id)
                        # For user_servers
                        if user_id not in user_servers:
                            user_servers[user_id] = set()
                        user_servers[user_id].add(server_name)
                        # For all unique users
                        all_unique_users.add(user_id)
                logger.info(
                    f"Found {len(server_stats)} different servers in response"
                )
            else:
                logger.warning(
                    f"No online users data for server {server['name']}"
                )
        except Exception as e:
            logger.error(
                f"Error fetching online users from server "
                f"{server['name']}: {e}"
            )
    # Convert sets to counts/lists
    server_stats_counts = {
        server: len(users)
        for server, users in server_stats.items()
    }
    server_users_lists = {
        server: list(users)
        for server, users in server_users.items()
    }
    user_servers_lists = {
        user: list(servers)
        for user, servers in user_servers.items()
    }
    return server_stats_counts, len(all_unique_users), all_unique_users, server_users_lists, user_servers_lists


def save_stats_to_metrics(db_client, db_name, total_unique_users, server_stats, server_users, user_servers, org):
    """
    Save the current stats to the metrics collection in MongoDB.
    """
    metrics_collection = db_client[db_name]['metrics']
    doc = {
        "timestamp": datetime.now(),
        "org": org,
        "total_unique_users": total_unique_users,
        "server_stats": server_stats,
        "server_users": server_users,
        "user_servers": user_servers
    }
    metrics_collection.insert_one(doc)


def format_message(server_stats, total_unique_users):
    """
    Format the message to be sent to Telegram
    """
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    message = "🟢 **Online Users Statistics**\n"
    message += f"📅 Last Updated: {current_time}\n"
    message += f"👥 Total Unique Users: **{total_unique_users}**\n\n"
    
    if server_stats:
        message += "**Server Breakdown:**\n"
        # Find the longest server name for alignment
        max_server_name_length = max(len(name) for name in server_stats.keys())
        # Find the longest user count for alignment
        max_user_count_length = max(len(str(count)) for count in server_stats.values())
        
        for server_name, user_count in sorted(server_stats.items()):
            padded_name = server_name.ljust(max_server_name_length)
            padded_count = str(user_count).rjust(max_user_count_length)
            message += (
                f"• {padded_name} : {padded_count} users\n"
            )
    else:
        message += "No active servers found.\n"
    
    return message


def update_telegram_message(bot_token, chat_id, message_id, message):
    """
    Update a specific Telegram message using the Bot API
    """
    url = f"https://api.telegram.org/bot{bot_token}/editMessageText"
    
    data = {
        'chat_id': chat_id,
        'message_id': message_id,
        'text': message,
        'parse_mode': 'Markdown'
    }
    
    try:
        response = requests.post(url, data=data)
        result = response.json()
        
        if result.get('ok'):
            logger.info("Message updated successfully")
            return True
        else:
            logger.error(f"Failed to update message: {result}")
            return False
            
    except Exception as e:
        logger.error(f"Error updating Telegram message: {e}")
        return False


def main():
    """Main function to update online statistics"""
    logger.info("Starting online statistics update...")
    
    # Load secrets
    secrets = load_secrets()
    if not secrets:
        logger.error("Failed to load secrets")
        return
    
    # Connect to database
    try:
        db_client = connect_to_database(secrets['DBConString'])
        db_name = secrets['DBName']
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        return
    
    # Get active servers
    servers = get_active_servers(db_client, db_name)
    if not servers:
        logger.warning("No active servers found")
        return
    
    # Get org from the first active server
    org = servers[0].get('org') if servers and 'org' in servers[0] else None
    
    # Get online statistics
    (server_stats, total_unique_users, all_unique_users, 
     server_users, user_servers) = get_online_statistics(servers)
    
    # Format message
    message = format_message(server_stats, total_unique_users)
    logger.info("Formatted message:\n" + message)
    
    # Update Telegram message
    bot_token = secrets.get('BotAPI')
    if not bot_token:
        logger.error("Bot token not found in secrets")
        return
    
    # Extract chat_id and message_id from secrets
    chat_id = secrets.get('OnlineUsersGroupID')  # Convert to proper format
    message_id = secrets.get('OnlineUsersMessageID')
    if not message_id:
        logger.error("OnlineUsersMessageID not found in secrets")
        return
    
    success = update_telegram_message(bot_token, chat_id, message_id, message)
    
    if success:
        logger.info("Online statistics update completed successfully")
    else:
        logger.error("Failed to update online statistics")
    
    # Save stats to metrics collection
    save_stats_to_metrics(
        db_client, db_name, total_unique_users, server_stats, server_users,
        user_servers, org
    )
    
    # Close database connection
    db_client.close()


if __name__ == "__main__":
    main() 