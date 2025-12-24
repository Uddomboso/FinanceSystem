"""
Stripe Payment Integration for PennyWise

This module handles ACH payments via Stripe + Plaid integration.
Used for the "Pay Now" feature to pay commitments directly from linked bank accounts.

FLOW:
1. User links bank via Plaid Link
2. We get a Plaid access_token and account_id
3. We exchange Plaid token for Stripe bank account token
4. Stripe can now debit the user's bank account

SANDBOX MODE:
- Uses Stripe test keys (sk_test_...)
- No real money moves
- Test with Plaid sandbox credentials
"""

import stripe
from core.config import Config
from core.logger import logger

# Initialize Stripe with secret key
stripe.api_key = Config.STRIPE_SECRET_KEY


def is_stripe_enabled():
    """Check if Stripe is properly configured"""
    return Config.STRIPE_ENABLED


def create_stripe_customer(user_id, email=None):
    """
    Create a Stripe customer for the user.
    
    Args:
        user_id: PennyWise user ID
        email: Optional user email
        
    Returns:
        Stripe customer ID or None on error
    """
    if not is_stripe_enabled():
        logger.warning("Stripe not enabled - using demo mode")
        return f"cus_demo_{user_id}"
    
    try:
        customer = stripe.Customer.create(
            metadata={"pennywise_user_id": str(user_id)},
            email=email,
            description=f"PennyWise User {user_id}"
        )
        logger.info(f"Created Stripe customer: {customer.id}")
        return customer.id
    except stripe.error.StripeError as e:
        logger.error(f"Stripe customer creation failed: {e}")
        return None


def get_or_create_stripe_customer(user_id, email=None):
    """
    Get existing Stripe customer or create new one.
    Stores customer ID in database for future use.
    """
    from database.db_manager import fetch_one, execute_query
    
    # Check if user already has a Stripe customer ID
    user = fetch_one("""
        SELECT stripe_customer_id FROM users WHERE user_id = ?
    """, (user_id,))
    
    if user and user.get('stripe_customer_id'):
        return user['stripe_customer_id']
    
    # Create new customer
    customer_id = create_stripe_customer(user_id, email)
    
    if customer_id:
        # Store in database (add column if needed)
        try:
            execute_query("""
                ALTER TABLE users ADD COLUMN stripe_customer_id TEXT
            """, commit=True)
        except:
            pass  # Column already exists
        
        execute_query("""
            UPDATE users SET stripe_customer_id = ? WHERE user_id = ?
        """, (customer_id, user_id), commit=True)
    
    return customer_id


