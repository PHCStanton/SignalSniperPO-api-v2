#!/usr/bin/env python3
"""
test_ssid_ec2.py - Test EC2 instance connectivity and SSID validation

This script tests the connectivity to the EC2 instance and validates the SSID
for Pocket Option WebSocket authentication. It's designed to be run locally
to verify that the EC2 instance is properly configured and can connect to
Pocket Option's WebSocket API.
"""

import os
import sys
import json
import time
import logging
import argparse
import asyncio
import websockets
import ssl
import dotenv
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"test_ssid_ec2_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)
logger = logging.getLogger(__name__)

# Default values
DEFAULT_CONFIG_PATH = "config/pocket_option_config.json"
DEFAULT_WS_URL = "wss://ws.po.trade/socket.io/?EIO=3&transport=websocket"
DEFAULT_TIMEOUT = 30  # seconds

async def test_websocket_connection(ssid, ws_url=DEFAULT_WS_URL, timeout=DEFAULT_TIMEOUT, test_mode=True):
    """
    Test WebSocket connection to Pocket Option using the provided SSID.
    
    Args:
        ssid: The SSID for authentication
        ws_url: WebSocket URL
        timeout: Connection timeout in seconds
        test_mode: Whether to use demo account (True) or real account (False)
    
    Returns:
        bool: True if connection and authentication successful, False otherwise
    """
    logger.info(f"Testing WebSocket connection to {ws_url}")
    logger.info(f"Using {'DEMO' if test_mode else 'REAL'} account mode")
    
    try:
        # Create SSL context
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        # Connect to WebSocket
        logger.info("Connecting to WebSocket...")
        async with websockets.connect(
            ws_url,
            ssl=ssl_context,
            ping_interval=None,
            ping_timeout=None,
            close_timeout=timeout
        ) as websocket:
            # Wait for initial message (typically "0{...}")
            initial_msg = await asyncio.wait_for(websocket.recv(), timeout=timeout)
            logger.info(f"Received initial message: {initial_msg[:50]}...")
            
            # Send ping message
            logger.info("Sending ping message (2)...")
            await websocket.send("2")
            
            # Wait for pong response
            pong = await asyncio.wait_for(websocket.recv(), timeout=timeout)
            logger.info(f"Received pong response: {pong}")
            
            if pong != "3":
                logger.error(f"Unexpected pong response: {pong}")
                return False
            
            # Authenticate with SSID
            auth_msg = f'42["auth",{{"session":"{ssid}","isDemo":{str(test_mode).lower()}}}]'
            logger.info("Sending authentication message...")
            logger.debug(f"Auth message: {auth_msg}")
            await websocket.send(auth_msg)
            
            # Wait for authentication response
            auth_response = await asyncio.wait_for(websocket.recv(), timeout=timeout)
            logger.info(f"Received authentication response: {auth_response[:100]}...")
            
            if '"success":true' in auth_response:
                logger.info("Authentication successful!")
                
                # Request account balance to further validate connection
                balance_msg = '42["getBalances",{}]'
                logger.info("Requesting account balance...")
                await websocket.send(balance_msg)
                
                # Wait for balance response
                balance_response = await asyncio.wait_for(websocket.recv(), timeout=timeout)
                logger.info(f"Received balance response: {balance_response[:100]}...")
                
                if '"name":"getBalances"' in balance_response:
                    logger.info("Balance request successful!")
                    return True
                else:
                    logger.error("Failed to get balance information")
                    return False
            else:
                logger.error("Authentication failed!")
                logger.error(f"Response: {auth_response}")
                return False
    
    except asyncio.TimeoutError:
        logger.error(f"Connection timed out after {timeout} seconds")
        return False
    except websockets.exceptions.ConnectionClosed as e:
        logger.error(f"WebSocket connection closed unexpectedly: {e}")
        return False
    except Exception as e:
        logger.error(f"Error during WebSocket connection: {e}")
        return False

async def test_ec2_connectivity(host, port=22, timeout=5):
    """
    Test connectivity to EC2 instance.
    
    Args:
        host: EC2 instance hostname or IP
        port: Port to test (default: 22 for SSH)
        timeout: Connection timeout in seconds
    
    Returns:
        bool: True if connection successful, False otherwise
    """
    logger.info(f"Testing connectivity to EC2 instance at {host}:{port}")
    
    try:
        # Create connection
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port),
            timeout=timeout
        )
        
        # Close connection immediately
        writer.close()
        await writer.wait_closed()
        
        logger.info(f"Successfully connected to {host}:{port}")
        return True
    
    except asyncio.TimeoutError:
        logger.error(f"Connection to {host}:{port} timed out after {timeout} seconds")
        return False
    except Exception as e:
        logger.error(f"Failed to connect to {host}:{port}: {e}")
        return False

async def main():
    """Main function to parse arguments and run tests."""
    parser = argparse.ArgumentParser(description='Test EC2 instance connectivity and SSID validation')
    parser.add_argument('--config', type=str, default=DEFAULT_CONFIG_PATH, help='Path to Pocket Option configuration file')
    parser.add_argument('--ssid', type=str, help='SSID for authentication (overrides config file)')
    parser.add_argument('--ws-url', type=str, default=DEFAULT_WS_URL, help='WebSocket URL')
    parser.add_argument('--timeout', type=int, default=DEFAULT_TIMEOUT, help='Connection timeout in seconds')
    parser.add_argument('--ec2-host', type=str, default='3.126.128.227', help='EC2 instance hostname or IP')
    parser.add_argument('--ec2-port', type=int, default=22, help='EC2 instance port (default: 22 for SSH)')
    parser.add_argument('--real', action='store_true', help='Use real account instead of demo account')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Set log level
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # Load .env file if it exists
    dotenv.load_dotenv()
    
    # Test EC2 connectivity
    ec2_connected = await test_ec2_connectivity(args.ec2_host, args.ec2_port)
    
    if not ec2_connected:
        logger.error("EC2 connectivity test failed. Please check your EC2 instance.")
        return False
    
    # Get SSID from arguments or config file
    ssid = args.ssid
    if not ssid:
        if os.path.exists(args.config):
            try:
                with open(args.config, 'r') as f:
                    config = json.load(f)
                    ssid = config.get('ssid')
                    if not ssid:
                        logger.error(f"No SSID found in config file {args.config}")
                        return False
            except Exception as e:
                logger.error(f"Error reading config file {args.config}: {e}")
                return False
        else:
            logger.error(f"Config file {args.config} not found and no SSID provided")
            return False
    
    # Test WebSocket connection
    ws_connected = await test_websocket_connection(
        ssid=ssid,
        ws_url=args.ws_url,
        timeout=args.timeout,
        test_mode=not args.real
    )
    
    if not ws_connected:
        logger.error("WebSocket connection test failed. Please check your SSID and network connection.")
        return False
    
    logger.info("All tests passed successfully!")
    return True

if __name__ == "__main__":
    print("Testing EC2 instance connectivity and SSID validation...")
    
    try:
        result = asyncio.run(main())
        if result:
            print("All tests passed successfully!")
            sys.exit(0)
        else:
            print("Tests failed. Check the log for details.")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {str(e)}")
        sys.exit(1)
