#!/usr/bin/env python3
"""
test_trade_execution.py - Script to test trade execution in self_bot.py

This script directly calls the signal processing functions in self_bot.py
to simulate receiving a signal and test the trade execution functionality.
"""

import os
import sys
import json
import asyncio
import logging
from datetime import datetime, timedelta
import pytz

# Import the SelfBot class from self_bot.py
from self_bot import SelfBot

async def test_trade_execution():
    """Test trade execution by simulating a signal."""
    # Create a SelfBot instance with test mode enabled
    bot = SelfBot(
        config_file="config/bot_config.json",
        telegram_config_file="config/telegram_config.json",
        pocket_option_config_file="config/pocket_option_config.json",
        verbose=True
    )
    
    # Force test mode
    bot.config["test_mode"] = True
    
    # Initialize database
    if not bot.initialize_database():
        print("Failed to initialize database")
        return
    
    # Initialize Pocket Option client
    if not bot.initialize_pocket_option():
        print("Failed to initialize Pocket Option client")
        return
    
    # Get timezone
    timezone = pytz.timezone(bot.config.get("timezone", "Africa/Johannesburg"))
    
    # Create a signal for 1 minute in the future
    now = datetime.now(timezone)
    timer_time = now + timedelta(minutes=1)
    timer = timer_time.strftime("%H:%M:%S")
    
    # Create a test signal
    signal = {
        "pair": "EUR/USD",
        "timer": timer,
        "direction": "HIGHER",
        "expiry": 1,
        "timestamp": datetime.now(timezone).isoformat(),
        "is_valid": True,
        "validation_message": "Signal is valid"
    }
    
    print(f"Created test signal: {signal}")
    
    # Save signal to database
    signal_id = bot.save_signal_to_db(signal)
    if signal_id:
        signal["id"] = signal_id
        print(f"Signal saved to database with ID: {signal_id}")
    
    # Schedule trade execution
    print(f"Scheduling trade execution for {signal['timer']} (about 1 minute from now)")
    await bot.schedule_trade_execution(signal)
    
    # Wait for trade to complete (expiry + buffer)
    print(f"Waiting for trade to complete (about {signal['expiry'] + 1} minutes)...")
    await asyncio.sleep((signal['expiry'] + 1) * 60)
    
    # Print final stats
    await bot.print_stats()
    
    # Close database connection
    if bot.db_conn:
        bot.db_conn.close()
    
    print("Test completed")

if __name__ == "__main__":
    print("Trade Execution Test")
    print("-------------------")
    print("This script tests trade execution by simulating a signal.")
    print("")
    
    try:
        asyncio.run(test_trade_execution())
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError during test: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
