#!/usr/bin/env python3
"""
fix_self_bot_balance.py - Diagnostic and fix script for Self Bot balance issues

This script tests the SSID in the current configuration and applies a fix
to the self_bot.py file to correctly retrieve the balance.
"""

import os
import sys
import json
import time
import asyncio
import urllib.parse
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("fix_self_bot_balance.log")
    ]
)
logger = logging.getLogger(__name__)

# Add the PocketOptionAPI-v2 directory to the path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'PocketOptionAPI-v2'))

try:
    from pocketoptionapi.stable_api import PocketOption
    import pocketoptionapi.global_value as global_value
except ImportError as e:
    logger.error(f"Error: pocketoptionapi package not found or cannot be imported: {str(e)}")
    logger.error("Make sure you're running this script from the correct directory.")
    sys.exit(1)

async def test_ssid_async(ssid, use_demo=False):
    """
    Test the SSID value asynchronously using the same approach as test_ssid_direct.py.
    
    Args:
        ssid: The SSID value to test
        use_demo: Whether to use the demo account
        
    Returns:
        dict: Test results including connection status, balance, and any errors
    """
    result = {
        "connection_status": False,
        "balance": None,
        "error": None
    }
    
    try:
        # Reset global values
        global_value.websocket_is_connected = False
        global_value.balance = None
        global_value.balance_updated = False
        
        # Create API instance
        api = PocketOption(ssid=ssid, demo=use_demo)
        
        # Try to connect
        logger.info("Connecting to Pocket Option API...")
        connection_result = api.connect()
        
        # Wait for connection to establish
        await asyncio.sleep(3)
        
        # Check connection status
        if api.check_connect():
            result["connection_status"] = True
            logger.info("Successfully connected to Pocket Option API")
            
            # Wait for balance to update with a polling approach
            logger.info("Checking account balance (this may take up to 20 seconds)...")
            
            start_time = time.time()
            while time.time() - start_time < 20:  # Wait up to 20 seconds
                balance = api.get_balance()
                if balance is not None:
                    result["balance"] = balance
                    logger.info(f"Successfully retrieved balance: {balance}")
                    break
                await asyncio.sleep(0.5)
            
            if result["balance"] is None:
                result["error"] = "Could not retrieve balance after 20 seconds. SSID may be invalid or expired."
                logger.warning(result["error"])
        else:
            result["error"] = "Failed to connect to Pocket Option API"
            logger.error(result["error"])
        
        # Disconnect
        try:
            api.disconnect()
        except Exception as e:
            logger.warning(f"Error during disconnection: {str(e)}")
        
    except Exception as e:
        result["error"] = str(e)
        logger.error(f"Error testing SSID: {str(e)}")
        
    return result

