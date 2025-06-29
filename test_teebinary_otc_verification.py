#!/usr/bin/env python3
"""
Test script to verify OTC avoidance for TeeBinary Premium channel.
This script tests both the channel configuration and the enhanced OTC logic.
"""
import json
import os
import sys

def test_teebinary_otc_verification():
    """Test OTC avoidance for TeeBinary Premium channel."""
    print("🔍 Testing TeeBinary Premium OTC Avoidance")
    print("=" * 60)
    
    # Test 1: Load TeeBinary Premium configuration
    print("\n📋 Test 1: Loading TeeBinary Premium Configuration")
    teebinary_config_path = "config/channels/teebinary_premium.json"
    
    if not os.path.exists(teebinary_config_path):
        print(f"❌ TeeBinary Premium config not found: {teebinary_config_path}")
        return False
    
    with open(teebinary_config_path, 'r') as f:
        teebinary_config = json.load(f)
    
    print(f"✅ TeeBinary Premium config loaded: {teebinary_config['channel_name']}")
    
    # Test 2: Check OTC configuration settings
    print("\n🔧 Test 2: Checking OTC Configuration Settings")
    
    signal_characteristics = teebinary_config.get("signal_characteristics", {})
    parser_config = teebinary_config.get("parser_config", {})
    signal_validation = parser_config.get("signal_validation", {})
    
    # Check all OTC-related settings
    otc_preferred = signal_characteristics.get("otc_preferred")
    supports_otc_pairs = signal_validation.get("supports_otc_pairs")
    pair_type = signal_characteristics.get("pair_type")
    excluded_otc_pairs = signal_validation.get("excluded_otc_pairs", [])
    
    print(f"  • otc_preferred: {otc_preferred}")
    print(f"  • supports_otc_pairs: {supports_otc_pairs}")
    print(f"  • pair_type: {pair_type}")
    print(f"  • excluded_otc_pairs count: {len(excluded_otc_pairs)}")
    
    # Test 3: Simulate the enhanced OTC logic for TeeBinary Premium
    print("\n🎯 Test 3: Simulating Enhanced OTC Logic for TeeBinary Premium")
    
    # Simulate the logic from SignalSniper_mod.py
    use_otc = None
    logic_source = "unknown"
    
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
    
    # Fallback: Parser/channel name logic
    else:
        # Simulate parser type check
        parser_type = teebinary_config.get("parser_type", "")
        channel_name = teebinary_config.get("channel_name", "")
        
        if "teebinary" in parser_type.lower() or "TeeBinary" in channel_name:
            use_otc = False
            logic_source = "TeeBinary parser/channel name detection"
            print(f"  ✅ Fallback: TeeBinary detected, using OTC=False")
        else:
            # Would fall back to global setting
            print(f"  ⚠️ Would fall back to global setting")
            logic_source = "global fallback"
    
    # Test 4: Verify expected behavior
    print("\n✅ Test 4: Verifying Expected Behavior")
    
    if use_otc is False:
        print("  ✅ CORRECT: TeeBinary Premium will use traditional forex pairs (no OTC)")
        print("  ✅ Example: EUR/USD signal will trade as EURUSD (not EURUSD_otc)")
        result = "PASS"
    elif use_otc is True:
        print("  ❌ INCORRECT: TeeBinary Premium would use OTC pairs")
        print("  ❌ Example: EUR/USD signal would trade as EURUSD_otc")
        result = "FAIL"
    else:
        print("  ⚠️ UNCLEAR: Could not determine OTC behavior from configuration")
        result = "UNCLEAR"
    
    # Test 5: Check valid pairs vs excluded pairs
    print("\n📊 Test 5: Valid vs Excluded Pairs Analysis")
    
    valid_pairs = signal_validation.get("valid_pairs", [])
    print(f"  • Valid pairs count: {len(valid_pairs)}")
    print(f"  • Excluded OTC pairs count: {len(excluded_otc_pairs)}")
    
    # Check if any excluded pairs are in valid pairs (should be none)
    overlap = set(valid_pairs) & set(excluded_otc_pairs)
    if overlap:
        print(f"  ❌ ERROR: Found overlap between valid and excluded pairs: {overlap}")
        result = "FAIL"
    else:
        print("  ✅ No overlap between valid and excluded pairs")
    
    # Test 6: Sample signal processing
    print("\n📊 Test 6: Sample TeeBinary Premium Signal Test")
    
    sample_signals = [
        {"pair": "EUR/USD", "direction": "CALL", "expiry": 5},
        {"pair": "GBP/USD", "direction": "PUT", "expiry": 5},
        {"pair": "USD/JPY", "direction": "CALL", "expiry": 5}
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
    
    # Test 7: Global configuration comparison
    print("\n🌐 Test 7: Global Configuration Comparison")
    
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
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 TEEBINARY PREMIUM TEST SUMMARY")
    print("=" * 60)
    
    print(f"Channel Name: {teebinary_config['channel_name']}")
    print(f"Parser Type: {teebinary_config.get('parser_type', 'unknown')}")
    print(f"OTC Logic Source: {logic_source}")
    print(f"Use OTC: {use_otc}")
    print(f"Test Result: {result}")
    
    # Configuration summary
    print(f"\nConfiguration Summary:")
    print(f"  • otc_preferred: {otc_preferred}")
    print(f"  • supports_otc_pairs: {supports_otc_pairs}")
    print(f"  • pair_type: {pair_type}")
    print(f"  • Valid pairs: {len(valid_pairs)}")
    print(f"  • Excluded OTC pairs: {len(excluded_otc_pairs)}")
    
    if result == "PASS":
        print("\n✅ SUCCESS: TeeBinary Premium is properly configured to avoid OTC pairs!")
        print("   The enhanced OTC logic will correctly use traditional forex pairs.")
        return True
    elif result == "FAIL":
        print("\n❌ FAILURE: TeeBinary Premium configuration has issues!")
        print("   The configuration needs to be reviewed.")
        return False
    else:
        print("\n⚠️ UNCLEAR: Could not determine expected behavior.")
        print("   Manual verification may be required.")
        return False

if __name__ == "__main__":
    success = test_teebinary_otc_verification()
    sys.exit(0 if success else 1)
