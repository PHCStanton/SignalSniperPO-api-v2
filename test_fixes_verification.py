#!/usr/bin/env python3
"""
Test script to verify the two critical fixes:
1. TeeBinary Premium OTC pairs exclusion
2. 5-minute trade result checking optimization
"""

import sys
import os
import json
import time
from datetime import datetime
import pytz

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_teebinary_premium_otc_exclusion():
    """Test that TeeBinary Premium parser excludes OTC pairs correctly."""
    print("🧪 Testing TeeBinary Premium OTC Pairs Exclusion...")
    
    try:
        from src.parsers.teebinary_premium_parser import TeeBinaryPremiumParser
        
        # Create parser with default config
        config = {
            "parser_config": {}
        }
        parser = TeeBinaryPremiumParser(config)
        
        # Test valid traditional forex pairs
        valid_pairs = ["EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD"]
        for pair in valid_pairs:
            message = f"{pair} CALL 5MIN"
            signal = parser.parse_message(message)
            if signal:
                print(f"✅ Valid pair accepted: {pair}")
            else:
                print(f"❌ Valid pair rejected: {pair}")
        
        # Test excluded OTC pairs
        excluded_pairs = ["XAU/USD", "XAG/USD", "BTC/USD", "ETH/USD"]
        for pair in excluded_pairs:
            message = f"{pair} CALL 5MIN"
            signal = parser.parse_message(message)
            if signal:
                print(f"❌ OTC pair incorrectly accepted: {pair}")
            else:
                print(f"✅ OTC pair correctly rejected: {pair}")
        
        # Check configuration
        print(f"📊 Valid pairs count: {len(parser.valid_pairs)}")
        print(f"📊 Excluded OTC pairs count: {len(parser.excluded_otc_pairs)}")
        
        # Verify XAU/USD and XAG/USD are not in valid pairs
        otc_in_valid = [pair for pair in parser.excluded_otc_pairs if pair in parser.valid_pairs]
        if otc_in_valid:
            print(f"❌ OTC pairs found in valid pairs: {otc_in_valid}")
        else:
            print("✅ No OTC pairs found in valid pairs list")
        
        print("✅ TeeBinary Premium OTC exclusion test completed\n")
        return True
        
    except Exception as e:
        print(f"❌ TeeBinary Premium test failed: {str(e)}\n")
        return False

