import telegram.ext as telext
from helpers.initial import connect_to_database, get_secrets_config
from dotenv import load_dotenv

from helpers.commands import start, menu, cancel, admin, cancel_command
from helpers.client.server import get_unified_servers, deliver_vmess, get_status, deliver_vmess_status
from helpers.client.user import get_userinfo
from helpers.client.ticket import receive_ticket, receive_ticket_inputed
from helpers.client.charge import user_charge_account, user_charge_account_with_plan, user_charge_acc_inputed, user_charge_acc_inputed_image, user_charge_rial_inputed_document
from helpers.client.purchase import (
    check_payment, payment as pay, newuser_purchase, newuser_purchase_select_plan, 
    newuser_purchase_interceptor, newuser_purchase_interceptor_inputed, 
    newuser_purchase_rial, newuser_purchase_rial_inputed, newuser_purchase_rial_inputed_image, 
    newuser_purchase_rial_inputed_document,
    newuser_purchase_receipt_crypto, newuser_purchase_receipt_crypto_inputed, 
    newuser_purchase_crypto_check_manually
)
from helpers.main_admin import manage_orgs
from helpers.org_admin.members import add_member_to_my_org, add_member_to_my_org_inputed, ban_member, ban_member_inputed
from helpers.org_admin.servers import manage_my_org_server, switch_server_active_join, change_server_traffic, change_server_traffic_inputed
from helpers.org_admin.announcements import admin_announcement, admin_announcement_inputed, direct_message_userid_inputed, direct_message_text_inputed, direct_message
from helpers.org_admin.charging import admin_charge_account, admin_charge_account_with_server, admin_charge_account_with_server_and_userid_and_amount, admin_charge_all_accounts, admin_charge_all_accounts_with_server, admin_charge_all_accounts_inputed,accept_receipt,reject_receipt,accept_automatic_receipt,accept_manualy_receipt,receipt_rejected,receipt_back
from telegram.ext import PicklePersistence
from helpers.bot_functions import usage_exceed
from helpers.states import (
    DELIVER_SERVER, DELIVER_USER_VMESS_STATUS, ORG_MNGMNT_SELECT_OPTION, MY_ORG_MNGMNT_SELECT_OPTION,
    RECEIVE_TICKET, USER_RECHARGE_ACCOUNT_SELECT_PLAN, USER_RECHARGE_ACCOUNT, USER_RECHARGE_ACCOUNT_RIAL_ZARIN, USER_RECHARGE_ACCOUNT_RIAL_ZARIN_PAID,
    NEWUSER_PURCHASE_SELECT_PLAN, NEWUSER_PURCHASE_INTERCEPTOR, NEWUSER_PURCHASE_INTERCEPTOR_INPUTED, NEWUSER_PURCHASE_RIAL, NEWUSER_PURCHASE_RIAL_INPUTED, NEWUSER_PURCHASE_RIAL_ZARIN, NUEWUSER_PURCHASE_RECEIPT_CRYPTO, NEWUSER_PURCHASE_FINAL, CHECK_TRANS_MANUALLY, PAID,
    ADMIN_MENU, ADDING_MEMEBER_TO_ORG, BAN_MEMBER, ADMIN_ANNOUNCEMENT, ADMIN_CHARGE_ACCOUNT_USERID, ADMIN_CHARGE_ACCOUNT_AMOUNT, ADMIN_CHARGE_ACCOUNT_FINAL, ADMIN_CHARGE_ALL_ACCOUNTS, ADMIN_CHARGE_ALL_ACCOUNTS_AMOUNT, LISTING_ORG_SERVERS, CHOSING_SERVER_EDIT_ACTION, CHANGING_SERVER_TRAFFIC, ADMIN_DIRECT_MESSAGE_USERID, ADMIN_DIRECT_MESSAGE_TEXT,
    REJECT, ACCEPT, REJECT_CHECK
)


############################# INITIAL #############################
load_dotenv()

(secrets, Config) = get_secrets_config()

try: 
    db_client = connect_to_database(secrets['DBConString'])
except Exception:
    print("Failed to connect to the database!")

PLANS = ['Basic', 'Family', 'Business', 'Enterprise', 'Premium', 'Ultimate']
############################# GLOBALS #############################
# Stages


