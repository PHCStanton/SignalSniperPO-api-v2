#!/usr/bin/env python3
"""
simulate_real_signal.py - Script to simulate a trading signal for the SelfBot

This script simulates a trading signal by sending messages to the Telegram channel
that the SelfBot is monitoring. It sends the two-message format that the bot
expects, with a timer set for 1 minute in the future.
"""

import os
import sys
import asyncio
import logging
from datetime import datetime, timedelta
import pytz
from telethon import TelegramClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def simulate_signal():
    """Simulate a trading signal by sending messages to the Telegram channel."""
    # Load Telegram API credentials from environment variables or config
    api_id = os.environ.get("TELEGRAM_API_ID")
    api_hash = os.environ.get("TELEGRAM_API_HASH")
    
    if not api_id or not api_hash:
        logger.error("Telegram API ID and hash are required. Set them as environment variables.")
        return False
    
    # Initialize Telegram client
    client = None
    try:
        client = TelegramClient('signal_simulator', int(api_id), api_hash)
        await client.connect()
        
        # Check if we're logged in
        if not await client.is_user_authorized():
            logger.error("Not logged in to Telegram. Please run the script again and complete the login process.")
            phone = input("Enter your phone number: ")
            await client.send_code_request(phone)
            code = input("Enter the code: ")
            await client.sign_in(phone, code)
        
        # Get the channel entity
        channel_name = input("Enter the channel username to send the signal to (e.g., 'BINARY_TRADING_CLUB_TEST'): ")
        channel = await client.get_entity(channel_name)
        
        # Get signal parameters
        pair = input("Enter the trading pair (e.g., 'EUR/USD'): ")
        direction = input("Enter the direction (HIGHER or LOWER): ").upper()
        expiry = int(input("Enter the expiry time in minutes (e.g., 1): "))
        
        # Calculate timer (1 minute in the future)
        timezone = pytz.utc
        now = datetime.now(timezone)
        timer_time = now + timedelta(minutes=1)
        timer = timer_time.strftime("%H:%M:%S")
        
        # First message format
        first_message = f"Trading Pair: {pair}"
        
        # Second message format
        second_message = f"""SET THE TIMER TO {timer}
Currency pair {pair}
{direction}
Trade time: {expiry} MIN"""
        
        # Send first message
        logger.info(f"Sending first message: {first_message}")
        await client.send_message(entity=channel_name, message=first_message)
        
        # Wait 2 seconds
        await asyncio.sleep(2)
        
        # Send second message
        logger.info(f"Sending second message: {second_message}")
        await client.send_message(entity=channel_name, message=second_message)
        
        logger.info(f"Signal sent successfully. Timer set for {timer} ({(timer_time - now).total_seconds():.2f} seconds from now)")
        
        return True
    except Exception as e:
        logger.error(f"Error in simulate_signal: {str(e)}")
        return False
    finally:
        # Ensure client is disconnected
        if client:
            try:
                await client.disconnect()
            except Exception as e:
                logger.error(f"Error disconnecting: {str(e)}")

if __name__ == "__main__":
    print("Signal Simulator for SelfBot")
    print("----------------------------")
    print("This script simulates a trading signal by sending messages to a Telegram channel.")
    print("The bot should detect these messages and execute a trade.")
    print("")
    
    # Ask for confirmation
    confirmation = input("Are you sure you want to send a simulated signal? (yes/no): ")
    if confirmation.lower() not in ["yes", "y"]:
        print("Simulation cancelled")
        sys.exit(0)
    
    try:
        result = asyncio.run(simulate_signal())
        if result:
            print("Signal sent successfully!")
        else:
            print("Failed to send signal.")
    except KeyboardInterrupt:
        print("\nSimulation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError during simulation: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
