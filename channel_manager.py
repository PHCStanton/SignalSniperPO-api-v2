#!/usr/bin/env python3
"""
Channel Manager for Modular Channel Architecture

This module provides the main ChannelManager class that coordinates
channel switching, parser loading, and message processing across
different Telegram channels.
"""

import os
import json
import importlib
import logging
import sys
from typing import Dict, Any, Optional, List
from datetime import datetime
import pytz

# Add src to path for parser imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.parsers.base_parser import BaseChannelParser, Signal

logger = logging.getLogger(__name__)

class ChannelManager:
    """
    Main manager class that coordinates all channel parsing operations.
    Handles channel switching, parser loading, and message processing.
    """
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = config_dir
        self.channels_dir = os.path.join(config_dir, "channels")
        self.main_config_file = os.path.join(config_dir, "telegram_config.json")
        
        # Current state
        self.current_parser = None
        self.current_channel_name = None
        self.current_channel_config = None
        
        # Parser cache for performance
        self.parser_cache = {}
        
        # Ensure directories exist
        os.makedirs(self.channels_dir, exist_ok=True)
        
        logger.info("ChannelManager initialized")
    
    def initialize_from_config(self) -> bool:
        """
        Initialize the channel manager from the main telegram config.
        This loads the currently active channel and sets up its parser.
        """
        try:
            # Load main telegram config
            main_config = self._load_main_config()
            if not main_config:
                logger.error("Failed to load main telegram config")
                return False
            
            # Get current channel name
            channel_name = main_config.get('channel_name')
            if not channel_name:
                logger.error("No channel_name found in main config")
                return False
            
            # Switch to the current channel
            if channel_name:
                success = self.switch_channel(channel_name, main_config)
            else:
                return False
            if success:
                logger.info(f"✅ ChannelManager initialized with channel: {channel_name}")
                return True
            else:
                logger.error(f"Failed to initialize channel: {channel_name}")
                return False
                
        except Exception as e:
            logger.error(f"Error initializing ChannelManager: {str(e)}")
            return False
    
    def switch_channel(self, channel_name: str, main_config: Optional[Dict[str, Any]] = None) -> bool:
        """
        Switch to a different channel parser.
        
        Args:
            channel_name: Name of the channel to switch to
            main_config: Optional main config dict (will load if not provided)
            
        Returns:
            True if switch was successful, False otherwise
        """
        try:
            # Load main config if not provided
            if main_config is None:
                loaded_config = self._load_main_config()
                if not loaded_config:
                    return False
                main_config = loaded_config
            
            # Load or create channel-specific configuration
            channel_config = self._load_or_create_channel_config(channel_name)
            
            # Merge main config data into channel config
            channel_config.update({
                'api_id': main_config.get('api_id'),
                'api_hash': main_config.get('api_hash'),
                'session_name': main_config.get('session_name'),
                'channel_id': main_config.get('channel_id'),
                'channel_name': channel_name  # Ensure channel name is set
            })
            
            # Create or get parser from cache
            parser = self._get_or_create_parser(channel_name, channel_config)
            if not parser:
                logger.error(f"Failed to create parser for channel: {channel_name}")
                return False
            
            # Update current state
            self.current_parser = parser
            self.current_channel_name = channel_name
            self.current_channel_config = channel_config
            
            logger.info(f"✅ Switched to channel: {channel_name} (Parser: {parser.__class__.__name__})")
            return True
            
        except Exception as e:
            logger.error(f"Error switching to channel {channel_name}: {str(e)}")
            return False
    
    def parse_message(self, message_text: str, message_data: Optional[Dict[str, Any]] = None) -> Optional[Signal]:
        """
        Parse a message using the current channel parser.
        
        Args:
            message_text: The text content of the message
            message_data: Additional message metadata
            
        Returns:
            Signal object if valid signal found, None otherwise
        """
        if not self.current_parser:
            logger.error("No parser initialized - call initialize_from_config() first")
            return None
        
        if message_data is None:
            message_data = {}
        
        try:
            # Parse the message
            signal = self.current_parser.parse_message(message_text, message_data)
            
            if signal:
                # Validate the signal
                is_valid, validation_message = self.current_parser.validate_signal(signal)
                
                if is_valid:
                    logger.info(f"✅ Valid signal parsed: {signal.pair} {signal.direction} {signal.expiry}min")
                    return signal
                else:
                    logger.warning(f"❌ Signal validation failed: {validation_message}")
                    return None
            
            return None
            
        except Exception as e:
            logger.error(f"Error parsing message: {str(e)}")
            return None
    
    def get_current_channel_info(self) -> Dict[str, Any]:
        """Get information about the current channel and parser."""
        if not self.current_parser:
            return {"error": "No parser initialized"}
        
        info = self.current_parser.get_channel_info()
        if self.current_channel_name:
            info.update({
                "manager_status": "active",
                "config_file": self._get_channel_config_file(self.current_channel_name)
            })
        else:
            info.update({
                "manager_status": "active",
                "config_file": "unknown"
            })
        return info
    
    def list_available_channels(self) -> List[str]:
        """List all available channel configurations."""
        channels = []
        if os.path.exists(self.channels_dir):
            for file in os.listdir(self.channels_dir):
                if file.endswith('.json'):
                    # Remove .json extension and convert back to readable name
                    channel_name = file[:-5].replace('_', ' ').title()
                    channels.append(channel_name)
        return channels
    
    def reset_parser_state(self) -> None:
        """Reset the current parser's state."""
        if self.current_parser:
            self.current_parser.reset_state()
            logger.info(f"Reset parser state for {self.current_channel_name}")
    
    def get_parsing_stats(self) -> Dict[str, Any]:
        """Get parsing statistics from the current parser."""
        if not self.current_parser:
            return {"error": "No parser initialized"}
        
        stats = self.current_parser.get_parsing_stats()
        stats.update({
            "manager_info": {
                "current_channel": self.current_channel_name,
                "parser_cache_size": len(self.parser_cache),
                "available_channels": len(self.list_available_channels())
            }
        })
        return stats
    
    # Private methods
    
    def _load_main_config(self) -> Optional[Dict[str, Any]]:
        """Load the main telegram configuration."""
        try:
            if not os.path.exists(self.main_config_file):
                logger.error(f"Main config file not found: {self.main_config_file}")
                return None
            
            with open(self.main_config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            logger.debug(f"Loaded main config from: {self.main_config_file}")
            return config
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing main config: {e}")
            return None
        except Exception as e:
            logger.error(f"Error loading main config: {e}")
            return None
    
    def _get_channel_config_file(self, channel_name: str) -> str:
        """Get the config file path for a specific channel."""
        # Handle specific known channel mappings first
        channel_mappings = {
            "♨️TeeBinary  Premium": "teebinary_premium.json",
            "♨️TeeBinary Premium": "teebinary_premium.json", 
            "TeeBinary Premium": "teebinary_premium.json",
            "TeeBinary_Premium": "teebinary_premium.json",
            "🎯Signal_Sniper_Test_Channel🎯": "signal_sniper_test_channel.json",
            "Signal_Sniper_Test_Channel": "signal_sniper_test_channel.json",
            "BINARY TRADING CLUB": "binary_trading_club.json",
            "Binary Trading Club": "binary_trading_club.json"
        }
        
        # Check if we have a specific mapping
        if channel_name in channel_mappings:
            return os.path.join(self.channels_dir, channel_mappings[channel_name])
        
        # Convert channel name to filename-safe format as fallback
        safe_name = channel_name.lower().replace(' ', '_').replace('-', '_')
        safe_name = ''.join(c for c in safe_name if c.isalnum() or c == '_')
        return os.path.join(self.channels_dir, f"{safe_name}.json")
    
    def _load_or_create_channel_config(self, channel_name: str) -> Dict[str, Any]:
        """Load channel configuration or create default if not found."""
        config_file = self._get_channel_config_file(channel_name)
        
        # Try to load existing config
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                logger.debug(f"Loaded channel config: {config_file}")
                return config
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing channel config {config_file}: {e}")
                # Fall through to create default
        
        # Create default configuration
        logger.info(f"Creating default config for channel: {channel_name}")
        default_config = self._create_default_channel_config(channel_name)
        
        # Save the default config
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved default channel config: {config_file}")
        except Exception as e:
            logger.error(f"Error saving default channel config: {e}")
        
        return default_config
    
    def _create_default_channel_config(self, channel_name: str) -> Dict[str, Any]:
        """Create a default configuration for a new channel."""
        return {
            "channel_name": channel_name,
            "parser_type": "generic",
            "enabled": True,
            "parser_config": {
                "message_patterns": {
                    "single_message_format": True,
                    "signal_regex": r"🎯 ([A-Z]{3}/[A-Z]{3}) (CALL|PUT) (\\d+)M"
                },
                "signal_validation": {
                    "required_fields": ["pair", "direction", "expiry"],
                    "valid_directions": ["HIGHER", "LOWER", "CALL", "PUT"],
                    "min_expiry_minutes": 1,
                    "max_expiry_minutes": 60
                },
                "pair_formats": ["XXX/XXX"],
                "preprocessing": {
                    "remove_emojis": False,
                    "normalize_whitespace": True,
                    "convert_to_uppercase": False
                }
            },
            "metadata": {
                "created_at": datetime.now(pytz.UTC).isoformat(),
                "description": f"Auto-generated config for {channel_name}",
                "version": "1.0",
                "channel_type": "binary_options"
            }
        }
    
    def _get_or_create_parser(self, channel_name: str, channel_config: Dict[str, Any]) -> Optional[BaseChannelParser]:
        """Get parser from cache or create new one."""
        parser_type = channel_config.get('parser_type', 'generic')
        cache_key = f"{channel_name}:{parser_type}"
        
        # Check cache first
        if cache_key in self.parser_cache:
            logger.debug(f"Using cached parser for {channel_name}")
            return self.parser_cache[cache_key]
        
        # Create new parser
        parser = self._create_parser(channel_name, channel_config)
        if parser:
            self.parser_cache[cache_key] = parser
            logger.debug(f"Created and cached parser for {channel_name}")
        
        return parser
    
    def _create_parser(self, channel_name: str, channel_config: Dict[str, Any]) -> Optional[BaseChannelParser]:
        """Create a parser instance for the given channel configuration."""
        parser_type = channel_config.get('parser_type', 'generic')
        
        try:
            # Try to import specific parser
            parser_class = self._load_parser_class(channel_name, parser_type)
            if parser_class:
                return parser_class(channel_config)
            
            # Fall back to generic parser
            logger.warning(f"Using generic parser for {channel_name}")
            return self._create_generic_parser(channel_config)
            
        except Exception as e:
            logger.error(f"Error creating parser for {channel_name}: {str(e)}")
            return None
    
    def _load_parser_class(self, channel_name: str, parser_type: str):
        """Load parser class dynamically."""
        try:
            # Convert names to module/class format
            if parser_type == 'generic':
                module_name = 'generic_parser'
                class_name = 'GenericParser'
            elif parser_type == 'multi_parser':
                module_name = 'multi_parser'
                class_name = 'MultiParser'
            elif parser_type == 'teebinary_premium':
                module_name = 'teebinary_premium_parser'
                class_name = 'TeeBinaryPremiumParser'
            elif parser_type == 'binary_trading_club':
                module_name = 'binary_trading_club_parser'
                class_name = 'BinaryTradingClubParser'
            elif parser_type == 'binarypulse_bot':
                module_name = 'binarypulse_bot_parser'
                class_name = 'BinaryPulseBotParser'
            else:
                # Convert parser_type to module name
                module_name = f"{parser_type.lower()}_parser"
                class_name = f"{parser_type.title().replace('_', '')}Parser"
            
            # Try to import the parser module
            module = importlib.import_module(f"src.parsers.{module_name}")
            parser_class = getattr(module, class_name)
            
            logger.debug(f"Loaded parser class: {module_name}.{class_name}")
            return parser_class
            
        except (ImportError, AttributeError) as e:
            logger.debug(f"Could not load parser {module_name}.{class_name}: {e}")
            return None
    
    def _create_generic_parser(self, channel_config: Dict[str, Any]) -> Optional[BaseChannelParser]:
        """Create a generic parser as fallback."""
        try:
            from src.parsers.generic_parser import GenericParser
            return GenericParser(channel_config)
        except ImportError:
            logger.error("Generic parser not available")
            return None
