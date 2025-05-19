#!/usr/bin/env python3
"""
test_environment.py - Tests the Python environment setup for the Pocket Option Trading Bot.

This script verifies that all required dependencies are installed and working correctly.
"""

import sys
import importlib
import platform

def check_module(module_name):
    """Check if a module is installed and get its version."""
    try:
        module = importlib.import_module(module_name)
        version = getattr(module, '__version__', 'Unknown')
        return True, version
    except ImportError:
        return False, None

def main():
    """Main function to test the environment."""
    print(f"Python Version: {platform.python_version()}")
    print(f"Python Implementation: {platform.python_implementation()}")
    print(f"System: {platform.system()} {platform.release()}")
    print("\nChecking required dependencies:")
    
    # List of required modules from requirements.txt
    required_modules = [
        'telethon',
        'websockets',
        'asyncio',
        'aiohttp',
        'dotenv',
        'pytz'
    ]
    
    all_installed = True
    
    for module_name in required_modules:
        installed, version = check_module(module_name)
        status = "✅ Installed" if installed else "❌ Not installed"
        version_info = f"(version: {version})" if installed and version != 'Unknown' else ""
        print(f"{module_name}: {status} {version_info}")
        
        if not installed:
            all_installed = False
    
    print("\nChecking built-in modules:")
    
    # List of required built-in modules
    builtin_modules = [
        'sqlite3',
        'argparse',
        'statistics'
    ]
    
    for module_name in builtin_modules:
        installed, version = check_module(module_name)
        status = "✅ Available" if installed else "❌ Not available"
        print(f"{module_name}: {status}")
        
        if not installed:
            all_installed = False
    
    # Check if pocketoptionapi is available
    print("\nChecking Pocket Option API module:")
    try:
        sys.path.append('.')  # Add current directory to path
        from pocketoptionapi.api import PocketOptionAPI
        print("pocketoptionapi: ✅ Available")
    except ImportError as e:
        print(f"pocketoptionapi: ❌ Not available ({str(e)})")
        all_installed = False
    
    # Overall result
    print("\nEnvironment check result:")
    if all_installed:
        print("✅ All required dependencies are installed and available.")
        print("The Python environment is set up correctly for the Pocket Option Trading Bot.")
    else:
        print("❌ Some dependencies are missing. Please install them before running the bot.")
    
    return 0 if all_installed else 1

if __name__ == "__main__":
    sys.exit(main())
