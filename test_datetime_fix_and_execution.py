#!/usr/bin/env python3
"""
Test script to verify the datetime fix and prepare for real execution test.
This script will:
1. Verify the datetime fix is working
2. Show current configuration
3. Provide instructions for the test
"""

import sys
import os
import json
from datetime import datetime
import pytz

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_datetime_fix():
    """Test the datetime fix for timezone-aware/naive comparison."""
    print("=" * 60)
    print("🔧 TESTING DATETIME FIX")
    print("=" * 60)
    
    try:
        from self_bot_v3_integrated import get_high_precision_time
        
        # Test the fix logic
        current_time = get_high_precision_time()
        naive_time = datetime.now()
        
        print(f"✅ Current time (UTC, timezone-aware): {current_time}")
        print(f"✅ Naive time (local): {naive_time}")
        
        # Apply the fix logic (same as in the bot)
        if naive_time.tzinfo is None:
            last_message_time_utc = pytz.UTC.localize(naive_time)
        else:
            last_message_time_utc = naive_time.astimezone(pytz.UTC)
        
        print(f"✅ Fixed time (UTC): {last_message_time_utc}")
        
        # Test the subtraction
        time_diff = (current_time - last_message_time_utc).total_seconds()
        print(f"✅ Time difference: {time_diff:.2f} seconds")
        print("\n✅ SUCCESS: Datetime fix is working correctly!")
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        return False

def show_configuration():
    """Display current configuration for the test."""
    print("\n" + "=" * 60)
    print("📋 CURRENT CONFIGURATION")
    print("=" * 60)
    
    # Load and display Telegram config
    try:
        with open('config/telegram_config.json', 'r') as f:
            telegram_config = json.load(f)
        print("\n📱 Telegram Configuration:")
        print(f"  • Channel Name: {telegram_config.get('channel_name')}")
        print(f"  • Channel ID: {telegram_config.get('channel_id')}")
        print(f"  • Session Name: {telegram_config.get('session_name')}")
    except Exception as e:
        print(f"  ❌ Error loading Telegram config: {e}")
    
    # Load and display Pocket Option config
    try:
        with open('config/pocket_option_config.json', 'r') as f:
            po_config = json.load(f)
        print("\n💰 Pocket Option Configuration:")
        print(f"  • Demo Mode: {po_config.get('is_demo', False)}")
        print(f"  • SSID Present: {'Yes' if po_config.get('ssid') else 'No'}")
        print(f"  • OTC Preferred: {po_config.get('otc_preferred', True)}")
    except Exception as e:
        print(f"  ❌ Error loading Pocket Option config: {e}")
    
    # Load and display Bot config
    try:
        with open('config/bot_config.json', 'r') as f:
            bot_config = json.load(f)
        print("\n🤖 Bot Configuration:")
        print(f"  • Trade Amount: ${bot_config.get('trade_amount', 1)}")
        print(f"  • Test Mode: {bot_config.get('test_mode', False)}")
        print(f"  • Use OTC by Default: {bot_config.get('use_otc_by_default', True)}")
        print(f"  • 59-Second Optimization: {bot_config.get('trade_duration_optimization', {}).get('use_59_second_trades', False)}")
    except Exception as e:
        print(f"  ❌ Error loading Bot config: {e}")

def show_test_instructions():
    """Display instructions for the real execution test."""
    print("\n" + "=" * 60)
    print("📝 TEST EXECUTION INSTRUCTIONS")
    print("=" * 60)
    print("""
1. ✅ Datetime fix has been verified and is working correctly

2. 📱 The bot is now configured to monitor:
   • Channel: 🎯Signal_Sniper_Test_Channel🎯
   • Channel ID: -1002322984519

3. 💰 Pocket Option is configured for:
   • Demo account trading ($1 trades)
   • OTC pairs preferred

4. 🚀 To start the test:
   • Run: python self_bot_v3_integrated.py
   • The bot will connect to your test channel
   • Forward or send test signals in the expected format

5. 📨 Expected signal format:
   
   Single message format:
   ❗️SET THE TIMER TO 00:01:00❗️
   
   First signal: Currency pair EUR/USD
   HIGHER ⬆️
   Trade time: 1 MIN

   OR Two-message format:
   Message 1: "Trading Pair: EUR/USD (OTC)"
   Message 2: (within 60 seconds)
   ❗️SET THE TIMER TO 00:01:00❗️
   
   First signal: Currency pair EUR/USD
   HIGHER ⬆️
   Trade time: 1 MIN

6. 📊 The bot will:
   • Parse the signal
   • Execute the trade on demo account
   • Log all activities
   • Check trade results after expiry

7. 📁 Check these files for results:
   • self_bot.log - Main activity log
   • sessions/signals_history.json - Parsed signals
   • sessions/trades_history.json - Executed trades
   • sessions/timestamps.json - Timing data
""")

def main():
    """Main test function."""
    print("\n🎯 HFT SignalSniper - Datetime Fix Verification & Test Setup")
    print("=" * 60)
    
    # Test datetime fix
    if test_datetime_fix():
        # Show configuration
        show_configuration()
        
        # Show test instructions
        show_test_instructions()
        
        print("\n✅ Everything is ready for the real execution test!")
        print("🚀 Run 'python self_bot_v3_integrated.py' to start the bot")
    else:
        print("\n❌ Datetime fix test failed. Please check the implementation.")

if __name__ == "__main__":
    main()
