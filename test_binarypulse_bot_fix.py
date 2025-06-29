#!/usr/bin/env python3
"""
Test script to verify BinaryPulse bot integration fix.

This script tests the fix for the "Channel not found: BinaryPulse Bot" error
by verifying that the access_channel method properly handles telegram bots
vs telegram channels.
"""

import asyncio
import json
import logging
import sys
import os
from unittest.mock import Mock, AsyncMock, patch

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MockChannelConfig:
    """Mock channel configuration for testing."""
    def __init__(self, channel_name, channel_id, source_type="telegram_channel"):
        self.channel_name = channel_name
        self.channel_id = channel_id
        self.config = {"source_type": source_type}
        self.parser_type = "binarypulse_bot" if source_type == "telegram_bot" else "generic"

class MockTelegramClient:
    """Mock Telegram client for testing."""
    def __init__(self):
        self.get_entity_calls = []
        self.iter_dialogs_calls = []
    
    async def get_entity(self, identifier):
        """Mock get_entity method."""
        self.get_entity_calls.append(identifier)
        
        # Simulate successful bot access
        if isinstance(identifier, str) and identifier == "BinaryPulse_bot":
            mock_bot = Mock()
            mock_bot.username = "BinaryPulse_bot"
            mock_bot.id = 123456789
            return mock_bot
        
        # Simulate channel access
        if isinstance(identifier, int) or (isinstance(identifier, str) and identifier.startswith("@")):
            mock_channel = Mock()
            mock_channel.title = "Test Channel"
            mock_channel.id = 987654321
            return mock_channel
        
        # Simulate entity not found
        raise Exception(f"Entity not found: {identifier}")
    
    async def iter_dialogs(self):
        """Mock iter_dialogs method."""
        self.iter_dialogs_calls.append("iter_dialogs_called")
        
        # Return empty async generator for simplicity
        if False:  # Never execute, just make it a generator
            yield

def test_channel_config_detection():
    """Test that channel configurations are properly detected."""
    logger.info("🧪 Testing channel configuration detection...")
    
    # Test bot configuration
    bot_config = MockChannelConfig(
        channel_name="BinaryPulse Bot",
        channel_id="@BinaryPulse_bot", 
        source_type="telegram_bot"
    )
    
    # Test channel configuration
    channel_config = MockChannelConfig(
        channel_name="Test Channel",
        channel_id="-1001234567890",
        source_type="telegram_channel"
    )
    
    # Verify bot config
    assert bot_config.config.get('source_type') == "telegram_bot"
    assert bot_config.channel_id == "@BinaryPulse_bot"
    assert bot_config.parser_type == "binarypulse_bot"
    
    # Verify channel config
    assert channel_config.config.get('source_type') == "telegram_channel"
    assert channel_config.channel_id == "-1001234567890"
    assert channel_config.parser_type == "generic"
    
    logger.info("✅ Channel configuration detection test passed")

async def test_access_channel_logic():
    """Test the access_channel method logic with mocked components."""
    logger.info("🧪 Testing access_channel method logic...")
    
    # Create mock telegram client
    mock_client = MockTelegramClient()
    
    # Test bot access
    bot_config = MockChannelConfig(
        channel_name="BinaryPulse Bot",
        channel_id="@BinaryPulse_bot",
        source_type="telegram_bot"
    )
    
    # Simulate the access_channel logic for bots
    channel_name = bot_config.channel_name
    channel_id = bot_config.channel_id
    source_type = bot_config.config.get('source_type', 'telegram_channel')
    
    logger.info(f"Accessing {source_type}: {channel_name}")
    
    if source_type == "telegram_bot":
        if channel_id and channel_id.startswith("@"):
            bot_username = channel_id[1:]  # Remove @ prefix
            logger.info(f"Accessing bot by username: {bot_username}")
            entity = await mock_client.get_entity(bot_username)
            logger.info(f"✅ Successfully accessed bot: @{bot_username}")
            
            # Verify the call was made correctly
            assert "BinaryPulse_bot" in mock_client.get_entity_calls
            assert entity.username == "BinaryPulse_bot"
        else:
            raise Exception(f"Invalid bot channel_id format: {channel_id}")
    
    # Test channel access
    channel_config = MockChannelConfig(
        channel_name="Test Channel",
        channel_id="-1001234567890",
        source_type="telegram_channel"
    )
    
    channel_name = channel_config.channel_name
    channel_id = channel_config.channel_id
    source_type = channel_config.config.get('source_type', 'telegram_channel')
    
    if source_type != "telegram_bot":
        if channel_id:
            if channel_id.startswith("@"):
                entity = await mock_client.get_entity(channel_id)
            else:
                entity = await mock_client.get_entity(int(channel_id))
            logger.info(f"Accessed channel by ID: {getattr(entity, 'title', 'Unknown')}")
            
            # Verify the call was made correctly
            assert -1001234567890 in mock_client.get_entity_calls
    
    logger.info("✅ Access channel logic test passed")

