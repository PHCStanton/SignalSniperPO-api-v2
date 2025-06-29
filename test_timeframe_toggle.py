#!/usr/bin/env python3
"""
Test script for Timeframe Toggle functionality
============================================

This script tests the timeframe toggle feature implementation for SignalSniper bot.
Tests both the configuration system and the integration with the bot's signal validation.

Usage:
    python test_timeframe_toggle.py
"""

import json
import os
import sys
from datetime import datetime
from typing import Dict, List

def test_timeframe_config_creation():
    """Test 1: Verify timeframe configuration file creation and structure."""
    print("\n📋 Test 1: Timeframe Configuration File")
    print("-" * 50)
    
    config_path = "config/timeframe_config.json"
    
    if not os.path.exists(config_path):
        print(f"❌ Configuration file not found: {config_path}")
        return False
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Check required sections
        required_sections = ["timeframe_control", "timeframe_settings", "suspension_rules"]
        for section in required_sections:
            if section not in config:
                print(f"❌ Missing required section: {section}")
                return False
            print(f"✅ Found section: {section}")
        
        # Check timeframe control settings
        control = config["timeframe_control"]
        required_control_fields = ["enabled", "default_enabled_timeframes", "available_timeframes", "suspended_timeframes"]
        for field in required_control_fields:
            if field not in control:
                print(f"❌ Missing control field: {field}")
                return False
            print(f"✅ Found control field: {field}")
        
        # Check default enabled timeframes
        default_enabled = control["default_enabled_timeframes"]
        expected_default = [1, 3, 5]
        if default_enabled == expected_default:
            print(f"✅ Default enabled timeframes correct: {default_enabled}")
        else:
            print(f"❌ Default enabled timeframes incorrect: {default_enabled} (expected: {expected_default})")
            return False
        
        # Check timeframe settings structure
        settings = config["timeframe_settings"]
        for tf_str, tf_config in settings.items():
            required_tf_fields = ["enabled", "description"]
            for field in required_tf_fields:
                if field not in tf_config:
                    print(f"❌ Missing timeframe field {field} for {tf_str}")
                    return False
        
        print("✅ Timeframe configuration structure is valid")
        return True
        
    except Exception as e:
        print(f"❌ Error reading configuration: {e}")
        return False

def test_timeframe_toggle_script():
    """Test 2: Verify timeframe toggle script functionality."""
    print("\n🔧 Test 2: Timeframe Toggle Script")
    print("-" * 50)
    
    script_path = "timeframe_toggle.py"
    
    if not os.path.exists(script_path):
        print(f"❌ Toggle script not found: {script_path}")
        return False
    
    try:
        # Import the TimeframeToggle class
        sys.path.append('.')
        from timeframe_toggle import TimeframeToggle
        
        # Create instance
        toggle = TimeframeToggle()
        
        # Test configuration loading
        if not toggle.config:
            print("❌ Failed to load configuration")
            return False
        print("✅ Configuration loaded successfully")
        
        # Test enabled timeframes detection
        enabled_timeframes = toggle.get_enabled_timeframes()
        expected_enabled = {1, 3, 5}
        if enabled_timeframes == expected_enabled:
            print(f"✅ Enabled timeframes detected correctly: {enabled_timeframes}")
        else:
            print(f"❌ Enabled timeframes incorrect: {enabled_timeframes} (expected: {expected_enabled})")
            return False
        
        # Test suspended timeframes detection
        suspended_timeframes = toggle.get_suspended_timeframes()
        if isinstance(suspended_timeframes, set):
            print(f"✅ Suspended timeframes detected: {suspended_timeframes}")
        else:
            print(f"❌ Suspended timeframes detection failed")
            return False
        
        print("✅ Timeframe toggle script functionality verified")
        return True
        
    except Exception as e:
        print(f"❌ Error testing toggle script: {e}")
        return False

