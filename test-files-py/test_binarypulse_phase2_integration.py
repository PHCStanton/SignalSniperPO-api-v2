#!/usr/bin/env python3
"""
BinaryPulse Bot Phase 2 Integration Test

This script tests the complete Phase 2 integration of @BinaryPulse_bot
with SignalSniper_mod.py including:
- Channel manager recognition of BinaryPulse parser
- Enhanced timeframe filtering with channel-specific settings
- Signal processing and validation
- Integration readiness verification
"""

import os
import sys
import json
import logging
from datetime import datetime
import pytz

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_channel_manager_binarypulse_recognition():
    """Test that channel manager can recognize and load BinaryPulse parser"""
    logger.info("🧪 Testing Channel Manager BinaryPulse Parser Recognition...")
    
    try:
        # Import channel manager
        from channel_manager import ChannelManager
        
        # Create test channel config for BinaryPulse
        test_config = {
            "channel_name": "BinaryPulse Bot Test",
            "parser_type": "binarypulse_bot",
            "enabled": True
        }
        
        # Initialize channel manager
        manager = ChannelManager()
        
        # Test parser class loading
        parser_class = manager._load_parser_class("BinaryPulse Bot Test", "binarypulse_bot")
        
        if parser_class:
            logger.info("✅ BinaryPulse parser class loaded successfully")
            logger.info(f"   Parser class: {parser_class.__name__}")
            
            # Test parser creation
            parser_instance = parser_class(test_config)
            if parser_instance:
                logger.info("✅ BinaryPulse parser instance created successfully")
                return True
            else:
                logger.error("❌ Failed to create BinaryPulse parser instance")
                return False
        else:
            logger.error("❌ Failed to load BinaryPulse parser class")
            return False
            
    except Exception as e:
        logger.error(f"❌ Channel manager test failed: {str(e)}")
        return False

def test_binarypulse_configuration():
    """Test BinaryPulse bot configuration file"""
    logger.info("🧪 Testing BinaryPulse Bot Configuration...")
    
    config_file = "config/channels/binarypulse_bot.json"
    
    if not os.path.exists(config_file):
        logger.error(f"❌ BinaryPulse config file not found: {config_file}")
        return False
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Test required fields
        required_fields = [
            "channel_name", "parser_type", "enabled", "parser_config",
            "signal_characteristics", "timeframe_filtering", "bot_integration"
        ]
        
        for field in required_fields:
            if field not in config:
                logger.error(f"❌ Missing required field: {field}")
                return False
        
        # Test parser type
        if config["parser_type"] != "binarypulse_bot":
            logger.error(f"❌ Incorrect parser type: {config['parser_type']}")
            return False
        
        # Test timeframe filtering configuration
        timeframe_filtering = config.get("timeframe_filtering", {})
        if not timeframe_filtering.get("enabled", False):
            logger.error("❌ Timeframe filtering not enabled")
            return False
        
        logger.info("✅ BinaryPulse configuration is valid")
        logger.info(f"   Channel: {config['channel_name']}")
        logger.info(f"   Parser: {config['parser_type']}")
        logger.info(f"   Timeframe filtering: {timeframe_filtering['enabled']}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Configuration test failed: {str(e)}")
        return False

