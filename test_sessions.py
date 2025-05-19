#!/usr/bin/env python3
"""
test_sessions.py - Script to test all existing Telegram session files.

This script tests all existing .session files in the current directory to see
if any of them are still valid and can be used for authentication without
requiring phone verification.

Usage:
    python test_sessions.py
"""

import os
import sys
import asyncio
import logging
import glob
import dotenv
from telethon import TelegramClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("test_sessions.log")
    ]
)
logger = logging.getLogger(__name__)

async def test_session(api_id, api_hash, session_name):
    """
    Test if a session file is valid and can be used for authentication.
    
    Args:
        api_id: Telegram API ID
        api_hash: Telegram API hash
        session_name: Session name to test
        
    Returns:
        Tuple of (bool, str) indicating if the session is valid and user info
    """
    logger.info(f"Testing session: {session_name}")
    
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
            await client.disconnect()
            return True, user_info
        else:
            logger.info(f"Session {session_name} is not authorized")
            await client.disconnect()
            return False, None
            
    except Exception as e:
        logger.error(f"Error testing session {session_name}: {str(e)}")
        return False, None

async def main():
    # Load environment variables
    dotenv.load_dotenv()
    
    # Get API credentials from environment
    api_id = os.environ.get('TELEGRAM_API_ID')
    api_hash = os.environ.get('TELEGRAM_API_HASH')
    
    if not api_id or not api_hash:
        logger.error("API credentials not found in environment variables")
        logger.info("Using default credentials from telegram_config.json")
        
        # Try to load from config file
        try:
            import json
            with open("config/telegram_config.json", 'r') as f:
                config = json.load(f)
                api_id = config.get('api_id')
                api_hash = config.get('api_hash')
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            # Use hardcoded values as last resort
            api_id = 28529262
            api_hash = "6e3dde953198895cddbd7396631a1da5"
    
    # Ensure api_id is an integer
    try:
        api_id = int(api_id)
    except ValueError:
        logger.error(f"API ID must be an integer, got: {api_id}")
        return False
    
    logger.info(f"Using API ID: {api_id}")
    logger.info(f"Using API Hash: {api_hash[:5]}...{api_hash[-5:]}")
    
    # Find all session files
    session_files = glob.glob("*.session")
    
    if not session_files:
        logger.info("No session files found")
        return False
    
    logger.info(f"Found {len(session_files)} session files: {', '.join(session_files)}")
    
    # Test each session file
    valid_sessions = []
    for session_file in session_files:
        session_name = session_file.replace(".session", "")
        valid, user_info = await test_session(api_id, api_hash, session_name)
        
        if valid:
            valid_sessions.append((session_name, user_info))
    
    # Print results
    if valid_sessions:
        logger.info(f"\nFound {len(valid_sessions)} valid session(s):")
        for session_name, user_info in valid_sessions:
            logger.info(f"  - {session_name}: {user_info}")
        
        # Check if pocket_option_userbot.session is valid
        default_session = "pocket_option_userbot"
        default_valid = any(session[0] == default_session for session in valid_sessions)
        
        if default_valid:
            logger.info(f"\nThe default session '{default_session}' is valid and can be used")
        else:
            logger.info(f"\nThe default session '{default_session}' is not valid")
            
            if valid_sessions:
                # Suggest using a valid session
                suggested_session = valid_sessions[0][0]
                logger.info(f"Consider using '{suggested_session}' instead by updating telegram_config.json")
        
        return True
    else:
        logger.info("\nNo valid sessions found. You will need to create a new session.")
        return False

if __name__ == "__main__":
    print("Telegram Session Tester")
    print("----------------------")
    print("Testing all existing session files...")
    
    try:
        success = asyncio.run(main())
        
        if success:
            print("\n✅ Found valid session(s)!")
            print("Check the log for details on which sessions are valid.")
        else:
            print("\n❌ No valid sessions found!")
            print("You will need to create a new session using telethon_setup.py or test_telegram_api.py.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError during test: {str(e)}")
        sys.exit(1)
