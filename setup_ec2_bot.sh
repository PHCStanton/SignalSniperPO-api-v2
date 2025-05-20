#!/bin/bash
# setup_ec2_bot.sh - Script to set up the Self Bot on the EC2 instance
# This script should be run on the EC2 instance

# Exit on error
set -e

echo "Setting up Self Bot on EC2 instance..."
echo "======================================"

# Create directory structure
echo "Creating directory structure..."
mkdir -p ~/selfbot/config
mkdir -p ~/selfbot/data
mkdir -p ~/selfbot/logs
mkdir -p ~/selfbot/pocketoptionapi/ws/channels
mkdir -p ~/selfbot/pocketoptionapi/ws/objects

# Install dependencies
echo "Installing dependencies..."
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv ~/selfbot/venv

# Activate virtual environment
source ~/selfbot/venv/bin/activate

# Install required packages
echo "Installing required packages..."
pip install telethon>=1.24.0 websockets>=10.3 asyncio>=3.4.3 aiohttp>=3.8.1 python-dotenv>=0.20.0 pytz>=2022.1 requests>=2.28.0 cryptography>=37.0.0

# Create configuration files
echo "Creating configuration files..."

# Create telegram_config.json
cat > ~/selfbot/config/telegram_config.json << 'EOL'
{
  "channel_name": "BINARY TRADING CLUB",
  "first_message_regex": "Trading Pair: (\\w+/\\w+)(?:\\s*\\(OTC\\))?",
  "second_message_regex": {
    "timer": "SET THE TIMER TO (\\d{2}:\\d{2}:\\d{2})",
    "pair": "Currency pair (\\w+/\\w+)",
    "direction": "(HIGHER|LOWER)",
    "expiry": "Trade time: (\\d+) MIN"
  },
  "pair_match_window": 60,
  "channel_id": -1002412213735,
  "api_id": 28529262,
  "api_hash": "6e3dde953198895cddbd7396631a1da5",
  "session_name": "pocket_option_userbot"
}
EOL

# Create pocket_option_config.json
cat > ~/selfbot/config/pocket_option_config.json << 'EOL'
{
  "ssid": "a:4:{s:10:\"session_id\";s:32:\"bde3d74bbc70c9e768874d0e3ec00fb4\";s:10:\"ip_address\";s:12:\"169.0.228.13\";s:10:\"user_agent\";s:111:\"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36\";s:13:\"last_activity\";i:1747546565;}dbad27acafe64d44d2a0ee59fe9380e1",
  "is_demo": true
}
EOL

# Create bot_config.json
cat > ~/selfbot/config/bot_config.json << 'EOL'
{
  "trade_amount": 1,
  "max_daily_trades": 20,
  "max_daily_loss": 50,
  "min_seconds_before_timer": 5,
  "test_mode": true,
  "test_mode_win_rate": 0.6,
  "stats_interval": 3600,
  "timezone": "Africa/Johannesburg",
  "log_level": "INFO",
  
  "risk_management": {
    "enabled": true,
    "max_consecutive_losses": 3,
    "max_trades_per_asset": 5,
    "max_trades_per_hour": 10,
    "recovery_mode": {
      "enabled": false,
      "increase_amount_after_loss": false,
      "increase_factor": 2.0,
      "max_recovery_attempts": 3
    }
  },
  
  "notifications": {
    "enabled": false,
    "telegram": {
      "enabled": false,
      "bot_token": "",
      "chat_id": "",
      "notify_on_signal": true,
      "notify_on_trade": true,
      "notify_on_result": true,
      "notify_on_error": true,
      "daily_report": true
    },
    "email": {
      "enabled": false,
      "smtp_server": "",
      "smtp_port": 587,
      "username": "",
      "password": "",
      "from_email": "",
      "to_email": "",
      "daily_report": true
    }
  },
  
  "advanced": {
    "reconnect_attempts": 3,
    "reconnect_delay": 5,
    "websocket_ping_interval": 30,
    "signal_buffer_size": 100,
    "trade_history_days": 30
  }
}
EOL

# Create .env file
cat > ~/selfbot/.env << 'EOL'
# Telegram API credentials
TELEGRAM_API_ID=28529262
TELEGRAM_API_HASH=6e3dde953198895cddbd7396631a1da5
EOL

# Create monitor_signals.py
echo "Creating monitor_signals.py..."
cat > ~/selfbot/monitor_signals.py << 'EOL'
#!/usr/bin/env python3
"""
monitor_signals.py - Script to monitor Telegram signals without executing trades.

This script connects to the BINARY TRADING CLUB Telegram channel and monitors
for trading signals in the two-message format. It parses and logs these signals
but does not execute any trades. This is useful for testing the signal detection
and parsing functionality without risking any real money.

Usage:
    python monitor_signals.py --telegram-config config/telegram_config.json --verbose
"""

