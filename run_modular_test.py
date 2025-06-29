#!/usr/bin/env python3
"""
run_modular_test.py - Simple test of the modular parsing system
"""
import sys
import json
from channel_manager import ChannelManager

def test_modular_parsing():
    """Test the modular parsing system with sample messages."""
    print("🚀 Testing Modular Channel Architecture")
    print("=" * 50)
    
    # Initialize channel manager
    manager = ChannelManager()
    
    # Initialize from config
    if not manager.initialize_from_config():
        print("❌ Failed to initialize channel manager")
        return
    
    # Get current channel info
    channel_info = manager.get_current_channel_info()
    print(f"📡 Current Channel: {channel_info.get('channel_name', 'Unknown')}")
    print(f"🔧 Parser Type: {channel_info.get('parser_type', 'Unknown')}")
    print()
    
    # Test messages for different formats
    test_messages = [
        # TeeBinary Premium format
        "EUR/USD CALL 5MIN",
        "GBP/USD PUT 5MIN",
        "XAU/USD CALL 5MIN",
        
        # Binary Trading Club format (first message)
        "Trading Pair: EUR/USD",
        
        # Generic format
        "🎯 EUR/USD CALL 1M",
        "🎯 GBP/USD PUT 5M",
        
        # Noise messages (should be ignored)
        "BE READY",
        "GO",
        "WAIT FOR SIGNAL",
        "Market analysis...",
    ]
    
    print("🧪 Testing Message Parsing:")
    print("-" * 30)
    
    parsed_count = 0
    for i, message in enumerate(test_messages, 1):
        print(f"\n📨 Test {i}: {message}")
        
        # Parse the message
        signal = manager.parse_message(message)
        
        if signal:
            parsed_count += 1
            print(f"✅ PARSED: {signal.pair} {signal.direction} {signal.expiry}min")
            print(f"   Parser: {getattr(signal, 'parser_used', 'unknown')}")
        else:
            print("❌ No signal parsed")
    
    print(f"\n📊 Results: {parsed_count}/{len(test_messages)} messages parsed successfully")
    
    # Show parsing stats
    stats = manager.get_parsing_stats()
    print(f"\n📈 Parser Stats:")
    for key, value in stats.items():
        if isinstance(value, dict):
            print(f"  {key}:")
            for sub_key, sub_value in value.items():
                print(f"    {sub_key}: {sub_value}")
        else:
            print(f"  {key}: {value}")

if __name__ == "__main__":
    test_modular_parsing()