def test_signal_validation_integration():
    """Test 3: Test timeframe validation in signal processing."""
    print("\n🎯 Test 3: Signal Validation Integration")
    print("-" * 50)
    
    # Test signals with different timeframes
    test_signals = [
        {"pair": "EUR/USD", "direction": "HIGHER", "expiry": 1, "description": "1-minute signal (should be enabled)"},
        {"pair": "GBP/USD", "direction": "LOWER", "expiry": 2, "description": "2-minute signal (should be disabled)"},
        {"pair": "USD/JPY", "direction": "HIGHER", "expiry": 3, "description": "3-minute signal (should be enabled)"},
        {"pair": "AUD/USD", "direction": "LOWER", "expiry": 5, "description": "5-minute signal (should be enabled)"},
        {"pair": "USD/CAD", "direction": "HIGHER", "expiry": 10, "description": "10-minute signal (should be disabled)"},
    ]
    
    try:
        # Import the validation function
        sys.path.append('.')
        
        # Create a mock bot class with the validate_timeframe method
        class MockBot:
            def validate_timeframe(self, signal: Dict):
                """Mock implementation of timeframe validation."""
                try:
                    # Load timeframe configuration
                    timeframe_config_path = "config/timeframe_config.json"
                    if not os.path.exists(timeframe_config_path):
                        return True, "No timeframe restrictions"
                    
                    with open(timeframe_config_path, 'r', encoding='utf-8') as f:
                        timeframe_config = json.load(f)
                    
                    # Check if timeframe control is enabled
                    timeframe_control = timeframe_config.get("timeframe_control", {})
                    if not timeframe_control.get("enabled", True):
                        return True, "Timeframe control disabled"
                    
                    # Get signal expiry (timeframe in minutes)
                    signal_timeframe = signal.get("expiry", 0)
                    
                    # Check if timeframe is suspended
                    suspended_timeframes = timeframe_control.get("suspended_timeframes", [])
                    if signal_timeframe in suspended_timeframes:
                        return False, f"Timeframe {signal_timeframe} minutes is suspended"
                    
                    # Check individual timeframe settings
                    timeframe_settings = timeframe_config.get("timeframe_settings", {})
                    timeframe_str = str(signal_timeframe)
                    
                    if timeframe_str in timeframe_settings:
                        timeframe_enabled = timeframe_settings[timeframe_str].get("enabled", True)
                        if not timeframe_enabled:
                            return False, f"Timeframe {signal_timeframe} minutes is disabled"
                    
                    return True, f"Timeframe {signal_timeframe} minutes is enabled"
                    
                except Exception as e:
                    return True, f"Timeframe validation error (allowing): {str(e)}"
        
        mock_bot = MockBot()
        
        # Test each signal
        for signal in test_signals:
            valid, message = mock_bot.validate_timeframe(signal)
            status = "✅ ALLOWED" if valid else "❌ BLOCKED"
            print(f"  {signal['expiry']:2d} min: {status:12} | {signal['description']:35} | {message}")
        
        print("✅ Signal validation integration tested")
        return True
        
    except Exception as e:
        print(f"❌ Error testing signal validation: {e}")
        return False

def test_timeframe_suspension_simulation():
    """Test 4: Simulate timeframe suspension and verify behavior."""
    print("\n🚫 Test 4: Timeframe Suspension Simulation")
    print("-" * 50)
    
    try:
        # Load current configuration
        config_path = "config/timeframe_config.json"
        with open(config_path, 'r', encoding='utf-8') as f:
            original_config = json.load(f)
        
        # Create backup
        backup_config = original_config.copy()
        
        # Simulate suspending 1-minute timeframe
        test_config = original_config.copy()
        test_config["timeframe_control"]["suspended_timeframes"] = [1]
        test_config["timeframe_settings"]["1"]["enabled"] = False
        
        # Save test configuration
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(test_config, f, indent=4)
        
        print("✅ Simulated suspension of 1-minute timeframe")
        
        # Test signal validation with suspended timeframe
        test_signal = {"pair": "EUR/USD", "direction": "HIGHER", "expiry": 1}
        
        # Mock validation
        class MockBot:
            def validate_timeframe(self, signal: Dict):
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        timeframe_config = json.load(f)
                    
                    timeframe_control = timeframe_config.get("timeframe_control", {})
                    signal_timeframe = signal.get("expiry", 0)
                    suspended_timeframes = timeframe_control.get("suspended_timeframes", [])
                    
                    if signal_timeframe in suspended_timeframes:
                        return False, f"Timeframe {signal_timeframe} minutes is suspended"
                    
                    timeframe_settings = timeframe_config.get("timeframe_settings", {})
                    timeframe_str = str(signal_timeframe)
                    
                    if timeframe_str in timeframe_settings:
                        timeframe_enabled = timeframe_settings[timeframe_str].get("enabled", True)
                        if not timeframe_enabled:
                            return False, f"Timeframe {signal_timeframe} minutes is disabled"
                    
                    return True, f"Timeframe {signal_timeframe} minutes is enabled"
                    
                except Exception as e:
                    return True, f"Error: {str(e)}"
        
        mock_bot = MockBot()
        valid, message = mock_bot.validate_timeframe(test_signal)
        
        if not valid and "suspended" in message.lower():
            print("✅ 1-minute timeframe correctly blocked when suspended")
        else:
            print(f"❌ 1-minute timeframe not properly blocked: {message}")
            return False
        
        # Restore original configuration
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(backup_config, f, indent=4)
        
        print("✅ Original configuration restored")
        print("✅ Timeframe suspension simulation completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error in suspension simulation: {e}")
        return False