def link_bank_account_to_stripe(plaid_access_token, plaid_account_id, user_id):
    """
    Exchange Plaid token for Stripe bank account token and attach to customer.
    
    This is the key integration point between Plaid and Stripe:
    1. Plaid provides verified bank account info
    2. We exchange it for a Stripe-compatible token
    3. Stripe can now debit this account
    
    Args:
        plaid_access_token: Plaid access token for the linked account
        plaid_account_id: Specific account ID from Plaid
        user_id: PennyWise user ID
        
    Returns:
        dict with bank_account_id and customer_id, or None on error
    """
    if not is_stripe_enabled():
        logger.warning("Stripe not enabled - returning demo bank account")
        return {
            "bank_account_id": f"ba_demo_{user_id}",
            "customer_id": f"cus_demo_{user_id}",
            "demo_mode": True
        }
    
    try:
        import requests
        from core.config import Config
        
        # Step 1: Get Stripe bank account token from Plaid
        # This uses Plaid's processor endpoint to create a Stripe-compatible token
        url = f"{Config.PLAID_BASE_URL}/processor/stripe/bank_account_token/create"
        headers = {"Content-Type": "application/json"}
        data = {
            "client_id": Config.PLAID_CLIENT_ID,
            "secret": Config.PLAID_SECRET,
            "access_token": plaid_access_token,
            "account_id": plaid_account_id
        }
        
        response = requests.post(url, json=data, headers=headers)
        result = response.json()
        
        if "error" in result:
            logger.error(f"Plaid-Stripe token exchange failed: {result['error']}")
            return None
        
        stripe_bank_token = result.get("stripe_bank_account_token")
        
        if not stripe_bank_token:
            logger.error("No Stripe bank token received from Plaid")
            return None
        
        # Step 2: Get or create Stripe customer
        customer_id = get_or_create_stripe_customer(user_id)
        
        if not customer_id:
            logger.error("Failed to get/create Stripe customer")
            return None
        
        # Step 3: Attach bank account to customer
        bank_account = stripe.Customer.create_source(
            customer_id,
            source=stripe_bank_token
        )
        
        logger.info(f"Linked bank account {bank_account.id} to customer {customer_id}")
        
        # Store bank account ID in database
        from database.db_manager import execute_query
        try:
            execute_query("""
                ALTER TABLE accounts ADD COLUMN stripe_bank_account_id TEXT
            """, commit=True)
        except:
            pass  # Column already exists
        
        execute_query("""
            UPDATE accounts 
            SET stripe_bank_account_id = ?
            WHERE account_id = ? AND user_id = ?
        """, (bank_account.id, plaid_account_id, user_id), commit=True)
        
        return {
            "bank_account_id": bank_account.id,
            "customer_id": customer_id,
            "demo_mode": False
        }
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error linking bank account: {e}")
        return None
    except Exception as e:
        logger.error(f"Error linking bank account to Stripe: {e}")
        return None


def charge_bank_account(user_id, amount_cents, description, commitment_id=None):
    """
    Charge the user's linked bank account via ACH.
    
    ACH transfers typically take 3-5 business days to complete.
    In sandbox mode, they complete instantly.
    
    Args:
        user_id: PennyWise user ID
        amount_cents: Amount in cents (e.g., 1000 = $10.00)
        description: Payment description (e.g., "Netflix - Monthly")
        commitment_id: Optional commitment ID for tracking
        
    Returns:
        dict with charge details or None on error
    """
    from database.db_manager import fetch_one
    
    if not is_stripe_enabled():
        logger.warning("Stripe not enabled - simulating charge")
        return {
            "charge_id": f"ch_demo_{commitment_id or 'test'}",
            "amount": amount_cents,
            "status": "succeeded",
            "demo_mode": True
        }
    
    try:
        # Get customer ID
        user = fetch_one("""
            SELECT stripe_customer_id FROM users WHERE user_id = ?
        """, (user_id,))
        
        if not user or not user.get('stripe_customer_id'):
            logger.error(f"No Stripe customer found for user {user_id}")
            return None
        
        customer_id = user['stripe_customer_id']
        
        # Create the charge
        charge = stripe.Charge.create(
            amount=amount_cents,
            currency="usd",
            customer=customer_id,
            description=description,
            metadata={
                "pennywise_user_id": str(user_id),
                "commitment_id": str(commitment_id) if commitment_id else None
            }
        )
        
        logger.info(f"Created charge {charge.id} for ${amount_cents/100:.2f}")
        
        return {
            "charge_id": charge.id,
            "amount": charge.amount,
            "status": charge.status,
            "demo_mode": False
        }
        
    except stripe.error.CardError as e:
        # Bank account declined
        logger.error(f"Bank account declined: {e}")
        return {"error": "Bank account declined", "details": str(e)}
    except stripe.error.StripeError as e:
        logger.error(f"Stripe charge error: {e}")
        return {"error": "Payment failed", "details": str(e)}