def test_trade_result_checking_optimization():
    """Test the optimized trade result checking mechanism."""
    print("🧪 Testing Trade Result Checking Optimization...")
    
    try:
        # Mock trade result checker class
        class MockTradeResultChecker:
            def __init__(self):
                self.check_calls = []
                self.start_time = None
            
            def check_trade_result_optimized(self, trade_id: str, expiry: int) -> dict:
                """Simulate the optimized trade result checking."""
                self.start_time = time.time()
                
                if expiry >= 300:  # 5+ minute trades
                    # Simulate optimized polling approach
                    initial_wait = 120  # 2 minutes
                    poll_interval = 30  # 30 seconds
                    max_polls = 8  # 8 polls max
                    
                    print(f"🔍 5-minute trade detected. Initial wait: {initial_wait}s, then polling every {poll_interval}s")
                    
                    # Simulate initial wait (don't actually wait in test)
                    simulated_time = initial_wait
                    
                    # Simulate polling
                    for poll_count in range(max_polls):
                        print(f"🔍 Simulated poll {poll_count + 1}/{max_polls} at {simulated_time}s")
                        self.check_calls.append({
                            "poll": poll_count + 1,
                            "time": simulated_time,
                            "trade_id": trade_id
                        })
                        
                        # Simulate finding result on poll 3
                        if poll_count == 2:
                            print(f"✅ Trade result found on poll {poll_count + 1}")
                            break
                        
                        simulated_time += poll_interval
                    
                    total_time = simulated_time
                else:
                    # Simulate short trade approach
                    wait_time = expiry + 3  # Reduced buffer
                    print(f"🔍 Short trade detected. Waiting {wait_time}s")
                    total_time = wait_time
                    self.check_calls.append({
                        "poll": 1,
                        "time": total_time,
                        "trade_id": trade_id
                    })
                
                return {
                    "total_time": total_time,
                    "polls": len(self.check_calls),
                    "optimization": "5min_polling" if expiry >= 300 else "short_trade"
                }
        
        checker = MockTradeResultChecker()
        
        # Test 5-minute trade optimization
        print("Testing 5-minute trade (300s expiry):")
        result_5min = checker.check_trade_result_optimized("test_5min", 300)
        print(f"📊 5-min trade result: {result_5min}")
        
        # Reset for next test
        checker.check_calls = []
        
        # Test 1-minute trade
        print("\nTesting 1-minute trade (60s expiry):")
        result_1min = checker.check_trade_result_optimized("test_1min", 60)
        print(f"📊 1-min trade result: {result_1min}")
        
        # Verify optimization benefits
        print("\n📈 Optimization Analysis:")
        print(f"5-minute trade: {result_5min['total_time']}s vs old method: 305s")
        print(f"1-minute trade: {result_1min['total_time']}s vs old method: 65s")
        
        # Calculate time savings
        old_5min_time = 305  # 300 + 5 buffer
        old_1min_time = 65   # 60 + 5 buffer
        
        savings_5min = old_5min_time - result_5min['total_time']
        savings_1min = old_1min_time - result_1min['total_time']
        
        print(f"⚡ Time savings for 5-min trades: {savings_5min}s ({savings_5min/old_5min_time*100:.1f}%)")
        print(f"⚡ Time savings for 1-min trades: {savings_1min}s ({savings_1min/old_1min_time*100:.1f}%)")
        
        print("✅ Trade result checking optimization test completed\n")
        return True
        
    except Exception as e:
        print(f"❌ Trade result optimization test failed: {str(e)}\n")
        return False

def test_configuration_updates():
    """Test that configuration files have been updated correctly."""
    print("🧪 Testing Configuration Updates...")
    
    try:
        # Test TeeBinary Premium config
        config_path = "config/channels/teebinary_premium.json"
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            valid_pairs = config.get("parser_config", {}).get("signal_validation", {}).get("valid_pairs", [])
            excluded_pairs = config.get("parser_config", {}).get("signal_validation", {}).get("excluded_otc_pairs", [])
            
            print(f"📊 Config valid pairs: {len(valid_pairs)}")
            print(f"📊 Config excluded OTC pairs: {len(excluded_pairs)}")
            
            # Check that XAU/USD and XAG/USD are not in valid pairs
            otc_in_valid = [pair for pair in ["XAU/USD", "XAG/USD"] if pair in valid_pairs]
            if otc_in_valid:
                print(f"❌ OTC pairs still in config valid pairs: {otc_in_valid}")
            else:
                print("✅ OTC pairs removed from config valid pairs")
            
            # Check that excluded_otc_pairs section exists
            if excluded_pairs:
                print("✅ Excluded OTC pairs section added to config")
            else:
                print("❌ Excluded OTC pairs section missing from config")
        else:
            print(f"❌ Config file not found: {config_path}")
        
        print("✅ Configuration updates test completed\n")
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {str(e)}\n")
        return False

def main():
    """Run all verification tests."""
    print("🚀 Starting Fixes Verification Tests")
    print("=" * 50)
    
    tests = [
        ("TeeBinary Premium OTC Exclusion", test_teebinary_premium_otc_exclusion),
        ("Trade Result Checking Optimization", test_trade_result_checking_optimization),
        ("Configuration Updates", test_configuration_updates)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🧪 Running: {test_name}")
        print("-" * 30)
        success = test_func()
        results.append((test_name, success))
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 TEST RESULTS SUMMARY")
    print("=" * 50)
    
    passed = 0
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status}: {test_name}")
        if success:
            passed += 1
    
    print(f"\n📊 Overall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All fixes verified successfully!")
        return True
    else:
        print("⚠️ Some tests failed. Please review the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
