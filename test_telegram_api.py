#!/usr/bin/env python3
"""
test_telegram_api.py - Script to test Telegram API credentials and session files.

This script helps diagnose authentication issues with Telegram by testing API credentials
and session files. It supports loading credentials from environment variables, command line
arguments, or hardcoded values, and can test with different session files.

Usage:
    python test_telegram_api.py --env
    python test_telegram_api.py --api-id YOUR_API_ID --api-hash YOUR_API_HASH
    python test_telegram_api.py --session test_session
"""

import os
import sys
import asyncio
import logging
import argparse
import dotenv
from telethon import TelegramClient
from telethon.errors import PhoneNumberInvalidError, ApiIdInvalidError, SessionPasswordNeededError

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("test_telegram_api.log")
    ]
)
logger = logging.getLogger(__name__)

async def test_auth(api_id, api_hash, session_name="test_session", test_existing_only=False):
    """
    Test Telegram authentication with the given credentials and session.
    
    Args:
        api_id: Telegram API ID
        api_hash: Telegram API hash
        session_name: Session name to use
        test_existing_only: If True, only test if already authorized
        
    Returns:
        True if authentication successful, False otherwise
    """
    logger.info(f"Testing Telegram API credentials with session: {session_name}")
    logger.info(f"API ID: {api_id}")
    logger.info(f"API Hash: {api_hash[:5]}...{api_hash[-5:]}")  # Show only parts of the hash for security
    
    try:
        # Create client
        client = TelegramClient(session_name, api_id, api_hash)
        
        # Connect
        logger.info("Connecting to Telegram...")
        await client.connect()
        logger.info("Connected successfully!")
        
        # Check if already authorized
        if await client.is_user_authorized():
            logger.info("Already authorized!")
            me = await client.get_me()
            logger.info(f"Logged in as: {me.first_name} {getattr(me, 'last_name', '')} (@{me.username})")
            await client.disconnect()
            return True
        elif test_existing_only:
            logger.info("Not authorized and test_existing_only is True. Skipping authentication.")
            await client.disconnect()
            return False
        
        # Not authorized, try to authenticate
        logger.info("Not authorized. Starting phone verification process...")
        
        # Get phone number with retry logic
        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            try:
                phone = input(f"Enter your phone number (with country code, e.g., +27123456789) [Attempt {attempt}/{max_attempts}]: ")
                await client.send_code_request(phone)
                break
            except PhoneNumberInvalidError:
                logger.error("Invalid phone number format. Please use international format with + prefix.")
                if attempt == max_attempts:
                    await client.disconnect()
                    return False
            except Exception as e:
                logger.error(f"Error sending code request: {str(e)}")
                if attempt == max_attempts:
                    await client.disconnect()
                    return False
                logger.info("Retrying...")
        
        # Get verification code with retry logic
        for attempt in range(1, max_attempts + 1):
            try:
                code = input(f"Enter the code you received [Attempt {attempt}/{max_attempts}]: ")
                await client.sign_in(phone, code)
                logger.info("Successfully signed in!")
                
                # Get user info after successful sign-in
                me = await client.get_me()
                logger.info(f"Logged in as: {me.first_name} {getattr(me, 'last_name', '')} (@{me.username})")
                await client.disconnect()
                return True
            except SessionPasswordNeededError:
                # Two-factor authentication is enabled
                password = input("Two-factor authentication is enabled. Please enter your password: ")
                await client.sign_in(password=password)
                logger.info("Successfully signed in with 2FA!")
                
                # Get user info after successful sign-in
                me = await client.get_me()
                logger.info(f"Logged in as: {me.first_name} {getattr(me, 'last_name', '')} (@{me.username})")
                await client.disconnect()
                return True
            except Exception as e:
                logger.error(f"Error during sign-in: {str(e)}")
                if attempt == max_attempts:
                    await client.disconnect()
                    return False
                logger.info("Retrying...")
        
        # Disconnect
        await client.disconnect()
        logger.info("Disconnected")
        return False
        
    except ApiIdInvalidError:
        logger.error("Invalid API ID or API Hash")
        return False
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return False

async def test_all_sessions(api_id, api_hash):
    """
    Test all existing session files with the given credentials.
    
    Args:
        api_id: Telegram API ID
        api_hash: Telegram API hash
        
    Returns:
        True if at least one session is valid, False otherwise
    """
    import glob
    
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
        logger.info(f"Testing session: {session_name}")
        
        if await test_auth(api_id, api_hash, session_name, test_existing_only=True):
            valid_sessions.append(session_name)
    
    if valid_sessions:
        logger.info(f"Valid sessions: {', '.join(valid_sessions)}")
        return True
    else:
        logger.info("No valid sessions found")
        return False

async def main():
    parser = argparse.ArgumentParser(description='Test Telegram API credentials')
    parser.add_argument('--api-id', type=int, help='Telegram API ID')
    parser.add_argument('--api-hash', type=str, help='Telegram API hash')
    parser.add_argument('--session', type=str, default='test_session', help='Session name')
    parser.add_argument('--env', action='store_true', help='Load API credentials from .env file')
    parser.add_argument('--test-all-sessions', action='store_true', help='Test all existing session files')
    
    args = parser.parse_args()
    
    # Load environment variables
    dotenv.load_dotenv()
    
    # Get API credentials
    api_id = None
    api_hash = None
    
    if args.env:
        # Try to load from environment variables
        api_id = os.environ.get('TELEGRAM_API_ID')
        api_hash = os.environ.get('TELEGRAM_API_HASH')
        
        if api_id:
            try:
                api_id = int(api_id)
            except ValueError:
                logger.error(f"TELEGRAM_API_ID must be an integer, got: {api_id}")
                return False
    elif args.api_id and args.api_hash:
        api_id = args.api_id
        api_hash = args.api_hash
    else:
        # Use hardcoded values as fallback
        api_id = 28529262
        api_hash = "6e3dde953198895cddbd7396631a1da5"
    
    if not api_id or not api_hash:
        logger.error("API credentials not found")
        return False
    
    if args.test_all_sessions:
        return await test_all_sessions(api_id, api_hash)
    else:
        return await test_auth(api_id, api_hash, args.session)

if __name__ == "__main__":
    print("Telegram API Credentials Test")
    print("----------------------------")
    
    try:
        success = asyncio.run(main())
        if success:
            print("\n✅ API credentials are valid!")
        else:
            print("\n❌ API credentials test failed!")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError during test: {str(e)}")
        sys.exit(1)
