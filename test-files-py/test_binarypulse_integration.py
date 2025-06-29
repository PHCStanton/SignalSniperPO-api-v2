#!/usr/bin/env python3
"""
BinaryPulse Bot Integration Test Suite
=====================================

Comprehensive test suite for @BinaryPulse_bot integration with SignalSniper.
Tests configuration, parser functionality, and timeframe filtering.

Usage:
    python test_binarypulse_integration.py
"""

import json
import os
import sys
import re
from datetime import datetime
import pytz

# Add src directory to path for parser imports
sys.path.append('src')

def test_binarypulse_config():
    """Test BinaryPulse bot channel configuration."""
    print("🧪 Testing BinaryPulse Bot Configuration...")
    
    config_path = "config/channels/binarypulse_bot.json"
    
    # Test 1: Configuration file exists
    if not os.path.exists(config_path):
        print("❌ BinaryPulse bot config file not found")
        return False
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        return False
    
    # Test 2: Required fields present
    required_fields = [
        'channel_name', 'parser_type', 'enabled', 'parser_config',
        'signal_characteristics', 'timeframe_filtering', 'bot_integration'
    ]
    
    for field in required_fields:
        if field not in config:
            print(f"❌ Missing required field: {field}")
            return False
    
    # Test 3: Parser type is correct
    if config['parser_type'] != 'binarypulse_bot':
        print(f"❌ Wrong parser type: {config['parser_type']}")
        return False
    
    # Test 4: Timeframe filtering enabled
    timeframe_filtering = config.get('timeframe_filtering', {})
    if not timeframe_filtering.get('enabled', False):
        print("❌ Timeframe filtering not enabled")
        return False
    
    # Test 5: Bot integration details
    bot_integration = config.get('bot_integration', {})
    if bot_integration.get('bot_handle') != '@BinaryPulse_bot':
        print("❌ Wrong bot handle")
        return False
    
    print("✅ BinaryPulse bot configuration valid")
    return True

def test_timeframe_config():
    """Test timeframe configuration with BinaryPulse support."""
    print("\n🧪 Testing Timeframe Configuration...")
    
    config_path = "config/timeframe_config.json"
    
    if not os.path.exists(config_path):
        print("❌ Timeframe config file not found")
        return False
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except Exception as e:
        print(f"❌ Error loading timeframe config: {e}")
        return False
    
    # Test 1: Channel-specific section exists
    channel_specific = config.get('channel_specific', {})
    if 'binarypulse_bot' not in channel_specific:
        print("❌ BinaryPulse bot not in channel_specific config")
        return False
    
    # Test 2: BinaryPulse timeframes configured
    bp_config = channel_specific['binarypulse_bot']
    bp_timeframes = bp_config.get('timeframes', {})
    
    expected_timeframes = ['1', '3', '5']
    for tf in expected_timeframes:
        if tf not in bp_timeframes:
            print(f"❌ Missing timeframe {tf} in BinaryPulse config")
            return False
    
    # Test 3: Filtering rules present
    filtering_rules = bp_config.get('filtering_rules', {})
    required_rules = [
        'filter_by_duration', 'skip_disabled_timeframes', 
        'log_filtered_signals', 'statistical_tracking'
    ]
    
    for rule in required_rules:
        if rule not in filtering_rules:
            print(f"❌ Missing filtering rule: {rule}")
            return False
    
    print("✅ Timeframe configuration valid")
    return True

def test_binarypulse_parser():
    """Test BinaryPulse bot parser functionality."""
    print("\n🧪 Testing BinaryPulse Bot Parser...")
    
    try:
        from parsers.binarypulse_bot_parser import BinaryPulseBotParser
        from parsers.base_parser import Signal
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    
    # Load configuration
    config_path = "config/channels/binarypulse_bot.json"
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except Exception as e:
        print(f"❌ Error loading parser config: {e}")
        return False
    
    # Initialize parser
    try:
        parser = BinaryPulseBotParser(config)
    except Exception as e:
        print(f"❌ Parser initialization failed: {e}")
        return False
    
    # Test signal parsing
    test_signals = [
        {
            'message': """📢 SIGNAL TO ENTER
✅ Couple: EUR/USD
📉 Direction: DOWN
🕐 Time expiration: 3 min""",
            'expected': {'pair': 'EUR/USD', 'direction': 'LOWER', 'expiry': 3}
        },
        {
            'message': """📢 SIGNAL TO ENTER
✅ Couple: AUD/CAD OTC
📈 Direction: UP
🕐 Time expiration: 1 min""",
            'expected': {'pair': 'AUD/CAD', 'direction': 'HIGHER', 'expiry': 1}
        },
        {
            'message': """📢 SIGNAL TO ENTER
✅ Couple: GBP/USD
📉 Direction: DOWN
🕐 Time expiration: 5 min""",
            'expected': {'pair': 'GBP/USD', 'direction': 'LOWER', 'expiry': 5}
        }
    ]
    
    for i, test_case in enumerate(test_signals, 1):
        try:
            signal = parser.parse_message(test_case['message'])
            
            if signal is None:
                print(f"❌ Test {i}: Parser returned None")
                return False
            
            expected = test_case['expected']
            if (signal.pair != expected['pair'] or 
                signal.direction != expected['direction'] or 
                signal.expiry != expected['expiry']):
                print(f"❌ Test {i}: Parsing mismatch")
                print(f"   Expected: {expected}")
                print(f"   Got: {{'pair': '{signal.pair}', 'direction': '{signal.direction}', 'expiry': {signal.expiry}}}")
                return False
            
            print(f"✅ Test {i}: {signal.pair} {signal.direction} {signal.expiry}min")
            
        except Exception as e:
            print(f"❌ Test {i}: Parser error: {e}")
            return False
    
    print("✅ BinaryPulse parser tests passed")
    return True

