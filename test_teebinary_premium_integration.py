#!/usr/bin/env python3
"""
TeeBinary Premium Integration Test

This script tests the complete TeeBinary Premium integration including:
- Parser functionality
- Channel configuration
- Multi-parser support in test channel
- Signal validation
- Channel manager integration
"""

import sys
import os
import json
import logging
from datetime import datetime
import pytz

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.parsers.teebinary_premium_parser import TeeBinaryPremiumParser
from src.parsers.multi_parser import MultiParser
from channel_manager import ChannelManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TeeBinaryPremiumIntegrationTest:
    """Comprehensive test suite for TeeBinary Premium integration"""
    
    def __init__(self):
        self.test_results = []
        self.passed_tests = 0
        self.failed_tests = 0
    
    def run_all_tests(self):
        """Run all integration tests"""
        logger.info("🚀 Starting TeeBinary Premium Integration Tests")
        logger.info("=" * 60)
        
        # Test 1: TeeBinary Premium Parser
        self.test_teebinary_premium_parser()
        
        # Test 2: Channel Configuration Loading
        self.test_channel_configuration()
        
        # Test 3: Multi-Parser Functionality
        self.test_multi_parser()
        
        # Test 4: Channel Manager Integration
        self.test_channel_manager_integration()
        
        # Test 5: Signal Validation
        self.test_signal_validation()
        
        # Test 6: Test Channel Multi-Parser Support
        self.test_test_channel_multi_parser()
        
        # Print results
        self.print_test_results()
    
    def test_teebinary_premium_parser(self):
        """Test TeeBinary Premium parser functionality"""
        logger.info("📋 Test 1: TeeBinary Premium Parser")
        
        try:
            # Load TeeBinary Premium config
            config_path = "config/channels/teebinary_premium.json"
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Create parser
            parser = TeeBinaryPremiumParser(config)
            
            # Test valid signals
            test_signals = [
                "EUR/USD CALL 5MIN",
                "GBP/USD PUT 5MIN",
                "USD/JPY CALL 5MIN",
                "XAU/USD PUT 5MIN"
            ]
            
            valid_count = 0
            for signal_text in test_signals:
                signal = parser.parse_message(signal_text)
                if signal:
                    valid_count += 1
                    logger.info(f"  ✅ Parsed: {signal.pair} {signal.direction} {signal.expiry}min")
                else:
                    logger.warning(f"  ❌ Failed to parse: {signal_text}")
            
            # Test invalid signals (should be ignored)
            invalid_signals = [
                "BE READY",
                "GO",
                "WAIT FOR SIGNAL",
                "EUR/USD CALL 1MIN",  # Wrong duration
                "INVALID/PAIR CALL 5MIN"  # Invalid pair
            ]
            
            ignored_count = 0
            for signal_text in invalid_signals:
                signal = parser.parse_message(signal_text)
                if signal is None:
                    ignored_count += 1
                    logger.info(f"  ✅ Correctly ignored: {signal_text}")
                else:
                    logger.warning(f"  ❌ Should have ignored: {signal_text}")
            
            success = (valid_count == len(test_signals) and ignored_count == len(invalid_signals))
            self.record_test("TeeBinary Premium Parser", success, 
                           f"Parsed {valid_count}/{len(test_signals)} valid signals, ignored {ignored_count}/{len(invalid_signals)} invalid signals")
            
        except Exception as e:
            self.record_test("TeeBinary Premium Parser", False, f"Exception: {str(e)}")
    
    def test_channel_configuration(self):
        """Test channel configuration loading"""
        logger.info("📋 Test 2: Channel Configuration")
        
        try:
            config_path = "config/channels/teebinary_premium.json"
            
            # Check if config file exists
            if not os.path.exists(config_path):
                self.record_test("Channel Configuration", False, "Config file not found")
                return
            
            # Load and validate config
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Check required fields
            required_fields = ['channel_name', 'channel_id', 'parser_type', 'enabled', 'parser_config']
            missing_fields = [field for field in required_fields if field not in config]
            
            if missing_fields:
                self.record_test("Channel Configuration", False, f"Missing fields: {missing_fields}")
                return
            
            # Validate specific values
            parser_config = config.get('parser_config', {})
            checks = [
                (config['channel_name'] == 'TeeBinary_Premium', "Channel name"),
                (config['channel_id'] == -1001222324493, "Channel ID"),
                (config['parser_type'] == 'teebinary_premium', "Parser type"),
                (config['enabled'] == True, "Enabled flag"),
                ('signal_pattern' in parser_config.get('message_patterns', {}), "Signal pattern in config")
            ]
            
            failed_checks = [desc for check, desc in checks if not check]
            
            if failed_checks:
                self.record_test("Channel Configuration", False, f"Failed checks: {failed_checks}")
            else:
                self.record_test("Channel Configuration", True, "All configuration fields valid")
                logger.info("  ✅ Configuration loaded and validated successfully")
            
        except Exception as e:
            self.record_test("Channel Configuration", False, f"Exception: {str(e)}")
    
    def test_multi_parser(self):
        """Test multi-parser functionality"""
        logger.info("📋 Test 3: Multi-Parser Functionality")
        
        try:
            # Load test channel config
            config_path = "config/channels/test_channel.json"
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Create multi-parser
            multi_parser = MultiParser(config)
            
            # Test different signal formats
            test_cases = [
                ("EUR/USD CALL 5MIN", "teebinary_premium", "TeeBinary Premium format"),
                ("Trading Pair: GBP/USD", "binary_trading_club", "Binary Trading Club format (partial)"),
                ("🎯 USD/JPY CALL 1M", "generic", "Generic format")
            ]
            
            successful_parses = 0
            for signal_text, expected_parser, description in test_cases:
                signal = multi_parser.parse_message(signal_text)
                
                if signal_text == "Trading Pair: GBP/USD":
                    # This is a partial signal, should not parse completely
                    if signal is None:
                        successful_parses += 1
                        logger.info(f"  ✅ {description}: Correctly handled partial signal")
                    else:
                        logger.warning(f"  ❌ {description}: Should not parse partial signal")
                else:
                    if signal:
                        used_parser = signal.raw_data.get('multi_parser_used', 'unknown') if signal.raw_data else 'unknown'
                        if used_parser == expected_parser:
                            successful_parses += 1
                            logger.info(f"  ✅ {description}: Used {used_parser} parser")
                        else:
                            logger.warning(f"  ❌ {description}: Expected {expected_parser}, got {used_parser}")
                    else:
                        logger.warning(f"  ❌ {description}: Failed to parse")
            
            # Check parser statistics
            stats = multi_parser.get_parsing_stats()
            has_stats = all(key in stats for key in ['parsing_attempts', 'successful_parses', 'parser_usage_stats'])
            
            success = (successful_parses >= 2 and has_stats)  # At least 2 successful parses
            self.record_test("Multi-Parser Functionality", success, 
                           f"Successfully parsed {successful_parses}/3 test cases, stats available: {has_stats}")
            
        except Exception as e:
            self.record_test("Multi-Parser Functionality", False, f"Exception: {str(e)}")
    
    def test_channel_manager_integration(self):
        """Test channel manager integration"""
        logger.info("📋 Test 4: Channel Manager Integration")
        
        try:
            # Create channel manager
            manager = ChannelManager()
            
            # Test loading TeeBinary Premium parser
            teebinary_config = {
                'channel_name': 'TeeBinary_Premium',
                'parser_type': 'teebinary_premium',
                'enabled': True,
                'parser_config': {}
            }
            
            parser = manager._create_parser('TeeBinary_Premium', teebinary_config)
            
            if parser and parser.__class__.__name__ == 'TeeBinaryPremiumParser':
                logger.info("  ✅ TeeBinary Premium parser created successfully")
                teebinary_success = True
            else:
                logger.warning("  ❌ Failed to create TeeBinary Premium parser")
                teebinary_success = False
            
            # Test loading Multi-Parser
            multi_config = {
                'channel_name': 'Test_Channel',
                'parser_type': 'multi_parser',
                'enabled': True,
                'parser_config': {}
            }
            
            multi_parser = manager._create_parser('Test_Channel', multi_config)
            
            if multi_parser and multi_parser.__class__.__name__ == 'MultiParser':
                logger.info("  ✅ Multi-parser created successfully")
                multi_success = True
            else:
                logger.warning("  ❌ Failed to create multi-parser")
                multi_success = False
            
            success = teebinary_success and multi_success
            self.record_test("Channel Manager Integration", success, 
                           f"TeeBinary parser: {teebinary_success}, Multi-parser: {multi_success}")
            
        except Exception as e:
            self.record_test("Channel Manager Integration", False, f"Exception: {str(e)}")
    
    def test_signal_validation(self):
        """Test signal validation"""
        logger.info("📋 Test 5: Signal Validation")
        
        try:
            # Load TeeBinary Premium config
            config_path = "config/channels/teebinary_premium.json"
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            parser = TeeBinaryPremiumParser(config)
            
            # Test valid signal
            valid_signal = parser.parse_message("EUR/USD CALL 5MIN")
            
            if valid_signal:
                is_valid, msg = parser.validate_signal(valid_signal)
                if is_valid:
                    logger.info("  ✅ Valid signal passed validation")
                    validation_success = True
                else:
                    logger.warning(f"  ❌ Valid signal failed validation: {msg}")
                    validation_success = False
            else:
                logger.warning("  ❌ Failed to parse valid signal")
                validation_success = False
            
            # Test direction mapping
            call_signal = parser.parse_message("GBP/USD CALL 5MIN")
            put_signal = parser.parse_message("USD/JPY PUT 5MIN")
            
            direction_mapping_success = (
                call_signal and call_signal.direction == "HIGHER" and
                put_signal and put_signal.direction == "LOWER"
            )
            
            if direction_mapping_success:
                logger.info("  ✅ Direction mapping (CALL→HIGHER, PUT→LOWER) working correctly")
            else:
                logger.warning("  ❌ Direction mapping failed")
            
            success = validation_success and direction_mapping_success
            self.record_test("Signal Validation", success, 
                           f"Validation: {validation_success}, Direction mapping: {direction_mapping_success}")
            
        except Exception as e:
            self.record_test("Signal Validation", False, f"Exception: {str(e)}")
    
    def test_test_channel_multi_parser(self):
        """Test test channel multi-parser configuration"""
        logger.info("📋 Test 6: Test Channel Multi-Parser Support")
        
        try:
            # Load test channel config
            config_path = "config/channels/test_channel.json"
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Check multi-parser configuration
            checks = [
                (config.get('parser_type') == 'multi_parser', "Parser type is multi_parser"),
                (config.get('channel_id') == -1002322984519, "Test channel ID correct"),
                ('parser_priority' in config.get('parser_config', {}), "Parser priority configured"),
                ('teebinary_premium' in config.get('parser_config', {}).get('parser_priority', []), "TeeBinary Premium in priority"),
                ('binary_trading_club' in config.get('parser_config', {}).get('parser_priority', []), "Binary Trading Club in priority")
            ]
            
            passed_checks = sum(1 for check, _ in checks if check)
            
            for check, description in checks:
                if check:
                    logger.info(f"  ✅ {description}")
                else:
                    logger.warning(f"  ❌ {description}")
            
            success = bool(passed_checks == len(checks))
            self.record_test("Test Channel Multi-Parser Support", success, 
                           f"Passed {passed_checks}/{len(checks)} configuration checks")
            
        except Exception as e:
            self.record_test("Test Channel Multi-Parser Support", False, f"Exception: {str(e)}")
    
    def record_test(self, test_name: str, success: bool, details: str):
        """Record test result"""
        self.test_results.append({
            'name': test_name,
            'success': success,
            'details': details,
            'timestamp': datetime.now(pytz.UTC).isoformat()
        })
        
        if success:
            self.passed_tests += 1
        else:
            self.failed_tests += 1
    
    def print_test_results(self):
        """Print comprehensive test results"""
        logger.info("=" * 60)
        logger.info("🎯 TEEBINARY PREMIUM INTEGRATION TEST RESULTS")
        logger.info("=" * 60)
        
        for result in self.test_results:
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            logger.info(f"{status} | {result['name']}")
            logger.info(f"     Details: {result['details']}")
            logger.info("")
        
        logger.info("=" * 60)
        logger.info(f"📊 SUMMARY: {self.passed_tests} PASSED, {self.failed_tests} FAILED")
        
        if self.failed_tests == 0:
            logger.info("🎉 ALL TESTS PASSED! TeeBinary Premium integration is ready!")
        else:
            logger.warning(f"⚠️  {self.failed_tests} tests failed. Please review and fix issues.")
        
        logger.info("=" * 60)
        
        return self.failed_tests == 0

def main():
    """Run the integration tests"""
    test_suite = TeeBinaryPremiumIntegrationTest()
    success = test_suite.run_all_tests()
    
    if success:
        print("\n🚀 TeeBinary Premium integration is ready for production!")
        print("📋 Next steps:")
        print("   1. Forward TeeBinary Premium signals to test channel for demo trading")
        print("   2. Validate signal parsing and trade execution")
        print("   3. Switch to live TeeBinary Premium channel when ready")
    else:
        print("\n⚠️  Integration tests failed. Please fix issues before proceeding.")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())
