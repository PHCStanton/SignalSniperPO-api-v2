#!/usr/bin/env python3
"""
check_telegram_session.py - Script to check if we have a valid Telegram session.

This script checks if we have a valid Telegram session file that can be used to
authenticate without requiring phone verification. It also verifies that we can
access the BINARY TRADING CLUB channel.

Usage:
    python check_telegram_session.py
"""

import os
import sys
import json
import asyncio
import logging
import argparse
import dotenv
from typing import Dict, Any, Optional, Tuple

# Import Telegram client
try:
    from telethon import TelegramClient
    from telethon.tl.types import Channel
except ImportError:
    print("Error: telethon package is not installed.")
    print("Please install it using: pip install telethon")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("check_telegram_session.log")
    ]
)
logger = logging.getLogger(__name__)

async def check_session(
    api_id: int,
    api_hash: str,
    session_name: str = "pocket_option_userbot"
) -> Tuple[bool, Optional[str]]:
    """
    Check if a session file is valid and can be used for authentication.
    
    Args:
        api_id: Telegram API ID
        api_hash: Telegram API hash
        session_name: Session name to test
        
    Returns:
        Tuple of (bool, str) indicating if the session is valid and user info
    """
    logger.info(f"Checking session: {session_name}")
    
    # Check if session file exists
    if not os.path.exists(f"{session_name}.session"):
        logger.warning(f"Session file {session_name}.session does not exist")
        return False, None
    
    try:
        # Create client
        client = TelegramClient(session_name, api_id, api_hash)
        
        # Connect
        await client.connect()
        
        # Check if authorized
        if await client.is_user_authorized():
            # Get user info
            me = await client.get_me()
            user_info = f"{me.first_name} {getattr(me, 'last_name', '')} (@{me.username})"
            logger.info(f"Session {session_name} is valid. Logged in as: {user_info}")
            
            # Disconnect
            await client.disconnect()
            return True, user_info
        else:
            logger.warning(f"Session {session_name} is not authorized")
            await client.disconnect()
            return False, None
            
    except Exception as e:
        logger.error(f"Error checking session {session_name}: {str(e)}")
        return False, None

async def check_channel_access(
    api_id: int,
    api_hash: str,
    session_name: str,
    channel_id: Optional[int] = None,
    channel_name: Optional[str] = None
) -> bool:
    """
    Check if we can access the specified channel.
    
    Args:
        api_id: Telegram API ID
        api_hash: Telegram API hash
        session_name: Session name to use
        channel_id: Channel ID to check
        channel_name: Channel name to check
        
    Returns:
        True if channel can be accessed, False otherwise
    """
    if not channel_id and not channel_name:
        logger.error("Either channel_id or channel_name must be specified")
        return False
    
    logger.info(f"Checking access to channel: {channel_name or channel_id}")
    
    try:
        # Create client
        client = TelegramClient(session_name, api_id, api_hash)
        
        # Connect
        await client.connect()
        
        # Check if authorized
        if not await client.is_user_authorized():
            logger.error(f"Session {session_name} is not authorized")
            await client.disconnect()
            return False
        
        # Try to access channel
        try:
            if channel_id:
                entity = await client.get_entity(int(channel_id))
                if isinstance(entity, Channel):
                    logger.info(f"Successfully accessed channel by ID: {entity.title}")
                    await client.disconnect()
                    return True
            
            if channel_name:
                # Try to find by name in dialog list
                async for dialog in client.iter_dialogs():
                    if dialog.name == channel_name:
                        logger.info(f"Successfully accessed channel by name: {dialog.name}")
                        await client.disconnect()
                        return True
            
            logger.warning(f"Channel not found: {channel_name or channel_id}")
            await client.disconnect()
            return False
            
        except Exception as e:
            logger.error(f"Error accessing channel: {str(e)}")
            await client.disconnect()
            return False
            
    except Exception as e:
        logger.error(f"Error checking channel access: {str(e)}")
        return False

async def main():
    parser = argparse.ArgumentParser(description='Check Telegram session and channel access')
    parser.add_argument('--api-id', type=int, help='Telegram API ID')
    parser.add_argument('--api-hash', type=str, help='Telegram API hash')
    parser.add_argument('--session', type=str, default='pocket_option_userbot', help='Session name to check')
    parser.add_argument('--config', type=str, default='config/telegram_config.json', help='Path to Telegram configuration file')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # Load environment variables
    dotenv.load_dotenv()
    
    # Load configuration
    config = {}
    if os.path.exists(args.config):
        try:
            with open(args.config, 'r') as f:
                config = json.load(f)
        except json.JSONDecodeError:
            logger.error(f"Error parsing config file: {args.config}")
    
    # Get API credentials
    api_id = args.api_id or config.get('api_id') or os.environ.get('TELEGRAM_API_ID')
    api_hash = args.api_hash or config.get('api_hash') or os.environ.get('TELEGRAM_API_HASH')
    
    # Ensure api_id is an integer
    if api_id:
        try:
            api_id = int(api_id)
        except ValueError:
            logger.error(f"API ID must be an integer, got: {api_id}")
            return
    
    if not api_id or not api_hash:
        logger.error("API credentials not found")
        return
    
    # Get session name
    session_name = args.session or config.get('session_name', 'pocket_option_userbot')
    
    # Check session
    valid, user_info = await check_session(api_id, api_hash, session_name)
    
    if valid:
        print(f"\n✅ Session {session_name} is valid")
        print(f"Logged in as: {user_info}")
        
        # Check channel access
        channel_id = config.get('channel_id')
        channel_name = config.get('channel_name', 'BINARY TRADING CLUB')
        
        if await check_channel_access(api_id, api_hash, session_name, channel_id, channel_name):
            print(f"\n✅ Can access channel: {channel_name}")
            print("\nReady to monitor signals!")
        else:
            print(f"\n❌ Cannot access channel: {channel_name}")
            print("\nPlease ensure your Telegram account is a member of this channel.")
    else:
        print(f"\n❌ Session {session_name} is not valid")
        print("\nYou need to create a new session using telethon_setup.py or test_telegram_api.py.")
        
        # List all session files
        import glob
        session_files = glob.glob("*.session")
        
        if session_files:
            print(f"\nFound {len(session_files)} session files: {', '.join(session_files)}")
            print("You can try one of these sessions by specifying --session SESSION_NAME")
        else:
            print("\nNo session files found.")

if __name__ == "__main__":
    print("Telegram Session Checker")
    print("----------------------")
    print("Checking if we have a valid Telegram session...")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nCheck interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError during check: {str(e)}")
        sys.exit(1)