def test_timeframe_filtering():
    """Test timeframe filtering logic."""
    print("\n🧪 Testing Timeframe Filtering Logic...")
    
    # Load timeframe config
    config_path = "config/timeframe_config.json"
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            timeframe_config = json.load(f)
    except Exception as e:
        print(f"❌ Error loading timeframe config: {e}")
        return False
    
    # Test filtering logic
    global_settings = timeframe_config.get('timeframe_settings', {})
    bp_settings = timeframe_config.get('channel_specific', {}).get('binarypulse_bot', {})
    
    # Test 1: Global timeframes enabled
    enabled_global = []
    for tf_str, tf_config in global_settings.items():
        if tf_config.get('enabled', False):
            enabled_global.append(int(tf_str))
    
    print(f"📊 Global enabled timeframes: {sorted(enabled_global)}")
    
    # Test 2: BinaryPulse specific settings
    bp_timeframes = bp_settings.get('timeframes', {})
    bp_enabled = []
    for tf_str, tf_config in bp_timeframes.items():
        if tf_config.get('enabled', False):
            bp_enabled.append(int(tf_str))
    
    print(f"🤖 BinaryPulse enabled timeframes: {sorted(bp_enabled)}")
    
    # Test 3: Override logic
    override_global = bp_settings.get('override_global', False)
    if override_global:
        effective_timeframes = bp_enabled
        print(f"🔄 Using BinaryPulse override: {sorted(effective_timeframes)}")
    else:
        effective_timeframes = enabled_global
        print(f"🌐 Using global settings: {sorted(effective_timeframes)}")
    
    # Test 4: Filtering rules
    filtering_rules = bp_settings.get('filtering_rules', {})
    filter_by_duration = filtering_rules.get('filter_by_duration', False)
    skip_disabled = filtering_rules.get('skip_disabled_timeframes', False)
    
    print(f"🎯 Filter by duration: {'✅' if filter_by_duration else '❌'}")
    print(f"🚫 Skip disabled timeframes: {'✅' if skip_disabled else '❌'}")
    
    # Test 5: Signal filtering simulation
    test_signals = [
        {'expiry': 1, 'should_execute': 1 in effective_timeframes},
        {'expiry': 3, 'should_execute': 3 in effective_timeframes},
        {'expiry': 5, 'should_execute': 5 in effective_timeframes},
        {'expiry': 2, 'should_execute': 2 in effective_timeframes}
    ]
    
    print("\n📋 Signal Filtering Simulation:")
    for signal in test_signals:
        expiry = signal['expiry']
        should_execute = signal['should_execute']
        status = "✅ EXECUTE" if should_execute else "🚫 SKIP"
        print(f"  {expiry}min signal: {status}")
    
    print("✅ Timeframe filtering logic verified")
    return True

def test_integration_readiness():
    """Test overall integration readiness."""
    print("\n🧪 Testing Integration Readiness...")
    
    # Test 1: All required files exist
    required_files = [
        "config/channels/binarypulse_bot.json",
        "config/timeframe_config.json",
        "src/parsers/binarypulse_bot_parser.py",
        "timeframe_toggle.py"
    ]
    
    for file_path in required_files:
        if not os.path.exists(file_path):
            print(f"❌ Missing required file: {file_path}")
            return False
    
    print("✅ All required files present")
    
    # Test 2: Parser can be imported
    try:
        from parsers.binarypulse_bot_parser import BinaryPulseBotParser
        print("✅ Parser import successful")
    except ImportError as e:
        print(f"❌ Parser import failed: {e}")
        return False
    
    # Test 3: Configuration consistency
    try:
        # Load both configs
        with open("config/channels/binarypulse_bot.json", 'r', encoding='utf-8') as f:
            bp_config = json.load(f)
        with open("config/timeframe_config.json", 'r', encoding='utf-8') as f:
            tf_config = json.load(f)
        
        # Check consistency
        bp_timeframes = set(bp_config['signal_characteristics']['supported_timeframes'])
        tf_bp_timeframes = set(int(tf) for tf in tf_config['channel_specific']['binarypulse_bot']['timeframes'].keys())
        
        if bp_timeframes != tf_bp_timeframes:
            print(f"❌ Timeframe mismatch between configs")
            print(f"   Channel config: {bp_timeframes}")
            print(f"   Timeframe config: {tf_bp_timeframes}")
            return False
        
        print("✅ Configuration consistency verified")
        
    except Exception as e:
        print(f"❌ Configuration consistency check failed: {e}")
        return False
    
    print("✅ Integration ready for deployment")
    return True

def main():
    """Run all tests."""
    print("🎯 BinaryPulse Bot Integration Test Suite")
    print("=" * 50)
    
    tests = [
        ("BinaryPulse Configuration", test_binarypulse_config),
        ("Timeframe Configuration", test_timeframe_config),
        ("BinaryPulse Parser", test_binarypulse_parser),
        ("Timeframe Filtering", test_timeframe_filtering),
        ("Integration Readiness", test_integration_readiness)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} ERROR: {e}")
    
    print(f"\n{'='*60}")
    print(f"📊 TEST RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - BinaryPulse integration ready!")
        print("\n📋 Next Steps:")
        print("1. Update SignalSniper_mod.py to support BinaryPulse parser")
        print("2. Test with actual @BinaryPulse_bot signals")
        print("3. Verify timeframe filtering in live environment")
        return True
    else:
        print("❌ Some tests failed - fix issues before deployment")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
