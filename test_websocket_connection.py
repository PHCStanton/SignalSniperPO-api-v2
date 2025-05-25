#!/usr/bin/env python3
"""
test_websocket_connection.py - Quick test for websocket connection in v1.5

This script tests the Pocket Option websocket connection using the same
configuration and imports as self_bot.py to ensure compatibility.
"""

import os
import sys
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the PocketOptionAPI-v2 directory to the path (same as self_bot.py)
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'PocketOptionAPI-v2'))

try:
    from pocketoptionapi.stable_api import PocketOption
    import pocketoptionapi.global_value as global_value
    logger.info("✅ Successfully imported PocketOption modules")
except ImportError as e:
    logger.error(f"❌ Import error: {e}")
    sys.exit(1)

def test_connection():
    """Test the websocket connection using the current configuration."""
    
    # Load configuration
    try:
        with open('config/pocket_option_config.json', 'r') as f:
            config = json.load(f)
        logger.info("✅ Configuration loaded successfully")
    except Exception as e:
        logger.error(f"❌ Error loading config: {e}")
        return False
    
    # Get SSID and demo mode
    ssid = config.get('ssid')
    is_demo = config.get('is_demo', True)
    
    if not ssid:
        logger.error("❌ No SSID found in configuration")
        return False
    
    logger.info(f"Testing connection with SSID: {ssid[:10]}... (Demo: {is_demo})")
    
    try:
        # Initialize client
        client = PocketOption(ssid, is_demo)
        logger.info("✅ PocketOption client created")
        
        # Connect
        result = client.connect()
        if result:
            logger.info("✅ Connection initiated successfully")
            
            # Check connection status
            import time
            time.sleep(3)  # Wait for connection to establish
            
            if client.check_connect():
                logger.info("✅ WebSocket connection established")
                
                # Try to get balance
                balance = client.get_balance()
                if balance is not None:
                    logger.info(f"✅ Balance retrieved: {balance}")
                    logger.info("🎉 All tests passed! WebSocket implementation is working correctly.")
                    return True
                else:
                    logger.warning("⚠️ Connection established but balance not available (SSID may be expired)")
                    return False
            else:
                logger.error("❌ WebSocket connection failed")
                return False
        else:
            logger.error("❌ Failed to initiate connection")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error during connection test: {e}")
        return False
    finally:
        try:
            client.disconnect()
            logger.info("✅ Disconnected cleanly")
        except:
            pass

if __name__ == "__main__":
    print("Pocket Option WebSocket Connection Test for v1.5")
    print("=" * 50)
    
    success = test_connection()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 SUCCESS: WebSocket implementation is ready for real trading!")
        print("Your self_bot.py should work correctly with the current configuration.")
    else:
        print("❌ FAILED: Please check your SSID or configuration.")
        print("You may need to get a fresh SSID from your Pocket Option account.")
    
    print("\nTo run your trading bot:")
    print("python self_bot.py --verbose")