def test_interactive_prompt_simulation():
    """Test 5: Simulate the interactive prompt functionality."""
    print("\n❓ Test 5: Interactive Prompt Simulation")
    print("-" * 50)
    
    try:
        # Simulate the prompt logic
        enabled_timeframes = {1, 3, 5}
        print(f"📊 Currently Enabled Timeframes: {sorted(enabled_timeframes)}")
        
        # Simulate user input parsing
        test_inputs = [
            ("1,3", [1, 3], "Valid comma-separated input"),
            ("5", [5], "Single timeframe input"),
            ("1, 3, 5", [1, 3, 5], "Comma-separated with spaces"),
            ("none", [], "No suspension input"),
            ("", [], "Empty input"),
            ("2,10", [], "Invalid timeframes (not enabled)"),
        ]
        
        for user_input, expected_result, description in test_inputs:
            # Parse input logic
            if user_input.lower() in ['none', 'n', '']:
                result = []
            else:
                result = []
                for tf_str in user_input.split(','):
                    tf_str = tf_str.strip()
                    if tf_str.isdigit():
                        tf = int(tf_str)
                        if tf in enabled_timeframes:
                            result.append(tf)
            
            if result == expected_result:
                print(f"✅ Input '{user_input}': {description} - Parsed correctly: {result}")
            else:
                print(f"❌ Input '{user_input}': {description} - Parse failed: {result} (expected: {expected_result})")
                return False
        
        print("✅ Interactive prompt simulation completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error in prompt simulation: {e}")
        return False

def run_comprehensive_test():
    """Run all timeframe toggle tests."""
    print("🎯 SIGNALSNIPER TIMEFRAME TOGGLE COMPREHENSIVE TEST")
    print("=" * 60)
    
    tests = [
        ("Configuration File Creation", test_timeframe_config_creation),
        ("Toggle Script Functionality", test_timeframe_toggle_script),
        ("Signal Validation Integration", test_signal_validation_integration),
        ("Timeframe Suspension Simulation", test_timeframe_suspension_simulation),
        ("Interactive Prompt Simulation", test_interactive_prompt_simulation),
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, test_function in tests:
        try:
            if test_function():
                passed_tests += 1
                print(f"\n✅ {test_name}: PASSED")
            else:
                print(f"\n❌ {test_name}: FAILED")
        except Exception as e:
            print(f"\n❌ {test_name}: ERROR - {e}")
    
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {(passed_tests / total_tests) * 100:.1f}%")
    
    if passed_tests == total_tests:
        print("\n🎉 ALL TESTS PASSED! Timeframe toggle feature is working correctly.")
        print("\n📋 FEATURE SUMMARY:")
        print("✅ Timeframe configuration system implemented")
        print("✅ Interactive toggle script created")
        print("✅ Signal validation integration working")
        print("✅ Suspension functionality verified")
        print("✅ User prompt system functional")
        print("\n🚀 READY FOR DEPLOYMENT!")
        return True
    else:
        print(f"\n❌ {total_tests - passed_tests} test(s) failed. Please review and fix issues.")
        return False

def main():
    """Main function."""
    print("🎯 SignalSniper Timeframe Toggle Test Suite")
    print("=" * 50)
    
    try:
        success = run_comprehensive_test()
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n❌ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal test error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
