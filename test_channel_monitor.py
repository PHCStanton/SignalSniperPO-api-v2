#!/usr/bin/env python3
"""
Quick Test Script for Channel Latency Monitor
============================================

This script runs a quick test of the channel latency monitor to verify
it's working correctly with the BINARY TRADING CLUB channel.
"""

import asyncio
import sys
import os

# Add the current directory to the path to import our monitor
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from channel_latency_monitor import BinaryTradingClubLatencyMonitor

async def quick_test():
    """Run a quick test of the channel latency monitor"""
    print("🧪 QUICK TEST: Channel Latency Monitor")
    print("=" * 50)
    
    monitor = BinaryTradingClubLatencyMonitor()
    
    try:
        # Initialize the monitor
        print("1️⃣ Initializing monitor...")
        if not await monitor.initialize():
            print("❌ Failed to initialize monitor")
            return False
        
        print("✅ Monitor initialized successfully")
        
        # Test message reception latency (quick test with 3 iterations)
        print("\n2️⃣ Testing message reception latency...")
        reception_result = await monitor.measure_message_reception_latency(3)
        
        if reception_result["success"]:
            print(f"✅ Reception test successful:")
            print(f"   Average: {reception_result['avg']:.2f}ms")
            print(f"   Channel: {reception_result['channel_name']}")
        else:
            print(f"❌ Reception test failed: {reception_result.get('error', 'Unknown error')}")
        
        # Test signal parsing performance
        print("\n3️⃣ Testing signal parsing performance...")
        parsing_result = await monitor.test_signal_parsing_performance()
        
        if "avg_total_time" in parsing_result:
            print(f"✅ Parsing test successful:")
            print(f"   Valid signals: {parsing_result['valid_signals']}/{parsing_result['total_tests']}")
            print(f"   Average parsing time: {parsing_result['avg_total_time']:.2f}ms")
        else:
            print("❌ Parsing test failed")
        
        print("\n🎯 QUICK TEST COMPLETE")
        print("✅ Channel latency monitor is working correctly")
        print("\nTo run full monitoring, use: python channel_latency_monitor.py")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False
    
    finally:
        await monitor.cleanup()

if __name__ == "__main__":
    success = asyncio.run(quick_test())
    sys.exit(0 if success else 1)
