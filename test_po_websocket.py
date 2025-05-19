#!/usr/bin/env python3
"""
Pocket Option WebSocket Connection Tester

This script tests the connection to Pocket Option's WebSocket API using an SSID cookie.
It provides detailed output and error handling to help diagnose connection issues.
"""

import websocket
import json
import threading
import time
import argparse
import sys
import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"po_websocket_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def on_open(ws):
    """Called when the WebSocket connection is opened."""
    logger.info("🔌 Connected to Pocket Option WebSocket")
    logger.info("📤 Sending Socket.IO handshake probe...")
    ws.send("40")

def on_message(ws, message, ssid):
    """Called when a message is received from the WebSocket."""
    logger.info(f"📥 Received: {message[:50]}..." if len(message) > 50 else f"📥 Received: {message}")
    
    if message.startswith("42[\"auth\""):
        logger.info("✅ Auth Message Received!")
        try:
            payload = json.loads(message[2:])  # Strip Socket.IO prefix
            event_type, data = payload
            logger.info(f"🎯 Event Type: {event_type}")
            logger.info("🔐 Session Payload (truncated):")
            
            # Print a truncated version of the payload for security
            safe_data = data.copy() if isinstance(data, dict) else {}
            if "session" in safe_data:
                safe_data["session"] = safe_data["session"][:20] + "..." if safe_data["session"] else None
            
            logger.info(json.dumps(safe_data, indent=2))
            
            # Save full session data to file for potential reuse
            with open("po_session_data.json", "w") as f:
                json.dump(data, f, indent=2)
            logger.info("💾 Full session data saved to po_session_data.json")
            
            # Check if we have a valid user ID
            if "uid" in data and data["uid"]:
                logger.info(f"✅ Successfully authenticated! User ID: {data['uid']}")
                logger.info(f"✅ Your SSID is valid and working correctly.")
                
                # Check if we have a session string
                if "session" in data and data["session"]:
                    logger.info("🔑 Session string received. This can be used for temporary authentication.")
                    
                    # Save session string to a separate file
                    with open("po_session_string.txt", "w") as f:
                        f.write(data["session"])
                    logger.info("💾 Session string saved to po_session_string.txt")
                    
                    # Update config file if it exists
                    config_path = "config/pocket_option_config.json"
                    if os.path.exists(config_path):
                        try:
                            with open(config_path, "r") as f:
                                config = json.load(f)
                            
                            # Ask user if they want to update the config
                            update_config = input("\n❓ Would you like to update your config file with this SSID? (y/n): ")
                            if update_config.lower() == 'y':
                                config["ssid"] = ssid
                                with open(config_path, "w") as f:
                                    json.dump(config, f, indent=2)
                                logger.info(f"✅ Updated {config_path} with your SSID")
                        except Exception as e:
                            logger.error(f"⚠️ Failed to update config file: {e}")
            else:
                logger.error("❌ Authentication failed. Your SSID may be expired or invalid.")
                
        except Exception as e:
            logger.error(f"⚠️ Failed to parse auth message: {e}")
            logger.error(f"⚠️ Raw message: {message[:100]}..." if len(message) > 100 else f"⚠️ Raw message: {message}")
    
    elif message.startswith("40"):
        logger.info("💬 Socket.IO handshake successful, connection established")
    
    elif message.startswith("0"):
        logger.info("💓 Received heartbeat ping")
    
    elif message.startswith("3"):
        logger.info("💓 Received heartbeat pong")
    
    else:
        logger.info(f"📨 Other message: {message}")

def on_error(ws, error):
    """Called when a WebSocket error occurs."""
    logger.error(f"❌ WebSocket Error: {error}")
    
    # Provide more helpful error messages for common issues
    if "connection refused" in str(error).lower():
        logger.error("⚠️ Connection refused. The server might be down or blocking connections.")
    elif "handshake" in str(error).lower():
        logger.error("⚠️ Handshake error. This might be due to an invalid URL or protocol issue.")
    elif "certificate" in str(error).lower():
        logger.error("⚠️ SSL Certificate error. Try using ws:// instead of wss:// or vice versa.")
    elif "timeout" in str(error).lower():
        logger.error("⚠️ Connection timeout. Check your internet connection or try again later.")

def on_close(ws, close_status_code, close_msg):
    """Called when the WebSocket connection is closed."""
    logger.info(f"🔌 WebSocket Closed: {close_status_code} {close_msg}")

def run_ws(ssid, use_ssl=False):
    """Run the WebSocket client."""
    # Socket.IO WebSocket endpoint
    protocol = "wss" if use_ssl else "ws"
    URL = f"{protocol}://po.trade/socket.io/?EIO=3&transport=websocket"
    
    logger.info(f"🔄 Connecting to: {URL}")
    
    # Enable trace for debugging
    websocket.enableTrace(True)
    
    # Create a custom on_message handler that includes the SSID
    def on_message_with_ssid(ws, message):
        on_message(ws, message, ssid)
    
    ws = websocket.WebSocketApp(
        URL,
        on_open=on_open,
        on_message=on_message_with_ssid,
        on_error=on_error,
        on_close=on_close,
        header=[f"Cookie: SSID={ssid}"]
    )

    ws.run_forever()

def main():
    """Main function to parse arguments and start the WebSocket client."""
    parser = argparse.ArgumentParser(description="Test Pocket Option WebSocket connection with your SSID")
    parser.add_argument("--ssid", help="Your Pocket Option SSID cookie value")
    parser.add_argument("--ssl", action="store_true", help="Use SSL (wss:// instead of ws://)")
    args = parser.parse_args()
    
    ssid = args.ssid
    use_ssl = args.ssl
    
    # If no SSID provided, prompt the user
    if not ssid:
        ssid = input("Enter your Pocket Option SSID: ")
    
    if not ssid:
        logger.error("❌ No SSID provided. Exiting.")
        sys.exit(1)
    
    logger.info("🚀 Starting Pocket Option WebSocket Test")
    logger.info(f"📝 Using SSID: {ssid[:5]}...{ssid[-5:]} (truncated for security)")
    logger.info(f"🔒 Using {'SSL (wss://)' if use_ssl else 'non-SSL (ws://)'} connection")
    
    # Start the WebSocket client in a separate thread
    thread = threading.Thread(target=run_ws, args=(ssid, use_ssl))
    thread.daemon = True  # Allow the program to exit even if the thread is running
    thread.start()
    
    try:
        # Keep the main thread running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("\n👋 Exiting program (Ctrl+C pressed)")

if __name__ == "__main__":
    main()
