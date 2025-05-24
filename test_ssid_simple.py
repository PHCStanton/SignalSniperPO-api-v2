#!/usr/bin/env python3
"""
test_ssid_simple.py - Simple SSID test matching self_bot.py approach

This script tests a provided SSID using the exact same approach as self_bot.py
"""

import os
import sys
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add the PocketOptionAPI-v2 directory to the path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'PocketOptionAPI-v2'))

try:
    from pocketoptionapi.stable_api import PocketOption
    import pocketoptionapi.global_value as global_value
    logger.info("Successfully imported PocketOption from pocketoptionapi.stable_api")
except ImportError as e:
    logger.error(f"Error: pocketoptionapi package not found: {str(e)}")
    sys.exit(1)

def test_ssid_simple(ssid, use_demo=True):
    """
    Test SSID using the exact same approach as self_bot.py
    
    Args:
        ssid: The SSID to test
        use_demo: Whether to use demo account
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info(f"Testing SSID: {ssid[:10]}... (Demo mode: {use_demo})")
        
        # Initialize the PocketOption client exactly like self_bot.py
        api = PocketOption(ssid, use_demo)
        
        # Connect to the API
        logger.info("Attempting to connect...")
        connection_result = api.connect()
        
        if connection_result:
            logger.info("Connection successful!")
            
            # Wait a moment for connection to stabilize
            time.sleep(2)
            
            # Check if we're actually connected
            if api.check_connect():
                logger.info("Connection verified!")
                
                # Try to get balance
                balance = api.get_balance()
                if balance is not None:
                    logger.info(f"✅ SUCCESS! Balance: {balance}")
                    return True
                else:
                    logger.warning("Connected but could not get balance")
                    
                    # Wait a bit longer and try again
                    time.sleep(3)
                    balance = api.get_balance()
                    if balance is not None:
                        logger.info(f"✅ SUCCESS! Balance: {balance}")
                        return True
                    else:
                        logger.error("❌ Could not retrieve balance after waiting")
            else:
                logger.error("❌ Connection check failed")
        else:
            logger.error("❌ Initial connection failed")
        
        # Try to disconnect cleanly
        try:
            api.disconnect()
        except Exception as e:
            logger.warning(f"Error during disconnect: {str(e)}")
        
        return False
        
    except Exception as e:
        logger.error(f"❌ Error testing SSID: {str(e)}")
        return False

def main():
    print("\nSimple Pocket Option SSID Tester")
    print("--------------------------------")
    print("This uses the exact same approach as self_bot.py")
    
    # Get SSID from user
    ssid = input("\nEnter SSID to test: ").strip()
    if not ssid:
        print("SSID is required. Exiting.")
        return
    
    # Ask about demo mode
    use_demo_input = input("Use demo account? (y/n, default: y): ").strip().lower()
    use_demo = use_demo_input != 'n'
    
    print(f"\nTesting with {'demo' if use_demo else 'real'} account...")
    
    # Test the SSID
    success = test_ssid_simple(ssid, use_demo)
    
    if success:
        print("\n🎉 SSID test PASSED! Your SSID is working correctly.")
    else:
        print("\n💥 SSID test FAILED. The SSID may be invalid or expired.")
        print("\nTroubleshooting:")
        print("1. Make sure you copied the complete SSID from your browser")
        print("2. Ensure you're logged into Pocket Option in your browser")
        print("3. Try getting a fresh SSID from your browser")
        print("4. Check your internet connection")

if __name__ == "__main__":
    main()
