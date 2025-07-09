import telegram
import telegram.ext as telext

from .rial import (
    check_payment,
    payment,
    newuser_purchase_rial,
    newuser_purchase_rial_inputed,
    newuser_purchase_rial_inputed_image,
    newuser_purchase_rial_inputed_document,
)
from .crypto import (
    newuser_purchase_receipt_crypto,
    newuser_purchase_receipt_crypto_inputed,
    newuser_purchase_crypto_check_manually,
    newuser_purchase_receipt_bitcoin,  # stub
    newuser_purchase_receipt_ethereum,  # stub
)
from .stripe import (
    newuser_purchase_stripe,
    newuser_purchase_stripe_webhook,
    newuser_purchase_stripe_confirm,
    newuser_purchase_stripe_subscription,  # stub
    newuser_purchase_stripe_refund,  # stub
)
from .orchestration import (
    newuser_purchase,
    newuser_purchase_select_plan,
    newuser_purchase_interceptor,
    newuser_purchase_interceptor_inputed,
)

__all__ = [
    # Rial payment functions
    'check_payment',
    'payment',
    'newuser_purchase_rial',
    'newuser_purchase_rial_inputed',
    'newuser_purchase_rial_inputed_image',
    'newuser_purchase_rial_inputed_document',
    # Crypto payment functions
    'newuser_purchase_receipt_crypto',
    'newuser_purchase_receipt_crypto_inputed',
    'newuser_purchase_crypto_check_manually',
    'newuser_purchase_receipt_bitcoin',
    'newuser_purchase_receipt_ethereum',
    # Stripe payment functions
    'newuser_purchase_stripe',
    'newuser_purchase_stripe_webhook',
    'newuser_purchase_stripe_confirm',
    'newuser_purchase_stripe_subscription',
    'newuser_purchase_stripe_refund',
    # Orchestration functions
    'newuser_purchase',
    'newuser_purchase_select_plan',
    'newuser_purchase_interceptor',
    'newuser_purchase_interceptor_inputed',
    # Utility functions
    'route_payment_by_type',
]

# --- Orchestration/dispatch logic ---

async def route_payment_by_type(update: telegram.Update, context: telext.ContextTypes.DEFAULT_TYPE, payment_type: str):
    """
    Route payment to the correct module based on payment type.
    
    Args:
        update: Telegram update object
        context: Telegram context object  
        payment_type: Type of payment ('rial', 'crypto', 'stripe', etc.)
    """
    if payment_type == 'rial':
        return await newuser_purchase_rial(update, context)
    elif payment_type == 'crypto' or payment_type == 'tron':
        return await newuser_purchase_receipt_crypto(update, context)
    elif payment_type == 'stripe':
        return await newuser_purchase_stripe(update, context)
    else:
        # Default to rial for backward compatibility
        return await newuser_purchase_rial(update, context)
