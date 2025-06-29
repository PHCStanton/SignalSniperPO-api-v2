#!/usr/bin/env python3
"""
Modular Channel Parser System for HFT SignalSniper Bot

This system provides a clean, extensible architecture for handling
different Telegram channels with their own parsing logic and configurations.

Directory Structure:
config/
├── telegram_config.json          # Main telegram config (your existing file)
├── channels/                     # Channel-specific configurations
│   ├── binary_trading_club.json
│   ├── forex_signals_pro.json
│   └── crypto_alerts_vip.json
src/
├── parsers/                      # Channel-specific parsers
│   ├── __init__.py
│   ├── base_parser.py           # Base parser class
│   ├── binary_trading_club.py
│   ├── forex_signals_pro.py
│   └── crypto_alerts_vip.py
"""

import os
import json
import importlib
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Signal:
    """Standard signal format that all parsers should return"""
    pair: str
    direction: str  # 'HIGHER' or 'LOWER'
    expiry_minutes: int
    timer: Optional[str] = None
    confidence: Optional[float] = None
    timestamp: datetime = None
    raw_data: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.raw_data is None:
            self.raw_data = {}

class BaseChannelParser(ABC):
    """
    Abstract base class for all channel parsers.
    Each channel parser should inherit from this class.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.channel_name = config.get('channel_name', 'Unknown')
        self.channel_id = config.get('channel_id')
        self.parser_config = config.get('parser_config', {})
        
    @abstractmethod
    def parse_message(self, message_text: str, message_data: Dict[str, Any]) -> Optional[Signal]:
        """
        Parse a single message and return a Signal object if valid.
        
        Args:
            message_text: The text content of the message
            message_data: Additional message metadata (timestamp, sender, etc.)
            
        Returns:
            Signal object if message contains valid trading signal, None otherwise
        """
        pass
    
    @abstractmethod
    def validate_signal(self, signal: Signal) -> bool:
        """
        Validate if the parsed signal meets the channel's criteria.
        
        Args:
            signal: The Signal object to validate
            
        Returns:
            True if signal is valid, False otherwise
        """
        pass
    
    def get_channel_info(self) -> Dict[str, Any]:
        """Return basic channel information"""
        return {
            'name': self.channel_name,
            'id': self.channel_id,
            'parser_type': self.__class__.__name__
        }

class ChannelConfigManager:
    """Manages loading and validation of channel configurations"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = config_dir
        self.channels_dir = os.path.join(config_dir, "channels")
        self.main_config_file = os.path.join(config_dir, "telegram_config.json")
        
        # Ensure directories exist
        os.makedirs(self.channels_dir, exist_ok=True)
    
    def load_main_config(self) -> Dict[str, Any]:
        """Load the main telegram configuration"""
        try:
            with open(self.main_config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Main config file not found: {self.main_config_file}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing main config: {e}")
            raise
    
    def get_channel_config_file(self, channel_name: str) -> str:
        """Get the config file path for a specific channel"""
        # Convert channel name to filename-safe format
        safe_name = channel_name.lower().replace(' ', '_').replace('-', '_')
        safe_name = ''.join(c for c in safe_name if c.isalnum() or c == '_')
        return os.path.join(self.channels_dir, f"{safe_name}.json")
    
    def load_channel_config(self, channel_name: str) -> Dict[str, Any]:
        """Load configuration for a specific channel"""
        config_file = self.get_channel_config_file(channel_name)
        
        if not os.path.exists(config_file):
            logger.warning(f"Channel config not found: {config_file}")
            return self.create_default_channel_config(channel_name)
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            logger.info(f"Loaded channel config: {config_file}")
            return config
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing channel config {config_file}: {e}")
            raise
    
    def save_channel_config(self, channel_name: str, config: Dict[str, Any]) -> bool:
        """Save configuration for a specific channel"""
        config_file = self.get_channel_config_file(channel_name)
        
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved channel config: {config_file}")
            return True
        except Exception as e:
            logger.error(f"Error saving channel config {config_file}: {e}")
            return False
    
    def create_default_channel_config(self, channel_name: str) -> Dict[str, Any]:
        """Create a default configuration for a new channel"""
        default_config = {
            "channel_name": channel_name,
            "parser_type": "generic",
            "enabled": True,
            "parser_config": {
                "message_patterns": [],
                "signal_validation": {
                    "required_fields": ["pair", "direction", "expiry_minutes"],
                    "valid_directions": ["HIGHER", "LOWER"],
                    "min_expiry_minutes": 1,
                    "max_expiry_minutes": 60
                },
                "pair_formats": ["XXX/XXX", "XXXYYY"],
                "preprocessing": {
                    "remove_emojis": True,
                    "normalize_whitespace": True,
                    "convert_to_uppercase": False
                }
            },
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "description": f"Auto-generated config for {channel_name}",
                "version": "1.0"
            }
        }
        
        # Save the default config
        self.save_channel_config(channel_name, default_config)
        return default_config

