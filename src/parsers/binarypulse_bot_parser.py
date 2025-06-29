#!/usr/bin/env python3
"""
BinaryPulse Bot Parser for SignalSniper

This parser handles signals from @BinaryPulse_bot which provides trading
signals in the format: "📢 SIGNAL TO ENTER ✅ Couple: XXX/XXX Direction:
UP/DOWN Time expiration: X min"
"""

import re
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import pytz

from .base_parser import BaseChannelParser, Signal

logger = logging.getLogger(__name__)


class BinaryPulseBotParser(BaseChannelParser):
    """
    Parser for @BinaryPulse_bot signals.
    
    Expected signal format:
    📢 SIGNAL TO ENTER
    ✅ Couple: AUD/CAD OTC
    📉 Direction: DOWN
    🕐 Time expiration: 3 min
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # BinaryPulse bot specific patterns
        default_pattern = (
            r'📢 SIGNAL TO ENTER\s*✅ Couple: ([A-Z]{3}/[A-Z]{3})'
            r'(?: OTC)?\s*(?:📉|📈) Direction: (UP|DOWN)\s*🕐 Time expiration: '
            r'(\d+) min'
        )
        self.signal_pattern = self.message_patterns.get(
            'signal_pattern', default_pattern
        )
        
        # Direction mapping
        self.direction_mapping = {
            'UP': 'HIGHER',
            'DOWN': 'LOWER'
        }
        
        logger.info(
            f"BinaryPulse Bot Parser initialized for {self.channel_name}"
        )
    
    def parse_message(
        self, 
        message_text: str, 
        message_data: Optional[Dict[str, Any]] = None
    ) -> Optional[Signal]:
        """
        Parse BinaryPulse bot message and extract trading signal.
        
        Args:
            message_text: The message text from @BinaryPulse_bot
            message_data: Additional message metadata
            
        Returns:
            Signal object if valid signal found, None otherwise
        """
        try:
            # Preprocess the message
            processed_text = self.preprocess_message(message_text)
            
            # Check if this is a signal message
            if not self._is_signal_message(processed_text):
                return None
            
            # Extract signal components using regex
            signal_data = self._extract_signal_data(processed_text)
            if not signal_data:
                return None
            
            # Create Signal object
            signal = Signal(
                pair=signal_data['pair'],
                direction=signal_data['direction'],
                expiry=signal_data['expiry'],
                timestamp=datetime.now(pytz.UTC),
                raw_data={
                    'original_message': message_text,
                    'processed_message': processed_text,
                    'parser_type': 'binarypulse_bot',
                    'bot_handle': '@BinaryPulse_bot'
                }
            )
            
            # Validate the signal
            is_valid, validation_message = self.validate_signal(signal)
            if not is_valid:
                logger.warning(
                    f"Invalid BinaryPulse signal: {validation_message}"
                )
                return None
            
            logger.info(
                f"✅ BinaryPulse signal parsed: {signal.pair} "
                f"{signal.direction} {signal.expiry}min"
            )
            return signal
            
        except Exception as e:
            logger.error(f"Error parsing BinaryPulse message: {str(e)}")
            logger.debug(f"Message text: {message_text}")
            return None
    
    def _is_signal_message(self, text: str) -> bool:
        """
        Check if the message contains a BinaryPulse trading signal.
        
        Args:
            text: Preprocessed message text
            
        Returns:
            True if message contains signal, False otherwise
        """
        # Check for signal indicators
        signal_indicators = [
            '📢 SIGNAL TO ENTER',
            '✅ Couple:',
            'Direction:',
            'Time expiration:'
        ]
        
        return all(indicator in text for indicator in signal_indicators)
    
    def _extract_signal_data(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Extract signal data from BinaryPulse message using regex.
        
        Args:
            text: Preprocessed message text
            
        Returns:
            Dictionary with signal data or None if extraction fails
        """
        try:
            # Try the main signal pattern
            match = re.search(
                self.signal_pattern, text, 
                re.IGNORECASE | re.MULTILINE | re.DOTALL
            )
            
            if match:
                pair = match.group(1)
                direction_raw = match.group(2)
                expiry = int(match.group(3))
                
                # Convert direction to standard format
                direction = self.direction_mapping.get(direction_raw.upper(), direction_raw.upper())
                
                return {
                    'pair': pair,
                    'direction': direction,
                    'expiry': expiry
                }
            
            # If main pattern fails, try alternative extraction
            return self._extract_alternative_format(text)
            
        except Exception as e:
            logger.error(f"Error extracting signal data: {str(e)}")
            return None
    
    def _extract_alternative_format(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Alternative extraction method for different message formats.
        
        Args:
            text: Preprocessed message text
            
        Returns:
            Dictionary with signal data or None if extraction fails
        """
        try:
            # Extract components separately
            pair_match = re.search(r'Couple:\s*([A-Z]{3}/[A-Z]{3})', text, re.IGNORECASE)
            direction_match = re.search(r'Direction:\s*(UP|DOWN)', text, re.IGNORECASE)
            expiry_match = re.search(r'Time expiration:\s*(\d+)\s*min', text, re.IGNORECASE)
            
            if pair_match and direction_match and expiry_match:
                pair = pair_match.group(1)
                direction_raw = direction_match.group(1)
                expiry = int(expiry_match.group(1))
                
                # Convert direction to standard format
                direction = self.direction_mapping.get(direction_raw.upper(), direction_raw.upper())
                
                return {
                    'pair': pair,
                    'direction': direction,
                    'expiry': expiry
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error in alternative extraction: {str(e)}")
            return None
    
    def validate_signal(self, signal: Signal) -> tuple[bool, str]:
        """
        Validate BinaryPulse bot signal with specific rules.
        
        Args:
            signal: Signal object to validate
            
        Returns:
            Tuple of (is_valid: bool, validation_message: str)
        """
        # First run base validation
        is_valid, message = super().validate_signal(signal)
        if not is_valid:
            return is_valid, message
        
        # BinaryPulse specific validations
        try:
            # Check if timeframe is supported (1, 3, 5 minutes)
            supported_timeframes = self.signal_validation.get('supported_timeframes', [1, 3, 5])
            if signal.expiry not in supported_timeframes:
                return False, f"Unsupported timeframe: {signal.expiry}min. BinaryPulse supports: {supported_timeframes}"
            
            # Validate pair format (XXX/XXX)
            if not re.match(r'^[A-Z]{3}/[A-Z]{3}$', signal.pair):
                return False, f"Invalid pair format: {signal.pair}. Expected format: XXX/XXX"
            
            return True, "BinaryPulse signal is valid"
            
        except Exception as e:
            logger.error(f"Error in BinaryPulse signal validation: {str(e)}")
            return False, f"Validation error: {str(e)}"
    
    def get_parsing_stats(self) -> Dict[str, Any]:
        """Return BinaryPulse parser statistics"""
        base_stats = super().get_parsing_stats()
        base_stats.update({
            'bot_handle': '@BinaryPulse_bot',
            'supported_timeframes': [1, 3, 5],
            'signal_format': '📢 SIGNAL TO ENTER format',
            'direction_mapping': self.direction_mapping,
            'otc_preferred': self.signal_validation.get('otc_preferred', True)
        })
        return base_stats
    
    def reset_state(self) -> None:
        """Reset BinaryPulse parser state"""
        super().reset_state()
        logger.debug("BinaryPulse parser state reset")
