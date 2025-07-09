import telegram
import telegram.ext as telext
from helpers.initial import get_secrets_config, set_lang

(secrets, Config) = get_secrets_config()
client_functions_texts = set_lang(Config['default_language'], 'client_functions')

# --- Crypto payment functions (Tron, etc.) ---

async def newuser_purchase_receipt_crypto(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    # ... (full function body from helpers/client/crypto.py)
    pass

async def newuser_purchase_receipt_crypto_inputed(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    # ... (full function body from helpers/client/crypto.py)
    pass

async def newuser_purchase_crypto_check_manually(update, context):
    # ... (full function body from helpers/client/crypto.py)
    pass

# --- Stubs for future coins ---

async def newuser_purchase_receipt_bitcoin(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    # TODO: Implement Bitcoin payment flow
    pass

async def newuser_purchase_receipt_ethereum(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE):
    # TODO: Implement Ethereum payment flow
    pass 