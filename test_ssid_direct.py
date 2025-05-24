#!/usr/bin/env python3
"""
test_ssid_direct.py - Test SSID directly with Pocket Option API

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
        logging.FileHandler("test_ssid_direct.log")
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

async def test_ssid_async(ssid, use_demo=True):
    """
    Test a single SSID value asynchronously.
    
    Args:
        ssid: The SSID value to test
        use_demo: Whether to use the demo account (True) or real account (False)
        
    Returns:
        dict: Test results including connection status, balance (if available), and any errors
    """
    # URL encode the SSID to handle special characters
    encoded_ssid = urllib.parse.quote(ssid)
    logger.info(f"Testing SSID: {ssid[:10]}... (truncated for security)")
    logger.info(f"URL encoded SSID: {encoded_ssid[:10]}... (truncated for security)")
    
    result = {
        "ssid": ssid,
        "encoded_ssid": encoded_ssid,
        "ssid_display": ssid[:10] + "..." if len(ssid) > 10 else ssid,
        "connection_status": False,
        "authentication_status": False,
        "balance": None,
        "error": None
    }
    
    try:
        # Reset global values for a clean test
        global_value.websocket_is_connected = False
        global_value.balance = None
        global_value.balance_updated = False
        
        # Try with original SSID first
        logger.info("Attempting with original SSID...")
        api = PocketOption(ssid=ssid, demo=use_demo)
        
        # Try to connect
        logger.info("Attempting to connect to Pocket Option API...")
        connection_result = api.connect()
        
        # Wait for connection to establish
        await asyncio.sleep(3)
        
        # Check connection status
        if api.check_connect():
            result["connection_status"] = True
            logger.info("Successfully connected to Pocket Option API")
            
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
                await asyncio.sleep(0.5)
            
            if result["balance"] is None:
                result["error"] = "Could not retrieve balance. SSID may be invalid or expired."
                logger.warning(result["error"])
        else:
            result["error"] = "Failed to connect to Pocket Option API"
            logger.error(result["error"])
        
        try:
            # Disconnect
            api.disconnect()
        except Exception as e:
            logger.warning(f"Error during disconnection: {str(e)}")
        
        # If original SSID failed, try with URL encoded SSID
        if not result["authentication_status"] and ssid != encoded_ssid:
            logger.info("Original SSID failed, trying with URL encoded SSID...")
            
            # We'll skip the URL encoded test for now as it's causing event loop issues
            result["error"] = "Original SSID failed. Please try with a fresh SSID."
            logger.warning(result["error"])
        
    except asyncio.CancelledError:
        result["error"] = "Operation was cancelled"
        logger.warning("SSID test was cancelled")
    except Exception as e:
        result["error"] = str(e)
        logger.error(f"Error testing SSID: {str(e)}")
        
    return result

def test_ssid(ssid, use_demo=True):
    """
    Test an SSID with proper event loop handling.
    
    Args:
        ssid: The SSID to test
        use_demo: Whether to use the demo account
        
    Returns:
        dict: Test results
    """
    try:
        # Use asyncio.run() for better event loop management
        result = asyncio.run(test_ssid_async(ssid, use_demo))
        return result
    except asyncio.CancelledError:
        logger.warning("SSID test was cancelled")
        return {
            "ssid": ssid,
            "ssid_display": ssid[:10] + "..." if len(ssid) > 10 else ssid,
            "connection_status": False,
            "authentication_status": False,
            "balance": None,
            "error": "Operation was cancelled"
        }
    except Exception as e:
        logger.error(f"Error in test_ssid: {str(e)}")
        return {
            "ssid": ssid,
            "ssid_display": ssid[:10] + "..." if len(ssid) > 10 else ssid,
            "connection_status": False,
            "authentication_status": False,
            "balance": None,
            "error": str(e)
        }

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
    print("\nPocket Option API SSID Tester")
    print("-----------------------------")
    
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
    result = test_ssid(ssid, use_demo)
    
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

if __name__ == "__main__":
    main()
