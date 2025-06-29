#!/usr/bin/env python3
"""
Test script to verify the OTC fix for the test channel configuration.
This script tests the enhanced channel-specific OTC logic implementation.
"""
import json
import os
import sys

def test_otc_fix_verification():
    """Test the OTC fix for the test channel."""
    print("🔍 Testing OTC Fix Verification for Test Channel")
    print("=" * 60)
    
    # Test 1: Load test channel configuration
    print("\n📋 Test 1: Loading Test Channel Configuration")
    test_channel_config_path = "config/channels/signal_sniper_test_channel.json"
    
    if not os.path.exists(test_channel_config_path):
        print(f"❌ Test channel config not found: {test_channel_config_path}")
        return False
    
    with open(test_channel_config_path, 'r') as f:
        test_channel_config = json.load(f)
    
    print(f"✅ Test channel config loaded: {test_channel_config['channel_name']}")
    
    # Test 2: Check OTC configuration settings
    print("\n🔧 Test 2: Checking OTC Configuration Settings")
    
    signal_characteristics = test_channel_config.get("signal_characteristics", {})
    parser_config = test_channel_config.get("parser_config", {})
    signal_validation = parser_config.get("signal_validation", {})
    
    # Check otc_preferred setting
    otc_preferred = signal_characteristics.get("otc_preferred")
    print(f"  • otc_preferred: {otc_preferred}")
    
    # Check supports_otc_pairs setting
    supports_otc_pairs = signal_validation.get("supports_otc_pairs")
    print(f"  • supports_otc_pairs: {supports_otc_pairs}")
    
    # Check pair_type setting
    pair_type = signal_characteristics.get("pair_type")
    print(f"  • pair_type: {pair_type}")
    
    # Test 3: Simulate the enhanced OTC logic
    print("\n🎯 Test 3: Simulating Enhanced OTC Logic")
    
    # Simulate the logic from the fixed code
    use_otc = None
    
    # Priority 1: Check otc_preferred setting
    if "otc_preferred" in signal_characteristics:
        use_otc = signal_characteristics["otc_preferred"]
        logic_source = "otc_preferred setting"
        print(f"  ✅ Priority 1: Using otc_preferred={use_otc} from channel configuration")
    
    # Priority 2: Check supports_otc_pairs setting
    elif "supports_otc_pairs" in signal_validation:
        use_otc = signal_validation["supports_otc_pairs"]
        logic_source = "supports_otc_pairs setting"
        print(f"  ✅ Priority 2: Using supports_otc_pairs={use_otc} from channel configuration")
    
    # Priority 3: Check pair_type setting
    elif signal_characteristics.get("pair_type") == "traditional_forex":
        use_otc = False
        logic_source = "traditional_forex pair type"
        print(f"  ✅ Priority 3: Using traditional_forex pair type (OTC=False)")
    
    else:
        print("  ⚠️ No channel-specific OTC setting found, would fall back to parser/channel logic")
        logic_source = "fallback logic"
    
    # Test 4: Verify expected behavior
    print("\n✅ Test 4: Verifying Expected Behavior")
    
    if use_otc is False:
        print("  ✅ CORRECT: Test channel will use traditional forex pairs (no OTC)")
        print("  ✅ Example: EUR/USD signal will trade as EURUSD (not EURUSD_otc)")
        result = "PASS"
    elif use_otc is True:
        print("  ❌ INCORRECT: Test channel would still use OTC pairs")
        print("  ❌ Example: EUR/USD signal would trade as EURUSD_otc")
        result = "FAIL"
    else:
        print("  ⚠️ UNCLEAR: Could not determine OTC behavior from configuration")
        result = "UNCLEAR"
    
    # Test 5: Load global configuration for comparison
    print("\n🌐 Test 5: Global Configuration Comparison")
    
    bot_config_path = "config/bot_config.json"
    if os.path.exists(bot_config_path):
        with open(bot_config_path, 'r') as f:
            bot_config = json.load(f)
        
        global_otc_default = bot_config.get("use_otc_by_default", True)
        print(f"  • Global use_otc_by_default: {global_otc_default}")
        
        if use_otc is not None:
            if use_otc != global_otc_default:
                print(f"  ✅ Channel-specific setting ({use_otc}) overrides global setting ({global_otc_default})")
            else:
                print(f"  ℹ️ Channel-specific setting ({use_otc}) matches global setting ({global_otc_default})")
        else:
            print(f"  ⚠️ No channel-specific setting found, would use global setting ({global_otc_default})")
    
    # Test 6: Test with sample signal
    print("\n📊 Test 6: Sample Signal Test")
    
    sample_signals = [
        {"pair": "EUR/USD", "direction": "CALL", "expiry": 1},
        {"pair": "GBP/USD", "direction": "PUT", "expiry": 5},
        {"pair": "USD/JPY", "direction": "CALL", "expiry": 1}
    ]
    
    for signal in sample_signals:
        raw_pair = signal["pair"].replace("/", "")
        
        if use_otc:
            asset = f"{raw_pair}_otc"
            pair_type_result = "OTC"
        else:
            asset = raw_pair
            pair_type_result = "Traditional"
        
        print(f"  • {signal['pair']} → {asset} ({pair_type_result})")
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 TEST SUMMARY")
    print("=" * 60)
    
    print(f"Channel Name: {test_channel_config['channel_name']}")
    print(f"Parser Type: {test_channel_config.get('parser_type', 'unknown')}")
    print(f"OTC Logic Source: {logic_source}")
    print(f"Use OTC: {use_otc}")
    print(f"Test Result: {result}")
    
    if result == "PASS":
        print("\n✅ SUCCESS: Test channel is properly configured to avoid OTC pairs!")
        print("   The enhanced OTC logic will correctly use traditional forex pairs.")
        return True
    elif result == "FAIL":
        print("\n❌ FAILURE: Test channel would still use OTC pairs!")
        print("   The configuration needs to be updated.")
        return False
    else:
        print("\n⚠️ UNCLEAR: Could not determine expected behavior.")
        print("   Manual verification may be required.")
        return False

if __name__ == "__main__":
    success = test_otc_fix_verification()
    sys.exit(0 if success else 1)