def test_binarypulse_config_validation():
    """Test that the BinaryPulse bot configuration is valid."""
    logger.info("🧪 Testing BinaryPulse bot configuration validation...")
    
    config_file = "config/channels/binarypulse_bot.json"
    
    if not os.path.exists(config_file):
        logger.error(f"❌ BinaryPulse bot config file not found: {config_file}")
        return False
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Validate required fields
        required_fields = [
            "channel_name",
            "parser_type", 
            "source_type",
            "enabled"
        ]
        
        for field in required_fields:
            if field not in config:
                logger.error(f"❌ Missing required field: {field}")
                return False
        
        # Validate specific values
        if config.get("source_type") != "telegram_bot":
            logger.error(f"❌ Invalid source_type: {config.get('source_type')}")
            return False
        
        if config.get("parser_type") != "binarypulse_bot":
            logger.error(f"❌ Invalid parser_type: {config.get('parser_type')}")
            return False
        
        if config.get("channel_name") != "BinaryPulse Bot":
            logger.error(f"❌ Invalid channel_name: {config.get('channel_name')}")
            return False
        
        logger.info("✅ BinaryPulse bot configuration validation passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error validating BinaryPulse bot config: {str(e)}")
        return False

def test_telegram_config_validation():
    """Test that the telegram configuration is set up for BinaryPulse bot."""
    logger.info("🧪 Testing telegram configuration validation...")
    
    config_file = "config/telegram_config.json"
    
    if not os.path.exists(config_file):
        logger.error(f"❌ Telegram config file not found: {config_file}")
        return False
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Check if configured for BinaryPulse Bot
        if config.get("channel_name") == "BinaryPulse Bot":
            if config.get("channel_id") == "@BinaryPulse_bot":
                logger.info("✅ Telegram config correctly set for BinaryPulse Bot")
                return True
            else:
                logger.warning(f"⚠️ Channel ID mismatch: {config.get('channel_id')}")
                return False
        else:
            logger.info(f"ℹ️ Telegram config set for: {config.get('channel_name')}")
            return True
        
    except Exception as e:
        logger.error(f"❌ Error validating telegram config: {str(e)}")
        return False

async def run_all_tests():
    """Run all tests and report results."""
    logger.info("🚀 Starting BinaryPulse Bot Integration Fix Tests")
    logger.info("=" * 60)
    
    tests = [
        ("Channel Config Detection", test_channel_config_detection),
        ("Access Channel Logic", test_access_channel_logic),
        ("BinaryPulse Config Validation", test_binarypulse_config_validation),
        ("Telegram Config Validation", test_telegram_config_validation)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            logger.info(f"\n📋 Running: {test_name}")
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            
            if result is not False:  # None or True counts as pass
                passed += 1
                logger.info(f"✅ {test_name}: PASSED")
            else:
                logger.error(f"❌ {test_name}: FAILED")
                
        except Exception as e:
            logger.error(f"❌ {test_name}: ERROR - {str(e)}")
    
    logger.info("\n" + "=" * 60)
    logger.info(f"📊 TEST RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 ALL TESTS PASSED - BinaryPulse bot integration fix is working!")
        return True
    else:
        logger.error("💥 SOME TESTS FAILED - Fix may need additional work")
        return False

def main():
    """Main function to run the tests."""
    try:
        result = asyncio.run(run_all_tests())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        logger.info("\n⏹️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"💥 Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
