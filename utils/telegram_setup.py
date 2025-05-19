#!/usr/bin/env python3
"""
telegram_setup.py - Sets up Telegram integration for the Pocket Option trading bot.

This script helps set up and test the Telegram integration for monitoring the
"BINARY TRADING CLUB" channel for trading signals. It supports both bot and user
account approaches and includes functionality to test connectivity and parse signals.
"""

import os
import re
import sys
import json
import asyncio
import logging
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union

try:
    from telethon import TelegramClient, events
    from telethon.tl.functions.channels import JoinChannelRequest
    from telethon.tl.functions.messages import GetHistoryRequest
    from telethon.tl.types import Channel, Message, PeerChannel, User
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
        logging.FileHandler("telegram_setup.log")
    ]
)
logger = logging.getLogger(__name__)

# Signal parsing regex patterns
FIRST_MESSAGE_PATTERN = r"Trading Pair: (\w+/\w+)(?:\s*\(OTC\))?"
SECOND_MESSAGE_TIMER_PATTERN = r"SET THE TIMER TO (\d{2}:\d{2}:\d{2})"
SECOND_MESSAGE_PAIR_PATTERN = r"Currency pair (\w+/\w+)"
SECOND_MESSAGE_DIRECTION_PATTERN = r"(HIGHER|LOWER)"
SECOND_MESSAGE_EXPIRY_PATTERN = r"Trade time: (\d+) MIN"

