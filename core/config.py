import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Central configuration management for PennyWise"""

    # API Keys
    GROQ_API_KEY = os.getenv("GROQ_API_KEY","demo_mode")
    PLAID_CLIENT_ID = os.getenv("PLAID_CLIENT_ID","demo_plaid_id")
    PLAID_SECRET = os.getenv("PLAID_SECRET","demo_plaid_secret")
    
    # Stripe API Keys (for ACH payments)
    STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "sk_test_demo")
    STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY", "pk_test_demo")

    # Feature Flags
    # DEMO_MODE is True only if BOTH Plaid AND GROQ are in demo mode
    PLAID_IN_DEMO = PLAID_CLIENT_ID == "demo_plaid_id" or PLAID_SECRET == "demo_plaid_secret"
    GROQ_IN_DEMO = GROQ_API_KEY == "demo_mode"
    STRIPE_IN_DEMO = STRIPE_SECRET_KEY == "sk_test_demo" or STRIPE_SECRET_KEY.startswith("sk_test_demo")
    DEMO_MODE = PLAID_IN_DEMO and GROQ_IN_DEMO
    PLAID_ENABLED = not PLAID_IN_DEMO
    STRIPE_ENABLED = not STRIPE_IN_DEMO

    # App Settings
    APP_NAME = "PennyWise v2"
    VERSION = "2.0.0"

    # API Endpoints
    GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
    PLAID_BASE_URL = os.getenv("PLAID_BASE_URL", "https://sandbox.plaid.com")
    
    # Plaid Webhook Endpoints (for sandbox testing)
    # Use /sandbox/transfer/fire_webhook for transfer-related webhooks (transfer completed, failed, etc.)
    # Use /sandbox/transactions/fire_webhook for transaction-related webhooks (new transactions detected)
    # Use /sandbox/item/fire_webhook for item-level webhooks (item status changes, re-authentication needed)
    PLAID_SANDBOX_TRANSFER_WEBHOOK_ENDPOINT = "/sandbox/transfer/fire_webhook"
    PLAID_SANDBOX_TRANSACTIONS_WEBHOOK_ENDPOINT = "/sandbox/transactions/fire_webhook"
    PLAID_SANDBOX_ITEM_WEBHOOK_ENDPOINT = "/sandbox/item/fire_webhook"

    @classmethod
    def validate_config(cls):
        """Validate configuration and provide helpful messages"""
        if cls.DEMO_MODE:
            print("🔧 Running in DEMO MODE - using mock data and AI tips")
            return True

        # Check what's configured
        plaid_ok = not cls.PLAID_IN_DEMO
        groq_ok = not cls.GROQ_IN_DEMO
        
        if plaid_ok:
            print("✅ Plaid API configured")
        else:
            print("⚠️  Plaid API not configured - using mock bank data")
        
        if groq_ok:
            print("✅ AI features enabled")
        else:
            print("⚠️  GROQ API not configured - AI features disabled")

        print("✅ Configuration validated - Running in LIVE MODE")
        return True

    @classmethod
    def get_mode_info(cls):
        """Get current mode information"""
        return {
            "demo_mode": cls.DEMO_MODE,
            "plaid_enabled": cls.PLAID_ENABLED,
            "ai_enabled": not cls.DEMO_MODE
        }