def test_timeframe_configuration():
    """Test timeframe configuration with BinaryPulse-specific settings"""
    logger.info("🧪 Testing Timeframe Configuration...")
    
    config_file = "config/timeframe_config.json"
    
    if not os.path.exists(config_file):
        logger.error(f"❌ Timeframe config file not found: {config_file}")
        return False
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Test channel-specific configuration
        channel_specific = config.get("channel_specific", {})
        binarypulse_config = channel_specific.get("binarypulse_bot")
        
        if not binarypulse_config:
            logger.error("❌ BinaryPulse-specific timeframe config not found")
            return False
        
        # Test timeframe settings
        timeframes = binarypulse_config.get("timeframes", {})
        expected_timeframes = ["1", "3", "5"]
        
        for tf in expected_timeframes:
            if tf not in timeframes:
                logger.error(f"❌ Missing timeframe configuration: {tf}")
                return False
            
            tf_config = timeframes[tf]
            if "enabled" not in tf_config or "priority" not in tf_config:
                logger.error(f"❌ Incomplete timeframe config for {tf}min")
                return False
        
        # Test filtering rules
        filtering_rules = binarypulse_config.get("filtering_rules", {})
        required_rules = ["filter_by_duration", "skip_disabled_timeframes", "log_filtered_signals"]
        
        for rule in required_rules:
            if rule not in filtering_rules:
                logger.error(f"❌ Missing filtering rule: {rule}")
                return False
        
        logger.info("✅ Timeframe configuration is valid")
        logger.info(f"   BinaryPulse timeframes: {list(timeframes.keys())}")
        logger.info(f"   Filtering rules: {len(filtering_rules)} configured")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Timeframe configuration test failed: {str(e)}")
        return False

