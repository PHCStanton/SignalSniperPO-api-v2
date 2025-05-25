#!/usr/bin/env python3
"""
test_ssid_fixed.py - Fixed SSID test with proper event loop handling

This script tests a provided SSID with the Pocket Option API
and provides detailed output about the authentication process.
"""

import os
import sys
import json
import time
import logging
import asyncio
import urllib.parse
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("test_ssid_fixed.log")
    ]
)
logger = logging.getLogger(__name__)

# Add the PocketOptionAPI-v2 directory to the path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'PocketOptionAPI-v2'))

try:
    # Try to import from stable_api first
    try:
        from pocketoptionapi.stable_api import PocketOption
        import pocketoptionapi.global_value as global_value
        logger.info("Successfully imported PocketOption from pocketoptionapi.stable_api")
    except ImportError as e1:
        logger.warning(f"Could not import from pocketoptionapi.stable_api: {str(e1)}")
        # If that fails, try to import from api
        try:
            from pocketoptionapi.api import PocketOption
            import pocketoptionapi.global_value as global_value
            logger.info("Successfully imported PocketOption from pocketoptionapi.api")
        except ImportError as e2:
            logger.warning(f"Could not import from pocketoptionapi.api: {str(e2)}")
            raise ImportError("Failed to import PocketOption from both stable_api and api modules")
except ImportError as e:
    logger.error(f"Error: pocketoptionapi package not found or cannot be imported: {str(e)}")
    logger.error("Make sure you're running this script from the correct directory.")
    sys.exit(1)

def test_ssid_sync(ssid, use_demo=True):
    """
    Test a single SSID value synchronously with proper cleanup.
    
    Args:
        ssid: The SSID value to test
        use_demo: Whether to use the demo account (True) or real account (False)
        
    Returns:
        dict: Test results including connection status, balance (if available), and any errors
    """
    logger.info(f"Testing SSID: {ssid[:10]}... (truncated for security)")
    
    result = {
        "ssid": ssid,
        "ssid_display": ssid[:10] + "..." if len(ssid) > 10 else ssid,
        "connection_status": False,
        "authentication_status": False,
        "balance": None,
        "error": None
    }
    
    api = None
    
    try:
        # Reset global values for a clean test
        global_value.websocket_is_connected = False
        global_value.balance = None
        global_value.balance_updated = False
        
        # Create API instance
        logger.info("Creating PocketOption API instance...")
        api = PocketOption(ssid=ssid, demo=use_demo)
        
        # Try to connect
        logger.info("Attempting to connect to Pocket Option API...")
        connection_result = api.connect()
        
        if not connection_result:
            result["error"] = "Failed to start connection"
            logger.error(result["error"])
            return result
        
        # Wait for connection to establish
        logger.info("Waiting for connection to establish...")
        start_time = time.time()
        while time.time() - start_time < 15:  # Wait up to 15 seconds
            if api.check_connect():
                result["connection_status"] = True
                logger.info("Successfully connected to Pocket Option API")
                break
            time.sleep(0.5)
        
        if not result["connection_status"]:
            result["error"] = "Connection timeout - could not establish websocket connection"
            logger.error(result["error"])
            return result
        
        # Try to get balance to verify authentication
        logger.info("Checking account balance...")
        
        # Wait for balance to update with a longer timeout
        start_time = time.time()
        while time.time() - start_time < 20:  # Wait up to 20 seconds
            balance = api.get_balance()
            if balance is not None:
                result["authentication_status"] = True
                result["balance"] = balance
                logger.info(f"Successfully authenticated. Balance: {balance}")
                break
            time.sleep(0.5)
        
        if result["balance"] is None:
            result["error"] = "Could not retrieve balance. SSID may be invalid or expired."
            logger.warning(result["error"])
        
    except Exception as e:
        result["error"] = str(e)
        logger.error(f"Error testing SSID: {str(e)}")
        
    finally:
        # Clean disconnect
        if api:
            try:
                logger.info("Disconnecting from API...")
                api.disconnect()
                time.sleep(1)  # Give time for cleanup
            except Exception as e:
                logger.warning(f"Error during disconnection: {str(e)}")
        
    return result

