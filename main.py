#!/usr/bin/env python3
"""
PennyWise Application Entry Point
Redirects to app_main.py for the new flow
"""
import sys
import os

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