def pay_commitment(user_id, commitment_id):
    """
    Pay a commitment using the user's linked bank account.
    
    This is the main function called by the "Pay Now" button.
    It will:
    1. Charge the bank account via Stripe (or simulate in demo mode)
    2. Deduct from the account balance
    3. Create a transaction record
    4. Mark the commitment as paid
    
    Args:
        user_id: PennyWise user ID
        commitment_id: Commitment to pay
        
    Returns:
        dict with payment result including redirect info
    """
    from database.db_manager import fetch_one, fetch_all, execute_query
    from datetime import date
    
    # Helper function to safely get value from sqlite3.Row
    def safe_get(row, key, default=None):
        try:
            if row is None:
                return default
            if key in row.keys():
                return row[key]
            return default
        except:
            return default
    
    # Get commitment details
    commitment = fetch_one("""
        SELECT cc.*, c.category_name, c.category_id
        FROM category_commitments cc
        JOIN categories c ON cc.category_id = c.category_id
        WHERE cc.commitment_id = ? AND cc.user_id = ?
    """, (commitment_id, user_id))
    
    if not commitment:
        return {"error": "Commitment not found"}
    
    # Check if already paid using safe_get
    if safe_get(commitment, 'is_paid', 0) == 1:
        return {"error": "Commitment already paid"}
    
    amount = commitment['amount']
    category_name = commitment['category_name']
    category_id = commitment['category_id']
    amount_cents = int(amount * 100)
    
    # Get primary account for balance deduction
    primary_account = fetch_one("""
        SELECT id, account_id, simulated_balance, bank_name
        FROM accounts
        WHERE user_id = ? AND account_type = 'salary' AND is_primary = 1
    """, (user_id,))
    
    if not primary_account:
        return {"error": "No primary account linked. Please link a bank account first."}
    
    account_id = primary_account['id']
    
    # Charge the bank account via Stripe
    result = charge_bank_account(
        user_id=user_id,
        amount_cents=amount_cents,
        description=f"{category_name} - Monthly Payment",
        commitment_id=commitment_id
    )
    
    if result and not result.get('error'):
        # 1. Deduct from simulated balance
        current_balance = safe_get(primary_account, 'simulated_balance')
        if current_balance is not None:
            new_balance = current_balance - amount
            execute_query("""
                UPDATE accounts SET simulated_balance = ? WHERE id = ?
            """, (new_balance, account_id), commit=True)
        
        # 2. Create transaction record
        today = date.today().isoformat()
        charge_id = result.get('charge_id', 'N/A')
        
        execute_query("""
            INSERT INTO transactions (
                user_id, account_id, category_id, amount, 
                transaction_type, description, date, 
                plaid_transaction_id, source
            ) VALUES (?, ?, ?, ?, 'expense', ?, ?, ?, 'stripe_payment')
        """, (
            user_id, 
            account_id, 
            category_id, 
            amount, 
            f"{category_name} - Payment (Stripe: {charge_id})",
            today,
            charge_id  # Use charge_id as plaid_transaction_id for tracking
        ), commit=True)
        
        # 3. Mark commitment as paid
        execute_query("""
            UPDATE category_commitments
            SET is_paid = 1, last_paid_date = CURRENT_TIMESTAMP
            WHERE commitment_id = ? AND user_id = ?
        """, (commitment_id, user_id), commit=True)
        
        # 4. Add notification
        execute_query("""
            INSERT INTO notifications (user_id, content, notification_type, created_at)
            VALUES (?, ?, 'payment', CURRENT_TIMESTAMP)
        """, (user_id, f"💳 Payment of ${amount:.2f} for {category_name} processed!"), commit=True)
        
        result['commitment_paid'] = True
        result['category_name'] = category_name
        result['amount'] = amount
        result['redirect_to_transactions'] = True
        
    return result


def get_payment_status(charge_id):
    """
    Check the status of a payment/charge.
    
    ACH payments can have these statuses:
    - pending: Payment initiated, waiting for bank
    - succeeded: Payment completed
    - failed: Payment failed
    
    Args:
        charge_id: Stripe charge ID
        
    Returns:
        Payment status string
    """
    if not is_stripe_enabled() or charge_id.startswith("ch_demo"):
        return "succeeded"  # Demo mode always succeeds
    
    try:
        charge = stripe.Charge.retrieve(charge_id)
        return charge.status
    except stripe.error.StripeError as e:
        logger.error(f"Error retrieving charge status: {e}")
        return "unknown"
