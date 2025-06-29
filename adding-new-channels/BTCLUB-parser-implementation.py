#!/usr/bin/env python3
"""
Binary Trading Club Parser

This parser handles the specific message format used by the Binary Trading Club channel.
It supports multi-message signals where information is spread across multiple messages.
"""

import re
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from .base_parser import BaseChannelParser, Signal

logger = logging.getLogger(__name__)

class BinaryTradingClubParser(BaseChannelParser):
    """
    Parser specifically designed for Binary Trading Club channel.
    
    This channel typically sends signals in multiple messages:
    1. First message: "Trading Pair: EUR/USD (OTC)"
    2. Second message: Contains timer, direction, and expiry info
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # Get parsing configuration
        parsing_config = self.parser_config.get('parsing_logic', {})
        self.multi_message_signal = parsing_config.get('multi_message_signal', True)
        self.pair_match_window = parsing_config.get('pair_match_window', 60)
        self.require_timer = parsing_config.get('require_timer', True)
        
        # Message patterns from config
        patterns = self.parser_config.get('message_patterns', {})
        self.first_message_regex = patterns.get('first_message_regex', 
            r"Trading Pair: (\w+/\w+)(?:\s*\(OTC\))?")
        self.second_message_patterns = patterns.get('second_message_regex', {})
        
        # Compile regex patterns
        self.first_pattern = re.compile(self.first_message_regex, re.IGNORECASE | re.MULTILINE)
        self.timer_pattern = re.compile(
            self.second_message_patterns.get('timer', r"SET THE TIMER TO (\d{2}:\d{2}:\d{2})"),
            re.IGNORECASE | re.MULTILINE
        )
        self.pair_pattern = re.compile(
            self.second_message_patterns.get('pair', r"Currency pair (\w+/\w+)"),
            re.IGNORECASE | re.MULTILINE
        )
        self.direction_pattern = re.compile(
            self.second_message_patterns.get('direction', r"(HIGHER|LOWER)"),
            re.IGNORECASE | re.MULTILINE
        )
        self.expiry_pattern = re.compile(
            self.second_message_patterns.get('expiry', r"Trade time: (\d+) MIN"),
            re.IGNORECASE | re.MULTILINE
        )
        
        # Store for multi-message parsing
        self.pending_pairs = {}  # Store pairs waiting for completion
        
    def preprocess_message(self, message_text: str) -> str:
        """Preprocess message text according to configuration"""
        preprocessing = self.parser_config.get('preprocessing', {})
        
        if preprocessing.get('normalize_whitespace', True):
            # Replace multiple whitespaces with single space
            message_text = re.sub(r'\s+', ' ', message_text.strip())
        
        if preprocessing.get('remove_emojis', True):
            # Remove emoji characters (basic approach)
            message_text = re.sub(r'[^\w\s:/().-]', '', message_text)
        
        if preprocessing.get('convert_to_uppercase', False):
            message_text = message_text.upper()
            
        return message_text
    
    def parse_message(self, message_text: str, message_data: Dict[str, Any]) -> Optional[Signal]:
        """
        Parse a message and return a Signal if valid.
        
        This handles both single-message and multi-message signals.
        """
        # Preprocess the message
        processed_text = self.preprocess_message(message_text)
        
        # Try to parse as complete signal first
        complete_signal = self._parse_complete_signal(processed_text, message_data)
        if complete_signal:
            return complete_signal
        
        # If multi-message parsing is enabled, try that
        if self.multi_message_signal:
            return self._parse_multi_message_signal(processed_text, message_data)
        
        return None
    
    def _parse_complete_signal(self, message_text: str, message_data: Dict[str, Any]) -> Optional[Signal]:
        """Try to parse a complete signal from a single message"""
        # Extract all components
        pair_match = self.first_pattern.search(message_text) or self.pair_pattern.search(message_text)
        timer_match = self.timer_pattern.search(message_text)
        direction_match = self.direction_pattern.search(message_text)
        expiry_match = self.expiry_pattern.search(message_text)
        
        if not pair_match or not direction_match or not expiry_match:
            return None
        
        # Extract values
        pair = pair_match.group(1).upper()
        direction = direction_match.group(1).upper()
        expiry_minutes = int(expiry_match.group(1))
        timer = timer_match.group(1) if timer_match else None
        
        # Validate timer requirement
        if self.require_timer and not timer:
            logger.debug("Timer required but not found in message")
            return None
        
        # Create signal
        signal = Signal(
            pair=pair,
            direction=direction,
            expiry_minutes=expiry_minutes,
            timer=timer,
            timestamp=datetime.now(),
            raw_data={
                'message_text': message_text,
                'message_data': message_data,
                'parsing_method': 'complete_signal'
            }
        )
        
        return signal
    
    def _parse_multi_message_signal(self, message_text: str, message_data: Dict[str, Any]) -> Optional[Signal]:
        """Handle multi-message signal parsing"""
        timestamp = message_data.get('timestamp', datetime.now())
        
        # Check if this is a "Trading Pair" message
        pair_match = self.first_pattern.search(message_text)
        if pair_match:
            pair = pair_match.group(1).upper()
            self.pending_pairs[pair] = {
                'pair': pair,
                'timestamp': timestamp,
                'first_message': message_text
            }
            logger.debug(f"Stored pending pair: {pair}")
            return None
        
        # Check if this message contains signal information
        timer_match = self.timer_pattern.search(message_text)
        direction_match = self.direction_pattern.search(message_text)
        expiry_match = self.expiry_pattern.search(message_text)
        pair_match = self.pair_pattern.search(message_text)
        
        if not (direction_match and expiry_match):
            return None
        
        # Try to find matching pair from recent messages
        target_pair = None
        
        # If pair is mentioned in this message, use it
        if pair_match:
            target_pair = pair_match.group(1).upper()
        else:
            # Find the most recent pending pair within the time window
            cutoff_time = timestamp - timedelta(seconds=self.pair_match_window)
            for pair, pair_data in self.pending_pairs.items():
                if pair_data['timestamp'] >= cutoff_time:
                    target_pair = pair
                    break
        
        if not target_pair:
            logger.debug("No matching pair found for signal information")
            return None
        
        # Extract signal information
        direction = direction_match.group(1).upper()
        expiry_minutes = int(expiry_match.group(1))
        timer = timer_match.group(1) if timer_match else None
        
        # Validate timer requirement
        if self.require_timer and not timer:
            logger.debug("Timer required but not found in signal message")
            return None
        
        # Create signal
        signal = Signal(
            pair=target_pair,
            direction=direction,
            expiry_minutes=expiry_minutes,
            timer=timer,
            timestamp=timestamp,
            raw_data={
                'message_text': message_text,
                'message_data': message_data,
                'parsing_method': 'multi_message',
                'first_message': self.pending_pairs.get(target_pair, {}).get('first_message', '')
            }
        )
        
        # Clean up old pending pairs
        self._cleanup_old_pending_pairs(timestamp)
        
        # Remove the used pair
        if target_pair in self.pending_pairs:
            del self.pending_pairs[target_pair]
        
        return signal
    
    def _cleanup_old_pending_pairs(self, current_timestamp: datetime):
        """Remove old pending pairs that are outside the match window"""
        cutoff_time = current_timestamp - timedelta(seconds=self.pair_match_window * 2)
        pairs_to_remove = [
            pair for pair, data in self.pending_pairs.items()
            if data['timestamp'] < cutoff_time
        ]
        
        for pair in pairs_to_remove:
            del self.pending_pairs[pair]
            logger.debug(f"Cleaned up old pending pair: {pair}")
    
    def validate_signal(self, signal: Signal) -> bool:
        """Validate the parsed signal against channel-specific rules"""
        validation_config = self.parser_config.get('signal_validation', {})
        
        # Check required fields
        required_fields = validation_config.get('required_fields', [])
        for field in required_fields:
            if not getattr(signal, field, None):
                logger.debug(f"Signal missing required field: {field}")
                return False
        
        # Check direction
        valid_directions = validation_config.get('valid_directions', ['HIGHER', 'LOWER'])
        if signal.direction not in valid_directions:
            logger.debug(f"Invalid direction: {signal.direction}")
            return False
        
        # Check expiry time bounds
        min_expiry = validation_config.get('min_expiry_minutes', 1)
        max_expiry = validation_config.get('max_expiry_minutes', 60)
        if not (min_expiry <= signal.expiry_minutes <= max_expiry):
            logger.debug(f"Expiry time out of bounds: {signal.expiry_minutes}")
            return False
        
        # Check valid pairs if configured
        valid_pairs = validation_config.get('valid_pairs', [])
        if valid_pairs and signal.pair not in valid_pairs:
            logger.debug(f"Invalid trading pair: {signal.pair}")
            return False
        
        # Validate pair format
        pair_formats = self.parser_config.get('pair_formats', ['XXX/XXX'])
        if not self._validate_pair_format(signal.pair, pair_formats):
            logger.debug(f"Invalid pair format: {signal.pair}")
            return False
        
        return True
    
    def _validate_pair_format(self, pair: str, valid_formats: list) -> bool:
        """Validate trading pair format"""
        for format_pattern in valid_formats:
            if format_pattern == 'XXX/XXX':
                if re.match(r'^[A-Z]{3}/[A-Z]{3}$', pair):
                    return True
            elif format_pattern == 'XXXYYY':
                if re.match(r'^[A-Z]{6}$', pair):
                    return True
        return False
    
    def get_parser_stats(self) -> Dict[str, Any]:
        """Get statistics about the parser's performance"""
        return {
            'pending_pairs_count': len(self.pending_pairs),
            'pending_pairs': list(self.pending_pairs.keys()),
            'multi_message_enabled': self.multi_message_signal,
            'pair_match_window': self.pair_match_window
        }