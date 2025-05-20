#!/usr/bin/env python3
"""
simulate_trading_signals.py - Simulate trading signals for testing Self Bot v1.0

This script simulates trading signals in the format expected by the Self Bot v1.0.
It sends two messages to the Telegram API that mimic the signal format from the
BINARY TRADING CLUB channel. This is useful for testing the bot's signal processing
and trade execution without having to wait for actual signals.
"""

import os
import sys
import json
import asyncio
import logging
import argparse
from datetime import datetime, timedelta
import pytz
import dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("simulate_trading_signals.log")
    ]
)
logger = logging.getLogger(__name__)

# Import Telegram client
try:
    from telethon import TelegramClient
    from telethon.tl.types import InputPeerUser, InputPeerChannel
except ImportError:
    logger.error("Error: telethon package is not installed.")
    logger.error("Please install it using: pip install telethon")
    sys.exit(1)

async def send_simulated_signals(
    api_id: int,
    api_hash: str,
    session_name: str,
    channel_id: int,
    asset: str = "EUR/USD",
    direction: str = "HIGHER",
    expiry: int = 5,
    delay_seconds: int = 30
):
    """
    Send simulated trading signals to a Telegram channel.
    
    Args:
        api_id: Telegram API ID
        api_hash: Telegram API hash
        session_name: Session name for Telethon
        channel_id: Channel ID to send signals to
        asset: Trading pair (e.g., "EUR/USD")
        direction: Trading direction ("HIGHER" or "LOWER")
        expiry: Expiry time in minutes
        delay_seconds: Delay between first and second message in seconds
    """
    try:
        # Initialize Telegram client
        client = TelegramClient(session_name, api_id, api_hash)
        await client.start()
        
        # Check if we're logged in
        if not await client.is_user_authorized():
            logger.error("Not authorized. Please run the script after logging in with your Telegram account.")
            await client.disconnect()
            return False
        
        # Get the channel entity
        try:
            channel = await client.get_entity(channel_id)
            logger.info(f"Found channel: {getattr(channel, 'title', channel_id)}")
        except Exception as e:
            logger.error(f"Error getting channel: {str(e)}")
            await client.disconnect()
            return False
        
        # Calculate timer for second message
        now = datetime.now(pytz.timezone('Africa/Johannesburg'))
        timer_time = now + timedelta(seconds=delay_seconds + 10)  # Add 10 seconds buffer
        timer = timer_time.strftime("%H:%M:%S")
        
        # First message format
        first_message = f"Trading Pair: {asset}"
        
        # Send first message
        logger.info(f"Sending first message: {first_message}")
        await client.send_message(channel, first_message)
        
        # Wait for specified delay
        logger.info(f"Waiting {delay_seconds} seconds before sending second message...")
        await asyncio.sleep(delay_seconds)
        
        # Second message format
        second_message = f"""
🔴 SET THE TIMER TO {timer} 🔴

Currency pair {asset}

{direction}

Trade time: {expiry} MIN
"""
        
        # Send second message
        logger.info(f"Sending second message with timer {timer}")
        await client.send_message(channel, second_message)
        
        logger.info("Simulated signals sent successfully")
        
        # Disconnect
        await client.disconnect()
        return True
    
    except Exception as e:
        logger.error(f"Error sending simulated signals: {str(e)}")
        return False

async def main():
    """Main function to parse arguments and send simulated signals."""
    parser = argparse.ArgumentParser(description='Simulate trading signals for testing Self Bot v1.0')
    parser.add_argument('--config', type=str, default='config/telegram_config.json', help='Path to Telegram configuration file')
    parser.add_argument('--asset', type=str, default='EUR/USD', help='Trading pair (e.g., "EUR/USD")')
    parser.add_argument('--direction', type=str, choices=['HIGHER', 'LOWER'], default='HIGHER', help='Trading direction')
    parser.add_argument('--expiry', type=int, default=5, help='Expiry time in minutes')
    parser.add_argument('--delay', type=int, default=30, help='Delay between first and second message in seconds')
    
    args = parser.parse_args()
    
    # Load .env file if it exists
    dotenv.load_dotenv()
    
    # Load configuration
    if os.path.exists(args.config):
        with open(args.config, 'r') as f:
            config = json.load(f)
    else:
        logger.error(f"Configuration file {args.config} not found.")
        return False
    
    # Get Telegram API credentials
    api_id = config.get("api_id") or os.environ.get("TELEGRAM_API_ID")
    api_hash = config.get("api_hash") or os.environ.get("TELEGRAM_API_HASH")
    session_name = config.get("session_name", "pocket_option_userbot")
    channel_id = config.get("channel_id")
    
    if not api_id or not api_hash:
        logger.error("Telegram API ID and hash are required. Set them in the config file or environment variables.")
        return False
    
    if not channel_id:
        logger.error("Channel ID is required. Set it in the config file.")
        return False
    
    # Send simulated signals
    return await send_simulated_signals(
        api_id=int(api_id),
        api_hash=api_hash,
        session_name=session_name,
        channel_id=int(channel_id),
        asset=args.asset,
        direction=args.direction,
        expiry=args.expiry,
        delay_seconds=args.delay
    )

if __name__ == "__main__":
    print("Simulating trading signals for testing Self Bot v1.0...")
    
    try:
        result = asyncio.run(main())
        if result:
            print("Signals sent successfully!")
            sys.exit(0)
        else:
            print("Failed to send signals.")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {str(e)}")
        sys.exit(1)
