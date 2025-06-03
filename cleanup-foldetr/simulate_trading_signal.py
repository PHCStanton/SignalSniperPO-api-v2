#!/usr/bin/env python3
"""
simulate_trading_signal.py - Simulate a trading signal for testing

This script simulates a trading signal in the format used by the BINARY TRADING CLUB
Telegram channel and passes it to the self_bot.py for processing. It's useful for
testing the trade execution flow without waiting for actual signals.
"""

import os
import sys
import json
import asyncio
import logging
import argparse
from datetime import datetime, timedelta
import pytz

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Import the SelfBot class from self_bot.py
try:
    from self_bot import SelfBot
except ImportError:
    logger.error("Error: self_bot.py not found or cannot be imported.")
    logger.error("Make sure you're running this script from the correct directory.")
    sys.exit(1)

async def simulate_signal(pair="EUR/USD", direction="HIGHER", expiry=1, delay_minutes=1, test_mode=True):
    """
    Simulate a trading signal and pass it to the SelfBot for processing.
    
    Args:
        pair: Trading pair (e.g., EUR/USD)
        direction: Trade direction (HIGHER or LOWER)
        expiry: Trade expiry in minutes
        delay_minutes: Minutes to delay before the trade timer
        test_mode: Whether to run in test mode
    """
    # Create a SelfBot instance
    bot = SelfBot(
        config_file="config/bot_config.json",
        telegram_config_file="config/telegram_config.json",
        pocket_option_config_file="config/pocket_option_config.json",
        verbose=True
    )
    
    # Force test mode if specified
    if test_mode:
        bot.config["test_mode"] = True
        logger.info("Running in test mode")
    else:
        bot.config["test_mode"] = False
        logger.info("Running in REAL mode - ACTUAL TRADES WILL BE EXECUTED")
    
    # Initialize database
    if not bot.initialize_database():
        logger.error("Failed to initialize database")
        return
    
    # Initialize Pocket Option client
    if not bot.initialize_pocket_option():
        logger.error("Failed to initialize Pocket Option client")
        return
    
    # Get timezone
    timezone = pytz.timezone(bot.config.get("timezone", "Africa/Johannesburg"))
    
    # Create a signal for the specified delay
    now = datetime.now(timezone)
    timer_time = now + timedelta(minutes=delay_minutes)
    timer = timer_time.strftime("%H:%M:%S")
    
    # Create a test signal
    signal = {
        "pair": pair,
        "timer": timer,
        "direction": direction,
        "expiry": expiry,
        "timestamp": datetime.now(timezone).isoformat(),
        "is_valid": True,
        "validation_message": "Signal is valid"
    }
    
    logger.info(f"Created simulated signal: {signal}")
    
    # Save signal to database
    signal_id = bot.save_signal_to_db(signal)
    if signal_id:
        signal["id"] = signal_id
        logger.info(f"Signal saved to database with ID: {signal_id}")
    
    # Schedule trade execution
    logger.info(f"Scheduling trade execution for {signal['timer']} ({delay_minutes} minute(s) from now)")
    await bot.schedule_trade_execution(signal)
    
    # Wait for trade to complete (expiry + buffer)
    wait_time = (delay_minutes + expiry + 1) * 60
    logger.info(f"Waiting for trade to complete (about {wait_time/60:.1f} minutes)...")
    await asyncio.sleep(wait_time)
    
    # Print final stats
    await bot.print_stats()
    
    # Close database connection
    if bot.db_conn:
        bot.db_conn.close()
    
    logger.info("Simulation completed")

def main():
    """Main function to parse arguments and run the simulation."""
    parser = argparse.ArgumentParser(description='Simulate a trading signal for testing')
    parser.add_argument('--pair', type=str, default='EUR/USD', help='Trading pair (default: EUR/USD)')
    parser.add_argument('--direction', type=str, choices=['HIGHER', 'LOWER'], default='HIGHER', help='Trade direction (default: HIGHER)')
    parser.add_argument('--expiry', type=int, default=1, help='Trade expiry in minutes (default: 1)')
    parser.add_argument('--delay', type=int, default=1, help='Minutes to delay before the trade timer (default: 1)')
    parser.add_argument('--real', action='store_true', help='Execute a real trade (default: test mode)')
    
    args = parser.parse_args()
    
    print("\nTrading Signal Simulator")
    print("----------------------")
    print(f"Trading pair: {args.pair}")
    print(f"Direction: {args.direction}")
    print(f"Expiry: {args.expiry} minute(s)")
    print(f"Delay: {args.delay} minute(s)")
    print(f"Mode: {'REAL' if args.real else 'Test'}")
    print("")
    
    # Confirm with user if real mode
    if args.real:
        print("WARNING: You are about to execute a REAL trade with REAL money!")
        confirm = input("Are you sure you want to proceed? (y/n): ").strip().lower()
        if confirm != 'y':
            print("Operation cancelled.")
            return
    
    try:
        asyncio.run(simulate_signal(
            pair=args.pair,
            direction=args.direction,
            expiry=args.expiry,
            delay_minutes=args.delay,
            test_mode=not args.real
        ))
    except KeyboardInterrupt:
        print("\nSimulation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError during simulation: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
