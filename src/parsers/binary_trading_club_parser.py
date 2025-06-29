#!/usr/bin/env python3
"""
Binary Trading Club Parser for Modular Channel Architecture

This parser handles the specific message format used by the Binary Trading Club channel.
It supports the two-message format where the first message contains the trading pair
and the second message contains the direction, timer, and expiry information.
"""

import re
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import pytz

from .base_parser import BaseChannelParser, Signal

logger = logging.getLogger(__name__)

class BinaryTradingClubParser(BaseChannelParser):
    """
    Parser specifically designed for Binary Trading Club channel format.
    
    Expected format:
    Message 1: "Trading Pair: EUR/USD"
    Message 2: "HIGHER\nSET THE TIMER TO 20:59:30\nTrade time: 1 MIN"
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # Binary Trading Club specific patterns
        self.first_message_pattern = r"Trading Pair:\s*([A-Z]{3}/[A-Z]{3})"
        self.timer_pattern = r"SET THE TIMER TO\s*(\d{2}:\d{2}:\d{2})"
        self.direction_pattern = r"\b(HIGHER|LOWER)\b"
        self.expiry_pattern = r"Trade time:\s*(\d+)\s*MIN"
        
        # Configuration for pair matching window
        self.pair_match_window = self.parser_config.get('pair_match_window', 60)  # seconds
        
        logger.info(f"BinaryTradingClubParser initialized for channel: {self.channel_name}")
    
    def parse_message(self, message_text: str, message_data: Optional[Dict[str, Any]] = None) -> Optional[Signal]:
        """
        Parse Binary Trading Club message format.
        
        Args:
            message_text: The text content of the message
            message_data: Additional message metadata
            
        Returns:
            Signal object if valid signal found, None otherwise
        """
        if message_data is None:
            message_data = {}
        
        try:
            # Preprocess the message
            text = self.preprocess_message(message_text)
            current_time = datetime.now(pytz.UTC)
            
            # Check if this is a first message (Trading Pair)
            first_match = re.search(self.first_message_pattern, text, re.IGNORECASE)
            if first_match:
                self.last_first_message = first_match.group(1)
                self.last_first_message_time = current_time
                logger.debug(f"BTC Parser: Stored trading pair: {self.last_first_message}")
                return None
            
            # Check if this is a second message and we have a stored first message
            if self.last_first_message and self.last_first_message_time:
                # Check if we're within the time window
                time_diff = (current_time - self.last_first_message_time).total_seconds()
                
                if time_diff <= self.pair_match_window:
                    # Try to parse the second message
                    signal = self._parse_second_message(text, current_time)
                    if signal:
                        # Reset state after successful parsing
                        self.last_first_message = None
                        self.last_first_message_time = None
                        return signal
                else:
                    # Reset state if too much time has passed
                    logger.debug(f"BTC Parser: Time window exceeded ({time_diff}s), resetting state")
                    self.last_first_message = None
                    self.last_first_message_time = None
            
            return None
            
        except Exception as e:
            logger.error(f"Error parsing message in BinaryTradingClubParser: {str(e)}")
            return None
    
    def _parse_second_message(self, text: str, timestamp: datetime) -> Optional[Signal]:
        """
        Parse the second message that contains direction, timer, and expiry.
        
        Args:
            text: Preprocessed message text
            timestamp: Current timestamp
            
        Returns:
            Signal object if parsing successful, None otherwise
        """
        try:
            # Extract direction
            direction_match = re.search(self.direction_pattern, text, re.IGNORECASE)
            if not direction_match:
                logger.debug("BTC Parser: No direction found in second message")
                return None
            
            direction = direction_match.group(1).upper()
            
            # Extract timer
            timer_match = re.search(self.timer_pattern, text)
            timer = timer_match.group(1) if timer_match else None
            
            # Extract expiry
            expiry_match = re.search(self.expiry_pattern, text, re.IGNORECASE)
            if not expiry_match:
                logger.debug("BTC Parser: No expiry found in second message")
                return None
            
            expiry = int(expiry_match.group(1))
            
            # Create signal (ensure we have a valid pair)
            if not self.last_first_message:
                logger.error("BTC Parser: No stored pair for signal creation")
                return None
                
            signal = Signal(
                pair=self.last_first_message,
                direction=direction,
                expiry=expiry,
                timer=timer,
                timestamp=timestamp,
                raw_data={
                    "original_text": text,
                    "parser_type": "binary_trading_club",
                    "multi_message": True
                }
            )
            
            logger.info(f"BTC Parser: Successfully parsed signal: {signal.pair} {signal.direction} {signal.expiry}min")
            return signal
            
        except (ValueError, AttributeError) as e:
            logger.error(f"Error parsing second message: {str(e)}")
            return None
    
    def validate_signal(self, signal: Signal) -> tuple[bool, str]:
        """
        Validate Binary Trading Club specific signal requirements.
        
        Args:
            signal: The Signal object to validate
            
        Returns:
            Tuple of (is_valid: bool, validation_message: str)
        """
        # First run base validation
        is_valid, message = super().validate_signal(signal)
        if not is_valid:
            return is_valid, message
        
        # Binary Trading Club specific validations
        try:
            # Check pair format (should be XXX/XXX)
            if not re.match(r'^[A-Z]{3}/[A-Z]{3}$', signal.pair):
                return False, f"Invalid pair format for BTC: {signal.pair}. Expected XXX/XXX format"
            
            # Check direction (should be HIGHER or LOWER)
            if signal.direction not in ['HIGHER', 'LOWER']:
                return False, f"Invalid direction for BTC: {signal.direction}. Must be HIGHER or LOWER"
            
            # Check expiry range (typically 1-5 minutes for BTC)
            btc_min_expiry = self.signal_validation.get('btc_min_expiry_minutes', 1)
            btc_max_expiry = self.signal_validation.get('btc_max_expiry_minutes', 5)
            
            if not (btc_min_expiry <= signal.expiry <= btc_max_expiry):
                return False, f"Invalid expiry for BTC: {signal.expiry}. Expected {btc_min_expiry}-{btc_max_expiry} minutes"
            
            # Check timer format if present
            if signal.timer and not re.match(r'^\d{2}:\d{2}:\d{2}$', signal.timer):
                return False, f"Invalid timer format for BTC: {signal.timer}. Expected HH:MM:SS"
            
            return True, "Signal is valid for Binary Trading Club"
            
        except Exception as e:
            logger.error(f"Error in BTC signal validation: {str(e)}")
            return False, f"Validation error: {str(e)}"
    
    def get_parsing_stats(self) -> Dict[str, Any]:
        """Return parsing statistics specific to Binary Trading Club."""
        stats = super().get_parsing_stats()
        stats.update({
            "parser_type": "binary_trading_club",
            "multi_message_format": True,
            "pair_match_window_seconds": self.pair_match_window,
            "has_pending_first_message": self.last_first_message is not None,
            "pending_pair": self.last_first_message,
            "supported_directions": ["HIGHER", "LOWER"],
            "typical_expiry_range": "1-5 minutes"
        })
        return stats
    
    def reset_state(self) -> None:
        """Reset parser state for Binary Trading Club."""
        super().reset_state()
        logger.debug("BTC Parser: State reset completed")
