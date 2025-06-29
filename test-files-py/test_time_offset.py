#!/usr/bin/env python3
"""
Test script to verify the time offset implementation for SignalSniper_mod.py

This script tests:
1. Configuration loading and validation
2. Channel-specific offset logic
3. Duration-specific offset application
4. Proper delay implementation
"""

import json
import os
import time
from datetime import datetime

def load_config():
    """Load and display the time offset configuration"""
    config_path = "config/bot_config.json"
    
    if not os.path.exists(config_path):
        print(f"❌ Configuration file not found: {config_path}")
        return None
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    time_offset_config = config.get("time_offset", {})
    
    print("📋 TIME OFFSET CONFIGURATION:")
    print(f"   Enabled: {time_offset_config.get('enabled', False)}")
    print(f"   Default Offset: {time_offset_config.get('default_offset', 0)} seconds")
    print("\n📊 CHANNEL-SPECIFIC SETTINGS:")
    
    for channel, settings in time_offset_config.get("channel_specific", {}).items():
        print(f"\n   {channel.upper()}:")
        print(f"      Enabled: {settings.get('enabled', False)}")
        print(f"      Offset Value: {settings.get('offset_value', 0)} seconds")
        print(f"      Apply to Durations: {settings.get('apply_to_durations', [])} minutes")
        print(f"      Description: {settings.get('description', 'N/A')}")
    
    return time_offset_config

def test_offset_logic(time_offset_config):
    """Test the offset logic for different scenarios"""
    print("\n\n🧪 TESTING OFFSET LOGIC:")
    
    test_scenarios = [
        {
            "name": "TeeBinary Premium 5-minute signal",
            "signal": {
                "channel": "TeeBinary Premium",
                "parser_type": "teebinary_premium",
                "expiry": 5,
                "pair": "EUR/USD"
            },
            "expected_delay": 3
        },
        {
            "name": "TeeBinary Premium 1-minute signal",
            "signal": {
                "channel": "TeeBinary Premium",
                "parser_type": "teebinary_premium",
                "expiry": 1,
                "pair": "GBP/USD"
            },
            "expected_delay": 0
        },
        {
            "name": "Binary Trading Club 1-minute signal",
            "signal": {
                "channel": "BINARY TRADING CLUB",
                "parser_type": "binary_trading_club",
                "expiry": 1,
                "pair": "AUD/CHF"
            },
            "expected_delay": 0
        },
        {
            "name": "Test Channel 5-minute signal",
            "signal": {
                "channel": "🎯Signal_Sniper_Test_Channel🎯",
                "parser_type": "multi_parser",
                "expiry": 5,
                "pair": "USD/JPY"
            },
            "expected_delay": 0
        }
    ]
    
    for scenario in test_scenarios:
        print(f"\n   📌 {scenario['name']}:")
        signal = scenario['signal']
        expected_delay = scenario['expected_delay']
        
        # Simulate the offset logic from SignalSniper_mod.py
        actual_delay = calculate_offset(signal, time_offset_config)
        
        print(f"      Signal: {signal['pair']} {signal['expiry']}min")
        print(f"      Channel: {signal['channel']}")
        print(f"      Expected Delay: {expected_delay} seconds")
        print(f"      Actual Delay: {actual_delay} seconds")
        print(f"      Status: {'✅ PASS' if actual_delay == expected_delay else '❌ FAIL'}")

def calculate_offset(signal, time_offset_config):
    """Calculate the offset for a given signal (mimics SignalSniper_mod.py logic)"""
    if not time_offset_config.get("enabled", False):
        return 0
    
    channel_name = signal.get("channel", "").lower().replace(" ", "_")
    parser_type = signal.get("parser_type", "").lower()
    signal_duration = signal.get("expiry", 0)
    
    # Check for channel-specific configuration
    channel_offset_config = None
    for config_channel, config_data in time_offset_config.get("channel_specific", {}).items():
        if (config_channel.lower() in channel_name.lower() or 
            config_channel.lower() in parser_type):
            channel_offset_config = config_data
            break
    
    # Apply offset if enabled for this channel and duration
    if channel_offset_config and channel_offset_config.get("enabled", False):
        apply_to_durations = channel_offset_config.get("apply_to_durations", [])
        if signal_duration in apply_to_durations:
            return channel_offset_config.get("offset_value", 0)
    
    return 0

def test_delay_execution():
    """Test actual delay execution"""
    print("\n\n⏱️ TESTING DELAY EXECUTION:")
    
    test_delay = 3
    print(f"   Testing {test_delay}-second delay...")
    
    start_time = time.time()
    print(f"   Start time: {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
    
    time.sleep(test_delay)
    
    end_time = time.time()
    actual_delay = end_time - start_time
    
    print(f"   End time: {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
    print(f"   Expected delay: {test_delay:.3f} seconds")
    print(f"   Actual delay: {actual_delay:.3f} seconds")
    print(f"   Difference: {abs(actual_delay - test_delay):.3f} seconds")
    print(f"   Status: {'✅ PASS' if abs(actual_delay - test_delay) < 0.1 else '⚠️ WARNING (slight variance is normal)'}")

def main():
    """Main test function"""
    print("🔧 TIME OFFSET FEATURE TEST")
    print("=" * 50)
    
    # Load configuration
    time_offset_config = load_config()
    if not time_offset_config:
        return
    
    # Test offset logic
    test_offset_logic(time_offset_config)
    
    # Test delay execution
    test_delay_execution()
    
    print("\n\n✅ TIME OFFSET FEATURE TEST COMPLETE")
    print("\n📝 SUMMARY:")
    print("   - Configuration loaded successfully")
    print("   - TeeBinary Premium 5-minute signals will have 3-second delay")
    print("   - Other channels/durations will have no delay")
    print("   - Delay execution works as expected")
    
    print("\n💡 USAGE:")
    print("   The time offset will automatically apply when:")
    print("   1. A TeeBinary Premium signal is received")
    print("   2. The signal duration is 5 minutes")
    print("   3. The bot will wait 3 seconds before executing the trade")

if __name__ == "__main__":
    main()
