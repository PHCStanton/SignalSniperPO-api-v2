#!/usr/bin/env python3
"""
Test Script for Modular Channel Architecture

This script tests the new modular channel architecture by:
1. Initializing the ChannelManager
2. Testing parser loading and switching
3. Testing message parsing with sample data
4. Validating the integration works correctly
"""

import logging
import json
from datetime import datetime
import pytz

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import our new architecture
from channel_manager import ChannelManager

def test_channel_manager_initialization():
    """Test basic ChannelManager initialization."""
    print("\n" + "="*60)
    print("🧪 TESTING: ChannelManager Initialization")
    print("="*60)
    
    try:
        # Create channel manager
        manager = ChannelManager()
        
        # Try to initialize from config
        success = manager.initialize_from_config()
        
        if success:
            print("✅ ChannelManager initialized successfully")
            
            # Get current channel info
            info = manager.get_current_channel_info()
            print(f"📊 Current Channel Info:")
            for key, value in info.items():
                print(f"   {key}: {value}")
            
            return manager
        else:
            print("❌ Failed to initialize ChannelManager")
            return None
            
    except Exception as e:
        print(f"❌ Error during initialization: {str(e)}")
        return None

def test_binary_trading_club_parsing(manager):
    """Test Binary Trading Club message parsing."""
    print("\n" + "="*60)
    print("🧪 TESTING: Binary Trading Club Message Parsing")
    print("="*60)
    
    if not manager:
        print("❌ No manager available for testing")
        return
    
    # Test messages in Binary Trading Club format
    test_messages = [
        {
            "description": "First message (Trading Pair)",
            "text": "Trading Pair: EUR/USD",
            "expected_result": None  # Should store pair but not return signal
        },
        {
            "description": "Second message (Direction + Timer + Expiry)",
            "text": "HIGHER\nSET THE TIMER TO 20:59:30\nTrade time: 1 MIN",
            "expected_result": "Signal"  # Should return complete signal
        },
        {
            "description": "Another first message",
            "text": "Trading Pair: GBP/USD",
            "expected_result": None
        },
        {
            "description": "Another second message",
            "text": "LOWER\nSET THE TIMER TO 21:05:15\nTrade time: 2 MIN",
            "expected_result": "Signal"
        }
    ]
    
    for i, test_msg in enumerate(test_messages, 1):
        print(f"\n📝 Test {i}: {test_msg['description']}")
        print(f"   Message: {repr(test_msg['text'])}")
        
        try:
            # Parse the message
            signal = manager.parse_message(test_msg['text'])
            
            if signal:
                print(f"✅ Signal parsed: {signal.pair} {signal.direction} {signal.expiry}min")
                if signal.timer:
                    print(f"   Timer: {signal.timer}")
                print(f"   Timestamp: {signal.timestamp}")
            else:
                print("   No signal returned (expected for first messages)")
                
            # Check if result matches expectation
            if test_msg['expected_result'] == "Signal" and signal:
                print("✅ Result matches expectation")
            elif test_msg['expected_result'] is None and not signal:
                print("✅ Result matches expectation")
            else:
                print("⚠️  Result doesn't match expectation")
                
        except Exception as e:
            print(f"❌ Error parsing message: {str(e)}")

def test_generic_parsing(manager):
    """Test generic parser with various message formats."""
    print("\n" + "="*60)
    print("🧪 TESTING: Generic Parser (Fallback)")
    print("="*60)
    
    if not manager:
        print("❌ No manager available for testing")
        return
    
    # Switch to a channel that will use generic parser
    print("🔄 Switching to test channel (will use generic parser)...")
    success = manager.switch_channel("Test Channel")
    
    if not success:
        print("❌ Failed to switch to test channel")
        return
    
    # Test various single-message formats
    test_messages = [
        "🎯 EUR/USD CALL 5M",
        "Currency pair GBP/USD HIGHER Trade time: 3 MIN",
        "EURUSD PUT 2",
        "USD/JPY ⬆️ 4 minutes"
    ]
    
    for i, msg in enumerate(test_messages, 1):
        print(f"\n📝 Test {i}: {repr(msg)}")
        
        try:
            signal = manager.parse_message(msg)
            
            if signal:
                print(f"✅ Signal parsed: {signal.pair} {signal.direction} {signal.expiry}min")
            else:
                print("   No signal parsed")
                
        except Exception as e:
            print(f"❌ Error parsing message: {str(e)}")

def test_channel_switching(manager):
    """Test switching between different channels."""
    print("\n" + "="*60)
    print("🧪 TESTING: Channel Switching")
    print("="*60)
    
    if not manager:
        print("❌ No manager available for testing")
        return
    
    # List available channels
    channels = manager.list_available_channels()
    print(f"📋 Available channels: {channels}")
    
    # Test switching to Binary Trading Club
    print("\n🔄 Switching to Binary Trading Club...")
    success = manager.switch_channel("BINARY TRADING CLUB")
    
    if success:
        print("✅ Successfully switched to Binary Trading Club")
        info = manager.get_current_channel_info()
        print(f"   Parser: {info.get('parser_type', 'unknown')}")
    else:
        print("❌ Failed to switch to Binary Trading Club")
    
    # Test switching to a generic channel
    print("\n🔄 Switching to Test Channel...")
    success = manager.switch_channel("Test Channel")
    
    if success:
        print("✅ Successfully switched to Test Channel")
        info = manager.get_current_channel_info()
        print(f"   Parser: {info.get('parser_type', 'unknown')}")
    else:
        print("❌ Failed to switch to Test Channel")

def test_parsing_stats(manager):
    """Test parsing statistics functionality."""
    print("\n" + "="*60)
    print("🧪 TESTING: Parsing Statistics")
    print("="*60)
    
    if not manager:
        print("❌ No manager available for testing")
        return
    
    try:
        stats = manager.get_parsing_stats()
        print("📊 Parsing Statistics:")
        print(json.dumps(stats, indent=2, default=str))
        
    except Exception as e:
        print(f"❌ Error getting parsing stats: {str(e)}")

def main():
    """Run all tests."""
    print("🚀 Starting Modular Channel Architecture Tests")
    print(f"⏰ Test started at: {datetime.now(pytz.UTC).isoformat()}")
    
    # Test 1: Initialize ChannelManager
    manager = test_channel_manager_initialization()
    
    # Test 2: Binary Trading Club parsing
    test_binary_trading_club_parsing(manager)
    
    # Test 3: Generic parsing
    test_generic_parsing(manager)
    
    # Test 4: Channel switching
    test_channel_switching(manager)
    
    # Test 5: Parsing statistics
    test_parsing_stats(manager)
    
    print("\n" + "="*60)
    print("🏁 All tests completed!")
    print("="*60)
    
    if manager:
        print(f"✅ Final channel: {manager.current_channel_name}")
        print(f"✅ Final parser: {manager.current_parser.__class__.__name__ if manager.current_parser else 'None'}")

if __name__ == "__main__":
    main()
