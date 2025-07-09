from diagrams import Diagram, Cluster, Node

def create_vpn_bot_flowchart():
    with Diagram("VPN Bot Flowchart", show=False):

        # Telegram Bot
        with Cluster("Telegram Bot"):
            bot = Node("VPN Bot", shape="cylinder")
            channel = Node("Join Channel", shape="folder")
            new_user = Node("New User", shape="cylinder")
            existing_user = Node("Existing User", shape="cylinder")

        # XUI Panel
        with Cluster("XUI Panel"):
            xui_panel = Node("XUI Panel", shape="database")

        # MongoDB Database
        with Cluster("MongoDB"):
            mongodb = Node("MongoDB", shape="database")

        # Telegram Bot Connections
        bot >> channel
        bot >> new_user
        bot >> existing_user

        # XUI Panel Connections
        bot << xui_panel

        # MongoDB Connections
        bot << mongodb

        # User Interactions
        with Cluster("User Interactions"):
            purchase_plan = Node("Purchase Plan", shape="box")
            send_receipt = Node("Send Receipt", shape="box")
            accept_receipt = Node("Accept Receipt", shape="box")
            send_ticket = Node("Send Ticket", shape="box")
            get_user_info = Node("Get User Info", shape="box")

        # User Interactions Connections
        new_user >> purchase_plan
        new_user >> send_receipt
        send_receipt >> accept_receipt
        existing_user >> send_ticket
        existing_user >> get_user_info

if __name__ == "__main__":
    create_vpn_bot_flowchart()

