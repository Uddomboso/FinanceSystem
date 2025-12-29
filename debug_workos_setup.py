"""
Debug script for WorkOS authentication setup
Tests .env loading, variable access, and WorkOS client initialization
"""

import os
import sys
import json
from datetime import datetime

# Log file path
LOG_PATH = r"c:\Users\asus\OneDrive\Desktop\PennyWise\.cursor\debug.log"

def debug_log(session_id, run_id, hypothesis_id, location, message, data=None):
    """Write debug log entry"""
    try:
        log_entry = {
            "sessionId": session_id,
            "runId": run_id,
            "hypothesisId": hypothesis_id,
            "location": location,
            "message": message,
            "timestamp": int(datetime.now().timestamp() * 1000),
            "data": data or {}
        }
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception as e:
        print(f"Failed to write log: {e}")

def mask_sensitive(value):
    """Mask sensitive values for display"""
    if not value:
        return "None"
    if len(value) <= 8:
        return "***"
    return value[:4] + "..." + value[-4:]

def main():
    session_id = "debug-workos-setup"
    run_id = "run1"
    
    print("=" * 60)
    print("WorkOS Authentication Setup Debug")
    print("=" * 60)
    print()
    
    # Hypothesis A: .env file not found or not loading
    print("[HYPOTHESIS A] Testing .env file loading...")
    debug_log(session_id, run_id, "A", "debug_workos_setup.py:main", "Starting .env load test", {})
    
    try:
        from dotenv import load_dotenv
        debug_log(session_id, run_id, "A", "debug_workos_setup.py:main", "dotenv imported successfully", {})
        
        # Check if .env file exists
        env_exists = os.path.exists(".env")
        debug_log(session_id, run_id, "A", "debug_workos_setup.py:main", ".env file check", {"exists": env_exists})
        print(f"  .env file exists: {env_exists}")
        
        if env_exists:
            # Try to load .env
            result = load_dotenv()
            debug_log(session_id, run_id, "A", "debug_workos_setup.py:main", "load_dotenv() called", {"result": result})
            print(f"  load_dotenv() result: {result}")
        else:
            print("  ⚠️  .env file not found in current directory")
            debug_log(session_id, run_id, "A", "debug_workos_setup.py:main", ".env file missing", {})
    except ImportError as e:
        print(f"  ✗ Failed to import dotenv: {e}")
        debug_log(session_id, run_id, "A", "debug_workos_setup.py:main", "dotenv import failed", {"error": str(e)})
        return
    except Exception as e:
        print(f"  ✗ Error loading .env: {e}")
        debug_log(session_id, run_id, "A", "debug_workos_setup.py:main", "load_dotenv error", {"error": str(e)})
        return
    
    print()
    
    # Hypothesis B: Environment variables not set
    print("[HYPOTHESIS B] Testing environment variable access...")
    
    # Test direct os.getenv
    api_key_direct = os.getenv("WORKOS_API_KEY")
    client_id_direct = os.getenv("WORKOS_CLIENT_ID")
    redirect_url_direct = os.getenv("WORKOS_REDIRECT_URL")
    
    debug_log(session_id, run_id, "B", "debug_workos_setup.py:main", "Direct os.getenv() values", {
        "api_key_set": bool(api_key_direct),
        "api_key_length": len(api_key_direct) if api_key_direct else 0,
        "client_id_set": bool(client_id_direct),
        "client_id_length": len(client_id_direct) if client_id_direct else 0,
        "redirect_url": redirect_url_direct or "None"
    })
    
    print(f"  WORKOS_API_KEY (direct): {mask_sensitive(api_key_direct) if api_key_direct else 'None'}")
    print(f"  WORKOS_CLIENT_ID (direct): {mask_sensitive(client_id_direct) if client_id_direct else 'None'}")
    print(f"  WORKOS_REDIRECT_URL (direct): {redirect_url_direct or 'None'}")
    
    # Test via Config class
    try:
        from core.config import Config
        debug_log(session_id, run_id, "B", "debug_workos_setup.py:main", "Config class imported", {})
        
        api_key_config = Config.WORKOS_API_KEY
        client_id_config = Config.WORKOS_CLIENT_ID
        redirect_url_config = Config.WORKOS_REDIRECT_URL
        
        debug_log(session_id, run_id, "B", "debug_workos_setup.py:main", "Config class values", {
            "api_key_set": bool(api_key_config),
            "api_key_length": len(api_key_config) if api_key_config else 0,
            "client_id_set": bool(client_id_config),
            "client_id_length": len(client_id_config) if client_id_config else 0,
            "redirect_url": redirect_url_config or "None"
        })
        
        print(f"  WORKOS_API_KEY (Config): {mask_sensitive(api_key_config) if api_key_config else 'None'}")
        print(f"  WORKOS_CLIENT_ID (Config): {mask_sensitive(client_id_config) if client_id_config else 'None'}")
        print(f"  WORKOS_REDIRECT_URL (Config): {redirect_url_config or 'None'}")
        
        # Check if values match
        values_match = (
            api_key_direct == api_key_config and
            client_id_direct == client_id_config and
            redirect_url_direct == redirect_url_config
        )
        debug_log(session_id, run_id, "B", "debug_workos_setup.py:main", "Value comparison", {"values_match": values_match})
        
    except Exception as e:
        print(f"  ✗ Error accessing Config class: {e}")
        debug_log(session_id, run_id, "B", "debug_workos_setup.py:main", "Config access error", {"error": str(e)})
    
    print()
    
    # Hypothesis C: WorkOS package not installed
    print("[HYPOTHESIS C] Testing WorkOS package import...")
    
    try:
        from workos import WorkOSClient
        debug_log(session_id, run_id, "C", "debug_workos_setup.py:main", "WorkOS import successful", {})
        print("  ✓ WorkOS package imported successfully")
        
        # Check WorkOS class attributes
        has_sso = hasattr(WorkOSClient, 'sso') or hasattr(WorkOSClient(None), 'sso')
        debug_log(session_id, run_id, "C", "debug_workos_setup.py:main", "WorkOS class check", {"has_sso": has_sso})
        
    except ImportError as e:
        print(f"  ✗ WorkOS package not installed: {e}")
        debug_log(session_id, run_id, "C", "debug_workos_setup.py:main", "WorkOS import failed", {"error": str(e)})
        print("  Install with: pip install workos")
        return
    except Exception as e:
        print(f"  ✗ Error importing WorkOS: {e}")
        debug_log(session_id, run_id, "C", "debug_workos_setup.py:main", "WorkOS import error", {"error": str(e)})
        return
    
    print()
    
    # Hypothesis D: WorkOS client initialization fails
    print("[HYPOTHESIS D] Testing WorkOS client initialization...")
    
    api_key = api_key_direct or api_key_config if 'api_key_config' in locals() else api_key_direct
    client_id = client_id_direct or client_id_config if 'client_id_config' in locals() else client_id_direct
    
    if not api_key:
        print("  ✗ Cannot initialize: WORKOS_API_KEY is not set")
        debug_log(session_id, run_id, "D", "debug_workos_setup.py:main", "API key missing", {})
        return
    
    if not client_id:
        print("  ✗ Cannot initialize: WORKOS_CLIENT_ID is not set")
        debug_log(session_id, run_id, "D", "debug_workos_setup.py:main", "Client ID missing", {})
        return
    
    debug_log(session_id, run_id, "D", "debug_workos_setup.py:main", "Before WorkOS initialization", {
        "api_key_length": len(api_key),
        "api_key_prefix": api_key[:4] if len(api_key) >= 4 else "short",
        "client_id_set": bool(client_id)
    })
    
    try:
        client = WorkOSClient(api_key=api_key, client_id=client_id)
        debug_log(session_id, run_id, "D", "debug_workos_setup.py:main", "WorkOS client initialized", {
            "client_type": str(type(client)),
            "has_sso": hasattr(client, 'sso')
        })
        print("  ✓ WorkOS client initialized successfully")
        
        # Test if sso attribute exists
        if hasattr(client, 'sso'):
            print("  ✓ WorkOS client has 'sso' attribute")
            debug_log(session_id, run_id, "D", "debug_workos_setup.py:main", "SSO attribute check", {"exists": True})
            
            # Test if get_authorization_url method exists
            if hasattr(client.sso, 'get_authorization_url'):
                print("  ✓ WorkOS client.sso.get_authorization_url() method exists")
                debug_log(session_id, run_id, "D", "debug_workos_setup.py:main", "get_authorization_url method check", {"exists": True})
            else:
                print("  ⚠️  WorkOS client.sso.get_authorization_url() method not found")
                debug_log(session_id, run_id, "D", "debug_workos_setup.py:main", "get_authorization_url method missing", {})
            
            # Test if get_profile_and_token method exists
            if hasattr(client.sso, 'get_profile_and_token'):
                print("  ✓ WorkOS client.sso.get_profile_and_token() method exists")
                debug_log(session_id, run_id, "D", "debug_workos_setup.py:main", "get_profile_and_token method check", {"exists": True})
            else:
                print("  ⚠️  WorkOS client.sso.get_profile_and_token() method not found")
                debug_log(session_id, run_id, "D", "debug_workos_setup.py:main", "get_profile_and_token method missing", {})
        else:
            print("  ⚠️  WorkOS client does not have 'sso' attribute")
            debug_log(session_id, run_id, "D", "debug_workos_setup.py:main", "SSO attribute missing", {})
        
    except Exception as e:
        print(f"  ✗ Failed to initialize WorkOS client: {e}")
        debug_log(session_id, run_id, "D", "debug_workos_setup.py:main", "WorkOS initialization failed", {
            "error": str(e),
            "error_type": type(e).__name__
        })
        import traceback
        traceback.print_exc()
        return
    
    print()
    
    # Hypothesis E: WorkOSAuthenticator initialization
    print("[HYPOTHESIS E] Testing WorkOSAuthenticator initialization...")
    
    try:
        from core.workos_auth import get_workos_authenticator
        debug_log(session_id, run_id, "E", "debug_workos_setup.py:main", "WorkOSAuthenticator imported", {})
        
        authenticator = get_workos_authenticator()
        debug_log(session_id, run_id, "E", "debug_workos_setup.py:main", "WorkOSAuthenticator retrieved", {
            "authenticator_type": str(type(authenticator))
        })
        
        is_configured = authenticator.is_configured()
        debug_log(session_id, run_id, "E", "debug_workos_setup.py:main", "is_configured() check", {
            "is_configured": is_configured,
            "has_workos": authenticator.workos is not None,
            "has_api_key": bool(authenticator.api_key),
            "has_client_id": bool(authenticator.client_id)
        })
        
        if is_configured:
            print("  ✓ WorkOSAuthenticator is configured")
            print(f"  ✓ WorkOS client available: {authenticator.workos is not None}")
        else:
            print("  ✗ WorkOSAuthenticator is not configured")
            print(f"    - WorkOS client: {authenticator.workos is not None}")
            print(f"    - API Key set: {bool(authenticator.api_key)}")
            print(f"    - Client ID set: {bool(authenticator.client_id)}")
        
    except Exception as e:
        print(f"  ✗ Error testing WorkOSAuthenticator: {e}")
        debug_log(session_id, run_id, "E", "debug_workos_setup.py:main", "WorkOSAuthenticator test error", {"error": str(e)})
        import traceback
        traceback.print_exc()
    
    print()
    print("=" * 60)
    print("Debug Summary")
    print("=" * 60)
    print("Check the log file for detailed information:")
    print(f"  {LOG_PATH}")
    print()

if __name__ == "__main__":
    main()