class TelegramSetup:
    def __init__(
        self,
        api_id: int,
        api_hash: str,
        bot_token: Optional[str] = None,
        session_name: str = "pocket_option_bot",
        config_file: str = "telegram_config.json"
    ):
        """
        Initialize the Telegram setup.
        
        Args:
            api_id: Telegram API ID
            api_hash: Telegram API hash
            bot_token: Bot token (if using a bot)
            session_name: Session name for telethon
            config_file: Configuration file path
        """
        self.api_id = api_id
        self.api_hash = api_hash
        self.bot_token = bot_token
        self.session_name = session_name
        self.config_file = config_file
        self.client = None
        self.channel = None
        self.channel_id = None
        self.channel_username = None
        self.config = self._load_config()
        
        # Signal tracking
        self.last_first_message = None
        self.last_first_message_time = None
        self.pending_signals = []
        
    def _load_config(self) -> Dict:
        """Load configuration from file or create default."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.error(f"Error parsing config file: {self.config_file}")
                
        # Default configuration
        return {
            "channel_name": "BINARY TRADING CLUB",
            "channel_username": None,  # Will be updated when found
            "channel_id": None,        # Will be updated when found
            "signal_parser": {
                "first_message_pattern": FIRST_MESSAGE_PATTERN,
                "second_message_timer_pattern": SECOND_MESSAGE_TIMER_PATTERN,
                "second_message_pair_pattern": SECOND_MESSAGE_PAIR_PATTERN,
                "second_message_direction_pattern": SECOND_MESSAGE_DIRECTION_PATTERN,
                "second_message_expiry_pattern": SECOND_MESSAGE_EXPIRY_PATTERN,
                "max_time_between_messages": 60  # seconds
            },
            "monitoring": {
                "enabled": True,
                "log_all_messages": False
            }
        }
    
    def _save_config(self) -> None:
        """Save configuration to file."""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=4)
        logger.info(f"Configuration saved to {self.config_file}")
    
    async def initialize(self) -> None:
        """Initialize the Telegram client."""
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
    
    async def find_channel(self, channel_name: Optional[str] = None) -> Optional[Channel]:
        """
        Find the channel by name or username.
        
        Args:
            channel_name: Channel name to search for (defaults to config value)
            
        Returns:
            Channel object if found, None otherwise
        """
        if not channel_name:
            channel_name = self.config["channel_name"]
            
        logger.info(f"Searching for channel: {channel_name}")
        
        # Try to find the channel in the dialog list
        async for dialog in self.client.iter_dialogs():
            if dialog.name == channel_name or (dialog.entity.username and dialog.entity.username == channel_name):
                self.channel = dialog.entity
                self.channel_id = dialog.id
                if hasattr(dialog.entity, 'username') and dialog.entity.username:
                    self.channel_username = dialog.entity.username
                
                # Update config
                self.config["channel_id"] = self.channel_id
                if self.channel_username:
                    self.config["channel_username"] = self.channel_username
                self._save_config()
                
                logger.info(f"Found channel: {dialog.name} (ID: {self.channel_id}, Username: {self.channel_username})")
                return dialog.entity
        
        logger.warning(f"Channel not found: {channel_name}")
        return None
    
    async def access_channel(self, channel_name: Optional[str] = None) -> bool:
        """
        Access a channel that the user is already a member of.
        
        Args:
            channel_name: Channel name to access
            
        Returns:
            True if channel found and accessed successfully, False otherwise
        """
        if not channel_name:
            channel_name = self.config["channel_name"]
            
        logger.info(f"Attempting to access channel: {channel_name}")
        
        # Find the channel in the user's dialog list
        channel = await self.find_channel(channel_name)
        
        if channel:
            logger.info(f"Successfully accessed channel: {channel_name}")
            return True
        else:
            logger.warning(f"Could not access channel: {channel_name}")
            logger.warning("Please ensure your Telegram account is already a member of this channel.")
            logger.warning("The bot cannot join channels - it can only access channels you've already joined.")
            return False
    
    async def get_recent_messages(self, limit: int = 10) -> List[Message]:
        """
        Get recent messages from the channel.
        
        Args:
            limit: Maximum number of messages to retrieve
            
        Returns:
            List of Message objects
        """
        if not self.channel:
            logger.error("Channel not found. Call find_channel() first.")
            return []
            
        try:
            logger.info(f"Retrieving {limit} recent messages from channel")
            
            # Get messages from channel
            messages = await self.client(GetHistoryRequest(
                peer=self.channel,
                limit=limit,
                offset_date=None,
                offset_id=0,
                max_id=0,
                min_id=0,
                add_offset=0,
                hash=0
            ))
            
            logger.info(f"Retrieved {len(messages.messages)} messages")
            return messages.messages
            
        except Exception as e:
            logger.error(f"Error retrieving messages: {str(e)}")
            return []
    
    def parse_first_message(self, message_text: str) -> Optional[str]:
        """
        Parse the first message of the signal format.
        
        Args:
            message_text: Message text to parse
            
        Returns:
            Trading pair if found, None otherwise
        """
        pattern = self.config["signal_parser"]["first_message_pattern"]
        match = re.search(pattern, message_text)
        
        if match:
            trading_pair = match.group(1)
            logger.info(f"Parsed first message: Trading pair = {trading_pair}")
            return trading_pair
        
        return None
    
    def parse_second_message(self, message_text: str) -> Optional[Dict]:
        """
        Parse the second message of the signal format.
        
        Args:
            message_text: Message text to parse
            
        Returns:
            Dictionary with signal details if parsed successfully, None otherwise
        """
        # Extract timer
        timer_match = re.search(self.config["signal_parser"]["second_message_timer_pattern"], message_text)
        if not timer_match:
            return None
        timer = timer_match.group(1)
        
        # Extract pair
        pair_match = re.search(self.config["signal_parser"]["second_message_pair_pattern"], message_text)
        if not pair_match:
            return None
        pair = pair_match.group(1)
        
        # Extract direction
        direction_match = re.search(self.config["signal_parser"]["second_message_direction_pattern"], message_text)
        if not direction_match:
            return None
        direction = direction_match.group(1)
        
        # Extract expiry
        expiry_match = re.search(self.config["signal_parser"]["second_message_expiry_pattern"], message_text)
        if not expiry_match:
            return None
        expiry = int(expiry_match.group(1))
        
        signal = {
            "timer": timer,
            "pair": pair,
            "direction": direction,
            "expiry": expiry
        }
        
        logger.info(f"Parsed second message: {signal}")
        return signal
    
    async def process_message(self, message: Message) -> None:
        """
        Process a message from the channel.
        
        Args:
            message: Message to process
        """
        if not message.text:
            return
            
        # Log all messages if enabled
        if self.config["monitoring"]["log_all_messages"]:
            sender = await message.get_sender()
            sender_name = getattr(sender, 'first_name', 'Unknown')
            logger.info(f"Message from {sender_name}: {message.text}")
        
        # Try to parse as first message
        trading_pair = self.parse_first_message(message.text)
        if trading_pair:
            self.last_first_message = trading_pair
            self.last_first_message_time = datetime.now()
            return
            
        # Try to parse as second message
        if self.last_first_message and self.last_first_message_time:
            # Check if the time between messages is within the allowed window
            time_diff = (datetime.now() - self.last_first_message_time).total_seconds()
            if time_diff <= self.config["signal_parser"]["max_time_between_messages"]:
                signal = self.parse_second_message(message.text)
                if signal:
                    # Verify that the pair matches
                    if signal["pair"] == self.last_first_message:
                        # Complete signal
                        complete_signal = {
                            "pair": self.last_first_message,
                            "timer": signal["timer"],
                            "direction": signal["direction"],
                            "expiry": signal["expiry"],
                            "timestamp": datetime.now().isoformat()
                        }
                        
                        logger.info(f"Complete signal detected: {complete_signal}")
                        self.pending_signals.append(complete_signal)
                        
                        # Reset tracking
                        self.last_first_message = None
                        self.last_first_message_time = None
                    else:
                        logger.warning(f"Pair mismatch: {self.last_first_message} vs {signal['pair']}")
    
    async def setup_message_handler(self) -> None:
        """Set up the message handler for the channel."""
        if not self.channel_id:
            logger.error("Channel ID not found. Call find_channel() first.")
            return
            
        @self.client.on(events.NewMessage(chats=self.channel_id))
        async def message_handler(event):
            await self.process_message(event.message)
            
        logger.info(f"Message handler set up for channel ID: {self.channel_id}")
    
    async def test_connectivity(self) -> bool:
        """
        Test connectivity to the Telegram channel.
        
        Returns:
            True if connected successfully, False otherwise
        """
        if not self.channel:
            logger.error("Channel not found. Call find_channel() first.")
            return False
            
        try:
            messages = await self.get_recent_messages(1)
            if messages:
                logger.info("Connectivity test successful")
                return True
            else:
                logger.warning("Connectivity test failed: No messages retrieved")
                return False
                
        except Exception as e:
            logger.error(f"Connectivity test failed: {str(e)}")
            return False
    
    async def run_signal_monitor(self, duration_seconds: int = 300) -> None:
        """
        Run the signal monitor for a specified duration.
        
        Args:
            duration_seconds: Duration to run the monitor in seconds
        """
        if not self.channel:
            logger.error("Channel not found. Call find_channel() first.")
            return
            
        # Set up message handler
        await self.setup_message_handler()
        
        logger.info(f"Starting signal monitor for {duration_seconds} seconds")
        logger.info("Press Ctrl+C to stop")
        
        try:
            # Process any recent messages
            messages = await self.get_recent_messages(5)
            for message in messages:
                await self.process_message(message)
                
            # Run for the specified duration
            end_time = datetime.now() + timedelta(seconds=duration_seconds)
            while datetime.now() < end_time:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Signal monitor stopped by user")
        except Exception as e:
            logger.error(f"Error in signal monitor: {str(e)}")
        finally:
            logger.info("Signal monitor stopped")
            
            # Print detected signals
            if self.pending_signals:
                logger.info(f"Detected {len(self.pending_signals)} signals:")
                for i, signal in enumerate(self.pending_signals):
                    logger.info(f"Signal {i+1}: {signal}")
            else:
                logger.info("No signals detected")
    
    async def close(self) -> None:
        """Close the Telegram client."""
        if self.client:
            await self.client.disconnect()
            logger.info("Telegram client disconnected")

async def main():
    parser = argparse.ArgumentParser(description='Set up Telegram integration for Pocket Option trading bot')
    parser.add_argument('--api-id', type=int, help='Telegram API ID')
    parser.add_argument('--api-hash', type=str, help='Telegram API hash')
    parser.add_argument('--bot-token', type=str, help='Telegram bot token (if using a bot)')
    parser.add_argument('--session', type=str, default='pocket_option_bot', help='Session name')
    parser.add_argument('--config', type=str, default='telegram_config.json', help='Configuration file path')
    parser.add_argument('--channel', type=str, help='Channel name or username to join')
    parser.add_argument('--monitor', action='store_true', help='Run signal monitor')
    parser.add_argument('--duration', type=int, default=300, help='Duration to run monitor (seconds)')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    
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
    
    # Create Telegram setup
    setup = TelegramSetup(
        api_id=int(api_id),
        api_hash=api_hash,
        bot_token=bot_token,
        session_name=args.session,
        config_file=args.config
    )
    
    try:
        # Initialize client
        await setup.initialize()
        
        # Find channel
        if args.channel:
            # Try to find the specified channel
            channel = await setup.find_channel(args.channel)
            
            # If not found, inform the user
            if not channel:
                print(f"\n❌ Channel '{args.channel}' not found in your dialogs.")
                print("Please ensure your Telegram account is already a member of this channel.")
                print("The bot cannot join channels - it can only access channels you've already joined.")
        else:
            # Use default channel from config
            channel = await setup.find_channel()
            
            # If not found, inform the user
            if not channel:
                print(f"\n❌ Channel '{setup.config['channel_name']}' not found in your dialogs.")
                print("Please ensure your Telegram account is already a member of this channel.")
                print("The bot cannot join channels - it can only access channels you've already joined.")
        
        # Test connectivity
        if setup.channel:
            connected = await setup.test_connectivity()
            if connected:
                print("\n✅ Successfully connected to the channel")
                
                # Print channel info
                print(f"\nChannel Information:")
                print(f"  Name: {setup.config['channel_name']}")
                print(f"  ID: {setup.config['channel_id']}")
                print(f"  Username: {setup.config['channel_username'] or 'N/A'}")
                
                # Run monitor if requested
                if args.monitor:
                    await setup.run_signal_monitor(args.duration)
            else:
                print("\n❌ Failed to connect to the channel")
        else:
            print("\n❌ Channel not found or joined")
            
    except Exception as e:
        logger.error(f"Error: {str(e)}")
    finally:
        # Close client
        await setup.close()

if __name__ == "__main__":
    print("Pocket Option Trading Bot - Telegram Setup")
    print("------------------------------------------")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nSetup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError during setup: {str(e)}")
        sys.exit(1)
