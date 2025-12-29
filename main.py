#!/usr/bin/env python3
"""
PennyWise Application Entry Point
Loads .env file before any other imports
"""
import sys
import os
from pathlib import Path

# Load .env file BEFORE any other imports
# Find .env file relative to this script's location
script_dir = Path(__file__).parent.absolute()
env_path = script_dir / ".env"

if env_path.exists():
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=env_path)
    print(f"✅ Loaded .env from: {env_path}")
else:
    print(f"⚠️  .env file not found at: {env_path}")
    # Try current directory as fallback
    from dotenv import load_dotenv
    load_dotenv()
    print("   Attempted fallback load from current directory")

# Verify WorkOS keys are loaded
print("\n🔍 Verifying WorkOS environment variables:")
api_key = os.getenv("WORKOS_API_KEY", "")
client_id = os.getenv("WORKOS_CLIENT_ID", "")
redirect_url = os.getenv("WORKOS_REDIRECT_URL", "")

if api_key:
    print(f"   ✅ WORKOS_API_KEY: {api_key[:8]}...{api_key[-4:] if len(api_key) > 12 else '***'}")
else:
    print("   ❌ WORKOS_API_KEY: NOT SET")

if client_id:
    print(f"   ✅ WORKOS_CLIENT_ID: {client_id[:8]}...{client_id[-4:] if len(client_id) > 12 else '***'}")
else:
    print("   ❌ WORKOS_CLIENT_ID: NOT SET")

if redirect_url:
    print(f"   ✅ WORKOS_REDIRECT_URL: {redirect_url}")
else:
    print("   ❌ WORKOS_REDIRECT_URL: NOT SET")

print()

def main():
    """Main application entry point - redirects to app_main.py"""
    print("🔧 Starting PennyWise application...")
    print("🔄 Redirecting to app_main.py for new flow...")
    
    # Import and run app_main
    try:
        from app_main import main as app_main
        return app_main()
    except ImportError as e:
        print(f"❌ Failed to import app_main: {e}")
        print("Please ensure app_main.py exists and is properly configured.")
        return 1
    except Exception as e:
        print(f"❌ Error running app_main: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
