#!/usr/bin/env python3
"""
Script to update server schema with new attributes:
- isRecommended: Boolean flag for recommended servers
- isNew: Boolean flag for new servers (can be used for special highlighting)
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from helpers.initial import get_secrets_config, connect_to_database

def update_server_schema():
    """Update server documents with new attributes."""
    try:
        (secrets, Config) = get_secrets_config()
        db_client = connect_to_database(secrets['DBConString'])
        
        print("🔄 Updating server schema...")
        
        # Get all servers
        servers = list(db_client[secrets['DBName']].servers.find({}))
        print(f"📊 Found {len(servers)} servers to update")
        
        updated_count = 0
        for server in servers:
            server_name = server['name']
            updates = {}
            
            # Add isRecommended if not present (default to False)
            if 'isRecommended' not in server:
                updates['isRecommended'] = False
                print(f"  ➕ Adding isRecommended=False to {server_name}")
            
            # Add isNew if not present (default to False)
            if 'isNew' not in server:
                updates['isNew'] = False
                print(f"  ➕ Adding isNew=False to {server_name}")
            
            # Update if there are changes
            if updates:
                result = db_client[secrets['DBName']].servers.update_one(
                    {'_id': server['_id']},
                    {'$set': updates}
                )
                if result.modified_count > 0:
                    updated_count += 1
        
        print(f"✅ Updated {updated_count} servers")
        
        # Show current server status
        print("\n📋 Current server status:")
        for server in db_client[secrets['DBName']].servers.find({}, {'name': 1, 'isRecommended': 1, 'isNew': 1}):
            recommended = "⭐" if server.get('isRecommended', False) else "  "
            new_tag = "🆕" if server.get('isNew', False) else "  "
            print(f"  {recommended} {new_tag} {server['name']}")
        
        db_client.close()
        print("\n🎉 Server schema update completed!")
        
    except Exception as e:
        print(f"❌ Error updating server schema: {e}")
        return False
    
    return True

def set_recommended_server(server_name, is_recommended=True):
    """Set a specific server as recommended."""
    try:
        (secrets, Config) = get_secrets_config()
        db_client = connect_to_database(secrets['DBConString'])
        
        result = db_client[secrets['DBName']].servers.update_one(
            {'name': server_name},
            {'$set': {'isRecommended': is_recommended}}
        )
        
        if result.modified_count > 0:
            status = "recommended" if is_recommended else "not recommended"
            print(f"✅ Server '{server_name}' is now {status}")
        else:
            print(f"❌ Server '{server_name}' not found")
        
        db_client.close()
        return True
        
    except Exception as e:
        print(f"❌ Error setting recommended server: {e}")
        return False

def set_new_server(server_name, is_new=True):
    """Set a specific server as new."""
    try:
        (secrets, Config) = get_secrets_config()
        db_client = connect_to_database(secrets['DBConString'])
        
        result = db_client[secrets['DBName']].servers.update_one(
            {'name': server_name},
            {'$set': {'isNew': is_new}}
        )
        
        if result.modified_count > 0:
            status = "new" if is_new else "not new"
            print(f"✅ Server '{server_name}' is now {status}")
        else:
            print(f"❌ Server '{server_name}' not found")
        
        db_client.close()
        return True
        
    except Exception as e:
        print(f"❌ Error setting new server: {e}")
        return False

def main():
    """Main function with interactive menu."""
    print("🚀 Server Schema Update Tool")
    print("=" * 40)
    
    while True:
        print("\nOptions:")
        print("1. Update all servers with new schema")
        print("2. Set server as recommended")
        print("3. Set server as new")
        print("4. Exit")
        
        choice = input("\nSelect option (1-4): ").strip()
        
        if choice == "1":
            update_server_schema()
        elif choice == "2":
            server_name = input("Enter server name: ").strip()
            if server_name:
                set_recommended_server(server_name)
        elif choice == "3":
            server_name = input("Enter server name: ").strip()
            if server_name:
                set_new_server(server_name)
        elif choice == "4":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid option. Please try again.")

if __name__ == "__main__":
    main() 