def load_ssid_from_config():
    """
    Load SSID from the configuration file.
    
    Returns:
        tuple: (ssid, use_demo) or (None, None) if not found
    """
    config_path = "config/pocket_option_config.json"
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        ssid = config.get('ssid')
        is_demo = config.get('is_demo', True)
        
        if ssid:
            logger.info(f"Loaded SSID from config: {ssid[:10]}...")
            return ssid, is_demo
        else:
            logger.warning("No SSID found in configuration file")
            return None, None
            
    except FileNotFoundError:
        logger.warning(f"Configuration file not found: {config_path}")
        return None, None
    except Exception as e:
        logger.error(f"Error reading configuration file: {str(e)}")
        return None, None

def update_config(valid_ssid):
    """
    Update the pocket_option_config.json file with the valid SSID.
    
    Args:
        valid_ssid: The valid SSID to save to the configuration file
    """
    config_path = "config/pocket_option_config.json"
    
    try:
        # Read the current configuration
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Update the SSID
        config['ssid'] = valid_ssid
        
        # Write the updated configuration
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.info(f"Successfully updated {config_path} with the valid SSID")
        print(f"\n✅ Successfully updated {config_path} with the valid SSID")
    except Exception as e:
        logger.error(f"Error updating configuration file: {str(e)}")
        print(f"\n❌ Error updating configuration file: {str(e)}")
        print("Please manually update the SSID in your configuration file.")

def main():
    print("\nPocket Option API SSID Tester (Fixed Version)")
    print("---------------------------------------------")
    
    # Try to load SSID from config first
    config_ssid, config_demo = load_ssid_from_config()
    
    if config_ssid:
        print(f"\nFound SSID in config file: {config_ssid[:10]}...")
        use_config = input("Use this SSID? (y/n, default: y): ").strip().lower()
        
        if use_config != 'n':
            ssid = config_ssid
            use_demo = config_demo
            print(f"Using SSID from config file")
        else:
            # Get SSID from user
            print("\nPlease enter the SSID to test:")
            ssid = input("SSID: ").strip()
            
            if not ssid:
                print("SSID is required. Exiting.")
                return
            
            # Ask if using demo account
            use_demo_input = input("Are you using a demo account? (y/n, default: y): ").strip().lower()
            use_demo = use_demo_input != 'n'
    else:
        # Get SSID from user
        print("\nPlease enter the SSID to test:")
        ssid = input("SSID: ").strip()
        
        if not ssid:
            print("SSID is required. Exiting.")
            return
        
        # Ask if using demo account
        use_demo_input = input("Are you using a demo account? (y/n, default: y): ").strip().lower()
        use_demo = use_demo_input != 'n'
    
    print(f"Using {'demo' if use_demo else 'real'} account")
    
    # Test the SSID
    result = test_ssid_sync(ssid, use_demo)
    
    # Print results
    print("\n" + "="*60)
    print("POCKET OPTION API SSID TEST RESULTS")
    print("="*60)
    
    print(f"\nSSID: {result['ssid_display']}")
    print(f"  Connection:     {'✅ Success' if result['connection_status'] else '❌ Failed'}")
    print(f"  Authentication: {'✅ Success' if result['authentication_status'] else '❌ Failed'}")
    
    if result['balance'] is not None:
        print(f"  Balance:        {result['balance']}")
        
    if result['error']:
        print(f"  Error:          {result['error']}")
    
    print("\n" + "="*60)
    
    # Update config if SSID is valid
    if result['authentication_status']:
        print("\n✅ SSID is valid!")
        if not config_ssid or config_ssid != result['ssid']:
            update_config_input = input("Would you like to update your configuration with this SSID? (y/n): ").strip().lower()
            if update_config_input == 'y':
                update_config(result['ssid'])
    else:
        print("\n❌ SSID is invalid or expired.")
        print("Please obtain a new SSID from your Pocket Option account.")
        print("\nTo get a new SSID:")
        print("1. Log in to your Pocket Option account in a web browser")
        print("2. Open the browser's developer tools (F12 or right-click > Inspect)")
        print("3. Go to the Application tab > Cookies > pocketoption.com")
        print("4. Find the 'ssid' cookie and copy its value")
        print("5. The SSID should be a 32-character hexadecimal string (like: 9b74fb8898f0ae9a9ef9e07f6d4ec399)")

if __name__ == "__main__":
    main()