import os
import sys
import json
import asyncio
import logging
import argparse
import re
from datetime import datetime, timedelta
import pytz
from typing import Dict, List, Optional, Tuple, Any, Union
import dotenv

# Import Telegram client
try:
    from telethon import TelegramClient, events
    from telethon.tl.types import Channel, Message
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
        logging.FileHandler("logs/monitor_signals.log")
    ]
)
logger = logging.getLogger(__name__)

class SignalMonitor:
    def __init__(
        self,
        telegram_config_file: str = "config/telegram_config.json",
        verbose: bool = False
    ):
        """
        Initialize the signal monitor.
        
        Args:
            telegram_config_file: Path to Telegram configuration file
            verbose: Enable verbose output
        """
        self.telegram_config_file = telegram_config_file
        self.verbose = verbose
        
        # Set logging level
        if verbose:
            logger.setLevel(logging.DEBUG)
        
        # Load configuration
        self.telegram_config = self._load_config(telegram_config_file)
        
        # Initialize client
        self.telegram_client = None
        
        # Signal tracking
        self.last_first_message = None
        self.last_first_message_time = None
        self.detected_signals = []
        
        # Timezone
        self.timezone = pytz.timezone("Africa/Johannesburg")
        
        # Stats
        self.stats = {
            "total_messages": 0,
            "first_messages": 0,
            "second_messages": 0,
            "complete_signals": 0,
            "start_time": datetime.now(self.timezone),
        }
    
    def _load_config(self, config_file: str) -> Dict[str, Any]:
        """Load configuration from file or create default."""
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.error(f"Error parsing config file: {config_file}")
                return {}
        else:
            logger.warning(f"Configuration file {config_file} not found. Using defaults.")
            return {}
    
    async def initialize_telegram(self) -> bool:
        """
        Initialize the Telegram client.
        
        Returns:
            True if initialized successfully, False otherwise
        """
        try:
            # Get Telegram API credentials
            api_id = self.telegram_config.get("api_id") or os.environ.get("TELEGRAM_API_ID")
            api_hash = self.telegram_config.get("api_hash") or os.environ.get("TELEGRAM_API_HASH")
            session_name = self.telegram_config.get("session_name", "pocket_option_userbot")
            
            if not api_id or not api_hash:
                logger.error("Telegram API ID and hash are required. Set them in the config file or environment variables.")
                return False
            
            logger.info("Initializing Telegram client...")
            
            # User account mode
            self.telegram_client = TelegramClient(session_name, int(api_id), api_hash)
            await self.telegram_client.start()
            logger.info("Started Telegram client in user account mode")
            
            # Check if we need to complete the phone verification process
            if not await self.telegram_client.is_user_authorized():
                logger.info("User not authorized. Please complete the login process.")
                await self.telegram_client.send_code_request(input("Enter your phone number: "))
                await self.telegram_client.sign_in(input("Enter your phone number again: "), input("Enter the code: "))
                logger.info("Successfully authenticated")
            else:
                logger.info("Already authenticated using existing session")
                me = await self.telegram_client.get_me()
                logger.info(f"Logged in as: {me.first_name} {getattr(me, 'last_name', '')} (@{me.username})")
            
            return True
        except Exception as e:
            logger.error(f"Error initializing Telegram client: {str(e)}")
            return False
    
    async def access_channel(self) -> Optional[Channel]:
        """
        Access a Telegram channel that the user is already a member of.
        
        Returns:
            Channel object if found, None otherwise
        """
        if not self.telegram_client:
            logger.error("Telegram client not initialized")
            return None
        
        channel_name = self.telegram_config.get("channel_name", "BINARY TRADING CLUB")
        channel_username = self.telegram_config.get("channel_username")
        channel_id = self.telegram_config.get("channel_id")
        
        logger.info(f"Accessing channel: {channel_name}")
        
        try:
            # Try to use channel ID if available
            if channel_id:
                try:
                    entity = await self.telegram_client.get_entity(int(channel_id))
                    logger.info(f"Accessed channel by ID: {entity.title}")
                    return entity
                except Exception as e:
                    logger.debug(f"Error accessing channel by ID: {str(e)}")
            
            # Try to use channel username if available
            if channel_username:
                try:
                    entity = await self.telegram_client.get_entity(channel_username)
                    logger.info(f"Accessed channel by username: {entity.title}")
                    return entity
                except Exception as e:
                    logger.debug(f"Error accessing channel by username: {str(e)}")
            
            # Try to find by name in dialog list
            async for dialog in self.telegram_client.iter_dialogs():
                if dialog.name == channel_name or (hasattr(dialog.entity, 'username') and dialog.entity.username == channel_username):
                    logger.info(f"Found channel in dialog list: {dialog.name}")
                    return dialog.entity
            
            logger.warning(f"Channel not found: {channel_name}")
            logger.warning("Please ensure your Telegram account is already a member of this channel.")
            return None
            
        except Exception as e:
            logger.error(f"Error accessing channel: {str(e)}")
            return None
    
    def parse_first_message(self, message_text: str) -> Optional[str]:
        """
        Parse the first message of the signal format.
        
        Args:
            message_text: Message text to parse
            
        Returns:
            Trading pair if found, None otherwise
        """
        pattern = self.telegram_config.get("first_message_regex", r"Trading Pair: (\w+/\w+)(?:\s*\(OTC\))?")
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
        second_message_regex = self.telegram_config.get("second_message_regex", {})
        
        # Extract timer
        timer_pattern = second_message_regex.get("timer", r"SET THE TIMER TO (\d{2}:\d{2}:\d{2})")
        timer_match = re.search(timer_pattern, message_text)
        if not timer_match:
            return None
        timer = timer_match.group(1)
        
        # Extract pair
        pair_pattern = second_message_regex.get("pair", r"Currency pair (\w+/\w+)")
        pair_match = re.search(pair_pattern, message_text)
        if not pair_match:
            return None
        pair = pair_match.group(1)
        
        # Extract direction
        direction_pattern = second_message_regex.get("direction", r"(HIGHER|LOWER)")
        direction_match = re.search(direction_pattern, message_text)
        if not direction_match:
            return None
        direction = direction_match.group(1)
        
        # Extract expiry
        expiry_pattern = second_message_regex.get("expiry", r"Trade time: (\d+) MIN")
        expiry_match = re.search(expiry_pattern, message_text)
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
            
        # Increment message counter
        self.stats["total_messages"] += 1
            
        # Log all messages
        sender = await message.get_sender()
        sender_name = getattr(sender, 'first_name', 'Unknown')
        logger.info(f"Message from {sender_name}: {message.text}")
        
        # Try to parse as first message
        trading_pair = self.parse_first_message(message.text)
        if trading_pair:
            self.last_first_message = trading_pair
            self.last_first_message_time = datetime.now(self.timezone)
            self.stats["first_messages"] += 1
            logger.info(f"Detected first message with trading pair: {trading_pair}")
            return
            
        # Try to parse as second message
        if self.last_first_message and self.last_first_message_time:
            # Check if the time between messages is within the allowed window
            pair_match_window = self.telegram_config.get("pair_match_window", 60)
            time_diff = (datetime.now(self.timezone) - self.last_first_message_time).total_seconds()
            
            if time_diff <= pair_match_window:
                signal = self.parse_second_message(message.text)
                if signal:
                    self.stats["second_messages"] += 1
                    
                    # Verify that the pair matches
                    if signal["pair"] == self.last_first_message:
                        # Complete signal
                        complete_signal = {
                            "pair": self.last_first_message,
                            "timer": signal["timer"],
                            "direction": signal["direction"],
                            "expiry": signal["expiry"],
                            "timestamp": datetime.now(self.timezone).isoformat()
                        }
                        
                        logger.info(f"Complete signal detected: {complete_signal}")
                        self.detected_signals.append(complete_signal)
                        self.stats["complete_signals"] += 1
                        
                        # Reset tracking
                        self.last_first_message = None
                        self.last_first_message_time = None
                    else:
                        logger.warning(f"Pair mismatch: {self.last_first_message} vs {signal['pair']}")
    
    async def setup_message_handler(self) -> None:
        """Set up the message handler for the channel."""
        if not self.telegram_client:
            logger.error("Telegram client not initialized")
            return
            
        channel_id = self.telegram_config.get("channel_id")
        if not channel_id:
            logger.error("Channel ID not found in configuration")
            return
            
        @self.telegram_client.on(events.NewMessage(chats=channel_id))
        async def message_handler(event):
            await self.process_message(event.message)
            
        logger.info(f"Message handler set up for channel ID: {channel_id}")
    
    async def print_stats(self) -> None:
        """Print monitoring statistics."""
        runtime = datetime.now(self.timezone) - self.stats["start_time"]
        runtime_str = str(runtime).split('.')[0]  # Remove microseconds
        
        print("\n" + "="*50)
        print(f"SIGNAL MONITORING STATISTICS - {datetime.now(self.timezone).strftime('%Y-%m-%d %H:%M:%S')} (SAST)")
        print("="*50)
        print(f"Runtime: {runtime_str}")
        print(f"Total messages: {self.stats['total_messages']}")
        print(f"First messages: {self.stats['first_messages']}")
        print(f"Second messages: {self.stats['second_messages']}")
        print(f"Complete signals: {self.stats['complete_signals']}")
        print("="*50)
        
        if self.detected_signals:
            print("\nDetected Signals:")
            for i, signal in enumerate(self.detected_signals):
                print(f"\nSignal {i+1}:")
                print(f"  Pair: {signal['pair']}")
                print(f"  Direction: {signal['direction']}")
                print(f"  Timer: {signal['timer']}")
                print(f"  Expiry: {signal['expiry']} minutes")
                print(f"  Detected at: {signal['timestamp']}")
        print("="*50)
    
    async def run(self, duration: Optional[int] = None) -> None:
        """
        Run the signal monitor.
        
        Args:
            duration: Duration to run in seconds (None for indefinite)
        """
        try:
            # Initialize Telegram client
            if not await self.initialize_telegram():
                logger.error("Failed to initialize Telegram client")
                return
                
            # Access channel
            channel = await self.access_channel()
            if not channel:
                logger.error("Failed to access channel")
                logger.error("Please ensure your Telegram account is already a member of the channel.")
                return
                
            # Set up message handler
            await self.setup_message_handler()
            
            # Print initial stats
            await self.print_stats()
            
            # Keep the monitor running
            logger.info("Signal monitor is running. Press Ctrl+C to stop.")
            
            if duration:
                logger.info(f"Monitor will run for {duration} seconds")
                end_time = datetime.now() + timedelta(seconds=duration)
                
                # Print stats every minute
                while datetime.now() < end_time:
                    await asyncio.sleep(60)
                    await self.print_stats()
                    
                logger.info(f"Monitor duration of {duration} seconds reached")
            else:
                # Print stats every 5 minutes
                while True:
                    await asyncio.sleep(300)
                    await self.print_stats()
                
        except KeyboardInterrupt:
            logger.info("Monitor interrupted by user")
        except Exception as e:
            logger.error(f"Error running monitor: {str(e)}")
        finally:
            # Close connections
            if self.telegram_client:
                await self.telegram_client.disconnect()
                
            logger.info("Monitor stopped")
            
            # Print final stats
            await self.print_stats()

