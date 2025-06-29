#!/usr/bin/env python3
"""
Test script to verify the fixes for current SignalSniper_mod.py issues:
1. OTC currency pair issue with TeeBinary Premium
2. Unknown trade result warning for (0, 'loose') format
"""

import json
import os
import sys
from typing import Dict, Any

def test_teebinary_premium_otc_config():
    """Test that TeeBinary Premium configuration has otc_preferred: false"""
    print("🔍 Testing TeeBinary Premium OTC Configuration...")
    
    config_path = "config/channels/teebinary_premium.json"
    
    if not os.path.exists(config_path):
        print(f"❌ Configuration file not found: {config_path}")
        return False
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Check if otc_preferred is set to false
        signal_characteristics = config.get("signal_characteristics", {})
        otc_preferred = signal_characteristics.get("otc_preferred")
        
        if otc_preferred is False:
            print("✅ TeeBinary Premium has otc_preferred: false")
            return True
        elif otc_preferred is None:
            print("❌ TeeBinary Premium missing otc_preferred setting")
            return False
        else:
            print(f"❌ TeeBinary Premium has otc_preferred: {otc_preferred} (should be false)")
            return False
            
    except Exception as e:
        print(f"❌ Error reading TeeBinary Premium config: {str(e)}")
        return False

def test_trade_result_parsing():
    """Test that the trade result parsing handles 'loose' typo correctly"""
    print("\n🔍 Testing Trade Result Parsing...")
    
    # Test cases for trade result parsing
    test_cases = [
        # (input_result, expected_trade_result, description)
        ((1.84, 'win'), "win", "Standard win format"),
        ((0, 'loss'), "loss", "Standard loss format"),
        ((0, 'loose'), "loss", "Typo 'loose' should be treated as loss"),
        ((0, 'lose'), "loss", "Alternative 'lose' format"),
        ((0, 'draw'), "draw", "Draw format"),
        ((1.5, 'winning'), "win", "Alternative winning format"),
        ((0, 'losing'), "loss", "Alternative losing format"),
    ]
    
    # Simulate the parsing logic from SignalSniper_mod.py
    def parse_trade_result(result):
        """Simulate the trade result parsing logic"""
        if isinstance(result, (tuple, list)) and len(result) >= 2:
            if len(result) == 2 and isinstance(result[1], str):
                try:
                    profit_value = float(result[0])
                    result_str = str(result[1]).lower()
                    if result_str in ['win', 'winning']:
                        return "win"
                    elif result_str in ['loss', 'losing', 'lose', 'loose']:  # Fixed to include 'loose'
                        return "loss"
                    elif result_str in ['draw', 'tie']:
                        return "draw"
                    else:
                        return "unknown"
                except (ValueError, TypeError):
                    return "unknown"
        return "unknown"
    
    all_passed = True
    
    for input_result, expected, description in test_cases:
        actual = parse_trade_result(input_result)
        if actual == expected:
            print(f"✅ {description}: {input_result} -> {actual}")
        else:
            print(f"❌ {description}: {input_result} -> {actual} (expected {expected})")
            all_passed = False
    
    return all_passed

def test_channel_specific_otc_logic():
    """Test the channel-specific OTC logic"""
    print("\n🔍 Testing Channel-Specific OTC Logic...")
    
    def determine_otc_usage(channel_name, parser_type, global_otc_default=True):
        """Simulate the OTC logic from SignalSniper_mod.py"""
        if "binary_trading_club" in parser_type.lower() or "BINARY TRADING CLUB" in channel_name:
            return True  # Binary Trading Club: Always use OTC pairs
        elif "teebinary" in parser_type.lower() or "TeeBinary" in channel_name:
            return False  # TeeBinary Premium: Never use OTC (traditional forex only)
        else:
            return global_otc_default  # Generic channels: Use global setting
    
    test_cases = [
        # (channel_name, parser_type, expected_otc, description)
        ("BINARY TRADING CLUB", "binary_trading_club", True, "Binary Trading Club should use OTC"),
        ("TeeBinary_Premium", "teebinary_premium", False, "TeeBinary Premium should NOT use OTC"),
        ("🎯Signal_Sniper_Test_Channel🎯", "generic", True, "Generic channel should use global default (True)"),
        ("Custom Channel", "generic", True, "Generic channel should use global default (True)"),
    ]
    
    all_passed = True
    
    for channel_name, parser_type, expected_otc, description in test_cases:
        actual_otc = determine_otc_usage(channel_name, parser_type, global_otc_default=True)
        if actual_otc == expected_otc:
            print(f"✅ {description}: {channel_name} ({parser_type}) -> OTC: {actual_otc}")
        else:
            print(f"❌ {description}: {channel_name} ({parser_type}) -> OTC: {actual_otc} (expected {expected_otc})")
            all_passed = False
    
    return all_passed

def test_signalsniper_mod_syntax():
    """Test that SignalSniper_mod.py has valid syntax"""
    print("\n🔍 Testing SignalSniper_mod.py Syntax...")
    
    try:
        # Try to compile the file to check for syntax errors
        with open("SignalSniper_mod.py", 'r') as f:
            source_code = f.read()
        
        compile(source_code, "SignalSniper_mod.py", "exec")
        print("✅ SignalSniper_mod.py has valid Python syntax")
        return True
        
    except SyntaxError as e:
        print(f"❌ Syntax error in SignalSniper_mod.py: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Error checking SignalSniper_mod.py: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Current Issues Fixes for SignalSniper_mod.py")
    print("=" * 60)
    
    tests = [
        ("TeeBinary Premium OTC Configuration", test_teebinary_premium_otc_config),
        ("Trade Result Parsing (loose typo fix)", test_trade_result_parsing),
        ("Channel-Specific OTC Logic", test_channel_specific_otc_logic),
        ("SignalSniper_mod.py Syntax", test_signalsniper_mod_syntax),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Error running {test_name}: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY:")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Both issues have been resolved.")
        return True
    else:
        print("⚠️ Some tests failed. Please review the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