class ParserFactory:
    """Factory class for creating channel-specific parsers"""
    
    def __init__(self, parsers_module_path: str = "src.parsers"):
        self.parsers_module_path = parsers_module_path
        self.parser_cache = {}
    
    def get_parser_class_name(self, channel_name: str, parser_type: str = None) -> str:
        """Generate parser class name from channel name"""
        if parser_type:
            return f"{parser_type.title()}Parser"
        
        # Convert channel name to class name format
        safe_name = channel_name.lower().replace(' ', '_').replace('-', '_')
        safe_name = ''.join(c for c in safe_name if c.isalnum() or c == '_')
        class_name = ''.join(word.capitalize() for word in safe_name.split('_'))
        return f"{class_name}Parser"
    
    def get_parser_module_name(self, channel_name: str, parser_type: str = None) -> str:
        """Generate parser module name from channel name"""
        if parser_type:
            return parser_type.lower()
        
        safe_name = channel_name.lower().replace(' ', '_').replace('-', '_')
        return ''.join(c for c in safe_name if c.isalnum() or c == '_')
    
    def create_parser(self, channel_config: Dict[str, Any]) -> BaseChannelParser:
        """Create a parser instance for the given channel configuration"""
        channel_name = channel_config.get('channel_name', 'unknown')
        parser_type = channel_config.get('parser_type', None)
        
        # Check cache first
        cache_key = f"{channel_name}:{parser_type}"
        if cache_key in self.parser_cache:
            parser_class = self.parser_cache[cache_key]
        else:
            parser_class = self._load_parser_class(channel_name, parser_type)
            self.parser_cache[cache_key] = parser_class
        
        return parser_class(channel_config)
    
    def _load_parser_class(self, channel_name: str, parser_type: str = None):
        """Load parser class dynamically"""
        module_name = self.get_parser_module_name(channel_name, parser_type)
        class_name = self.get_parser_class_name(channel_name, parser_type)
        
        try:
            # Try to import the specific parser module
            full_module_path = f"{self.parsers_module_path}.{module_name}"
            module = importlib.import_module(full_module_path)
            parser_class = getattr(module, class_name)
            logger.info(f"Loaded parser: {full_module_path}.{class_name}")
            return parser_class
        except (ImportError, AttributeError) as e:
            logger.warning(f"Could not load parser {full_module_path}.{class_name}: {e}")
            # Fall back to generic parser
            return self._load_generic_parser()
    
    def _load_generic_parser(self):
        """Load the generic parser as fallback"""
        try:
            module = importlib.import_module(f"{self.parsers_module_path}.generic")
            return getattr(module, "GenericParser")
        except (ImportError, AttributeError):
            logger.error("Could not load generic parser fallback")
            raise ImportError("No parser available for channel")

class ChannelParserManager:
    """Main manager class that coordinates all parsing operations"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_manager = ChannelConfigManager(config_dir)
        self.parser_factory = ParserFactory()
        self.current_parser = None
        self.current_channel_name = None
    
    def initialize_from_main_config(self) -> bool:
        """Initialize the parser based on main telegram config"""
        try:
            main_config = self.config_manager.load_main_config()
            channel_name = main_config.get('channel_name')
            
            if not channel_name:
                logger.error("No channel_name found in main config")
                return False
            
            return self.switch_channel(channel_name)
        except Exception as e:
            logger.error(f"Error initializing from main config: {e}")
            return False
    
    def switch_channel(self, channel_name: str) -> bool:
        """Switch to a different channel parser"""
        try:
            # Load channel-specific configuration
            channel_config = self.config_manager.load_channel_config(channel_name)
            
            # Add main config data to channel config
            main_config = self.config_manager.load_main_config()
            channel_config.update({
                'api_id': main_config.get('api_id'),
                'api_hash': main_config.get('api_hash'),
                'session_name': main_config.get('session_name'),
                'channel_id': main_config.get('channel_id')
            })
            
            # Create parser instance
            self.current_parser = self.parser_factory.create_parser(channel_config)
            self.current_channel_name = channel_name
            
            logger.info(f"Switched to channel: {channel_name}")
            return True
        except Exception as e:
            logger.error(f"Error switching to channel {channel_name}: {e}")
            return False
    
    def parse_message(self, message_text: str, message_data: Dict[str, Any] = None) -> Optional[Signal]:
        """Parse a message using the current channel parser"""
        if not self.current_parser:
            logger.error("No parser initialized")
            return None
        
        if message_data is None:
            message_data = {}
        
        try:
            signal = self.current_parser.parse_message(message_text, message_data)
            
            if signal and self.current_parser.validate_signal(signal):
                logger.info(f"Valid signal parsed: {signal.pair} {signal.direction} {signal.expiry_minutes}min")
                return signal
            elif signal:
                logger.warning(f"Signal validation failed: {signal}")
            
            return None
        except Exception as e:
            logger.error(f"Error parsing message: {e}")
            return None
    
    def get_current_channel_info(self) -> Dict[str, Any]:
        """Get information about the current channel"""
        if not self.current_parser:
            return {"error": "No parser initialized"}
        
        return self.current_parser.get_channel_info()
    
    def list_available_channels(self) -> List[str]:
        """List all available channel configurations"""
        channels = []
        if os.path.exists(self.config_manager.channels_dir):
            for file in os.listdir(self.config_manager.channels_dir):
                if file.endswith('.json'):
                    channels.append(file[:-5])  # Remove .json extension
        return channels

# Example usage and testing
if __name__ == "__main__":
    # Example of how to use the system
    manager = ChannelParserManager()
    
    # Initialize from main config
    if manager.initialize_from_main_config():
        print("✅ Parser initialized successfully")
        
        # Get current channel info
        info = manager.get_current_channel_info()
        print(f"📡 Current channel: {info}")
        
        # Example message parsing
        test_message = "Trading Pair: EUR/USD\nSET THE TIMER TO 15:30:00\nHIGHER\nTrade time: 5 MIN"
        signal = manager.parse_message(test_message)
        
        if signal:
            print(f"🎯 Parsed signal: {signal}")
        else:
            print("❌ No valid signal found")
    else:
        print("❌ Failed to initialize parser")