async def main():
    parser = argparse.ArgumentParser(description='Monitor Telegram signals without executing trades')
    parser.add_argument('--telegram-config', type=str, default='config/telegram_config.json', help='Path to Telegram configuration file')
    parser.add_argument('--duration', type=int, help='Duration to run in seconds')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose output')
    parser.add_argument('--test-mode', action='store_true', help='Run in test mode (no trade execution)')
    
    args = parser.parse_args()
    
    # Load environment variables
    dotenv.load_dotenv()
    
    # Create monitor
    monitor = SignalMonitor(
        telegram_config_file=args.telegram_config,
        verbose=args.verbose
    )
    
    try:
        # Run monitor
        await monitor.run(args.duration)
    except Exception as e:
        print(f"Error running monitor: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    print("Telegram Signal Monitor")
    print("----------------------")
    print("This script monitors the BINARY TRADING CLUB Telegram channel for trading signals")
    print("and logs them without executing any trades.")
    print("")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nMonitor interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError running monitor: {str(e)}")
        sys.exit(1)
EOL

# Create systemd service file
echo "Creating systemd service file..."
cat > ~/selfbot_service.service << 'EOL'
[Unit]
Description=Self Bot Service
After=network.target

[Service]
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/selfbot
ExecStart=/home/ubuntu/selfbot/venv/bin/python3 /home/ubuntu/selfbot/monitor_signals.py --telegram-config config/telegram_config.json --verbose
Restart=always
EnvironmentFile=/home/ubuntu/selfbot/.env

[Install]
WantedBy=multi-user.target
EOL

# Install systemd service
echo "Installing systemd service..."
sudo mv ~/selfbot_service.service /etc/systemd/system/selfbot.service
sudo systemctl daemon-reload
sudo systemctl enable selfbot.service

# Create session file
echo "Creating session file..."
if [ -f ~/pocket_option_userbot.session ]; then
    cp ~/pocket_option_userbot.session ~/selfbot/pocket_option_userbot.session
fi

echo "Setup complete!"
echo "You can now start the Self Bot with: sudo systemctl start selfbot.service"
echo "To check the status: sudo systemctl status selfbot.service"
echo "To view logs: sudo journalctl -u selfbot.service -f"
