#!/usr/bin/env python3
"""
send_test_message.py - Sends a test message to a Telegram channel or chat.

This script sends a test message to a Telegram channel or chat to verify connectivity.
It can be used to ensure that the bot has the necessary permissions to access the channel.
"""

import os
import sys
import json
import asyncio
import logging
import argparse
from datetime import datetime
from typing import Optional, Dict, Any

try:
    from telethon import TelegramClient, events
    from telethon.tl.types import Channel, Chat, User
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
        logging.FileHandler("telegram_test.log")
    ]
)
logger = logging.getLogger(__name__)

class TelegramTester:
    def __init__(
        self,
        api_id: int,
        api_hash: str,
        bot_token: Optional[str] = None,
        session_name: str = "telegram_test",
        config_file: Optional[str] = None,
        verbose: bool = False
    ):
        """
        Initialize the Telegram tester.
        
        Args:
            api_id: Telegram API ID
            api_hash: Telegram API hash
            bot_token: Bot token (if using a bot)
            session_name: Session name for telethon
            config_file: Configuration file path (optional)
            verbose: Enable verbose output
        """
        self.api_id = api_id
        self.api_hash = api_hash
        self.bot_token = bot_token
        self.session_name = session_name
        self.config_file = config_file
        self.verbose = verbose
        self.client = None
        self.config = self._load_config()
        
        # Set logging level
        if verbose:
            logger.setLevel(logging.DEBUG)
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default."""
        if self.config_file and os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.error(f"Error parsing config file: {self.config_file}")
                
        # Default configuration
        return {
            "channel_name": "BINARY TRADING CLUB",
            "channel_username": None,
            "channel_id": None,
            "test_message": "This is a test message from the Pocket Option trading bot. Time: {time}",
            "delete_after": True,
            "delete_delay": 5  # seconds
        }
    
    def _save_config(self) -> None:
        """Save configuration to file."""
        if not self.config_file:
            return
            
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=4)
        logger.info(f"Configuration saved to {self.config_file}")
    
    async def initialize(self) -> bool:
        """
        Initialize the Telegram client.
        
        Returns:
            True if initialized successfully, False otherwise
        """
        try:
            logger.info("Initializing Telegram client...")
            
            if self.bot_token:
                # Bot mode
                self.client = TelegramClient(self.session_name, self.api_id, self.api_hash)
                await self.client.start(bot_token=self.bot_token)
                logger.info("Started Telegram client in bot mode")
            else:
                # User account mode
                self.client = TelegramClient(self.session_name, self.api_id, self.api_hash)
                await self.client.start()
                logger.info("Started Telegram client in user account mode")
                
                # Check if we need to complete the phone verification process
                if not await self.client.is_user_authorized():
                    logger.info("User not authorized. Please complete the login process.")
                    await self.client.send_code_request(input("Enter your phone number: "))
                    await self.client.sign_in(input("Enter your phone number again: "), input("Enter the code: "))
            
            return True
        except Exception as e:
            logger.error(f"Error initializing Telegram client: {str(e)}")
            return False
    
    async def find_channel(self, channel_identifier: Optional[str] = None) -> Optional[Channel]:
        """
        Find a channel by name, username, or ID.
        
        Args:
            channel_identifier: Channel name, username, or ID (defaults to config value)
            
        Returns:
            Channel object if found, None otherwise
        """
        if not channel_identifier:
            # Try to use channel_id from config
            if self.config["channel_id"]:
                channel_identifier = self.config["channel_id"]
            # Try to use channel_username from config
            elif self.config["channel_username"]:
                channel_identifier = self.config["channel_username"]
            # Use channel_name from config
            else:
                channel_identifier = self.config["channel_name"]
        
        logger.info(f"Searching for channel: {channel_identifier}")
        
        try:
            # Try to interpret as channel ID
            if isinstance(channel_identifier, int) or (isinstance(channel_identifier, str) and channel_identifier.isdigit()):
                entity = await self.client.get_entity(int(channel_identifier))
                if isinstance(entity, Channel):
                    logger.info(f"Found channel by ID: {entity.title}")
                    self.config["channel_id"] = entity.id
                    self.config["channel_name"] = entity.title
                    if hasattr(entity, 'username') and entity.username:
                        self.config["channel_username"] = entity.username
                    self._save_config()
                    return entity
            
            # Try to interpret as username
            if isinstance(channel_identifier, str) and (channel_identifier.startswith('@') or '/' not in channel_identifier):
                username = channel_identifier.lstrip('@')
                try:
                    entity = await self.client.get_entity(username)
                    if isinstance(entity, Channel):
                        logger.info(f"Found channel by username: {entity.title}")
                        self.config["channel_id"] = entity.id
                        self.config["channel_name"] = entity.title
                        self.config["channel_username"] = username
                        self._save_config()
                        return entity
                except Exception as e:
                    logger.debug(f"Error finding channel by username: {str(e)}")
            
            # Try to find by name in dialog list
            async for dialog in self.client.iter_dialogs():
                if dialog.name == channel_identifier or (dialog.entity.username and dialog.entity.username == channel_identifier.lstrip('@')):
                    if isinstance(dialog.entity, Channel):
                        logger.info(f"Found channel in dialog list: {dialog.name}")
                        self.config["channel_id"] = dialog.id
                        self.config["channel_name"] = dialog.name
                        if hasattr(dialog.entity, 'username') and dialog.entity.username:
                            self.config["channel_username"] = dialog.entity.username
                        self._save_config()
                        return dialog.entity
            
            logger.warning(f"Channel not found: {channel_identifier}")
            return None
            
        except Exception as e:
            logger.error(f"Error finding channel: {str(e)}")
            return None
    
    async def send_test_message(self, channel: Any, message: Optional[str] = None) -> Optional[Any]:
        """
        Send a test message to a channel.
        
        Args:
            channel: Channel to send message to
            message: Message to send (defaults to config value)
            
        Returns:
            Message object if sent successfully, None otherwise
        """
        if not message:
            message = self.config["test_message"]
        
        # Format message with current time
        message = message.format(time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        logger.info(f"Sending test message to channel: {message}")
        
        try:
            sent_message = await self.client.send_message(channel, message)
            logger.info("Test message sent successfully")
            return sent_message
        except Exception as e:
            logger.error(f"Error sending test message: {str(e)}")
            return None
    
    async def delete_message(self, message: Any, delay: Optional[int] = None) -> bool:
        """
        Delete a message after a delay.
        
        Args:
            message: Message to delete
            delay: Delay in seconds before deleting (defaults to config value)
            
        Returns:
            True if deleted successfully, False otherwise
        """
        if not delay:
            delay = self.config["delete_delay"]
        
        logger.info(f"Deleting message after {delay} seconds...")
        
        try:
            await asyncio.sleep(delay)
            await self.client.delete_messages(message.chat_id, message)
            logger.info("Message deleted successfully")
            return True
        except Exception as e:
            logger.error(f"Error deleting message: {str(e)}")
            return False
    
    async def close(self) -> None:
        """Close the Telegram client."""
        if self.client:
            await self.client.disconnect()
            logger.info("Telegram client disconnected")

async def main():
    parser = argparse.ArgumentParser(description='Send a test message to a Telegram channel or chat')
    parser.add_argument('--api-id', type=int, help='Telegram API ID')
    parser.add_argument('--api-hash', type=str, help='Telegram API hash')
    parser.add_argument('--bot-token', type=str, help='Telegram bot token (if using a bot)')
    parser.add_argument('--session', type=str, default='telegram_test', help='Session name')
    parser.add_argument('--config', type=str, help='Configuration file path')
    parser.add_argument('--channel', type=str, help='Channel name, username, or ID')
    parser.add_argument('--message', type=str, help='Message to send')
    parser.add_argument('--no-delete', action='store_true', help='Do not delete the message after sending')
    parser.add_argument('--delete-delay', type=int, default=5, help='Delay in seconds before deleting the message')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose output')
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # Check for required arguments
    if not args.api_id or not args.api_hash:
        # Try to load from environment variables
        api_id = os.environ.get('TELEGRAM_API_ID')
        api_hash = os.environ.get('TELEGRAM_API_HASH')
        bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
        
        if not api_id or not api_hash:
            parser.error("API ID and API hash are required. Provide them as arguments or set TELEGRAM_API_ID and TELEGRAM_API_HASH environment variables.")
    else:
        api_id = args.api_id
        api_hash = args.api_hash
        bot_token = args.bot_token
    
    # Create tester
    tester = TelegramTester(
        api_id=int(api_id),
        api_hash=api_hash,
        bot_token=bot_token,
        session_name=args.session,
        config_file=args.config,
        verbose=args.verbose
    )
    
    # Update config from arguments
    if args.message:
        tester.config["test_message"] = args.message
    
    if args.no_delete:
        tester.config["delete_after"] = False
    
    if args.delete_delay:
        tester.config["delete_delay"] = args.delete_delay
    
    try:
        # Initialize client
        initialized = await tester.initialize()
        if not initialized:
            logger.error("Failed to initialize Telegram client")
            return
        
        # Find channel
        channel = await tester.find_channel(args.channel)
        if not channel:
            logger.error("Failed to find channel")
            return
        
        # Send test message
        message = await tester.send_test_message(channel)
        if not message:
            logger.error("Failed to send test message")
            return
        
        # Delete message if configured
        if tester.config["delete_after"]:
            await tester.delete_message(message)
            
    except Exception as e:
        logger.error(f"Error: {str(e)}")
    finally:
        # Close client
        await tester.close()

if __name__ == "__main__":
    print("Pocket Option Trading Bot - Telegram Test")
    print("----------------------------------------")
    print("This script sends a test message to a Telegram channel or chat to verify connectivity.")
    print("")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError during test: {str(e)}")
        sys.exit(1)
