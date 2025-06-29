#!/usr/bin/env python3
"""
Generic Parser for Modular Channel Architecture

This parser provides a fallback implementation that can handle
basic signal formats. It's used when no specific parser is available
for a channel or as a starting point for new channels.
"""

import re
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import pytz

from .base_parser import BaseChannelParser, Signal

logger = logging.getLogger(__name__)

class GenericParser(BaseChannelParser):
    """
    Generic parser that can handle common signal formats.
    This serves as a fallback when no specific parser is available.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # Common signal patterns
        self.single_message_patterns = [
            # Pattern 1: 🎯 EUR/USD CALL 5M
            r"🎯\s*([A-Z]{3}/[A-Z]{3})\s+(CALL|PUT|HIGHER|LOWER)\s+(\d+)M",
            # Pattern 2: Currency pair EUR/USD HIGHER Trade time: 5 MIN
            r"Currency pair\s+([A-Z]{3}/[A-Z]{3}).*?(HIGHER|LOWER).*?Trade time:\s*(\d+)\s*MIN",
            # Pattern 3: EUR/USD ⬆️ 5 minutes
            r"([A-Z]{3}/[A-Z]{3})\s*[⬆️⬇️]\s*(\d+)\s*minutes?",
            # Pattern 4: Simple format: EURUSD CALL 5
            r"([A-Z]{6})\s+(CALL|PUT|HIGHER|LOWER)\s+(\d+)"
        ]
        
        # Timer patterns
        self.timer_patterns = [
            r"SET THE TIMER TO\s*(\d{2}:\d{2}:\d{2})",
            r"Timer:\s*(\d{2}:\d{2}:\d{2})",
            r"⏰\s*(\d{2}:\d{2}:\d{2})"
        ]
        
        logger.info(f"GenericParser initialized for channel: {self.channel_name}")
    
    def parse_message(self, message_text: str, message_data: Optional[Dict[str, Any]] = None) -> Optional[Signal]:
        """
        Parse a message using generic patterns.
        
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
            
            # Try single message format first
            signal = self._parse_single_message(text)
            if signal:
                return signal
            
            # Try multi-message format
            signal = self._parse_multi_message(text, message_data)
            if signal:
                return signal
            
            return None
            
        except Exception as e:
            logger.error(f"Error parsing message in GenericParser: {str(e)}")
            return None
    
    def _parse_single_message(self, text: str) -> Optional[Signal]:
        """Parse a single message that contains complete signal information."""
        for pattern in self.single_message_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                try:
                    groups = match.groups()
                    
                    # Extract basic components
                    pair = groups[0]
                    direction = groups[1].upper()
                    
                    # Handle different group structures
                    if len(groups) >= 3:
                        expiry = int(groups[2])
                    else:
                        # Try to find expiry in the text
                        expiry_match = re.search(r"(\d+)\s*(?:M|MIN|minutes?)", text, re.IGNORECASE)
                        if expiry_match:
                            expiry = int(expiry_match.group(1))
                        else:
                            expiry = 5  # Default to 5 minutes
                    
                    # Normalize pair format
                    pair = self._normalize_pair(pair)
                    
                    # Normalize direction
                    direction = self._normalize_direction(direction)
                    
                    # Extract timer if present
                    timer = self._extract_timer(text)
                    
                    # Create signal
                    signal = Signal(
                        pair=pair,
                        direction=direction,
                        expiry=expiry,
                        timer=timer,
                        timestamp=datetime.now(pytz.UTC),
                        raw_data={"original_text": text, "pattern_used": pattern}
                    )
                    
                    logger.info(f"GenericParser: Parsed single message signal: {pair} {direction} {expiry}min")
                    return signal
                    
                except (ValueError, IndexError) as e:
                    logger.debug(f"Error processing match from pattern {pattern}: {str(e)}")
                    continue
        
        return None
    
    def _parse_multi_message(self, text: str, message_data: Dict[str, Any]) -> Optional[Signal]:
        """Parse multi-message format (like Binary Trading Club)."""
        current_time = datetime.now(pytz.UTC)
        
        # Check if this looks like a first message
        first_message_match = re.search(r"Trading Pair:\s*([A-Z]{3}/[A-Z]{3})", text, re.IGNORECASE)
        if first_message_match:
            self.last_first_message = first_message_match.group(1)
            self.last_first_message_time = current_time
            logger.debug(f"GenericParser: Stored first message pair: {self.last_first_message}")
            return None
        
        # Check if this looks like a second message and we have a first message
        if self.last_first_message and self.last_first_message_time:
            # Check time window (default 60 seconds)
            time_diff = (current_time - self.last_first_message_time).total_seconds()
            max_window = self.parser_config.get('pair_match_window', 60)
            
            if time_diff <= max_window:
                # Try to extract signal components
                timer = self._extract_timer(text)
                direction = self._extract_direction(text)
                expiry = self._extract_expiry(text)
                
                if direction and expiry:
                    signal = Signal(
                        pair=self.last_first_message,
                        direction=direction,
                        expiry=expiry,
                        timer=timer,
                        timestamp=current_time,
                        raw_data={"original_text": text, "multi_message": True}
                    )
                    
                    # Reset state
                    self.last_first_message = None
                    self.last_first_message_time = None
                    
                    logger.info(f"GenericParser: Parsed multi-message signal: {signal.pair} {signal.direction} {signal.expiry}min")
                    return signal
            else:
                # Reset state if too much time has passed
                self.last_first_message = None
                self.last_first_message_time = None
        
        return None
    
    def _normalize_pair(self, pair: str) -> str:
        """Normalize currency pair format."""
        # Remove any non-alphanumeric characters except /
        pair = re.sub(r'[^A-Za-z/]', '', pair).upper()
        
        # Convert EURUSD to EUR/USD format
        if len(pair) == 6 and '/' not in pair:
            pair = f"{pair[:3]}/{pair[3:]}"
        
        return pair
    
    def _normalize_direction(self, direction: str) -> str:
        """Normalize direction to HIGHER/LOWER format."""
        direction = direction.upper()
        
        # Convert CALL/PUT to HIGHER/LOWER
        if direction in ['CALL', 'UP', '⬆️', 'BUY']:
            return 'HIGHER'
        elif direction in ['PUT', 'DOWN', '⬇️', 'SELL']:
            return 'LOWER'
        
        return direction
    
    def _extract_timer(self, text: str) -> Optional[str]:
        """Extract timer from text."""
        for pattern in self.timer_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    
    def _extract_direction(self, text: str) -> Optional[str]:
        """Extract direction from text."""
        direction_patterns = [
            r"\b(HIGHER|LOWER|CALL|PUT|UP|DOWN)\b",
            r"[⬆️⬇️]"
        ]
        
        for pattern in direction_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                direction = match.group(1) if match.group(1) else match.group(0)
                return self._normalize_direction(direction)
        
        return None
    
    def _extract_expiry(self, text: str) -> Optional[int]:
        """Extract expiry time from text."""
        expiry_patterns = [
            r"Trade time:\s*(\d+)\s*MIN",
            r"(\d+)\s*(?:M|MIN|minutes?)",
            r"Expiry:\s*(\d+)"
        ]
        
        for pattern in expiry_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    continue
        
        return None
    
    def get_parsing_stats(self) -> Dict[str, Any]:
        """Return parsing statistics for the generic parser."""
        stats = super().get_parsing_stats()
        stats.update({
            "parser_type": "generic",
            "supported_patterns": len(self.single_message_patterns),
            "multi_message_support": True,
            "last_first_message": self.last_first_message is not None
        })
        return stats
