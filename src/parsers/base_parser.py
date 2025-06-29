#!/usr/bin/env python3
"""
Base Parser Class for Modular Channel Architecture

This module provides the abstract base class that all channel-specific parsers
must inherit from. It defines the standard interface and common functionality.
"""

import re
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from datetime import datetime
import pytz

logger = logging.getLogger(__name__)

@dataclass
class Signal:
    """Standard signal format that all parsers should return"""
    pair: str
    direction: str  # 'HIGHER' or 'LOWER'
    expiry: int  # in minutes
    timer: Optional[str] = None
    confidence: Optional[float] = None
    timestamp: Optional[datetime] = None
    raw_data: Optional[Dict[str, Any]] = None
    signal_id: Optional[str] = None
    session_id: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(pytz.UTC)
        if self.raw_data is None:
            self.raw_data = {}

class BaseChannelParser(ABC):
    """
    Abstract base class for all channel parsers.
    Each channel parser should inherit from this class and implement the required methods.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.channel_name = config.get('channel_name', 'Unknown')
        self.channel_id = config.get('channel_id')
        self.parser_config = config.get('parser_config', {})
        self.enabled = config.get('enabled', True)
        
        # Common configuration
        self.preprocessing = self.parser_config.get('preprocessing', {})
        self.signal_validation = self.parser_config.get('signal_validation', {})
        self.message_patterns = self.parser_config.get('message_patterns', {})
        
        # State for multi-message signals
        self.last_first_message = None
        self.last_first_message_time = None
        
        logger.info(f"Initialized {self.__class__.__name__} for channel: {self.channel_name}")
    
    @abstractmethod
    def parse_message(self, message_text: str, message_data: Optional[Dict[str, Any]] = None) -> Optional[Signal]:
        """
        Parse a single message and return a Signal object if valid.
        
        Args:
            message_text: The text content of the message
            message_data: Additional message metadata (timestamp, sender, etc.)
            
        Returns:
            Signal object if message contains valid trading signal, None otherwise
        """
        pass
    
    def validate_signal(self, signal: Signal) -> Tuple[bool, str]:
        """
        Validate if the parsed signal meets the channel's criteria.
        
        Args:
            signal: The Signal object to validate
            
        Returns:
            Tuple of (is_valid: bool, validation_message: str)
        """
        try:
            validation_config = self.signal_validation
            
            # Check required fields
            required_fields = validation_config.get('required_fields', ['pair', 'direction', 'expiry'])
            for field in required_fields:
                if not hasattr(signal, field) or getattr(signal, field) is None:
                    return False, f"Missing required field: {field}"
            
            # Validate direction
            valid_directions = validation_config.get('valid_directions', ['HIGHER', 'LOWER'])
            if signal.direction not in valid_directions:
                return False, f"Invalid direction: {signal.direction}. Must be one of {valid_directions}"
            
            # Validate expiry range
            min_expiry = validation_config.get('min_expiry_minutes', 1)
            max_expiry = validation_config.get('max_expiry_minutes', 60)
            if not (min_expiry <= signal.expiry <= max_expiry):
                return False, f"Invalid expiry: {signal.expiry}. Must be between {min_expiry} and {max_expiry} minutes"
            
            # Validate pair format if specified
            valid_pairs = validation_config.get('valid_pairs', [])
            if valid_pairs and signal.pair not in valid_pairs:
                return False, f"Invalid pair: {signal.pair}. Must be one of {valid_pairs}"
            
            return True, "Signal is valid"
            
        except Exception as e:
            logger.error(f"Error validating signal: {str(e)}")
            return False, f"Validation error: {str(e)}"
    
    def preprocess_message(self, message_text: str) -> str:
        """
        Apply preprocessing to message text based on configuration.
        
        Args:
            message_text: Raw message text
            
        Returns:
            Preprocessed message text
        """
        text = message_text
        
        # Remove emojis if configured
        if self.preprocessing.get('remove_emojis', False):
            text = re.sub(r'[^\x00-\x7F]+', '', text)
        
        # Normalize whitespace if configured
        if self.preprocessing.get('normalize_whitespace', True):
            text = re.sub(r'\s+', ' ', text).strip()
        
        # Convert to uppercase if configured
        if self.preprocessing.get('convert_to_uppercase', False):
            text = text.upper()
        
        return text
    
    def extract_with_regex(self, text: str, pattern: str, group: int = 1) -> Optional[str]:
        """
        Extract text using regex pattern.
        
        Args:
            text: Text to search in
            pattern: Regex pattern
            group: Group number to extract (default: 1)
            
        Returns:
            Extracted text or None if not found
        """
        try:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match and len(match.groups()) >= group:
                return match.group(group)
            return None
        except Exception as e:
            logger.error(f"Error extracting with regex '{pattern}': {str(e)}")
            return None
    
    def get_channel_info(self) -> Dict[str, Any]:
        """Return basic channel information"""
        return {
            'name': self.channel_name,
            'id': self.channel_id,
            'parser_type': self.__class__.__name__,
            'enabled': self.enabled,
            'config_version': self.config.get('metadata', {}).get('version', '1.0')
        }
    
    def get_parsing_stats(self) -> Dict[str, Any]:
        """Return parsing statistics (to be overridden by subclasses if needed)"""
        return {
            'parser_name': self.__class__.__name__,
            'channel_name': self.channel_name,
            'enabled': self.enabled
        }
    
    def reset_state(self) -> None:
        """Reset parser state (useful for multi-message parsers)"""
        self.last_first_message = None
        self.last_first_message_time = None
        logger.debug(f"Reset parser state for {self.channel_name}")