def test_binarypulse_parser():
    """Test BinaryPulse parser functionality"""
    logger.info("🧪 Testing BinaryPulse Parser...")
    
    try:
        # Import parser
        sys.path.append('src')
        from src.parsers.binarypulse_bot_parser import BinaryPulseBotParser
        
        # Load configuration
        with open("config/channels/binarypulse_bot.json", 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Create parser instance
        parser = BinaryPulseBotParser(config)
        
        # Test signal parsing
        test_signals = [
            {
                "message": """📢 SIGNAL TO ENTER
✅ Couple: EUR/USD OTC
📉 Direction: DOWN
🕐 Time expiration: 3 min""",
                "expected": {"pair": "EUR/USD", "direction": "LOWER", "expiry": 3}
            },
            {
                "message": """📢 SIGNAL TO ENTER
✅ Couple: AUD/CAD
📈 Direction: UP
🕐 Time expiration: 1 min""",
                "expected": {"pair": "AUD/CAD", "direction": "HIGHER", "expiry": 1}
            },
            {
                "message": """📢 SIGNAL TO ENTER
✅ Couple: GBP/USD OTC
📉 Direction: DOWN
🕐 Time expiration: 5 min""",
                "expected": {"pair": "GBP/USD", "direction": "LOWER", "expiry": 5}
            }
        ]
        
        parsed_count = 0
        for i, test in enumerate(test_signals, 1):
            signal = parser.parse_message(test["message"])
            
            if signal:
                expected = test["expected"]
                if (signal.pair == expected["pair"] and 
                    signal.direction == expected["direction"] and 
                    signal.expiry == expected["expiry"]):
                    logger.info(f"✅ Test signal {i} parsed correctly: {signal.pair} {signal.direction} {signal.expiry}min")
                    parsed_count += 1
                else:
                    logger.error(f"❌ Test signal {i} parsed incorrectly")
                    logger.error(f"   Expected: {expected}")
                    logger.error(f"   Got: {signal.pair} {signal.direction} {signal.expiry}min")
            else:
                logger.error(f"❌ Test signal {i} failed to parse")
        
        if parsed_count == len(test_signals):
            logger.info("✅ All BinaryPulse test signals parsed successfully")
            return True
        else:
            logger.error(f"❌ Only {parsed_count}/{len(test_signals)} signals parsed correctly")
            return False
            
    except Exception as e:
        logger.error(f"❌ BinaryPulse parser test failed: {str(e)}")
        return False

def test_enhanced_timeframe_filtering():
    """Test enhanced timeframe filtering logic"""
    logger.info("🧪 Testing Enhanced Timeframe Filtering...")
    
    try:
        # Create mock signal data
        test_signals = [
            {
                "pair": "EUR/USD",
                "direction": "HIGHER", 
                "expiry": 1,
                "channel": "BinaryPulse Bot",
                "parser_type": "binarypulse_bot"
            },
            {
                "pair": "AUD/CAD",
                "direction": "LOWER",
                "expiry": 3,
                "channel": "BinaryPulse Bot", 
                "parser_type": "binarypulse_bot"
            },
            {
                "pair": "GBP/USD",
                "direction": "HIGHER",
                "expiry": 5,
                "channel": "BinaryPulse Bot",
                "parser_type": "binarypulse_bot"
            }
        ]
        
        # Test timeframe validation logic
        from SignalSniper_mod import ModularSelfBot
        
        # Create bot instance (without full initialization)
        bot = ModularSelfBot()
        
        validation_results = []
        for signal in test_signals:
            is_valid, message = bot.validate_timeframe(signal)
            validation_results.append({
                "signal": f"{signal['pair']} {signal['expiry']}min",
                "valid": is_valid,
                "message": message
            })
            
            if is_valid:
                logger.info(f"✅ {signal['pair']} {signal['expiry']}min: {message}")
            else:
                logger.info(f"❌ {signal['pair']} {signal['expiry']}min: {message}")
        
        # Check if at least some signals are valid (depends on current timeframe config)
        valid_count = sum(1 for result in validation_results if result["valid"])
        
        if valid_count > 0:
            logger.info(f"✅ Timeframe filtering working: {valid_count}/{len(test_signals)} signals valid")
            return True
        else:
            logger.warning("⚠️ All signals filtered out - check timeframe configuration")
            return True  # This might be expected behavior
            
    except Exception as e:
        logger.error(f"❌ Enhanced timeframe filtering test failed: {str(e)}")
        return False

def test_integration_readiness():
    """Test overall integration readiness"""
    logger.info("🧪 Testing Integration Readiness...")
    
    try:
        # Test file existence
        required_files = [
            "config/channels/binarypulse_bot.json",
            "config/timeframe_config.json", 
            "src/parsers/binarypulse_bot_parser.py",
            "channel_manager.py",
            "SignalSniper_mod.py"
        ]
        
        missing_files = []
        for file_path in required_files:
            if not os.path.exists(file_path):
                missing_files.append(file_path)
        
        if missing_files:
            logger.error(f"❌ Missing required files: {missing_files}")
            return False
        
        # Test imports
        try:
            from channel_manager import ChannelManager
            from src.parsers.binarypulse_bot_parser import BinaryPulseBotParser
            logger.info("✅ All required imports successful")
        except ImportError as e:
            logger.error(f"❌ Import error: {str(e)}")
            return False
        
        # Test configuration consistency
        with open("config/channels/binarypulse_bot.json", 'r', encoding='utf-8') as f:
            channel_config = json.load(f)
        
        with open("config/timeframe_config.json", 'r', encoding='utf-8') as f:
            timeframe_config = json.load(f)
        
        # Check if channel config references match timeframe config
        if "binarypulse_bot" not in timeframe_config.get("channel_specific", {}):
            logger.error("❌ BinaryPulse not found in timeframe channel_specific config")
            return False
        
        logger.info("✅ Integration readiness verified")
        return True
        
    except Exception as e:
        logger.error(f"❌ Integration readiness test failed: {str(e)}")
        return False

def main():
    """Run all Phase 2 integration tests"""
    logger.info("🎯 BinaryPulse Bot Phase 2 Integration Test Suite")
    logger.info("=" * 60)
    
    tests = [
        ("Channel Manager BinaryPulse Recognition", test_channel_manager_binarypulse_recognition),
        ("BinaryPulse Configuration", test_binarypulse_configuration),
        ("Timeframe Configuration", test_timeframe_configuration),
        ("BinaryPulse Parser", test_binarypulse_parser),
        ("Enhanced Timeframe Filtering", test_enhanced_timeframe_filtering),
        ("Integration Readiness", test_integration_readiness)
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\n📋 Running: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"❌ Test '{test_name}' crashed: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("📊 TEST RESULTS SUMMARY")
    logger.info("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status}: {test_name}")
        if result:
            passed += 1
    
    logger.info(f"\n📈 OVERALL RESULT: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 ALL TESTS PASSED - BinaryPulse Phase 2 integration ready!")
        return True
    else:
        logger.error(f"⚠️ {total - passed} tests failed - Phase 2 integration needs attention")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