############################# Main #############################

if __name__ == '__main__':
    persistence = PicklePersistence(filepath="conversationbot")
    application = telext.ApplicationBuilder().token(secrets['BotAPI']).arbitrary_callback_data(True).persistence(persistence).build()

    start_handler = telext.CommandHandler('start', start)
    menu_handler = telext.CommandHandler('menu', menu)
    cancel_handler = telext.CallbackQueryHandler(cancel, pattern='^Cancel$')


    ### Main Menu Handlers ###
    status_handler = telext.ConversationHandler(
        entry_points=[telext.CallbackQueryHandler(get_status, pattern='^Get Vmess Status$')],
        states={
            DELIVER_USER_VMESS_STATUS: [
              telext.CallbackQueryHandler(deliver_vmess_status, pattern=lambda z: z in [s['name'] for s in db_client[secrets['DBName']].servers.find(projection={'name': True})]),
            ]
        },
        fallbacks=[cancel_handler],
        per_message=True,
        allow_reentry=False,
        name="status_handler"
    )

    vmess_handler = telext.ConversationHandler(
        entry_points=[telext.CallbackQueryHandler(get_unified_servers, pattern='^Get Servers$')],
        states={
            DELIVER_SERVER: [
                telext.CallbackQueryHandler(deliver_vmess, pattern=lambda z: z in [s['name'] for s in db_client[secrets['DBName']].servers.find(projection={'name': True})]),
            ],
        },
        fallbacks=[telext.CallbackQueryHandler(cancel, pattern='^Cancel$')],
        per_message=True,
        allow_reentry=False,
        name="vmess_handler"
    )



    userinfo_handler = telext.ConversationHandler(
        entry_points=[telext.CallbackQueryHandler(get_userinfo, pattern='^Get User Info$')],
        states={},
        fallbacks=[],
        per_message=True,
        allow_reentry=False,
        name="userinfo_handler"
    )

    receive_ticket_handler = telext.ConversationHandler(
        entry_points=[telext.CallbackQueryHandler(receive_ticket, pattern='^Receive Ticket$')],
        states={
            RECEIVE_TICKET: [
                telext.MessageHandler(telext.filters.Regex(r'^[\s\S]*$'), receive_ticket_inputed)
            ],
        },
        fallbacks=[
            telext.CallbackQueryHandler(cancel, pattern='^Cancel$')
        ],
        per_message=False,
        allow_reentry=True,
        name="receive_ticket_handler"
    )

    charge_acc_handler = telext.ConversationHandler(
        entry_points=[telext.CallbackQueryHandler(user_charge_account, pattern='^Charge Account$')],
        states={
            USER_RECHARGE_ACCOUNT_SELECT_PLAN: [
                telext.CallbackQueryHandler(user_charge_account_with_plan, pattern=lambda z: z.get('plan', '') in PLANS),
            ],
            USER_RECHARGE_ACCOUNT: [
                telext.MessageHandler(telext.filters.Regex(r'^[\s\S]*$'), user_charge_acc_inputed),
                telext.MessageHandler(telext.filters.PHOTO, user_charge_acc_inputed_image),
                telext.MessageHandler(telext.filters.Document.ALL, user_charge_rial_inputed_document),
            ],
            USER_RECHARGE_ACCOUNT_RIAL_ZARIN: [
                telext.CallbackQueryHandler(pay, pattern='Pay now')
            ],
            USER_RECHARGE_ACCOUNT_RIAL_ZARIN_PAID: [
                telext.CallbackQueryHandler(check_payment,pattern='Paid'),
                
            ],
        },
        fallbacks=[telext.CallbackQueryHandler(cancel, pattern='^Cancel$')],
        per_message=False,
        allow_reentry=True,
        name="charge_acc_handler"
    )

    purchase_acc_handler = telext.ConversationHandler(
        entry_points=[telext.CallbackQueryHandler(newuser_purchase, pattern='^Purchase Account$')],
        states={
            NEWUSER_PURCHASE_SELECT_PLAN: [
                telext.MessageHandler(telext.filters.Regex("^[0-9]*$"), newuser_purchase_select_plan)
            ],
            NEWUSER_PURCHASE_INTERCEPTOR: [
                telext.CallbackQueryHandler(newuser_purchase_interceptor, pattern=lambda z: z.get('plan', '') in PLANS),
            ],
            NEWUSER_PURCHASE_INTERCEPTOR_INPUTED: [
                telext.CallbackQueryHandler(newuser_purchase_interceptor_inputed, pattern=lambda z: z.get('method', '') == 'rial' or z.get('method', '') == 'tron'),
            ],
            NEWUSER_PURCHASE_RIAL: [
                
                telext.CallbackQueryHandler(newuser_purchase_rial, pattern=None),
            ],
            NEWUSER_PURCHASE_RIAL_INPUTED: [
                telext.MessageHandler(telext.filters.Regex(r'^[\s\S]*$'), newuser_purchase_rial_inputed),
                telext.MessageHandler(telext.filters.PHOTO, newuser_purchase_rial_inputed_image),
                telext.MessageHandler(telext.filters.Document.ALL, newuser_purchase_rial_inputed_document),
            ],
            NEWUSER_PURCHASE_RIAL_ZARIN: [
                telext.CallbackQueryHandler(pay, pattern='Pay now')
            ],
            PAID: [
                telext.CallbackQueryHandler(check_payment,pattern='Paid'),
                
            ],
            NUEWUSER_PURCHASE_RECEIPT_CRYPTO: [
                telext.CallbackQueryHandler(newuser_purchase_receipt_crypto, pattern=lambda z: z.get('plan', '') in PLANS),
            ],
            NEWUSER_PURCHASE_FINAL: [
                telext.MessageHandler(telext.filters.Regex(r'^[\s\S]*$'), newuser_purchase_receipt_crypto_inputed)
            ],
            CHECK_TRANS_MANUALLY: [
                telext.CallbackQueryHandler(newuser_purchase_crypto_check_manually, pattern='^Check Manually$'),
            ]
        },
        fallbacks=[telext.CallbackQueryHandler(cancel, pattern='^Cancel$')],
        per_message=False,
        allow_reentry=True,
        name="purchase_acc_handler"
    )


    admin_handler = telext.ConversationHandler(
        entry_points=[
            telext.CommandHandler('admin', admin)
        ],
        states={
            ADMIN_MENU: [
                telext.CallbackQueryHandler(manage_orgs, pattern='^Manage Organizations$'),
                telext.CallbackQueryHandler(manage_my_org_server, pattern=lambda z: z in [
                    f"Manage: {org['name']}" for org in db_client[secrets['DBName']].orgs.find()
                ]),
            ],
            ORG_MNGMNT_SELECT_OPTION: [
                telext.CallbackQueryHandler(usage_exceed, pattern='^Exceed Users: Hard Coded$'),
            ],
            MY_ORG_MNGMNT_SELECT_OPTION: [
                telext.CallbackQueryHandler(add_member_to_my_org, pattern=lambda z: z.get('task', '') == 'Add Member to org' if type(z) is dict else False),
                telext.CallbackQueryHandler(ban_member, pattern=lambda z: z.get('task', '') == 'Ban Member' if type(z) is dict else False),
                telext.CallbackQueryHandler(admin_announcement, pattern=lambda z: z.get('task', '') == 'Admin Announcement' if type(z) is dict else False),
                telext.CallbackQueryHandler(admin_charge_account, pattern=lambda z: z.get('task', '') == 'Admin Charge Account' if type(z) is dict else False),
                telext.CallbackQueryHandler(admin_charge_all_accounts, pattern=lambda z: z.get('task', '') == 'Admin Charge All Accounts' if type(z) is dict else False),
                telext.CallbackQueryHandler(manage_orgs, pattern=lambda z: z.get('task', '') == 'List Org Servers' if type(z) is dict else False),
                telext.CallbackQueryHandler(direct_message, pattern=lambda z: z.get('task', '') == 'Direct Message' if type(z) is dict else False),
            ],
            ADDING_MEMEBER_TO_ORG: [
                telext.MessageHandler(telext.filters.Regex("^[0-9]*$"), add_member_to_my_org_inputed)
            ],
            BAN_MEMBER: [
                telext.MessageHandler(telext.filters.Regex("^[0-9]*$"), ban_member_inputed)
            ],
            ADMIN_ANNOUNCEMENT: [
                telext.MessageHandler(telext.filters.Regex(r'^[\s\S]*$'), admin_announcement_inputed)
            ],
            ADMIN_DIRECT_MESSAGE_USERID: [
                telext.MessageHandler(telext.filters.Regex("^[0-9]*$"), direct_message_userid_inputed)
            ],
            ADMIN_DIRECT_MESSAGE_TEXT: [
                telext.MessageHandler(telext.filters.Regex(r'^[\s\S]*$'), direct_message_text_inputed)
            ],
            ADMIN_CHARGE_ACCOUNT_USERID: [
                telext.CallbackQueryHandler(admin_charge_account_with_server, pattern=lambda z: z in [s['name'] for s in db_client[secrets['DBName']].servers.find(projection={'name': True})]),
            ],
            ADMIN_CHARGE_ACCOUNT_AMOUNT: [
                # telext.MessageHandler(telext.filters.Regex("r'^[\s\S]*$'"), admin_charge_account_with_server_and_userid),
            ],
            ADMIN_CHARGE_ACCOUNT_FINAL: [
                telext.MessageHandler(telext.filters.Regex(r'^[\s\S]*$'), admin_charge_account_with_server_and_userid_and_amount),
            ],
            ADMIN_CHARGE_ALL_ACCOUNTS: [
                telext.CallbackQueryHandler(admin_charge_all_accounts_with_server, pattern=lambda z: z in [s['name'] for s in db_client[secrets['DBName']].servers.find(projection={'name': True})]),
            ],
            ADMIN_CHARGE_ALL_ACCOUNTS_AMOUNT: [
                telext.MessageHandler(telext.filters.Regex("^[0-9]*$"), admin_charge_all_accounts_inputed),
            ],
            LISTING_ORG_SERVERS: [
                telext.CallbackQueryHandler(manage_my_org_server, pattern=lambda z: z.get('task', '') == 'Manage Server' if type(z) is dict else False),
            ],
            CHOSING_SERVER_EDIT_ACTION: [
                telext.CallbackQueryHandler(switch_server_active_join, pattern=lambda z: z.get('task', '') == 'Switch Server Active Join' if type(z) is dict else False),
                telext.CallbackQueryHandler(change_server_traffic, pattern=lambda z: z.get('task', '') == 'Change Server Traffic' if type(z) is dict else False),
            ],
            CHANGING_SERVER_TRAFFIC: [
                telext.MessageHandler(telext.filters.Regex("^[0-9]*$"), change_server_traffic_inputed)
            ],
        },
        fallbacks=[
            telext.CallbackQueryHandler(cancel, pattern='^Cancel$'),
            telext.CommandHandler('cancel', cancel_command)
        ],
        per_message=False,
        allow_reentry=False,
        name="admin_handler"
    )

    receipt_checking_handler=telext.ConversationHandler(
        entry_points=[
            telext.CallbackQueryHandler(accept_receipt,pattern='^Accept$'),
            telext.CallbackQueryHandler(reject_receipt,pattern='^Reject$')
        ],
        states={
            REJECT:[


            ],
            ACCEPT:[
                telext.CallbackQueryHandler(accept_manualy_receipt,pattern='^Manualy$'),
                telext.CallbackQueryHandler(accept_automatic_receipt,pattern='^Automatic$'),
            ],
            REJECT_CHECK:[
                telext.CallbackQueryHandler(receipt_rejected,pattern='^Reject_sure$'),
                telext.CallbackQueryHandler(receipt_back,pattern='^Back$'),
            ]

        },
        fallbacks=[
            
        ],
        persistent=True,
        allow_reentry=True,
        name="receipt_checking_handler"
           
    )

    # Add ConversationHandler to application that will be used for handling updates

    application.add_handler(start_handler)
    application.add_handler(menu_handler)
    application.add_handler(admin_handler)

    application.add_handler(vmess_handler)
    application.add_handler(userinfo_handler)
    application.add_handler(receive_ticket_handler)
    application.add_handler(charge_acc_handler)
    application.add_handler(purchase_acc_handler)
    application.add_handler(status_handler)

    
    application.add_handler(cancel_handler, group=10)
    application.add_handler(receipt_checking_handler)
    
    application.run_polling()