def apply_fix_to_self_bot():
    """
    Apply the fix to self_bot.py to correctly retrieve the balance.
    This function will replace the initialize_pocket_option method 
    with a version that uses a polling approach similar to test_ssid_direct.py.
    """
    file_path = "self_bot.py"
    
    try:
        # Read the current content of self_bot.py
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Find the initialize_pocket_option method
        method_start = content.find("    def initialize_pocket_option")
        if method_start == -1:
            logger.error("Could not find initialize_pocket_option method in self_bot.py")
            return False
        
        # Find the start of the next method
        method_end = content.find("    def ", method_start + 10)
        if method_end == -1:
            logger.error("Could not find the end of initialize_pocket_option method")
            return False
        
        # Extract the original method indentation
        lines = content[method_start:method_end].split('\n')
        indentation = ""
        for line in lines:
            if line.strip() and not line.strip().startswith("def"):
                indentation = line[:len(line) - len(line.lstrip())]
                break
        
        # Create the new method
        new_method = """    def initialize_pocket_option(self) -> bool:
        \"\"\"
        Initialize the Pocket Option API client using PocketOptionAPI-v2.
        
        Returns:
            True if initialized successfully, False otherwise
        \"\"\"
        try:
            # Get SSID from config
            ssid = self.pocket_option_config.get("ssid")
            if not ssid:
                logger.error("No SSID provided in configuration")
                return False
            
            # Get demo mode setting
            is_demo = self.pocket_option_config.get("is_demo", True)
            
            # Initialize the PocketOption client
            logger.info(f"Initializing Pocket Option client (Demo mode: {is_demo})")
            self.pocket_option_client = PocketOption(ssid, is_demo)
            
            # Connect to the API
            connection_result = self.pocket_option_client.connect()
            if connection_result:
                logger.info("Successfully connected to Pocket Option API")
                
                # Get account balance with polling approach
                logger.info("Checking account balance (this may take up to 20 seconds)...")
                
                # Wait for the balance to be updated
                balance = None
                max_attempts = 40  # 20 seconds with 0.5 second intervals
                for attempt in range(max_attempts):
                    balance = self.pocket_option_client.get_balance()
                    if balance is not None:
                        logger.info(f"Account balance: {balance}")
                        return True
                    
                    # Wait and try again
                    time.sleep(0.5)
                
                logger.error("Failed to retrieve account balance after multiple attempts")
                return False
            else:
                logger.error("Failed to connect to Pocket Option API")
                return False
        except Exception as e:
            logger.error(f"Error initializing Pocket Option client: {str(e)}")
            return False
"""
        
        # Replace the method in the content
        new_content = content[:method_start] + new_method + content[method_end:]
        
        # Create a backup of the original file
        backup_path = f"{file_path}.bak"
        with open(backup_path, 'w') as f:
            f.write(content)
            logger.info(f"Created backup of original file at {backup_path}")
        
        # Write the new content
        with open(file_path, 'w') as f:
            f.write(new_content)
            logger.info(f"Applied fix to {file_path}")
        
        return True
    except Exception as e:
        logger.error(f"Error applying fix to self_bot.py: {str(e)}")
        return False

async def main():
    print("\nSelf Bot Balance Fix Utility")
    print("---------------------------")
    
    # First, test the SSID from the current configuration
    try:
        with open("config/pocket_option_config.json", 'r') as f:
            config = json.load(f)
            
        ssid = config.get("ssid")
        is_demo = config.get("is_demo", False)
        
        if not ssid:
            print("No SSID found in configuration. Please update your configuration first.")
            return
            
        print(f"\nTesting SSID from configuration (Demo mode: {is_demo})...")
        result = await test_ssid_async(ssid, is_demo)
        
        print("\n" + "="*60)
        print("SSID TEST RESULTS")
        print("="*60)
        
        print(f"\nConnection:     {'✅ Success' if result['connection_status'] else '❌ Failed'}")
        
        if result['balance'] is not None:
            print(f"Balance:        {result['balance']}")
        else:
            print("Balance:        ❌ Not available")
            
        if result['error']:
            print(f"Error:          {result['error']}")
        
        print("\n" + "="*60)
        
        # If the SSID is working, apply the fix
        if result['connection_status'] and result['balance'] is not None:
            print("\nSSID is valid and working correctly.")
            
            # Ask whether to apply the fix
            apply_fix = input("\nDo you want to apply the fix to self_bot.py? (y/n): ").strip().lower()
            
            if apply_fix == 'y':
                if apply_fix_to_self_bot():
                    print("\n✅ Fix applied successfully to self_bot.py")
                    print("You can now run self_bot.py to test the fix.")
                else:
                    print("\n❌ Failed to apply fix to self_bot.py")
            else:
                print("\nFix not applied. You can run this script again later if needed.")
        else:
            print("\nSSID test failed. Please get a fresh SSID and update your configuration before applying the fix.")
            print("\nTo get a new SSID:")
            print("1. Log in to your Pocket Option account in a web browser")
            print("2. Open the browser's developer tools (F12 or right-click > Inspect)")
            print("3. Go to the Application tab > Cookies > pocketoption.com")
            print("4. Find the 'ssid' cookie and copy its value")
    except Exception as e:
        print(f"\nError: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
