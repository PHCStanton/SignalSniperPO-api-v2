#!/usr/bin/env python3
"""
test_real_trade.py - Script to test real trade execution in self_bot.py

This script directly calls the signal processing functions in self_bot.py
to simulate receiving a signal and test the real trade execution functionality.
"""

import os
import sys
import json
import asyncio
import logging
import threading # <--- Add this import
from datetime import datetime, timedelta
import pytz

# Import the SelfBot class from self_bot.py
from self_bot import SelfBot

async def test_real_trade_execution():
    """Test real trade execution by simulating a signal."""
    # Create a SelfBot instance with real mode enabled
    bot = SelfBot(
        config_file="config/bot_config.json",
        telegram_config_file="config/telegram_config.json",
        pocket_option_config_file="config/pocket_option_config.json",
        verbose=True
    )
    
    # Ensure test mode is disabled for real trading
    bot.config["test_mode"] = False
    
    # Initialize JSON storage (already done in SelfBot.__init__)
    # if not bot.initialize_json_storage():  # Or simply rely on __init__
    #     print("Failed to initialize JSON storage")
    #     return
    
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
    signal_id = f"test_signal_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    signal = {
        "id": signal_id, # Ensure signal has an ID
        "pair": "EUR/USD",
        "timer": timer, # This timer is for scheduling, actual execution is immediate in this test
        "direction": "HIGHER",
        "expiry": 1, # 1 minute
        "timestamp": datetime.now(timezone).isoformat(),
        "is_valid": True, # Assume valid for test
        "validation_message": "Signal is valid for test",
        "session_id": bot.session_id # Include session_id
    }
    
    print(f"Created real trade signal: {signal}")
    
    # Save signal using JSONStorageManager
    if bot.storage.save_signal(signal):
        print(f"Signal saved to JSON storage with ID: {signal['id']}")
    else:
        print(f"Failed to save signal with ID: {signal['id']}")
        return

    # Setup session amount if not already done (SelfBot usually does this in main flow)
    if bot.session_amount is None:
        if not bot.setup_session_amount(): # This is interactive
            print("Failed to setup session amount or user cancelled. Using default from config if any, or $1.")
            bot.session_amount = bot.config.get("trade_amount", 1)


    # Execute trade directly (it runs in a thread)
    # Note: The original 'timer' in the signal was for scheduling.
    # Here, we are directly invoking execution.
    # The `execute_trade_threaded` will handle the logic.
    print(f"Executing real trade for signal ID: {signal['id']}")
    # bot.execute_trade_threaded(signal) # This is how SelfBot calls it internally
    
    # For a direct test, we might need to ensure the bot's state is ready
    # (e.g., pocket_option_client is connected and balance checked).
    # The execute_trade_threaded method itself is not async.
    # It spawns another thread for checking results.
    
    # Simulate the part of process_message that calls execute_trade_threaded
    # This ensures the trade is added to active_trades and stats are updated.
    if signal["is_valid"]:
        bot.stats["valid_signals"] += 1 # Manually update as process_message would
        # bot.pending_signals.append(signal) # Not strictly needed for this direct test
        
        # Execute trade using threading to avoid event loop conflict
        print("🚀 EXECUTING TRADE (Test Script Invocation)")
        trade_thread = threading.Thread(target=bot.execute_trade_threaded, args=(signal,))
        trade_thread.daemon = True
        trade_thread.start()
        trade_thread.join(timeout=10) # Wait briefly for the trade to be placed
    else:
        print("Signal marked invalid, not executing.")
        return

    # Wait for trade to complete (expiry + buffer for result checking thread)
    # The result checking thread inside execute_trade_threaded will sleep for expiry + 5 seconds
    wait_time_seconds = (signal['expiry'] * 60) + 15 # Add more buffer
    print(f"Waiting for trade to complete and result to be checked (about {wait_time_seconds / 60:.1f} minutes)...")
    await asyncio.sleep(wait_time_seconds)
    
    # Print final stats from bot.stats or bot.session_data
    print("\n--- Final Stats ---")
    print(f"Session ID: {bot.session_data.get('session_id')}")
    print(f"Start Time: {bot.session_data.get('start_time')}")
    print(f"Initial Balance: ${bot.session_data.get('balance_start', 0.0):.2f}")
    print(f"Session Amount: ${bot.session_data.get('session_amount', bot.config.get('trade_amount',1)):.2f}")
    print(f"Total Trades Executed in Session: {bot.session_data.get('trades_count', 0)}")
    print(f"Wins: {bot.session_data.get('wins', 0)}")
    print(f"Losses: {bot.session_data.get('losses', 0)}")
    print(f"Draws: {bot.session_data.get('draws', 0)}")
    print(f"Total Profit/Loss: ${bot.session_data.get('profit_loss', 0.0):.2f}")
    print("--------------------")
    
    # No database connection to close
    
    print("Real trade test completed")

if __name__ == "__main__":
    print("Real Trade Execution Test")
    print("-----------------------")
    print("This script tests REAL trade execution by simulating a signal.")
    print("WARNING: This will place a REAL trade with REAL money.")
    print("")
    
    # Ask for confirmation
    confirmation = input("Are you sure you want to proceed with a real trade? (yes/no): ")
    if confirmation.lower() not in ["yes", "y"]:
        print("Test cancelled by user")
        sys.exit(0)
    
    try:
        asyncio.run(test_real_trade_execution())
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError during test: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
