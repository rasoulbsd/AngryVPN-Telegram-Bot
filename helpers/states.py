"""
Centralized state definitions for all ConversationHandlers in the bot.
Import from this file instead of defining states in each module.
"""

# User menu states
NEW_USER_MENU = range(1)

# Ticketing and recharge states
(
    RECEIVE_TICKET,
    USER_RECHARGE_ACCOUNT_SELECT_PLAN,
    USER_RECHARGE_ACCOUNT,
    USER_RECHARGE_ACCOUNT_RIAL_ZARIN,
    USER_RECHARGE_ACCOUNT_RIAL_ZARIN_PAID
) = range(5)

# New user purchase states
(
    NEWUSER_PURCHASE_SELECT_PLAN,
    NEWUSER_PURCHASE_INTERCEPTOR,
    NEWUSER_PURCHASE_INTERCEPTOR_INPUTED,
    NEWUSER_PURCHASE_RIAL,
    NEWUSER_PURCHASE_RIAL_INPUTED,
    NEWUSER_PURCHASE_RIAL_ZARIN,
    NEWUSER_PURCHASE_CAD,
    NEWUSER_PURCHASE_CAD_INPUTED,
    NUEWUSER_PURCHASE_RECEIPT_CRYPTO,
    NEWUSER_PURCHASE_FINAL,
    CHECK_TRANS_MANUALLY,
    PAID
) = range(12)

# Admin and org management states
(
    ADMIN_MENU,
    ORG_MNGMNT_SELECT_OPTION,
    MY_ORG_MNGMNT_SELECT_OPTION,
    ADDING_MEMEBER_TO_ORG,
    BAN_MEMBER,
    ADMIN_ANNOUNCEMENT,
    ADMIN_CHARGE_ACCOUNT_USERID,
    ADMIN_CHARGE_ACCOUNT_AMOUNT,
    ADMIN_CHARGE_ACCOUNT_FINAL,
    ADMIN_CHARGE_ALL_ACCOUNTS,
    ADMIN_CHARGE_ALL_ACCOUNTS_AMOUNT,
    LISTING_ORG_SERVERS,
    CHOSING_SERVER_EDIT_ACTION,
    CHANGING_SERVER_TRAFFIC,
    ADMIN_DIRECT_MESSAGE_USERID,
    ADMIN_DIRECT_MESSAGE_TEXT,
    VMESS_TEST_SELECT_ENDPOINT,
    VMESS_TEST_INPUT_CONFIG
) = range(18)

# Vmess and server delivery states
DELIVER_SERVER = range(1)
DELIVER_USER_VMESS_STATUS = range(1)
DELIVER_REFRESH_VMESS = range(1)
REVOKE_SERVERS = range(1)

# Receipt checking states
REJECT, ACCEPT, REJECT_CHECK, RESUBMMIT = range(4)

# Add any additional states here as needed
