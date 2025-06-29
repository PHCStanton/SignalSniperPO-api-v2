#!/usr/bin/env python3
"""
TeeBinary Premium Parser

This parser handles signals from the TeeBinary Premium channel.
Signal format: {PAIR} {CALL|PUT} 5MIN (e.g., "EUR/USD CALL 5MIN")

Key characteristics:
- Single message format
- Traditional forex pairs (EUR/USD, GBP/USD, etc.)
- Fixed 5-minute duration
- CALL/PUT direction mapping to HIGHER/LOWER
- Filters out non-signal messages like "BE READY", "GO", etc.
"""

import re
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import pytz

from .base_parser import BaseChannelParser, Signal

logger = logging.getLogger(__name__)

class TeeBinaryPremiumParser(BaseChannelParser):
    """Parser for TeeBinary Premium channel signals"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # TeeBinary Premium specific patterns
        self.signal_pattern = self.parser_config.get(
            'signal_pattern', 
            r'^([A-Z]{3}/[A-Z]{3})\s+(CALL|PUT)\s+5MIN\s*$'
        )
        
        # Traditional forex pairs ONLY - NO OTC PAIRS
        self.valid_pairs = self.parser_config.get('valid_pairs', [
            'EUR/USD', 'GBP/USD', 'USD/JPY', 'USD/CHF', 'AUD/USD', 'USD/CAD',
            'NZD/USD', 'EUR/GBP', 'EUR/JPY', 'GBP/JPY', 'CHF/JPY', 'AUD/JPY',
            'CAD/JPY', 'NZD/JPY', 'EUR/CHF', 'GBP/CHF', 'AUD/CHF', 'CAD/CHF',
            'NZD/CHF', 'EUR/AUD', 'GBP/AUD', 'EUR/CAD', 'GBP/CAD', 'EUR/NZD',
            'GBP/NZD', 'AUD/CAD', 'AUD/NZD', 'CAD/CHF'
        ])
        
        # Explicitly exclude OTC pairs
        self.excluded_otc_pairs = [
            'XAU/USD', 'XAG/USD', 'BTC/USD', 'ETH/USD', 'LTC/USD', 'XRP/USD',
            'ADA/USD', 'DOT/USD', 'LINK/USD', 'BCH/USD', 'EOS/USD', 'TRX/USD'
        ]
        
        # Messages to ignore (noise filtering)
        self.ignore_patterns = self.parser_config.get('ignore_patterns', [
            r'BE\s+READY',
            r'^GO\s*$',
            r'WAIT',
            r'PREPARE',
            r'GET\s+READY',
            r'ATTENTION',
            r'ALERT',
            r'NOTICE',
            r'UPDATE',
            r'NEWS',
            r'MARKET\s+CLOSED',
            r'TRADING\s+CLOSED'
        ])
        
        logger.info(f"TeeBinary Premium parser initialized with {len(self.valid_pairs)} valid pairs")
    
    def parse_message(self, message_text: str, message_data: Optional[Dict[str, Any]] = None) -> Optional[Signal]:
        """
        Parse TeeBinary Premium signal message.
        
        Expected format: "EUR/USD CALL 5MIN"
        
        Args:
            message_text: The message text to parse
            message_data: Additional message metadata
            
        Returns:
            Signal object if valid signal found, None otherwise
        """
        try:
            # Preprocess the message
            processed_text = self.preprocess_message(message_text)
            
            # Check if message should be ignored
            if self._should_ignore_message(processed_text):
                logger.debug(f"Ignoring non-signal message: {processed_text[:50]}...")
                return None
            
            # Try to match the signal pattern
            match = re.match(self.signal_pattern, processed_text.strip(), re.IGNORECASE)
            
            if not match:
                logger.debug(f"Message doesn't match TeeBinary Premium pattern: {processed_text}")
                return None
            
            # Extract signal components
            pair = match.group(1).upper()
            direction_raw = match.group(2).upper()
            
            # Validate pair
            if pair not in self.valid_pairs:
                logger.warning(f"Invalid pair for TeeBinary Premium: {pair}")
                return None
            
            # Map direction: CALL -> HIGHER, PUT -> LOWER
            direction_mapping = {
                'CALL': 'HIGHER',
                'PUT': 'LOWER'
            }
            
            direction = direction_mapping.get(direction_raw)
            if not direction:
                logger.warning(f"Invalid direction for TeeBinary Premium: {direction_raw}")
                return None
            
            # Fixed 5-minute expiry for TeeBinary Premium
            expiry = 5
            
            # Create signal object
            signal = Signal(
                pair=pair,
                direction=direction,
                expiry=expiry,
                timestamp=datetime.now(pytz.UTC),
                raw_data={
                    'original_message': message_text,
                    'processed_message': processed_text,
                    'channel': 'TeeBinary_Premium',
                    'direction_raw': direction_raw,
                    'parser': 'TeeBinaryPremiumParser'
                }
            )
            
            # Validate the signal
            is_valid, validation_msg = self.validate_signal(signal)
            if not is_valid:
                logger.warning(f"Signal validation failed: {validation_msg}")
                return None
            
            logger.info(f"Successfully parsed TeeBinary Premium signal: {pair} {direction} {expiry}MIN")
            return signal
            
        except Exception as e:
            logger.error(f"Error parsing TeeBinary Premium message: {str(e)}")
            logger.debug(f"Message content: {message_text}")
            return None
    
    def _should_ignore_message(self, message_text: str) -> bool:
        """
        Check if message should be ignored based on ignore patterns.
        
        Args:
            message_text: The message text to check
            
        Returns:
            True if message should be ignored, False otherwise
        """
        for pattern in self.ignore_patterns:
            if re.search(pattern, message_text, re.IGNORECASE):
                return True
        return False
    
    def validate_signal(self, signal: Signal) -> tuple[bool, str]:
        """
        Validate TeeBinary Premium specific signal requirements.
        
        Args:
            signal: The Signal object to validate
            
        Returns:
            Tuple of (is_valid: bool, validation_message: str)
        """
        # First run base validation
        is_valid, msg = super().validate_signal(signal)
        if not is_valid:
            return is_valid, msg
        
        # TeeBinary Premium specific validations
        
        # Check if pair is in valid traditional forex pairs
        if signal.pair not in self.valid_pairs:
            return False, f"Invalid pair for TeeBinary Premium: {signal.pair}. Must be traditional forex pair."
        
        # Check if expiry is exactly 5 minutes
        if signal.expiry != 5:
            return False, f"Invalid expiry for TeeBinary Premium: {signal.expiry}. Must be exactly 5 minutes."
        
        # Check direction is valid
        if signal.direction not in ['HIGHER', 'LOWER']:
            return False, f"Invalid direction for TeeBinary Premium: {signal.direction}. Must be HIGHER or LOWER."
        
        return True, "TeeBinary Premium signal is valid"
    
    def get_parsing_stats(self) -> Dict[str, Any]:
        """Return TeeBinary Premium specific parsing statistics"""
        base_stats = super().get_parsing_stats()
        base_stats.update({
            'signal_format': 'single_message',
            'typical_duration': '5_minutes',
            'pair_type': 'traditional_forex',
            'direction_format': 'CALL/PUT',
            'valid_pairs_count': len(self.valid_pairs),
            'ignore_patterns_count': len(self.ignore_patterns)
        })
        return base_stats
    
    def get_channel_info(self) -> Dict[str, Any]:
        """Return TeeBinary Premium channel information"""
        base_info = super().get_channel_info()
        base_info.update({
            'signal_format': 'PAIR CALL/PUT 5MIN',
            'example_signal': 'EUR/USD CALL 5MIN',
            'supported_pairs': len(self.valid_pairs),
            'fixed_duration': '5 minutes'
        })
        return base_info
