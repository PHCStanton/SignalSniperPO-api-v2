#!/usr/bin/env python3
"""
simulate_test_signals.py - Script to simulate trading signals for testing.

This script simulates the two-message format used by the BINARY TRADING CLUB
channel to test the signal monitoring functionality. It can send test signals
to a specified Telegram channel or directly to the monitor_signals.py script.

Usage:
    python simulate_test_signals.py --channel-id YOUR_TEST_CHANNEL_ID
    python simulate_test_signals.py --local-test
"""

import os
import sys
import json
import asyncio
import logging
import argparse
import random
from datetime import datetime, timedelta
import pytz
import dotenv

# Import Telegram client
try:
    from telethon import TelegramClient
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
        logging.FileHandler("simulate_signals.log")
    ]
)
logger = logging.getLogger(__name__)

# Sample trading pairs
TRADING_PAIRS = [
    "EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD", "USD/CAD",
    "NZD/USD", "USD/CHF", "EUR/GBP", "EUR/JPY", "GBP/JPY"
]

# Sample directions
DIRECTIONS = ["HIGHER", "LOWER"]

# Sample expiry times (in minutes)
EXPIRY_TIMES = [1, 2, 3, 5, 10, 15]

class SignalSimulator:
    def __init__(
        self,
        api_id: int,
        api_hash: str,
        session_name: str = "test_session",
        channel_id: int = None,
        timezone: str = "Africa/Johannesburg"
    ):
        """
        Initialize the signal simulator.
        
        Args:
            api_id: Telegram API ID
            api_hash: Telegram API hash
            session_name: Session name for telethon
            channel_id: Channel ID to send signals to
            timezone: Timezone for signal timers
        """
        self.api_id = api_id
        self.api_hash = api_hash
        self.session_name = session_name
        self.channel_id = channel_id
        self.timezone = pytz.timezone(timezone)
        self.client = None
    
    async def initialize(self) -> bool:
        """
        Initialize the Telegram client.
        
        Returns:
            True if initialized successfully, False otherwise
        """
        try:
            logger.info("Initializing Telegram client...")
            
            self.client = TelegramClient(self.session_name, self.api_id, self.api_hash)
            await self.client.start()
            
            if not await self.client.is_user_authorized():
                logger.info("User not authorized. Please complete the login process.")
                await self.client.send_code_request(input("Enter your phone number: "))
                await self.client.sign_in(input("Enter your phone number again: "), input("Enter the code: "))
                logger.info("Successfully authenticated")
            else:
                logger.info("Already authenticated using existing session")
                me = await self.client.get_me()
                logger.info(f"Logged in as: {me.first_name} {getattr(me, 'last_name', '')} (@{me.username})")
            
            return True
        except Exception as e:
            logger.error(f"Error initializing Telegram client: {str(e)}")
            return False
    
    def generate_signal(self) -> dict:
        """
        Generate a random trading signal.
        
        Returns:
            Dictionary with signal details
        """
        # Select random trading pair
        pair = random.choice(TRADING_PAIRS)
        
        # Select random direction
        direction = random.choice(DIRECTIONS)
        
        # Select random expiry time
        expiry = random.choice(EXPIRY_TIMES)
        
        # Generate timer (current time + 1-5 minutes)
        now = datetime.now(self.timezone)
        timer_time = now + timedelta(minutes=random.randint(1, 5))
        timer = timer_time.strftime("%H:%M:%S")
        
        return {
            "pair": pair,
            "direction": direction,
            "expiry": expiry,
            "timer": timer
        }
    
    def format_first_message(self, signal: dict) -> str:
        """
        Format the first message of the signal.
        
        Args:
            signal: Signal details
            
        Returns:
            Formatted first message
        """
        return f"Trading Pair: {signal['pair']}"
    
    def format_second_message(self, signal: dict) -> str:
        """
        Format the second message of the signal.
        
        Args:
            signal: Signal details
            
        Returns:
            Formatted second message
        """
        return (
            f"SET THE TIMER TO {signal['timer']}\n"
            f"Currency pair {signal['pair']}\n"
            f"{signal['direction']}\n"
            f"Trade time: {signal['expiry']} MIN"
        )
    
    async def send_signal_to_channel(self, signal: dict) -> bool:
        """
        Send a signal to the specified channel.
        
        Args:
            signal: Signal details
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.client or not self.channel_id:
            logger.error("Client not initialized or channel ID not specified")
            return False
        
        try:
            # Format messages
            first_message = self.format_first_message(signal)
            second_message = self.format_second_message(signal)
            
            # Send first message
            logger.info(f"Sending first message: {first_message}")
            await self.client.send_message(self.channel_id, first_message)
            
            # Wait a few seconds between messages
            await asyncio.sleep(random.uniform(1.5, 3.0))
            
            # Send second message
            logger.info(f"Sending second message: {second_message}")
            await self.client.send_message(self.channel_id, second_message)
            
            logger.info("Signal sent successfully")
            return True
        except Exception as e:
            logger.error(f"Error sending signal: {str(e)}")
            return False
    
    async def simulate_signals(self, count: int = 1, interval: int = 60) -> None:
        """
        Simulate multiple signals.
        
        Args:
            count: Number of signals to simulate
            interval: Interval between signals in seconds
        """
        logger.info(f"Simulating {count} signals with {interval} seconds interval")
        
        for i in range(count):
            signal = self.generate_signal()
            logger.info(f"Simulating signal {i+1}/{count}: {signal}")
            
            success = await self.send_signal_to_channel(signal)
            
            if success:
                logger.info(f"Signal {i+1}/{count} simulated successfully")
            else:
                logger.error(f"Failed to simulate signal {i+1}/{count}")
            
            if i < count - 1:
                logger.info(f"Waiting {interval} seconds before next signal")
                await asyncio.sleep(interval)
    
    async def close(self) -> None:
        """Close the Telegram client."""
        if self.client:
            await self.client.disconnect()
            logger.info("Telegram client disconnected")

def simulate_local_signals(count: int = 1, interval: int = 5) -> None:
    """
    Simulate signals locally by directly calling the monitor_signals.py script.
    
    Args:
        count: Number of signals to simulate
        interval: Interval between signals in seconds
    """
    logger.info(f"Simulating {count} signals locally with {interval} seconds interval")
    
    # Import the SignalMonitor class from monitor_signals.py
    try:
        sys.path.append(os.getcwd())
        from monitor_signals import SignalMonitor
    except ImportError:
        logger.error("Error importing SignalMonitor from monitor_signals.py")
        logger.error("Make sure monitor_signals.py is in the current directory")
        return
    
    # Create a mock Message class for testing
    class MockMessage:
        def __init__(self, text):
            self.text = text
        
        async def get_sender(self):
            class MockSender:
                first_name = "Test Simulator"
            return MockSender()
    
    # Create a signal monitor instance
    monitor = SignalMonitor(telegram_config_file="config/telegram_config.json", verbose=True)
    
    # Generate and process signals
    for i in range(count):
        # Generate a random signal
        signal = {
            "pair": random.choice(TRADING_PAIRS),
            "direction": random.choice(DIRECTIONS),
            "expiry": random.choice(EXPIRY_TIMES),
            "timer": (datetime.now() + timedelta(minutes=random.randint(1, 5))).strftime("%H:%M:%S")
        }
        
        # Format messages
        first_message = f"Trading Pair: {signal['pair']}"
        second_message = (
            f"SET THE TIMER TO {signal['timer']}\n"
            f"Currency pair {signal['pair']}\n"
            f"{signal['direction']}\n"
            f"Trade time: {signal['expiry']} MIN"
        )
        
        logger.info(f"Simulating signal {i+1}/{count}: {signal}")
        
        # Process first message
        logger.info(f"Processing first message: {first_message}")
        asyncio.run(monitor.process_message(MockMessage(first_message)))
        
        # Wait a few seconds between messages
        time.sleep(random.uniform(1.5, 3.0))
        
        # Process second message
        logger.info(f"Processing second message: {second_message}")
        asyncio.run(monitor.process_message(MockMessage(second_message)))
        
        logger.info(f"Signal {i+1}/{count} simulated successfully")
        
        if i < count - 1:
            logger.info(f"Waiting {interval} seconds before next signal")
            time.sleep(interval)
    
    # Print final stats
    asyncio.run(monitor.print_stats())

async def main():
    parser = argparse.ArgumentParser(description='Simulate trading signals for testing')
    parser.add_argument('--api-id', type=int, help='Telegram API ID')
    parser.add_argument('--api-hash', type=str, help='Telegram API hash')
    parser.add_argument('--session', type=str, default='test_session', help='Session name')
    parser.add_argument('--channel-id', type=int, help='Channel ID to send signals to')
    parser.add_argument('--count', type=int, default=1, help='Number of signals to simulate')
    parser.add_argument('--interval', type=int, default=60, help='Interval between signals in seconds')
    parser.add_argument('--local-test', action='store_true', help='Simulate signals locally without sending to Telegram')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # Load environment variables
    dotenv.load_dotenv()
    
    if args.local_test:
        # Import time module for local testing
        import time
        
        # Simulate signals locally
        simulate_local_signals(args.count, args.interval)
        return
    
    # Get API credentials
    api_id = args.api_id or os.environ.get('TELEGRAM_API_ID')
    api_hash = args.api_hash or os.environ.get('TELEGRAM_API_HASH')
    
    if not api_id or not api_hash:
        # Try to load from config file
        try:
            with open("config/telegram_config.json", 'r') as f:
                config = json.load(f)
                api_id = config.get('api_id')
                api_hash = config.get('api_hash')
        except (FileNotFoundError, json.JSONDecodeError):
            pass
    
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
    
    # Get channel ID
    channel_id = args.channel_id
    if not channel_id:
        # Try to load from config file
        try:
            with open("config/telegram_config.json", 'r') as f:
                config = json.load(f)
                channel_id = config.get('channel_id')
        except (FileNotFoundError, json.JSONDecodeError):
            pass
    
    if not channel_id:
        logger.error("Channel ID not specified")
        return
    
    # Create simulator
    simulator = SignalSimulator(
        api_id=api_id,
        api_hash=api_hash,
        session_name=args.session,
        channel_id=channel_id
    )
    
    try:
        # Initialize client
        if not await simulator.initialize():
            logger.error("Failed to initialize Telegram client")
            return
        
        # Simulate signals
        await simulator.simulate_signals(args.count, args.interval)
    except Exception as e:
        logger.error(f"Error simulating signals: {str(e)}")
    finally:
        # Close client
        await simulator.close()

if __name__ == "__main__":
    print("Trading Signal Simulator")
    print("----------------------")
    print("This script simulates trading signals for testing the signal monitoring functionality.")
    print("")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nSimulation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError during simulation: {str(e)}")
        sys.exit(1)
