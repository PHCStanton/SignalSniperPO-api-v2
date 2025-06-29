#!/usr/bin/env python3
"""
Multi Parser for Test Channel

This parser supports multiple signal formats for comprehensive testing.
It tries different parsers in priority order to handle various signal formats.

Supported formats:
- TeeBinary Premium: PAIR CALL/PUT 5MIN
- Binary Trading Club: 2-message format
- Generic: 🎯 PAIR DIRECTION DURATION
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import pytz

from .base_parser import BaseChannelParser, Signal
from .teebinary_premium_parser import TeeBinaryPremiumParser
from .binary_trading_club_parser import BinaryTradingClubParser
from .generic_parser import GenericParser

logger = logging.getLogger(__name__)

class MultiParser(BaseChannelParser):
    """Parser that supports multiple signal formats for testing"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # Get parser priority from config
        self.parser_priority = self.parser_config.get('parser_priority', [
            'teebinary_premium',
            'binary_trading_club', 
            'generic'
        ])
        
        # Initialize sub-parsers
        self.sub_parsers = {}
        self._initialize_sub_parsers(config)
        
        # Statistics tracking
        self.parsing_attempts = 0
        self.successful_parses = 0
        self.parser_usage_stats = {parser: 0 for parser in self.parser_priority}
        
        logger.info(f"MultiParser initialized with {len(self.sub_parsers)} sub-parsers")
    
    def _initialize_sub_parsers(self, config: Dict[str, Any]) -> None:
        """Initialize all sub-parsers with appropriate configurations"""
        try:
            # TeeBinary Premium parser
            if 'teebinary_premium' in self.parser_priority:
                teebinary_config = self._create_teebinary_config(config)
                self.sub_parsers['teebinary_premium'] = TeeBinaryPremiumParser(teebinary_config)
                logger.debug("Initialized TeeBinary Premium sub-parser")
            
            # Binary Trading Club parser
            if 'binary_trading_club' in self.parser_priority:
                btc_config = self._create_btc_config(config)
                self.sub_parsers['binary_trading_club'] = BinaryTradingClubParser(btc_config)
                logger.debug("Initialized Binary Trading Club sub-parser")
            
            # Generic parser
            if 'generic' in self.parser_priority:
                generic_config = self._create_generic_config(config)
                self.sub_parsers['generic'] = GenericParser(generic_config)
                logger.debug("Initialized Generic sub-parser")
                
        except Exception as e:
            logger.error(f"Error initializing sub-parsers: {str(e)}")
    
    def _create_teebinary_config(self, base_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create configuration for TeeBinary Premium parser"""
        return {
            'channel_name': base_config.get('channel_name', 'Test Channel'),
            'channel_id': base_config.get('channel_id'),
            'parser_type': 'teebinary_premium',
            'enabled': True,
            'parser_config': {
                'signal_pattern': r'^([A-Z]{3}/[A-Z]{3})\s+(CALL|PUT)\s+5MIN\s*$',
                'signal_validation': {
                    'required_fields': ['pair', 'direction', 'expiry'],
                    'valid_directions': ['HIGHER', 'LOWER'],
                    'min_expiry_minutes': 5,
                    'max_expiry_minutes': 5
                },
                'preprocessing': {
                    'remove_emojis': False,
                    'normalize_whitespace': True,
                    'convert_to_uppercase': False
                }
            }
        }
    
    def _create_btc_config(self, base_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create configuration for Binary Trading Club parser"""
        return {
            'channel_name': base_config.get('channel_name', 'Test Channel'),
            'channel_id': base_config.get('channel_id'),
            'parser_type': 'binary_trading_club',
            'enabled': True,
            'parser_config': {
                'message_patterns': {
                    'multi_message_format': True,
                    'first_message_pattern': r'Trading Pair:\s*([A-Z]{3}/[A-Z]{3})',
                    'timer_pattern': r'SET THE TIMER TO\s*(\d{2}:\d{2}:\d{2})',
                    'direction_pattern': r'\b(HIGHER|LOWER)\b',
                    'expiry_pattern': r'Trade time:\s*(\d+)\s*MIN'
                },
                'signal_validation': {
                    'required_fields': ['pair', 'direction', 'expiry'],
                    'valid_directions': ['HIGHER', 'LOWER'],
                    'min_expiry_minutes': 1,
                    'max_expiry_minutes': 5
                },
                'preprocessing': {
                    'remove_emojis': False,
                    'normalize_whitespace': True,
                    'convert_to_uppercase': False
                }
            }
        }
    
    def _create_generic_config(self, base_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create configuration for Generic parser"""
        return {
            'channel_name': base_config.get('channel_name', 'Test Channel'),
            'channel_id': base_config.get('channel_id'),
            'parser_type': 'generic',
            'enabled': True,
            'parser_config': {
                'message_patterns': {
                    'single_message_format': True,
                    'signal_regex': r'🎯 ([A-Z]{3}/[A-Z]{3}) (CALL|PUT|HIGHER|LOWER) (\d+)M'
                },
                'signal_validation': {
                    'required_fields': ['pair', 'direction', 'expiry'],
                    'valid_directions': ['HIGHER', 'LOWER', 'CALL', 'PUT'],
                    'min_expiry_minutes': 1,
                    'max_expiry_minutes': 60
                },
                'preprocessing': {
                    'remove_emojis': False,
                    'normalize_whitespace': True,
                    'convert_to_uppercase': False
                }
            }
        }
    
    def parse_message(self, message_text: str, message_data: Optional[Dict[str, Any]] = None) -> Optional[Signal]:
        """
        Parse message using multiple parsers in priority order.
        
        Args:
            message_text: The message text to parse
            message_data: Additional message metadata
            
        Returns:
            Signal object if any parser successfully parses the message, None otherwise
        """
        self.parsing_attempts += 1
        
        try:
            # Preprocess the message
            processed_text = self.preprocess_message(message_text)
            
            # Try each parser in priority order
            for parser_name in self.parser_priority:
                if parser_name not in self.sub_parsers:
                    continue
                
                try:
                    parser = self.sub_parsers[parser_name]
                    signal = parser.parse_message(processed_text, message_data)
                    
                    if signal:
                        # Update statistics
                        self.successful_parses += 1
                        self.parser_usage_stats[parser_name] += 1
                        
                        # Add multi-parser metadata
                        if signal.raw_data is None:
                            signal.raw_data = {}
                        signal.raw_data.update({
                            'multi_parser_used': parser_name,
                            'multi_parser_attempt': self.parsing_attempts,
                            'original_message': message_text,
                            'processed_message': processed_text
                        })
                        
                        logger.info(f"✅ MultiParser: {parser_name} successfully parsed signal: {signal.pair} {signal.direction} {signal.expiry}min")
                        return signal
                        
                except Exception as e:
                    logger.debug(f"Parser {parser_name} failed: {str(e)}")
                    continue
            
            # No parser succeeded
            logger.debug(f"MultiParser: No parser could handle message: {processed_text[:50]}...")
            return None
            
        except Exception as e:
            logger.error(f"Error in MultiParser.parse_message: {str(e)}")
            return None
    
    def validate_signal(self, signal: Signal) -> tuple[bool, str]:
        """
        Validate signal using the parser that created it.
        
        Args:
            signal: The Signal object to validate
            
        Returns:
            Tuple of (is_valid: bool, validation_message: str)
        """
        try:
            # First run base validation
            is_valid, msg = super().validate_signal(signal)
            if not is_valid:
                return is_valid, msg
            
            # Get the parser that created this signal
            parser_used = signal.raw_data.get('multi_parser_used') if signal.raw_data else None
            
            if parser_used and parser_used in self.sub_parsers:
                # Use the specific parser's validation
                parser = self.sub_parsers[parser_used]
                return parser.validate_signal(signal)
            else:
                # Use base validation
                return True, "MultiParser signal is valid"
                
        except Exception as e:
            logger.error(f"Error validating signal in MultiParser: {str(e)}")
            return False, f"Validation error: {str(e)}"
    
    def reset_state(self) -> None:
        """Reset state for all sub-parsers"""
        super().reset_state()
        for parser in self.sub_parsers.values():
            parser.reset_state()
        logger.debug("Reset state for all sub-parsers")
    
    def get_parsing_stats(self) -> Dict[str, Any]:
        """Return comprehensive parsing statistics"""
        base_stats = super().get_parsing_stats()
        
        # Calculate success rate
        success_rate = (self.successful_parses / self.parsing_attempts * 100) if self.parsing_attempts > 0 else 0
        
        base_stats.update({
            'parser_type': 'multi_parser',
            'sub_parsers': list(self.sub_parsers.keys()),
            'parser_priority': self.parser_priority,
            'parsing_attempts': self.parsing_attempts,
            'successful_parses': self.successful_parses,
            'success_rate_percent': round(success_rate, 2),
            'parser_usage_stats': self.parser_usage_stats,
            'most_used_parser': max(self.parser_usage_stats, key=lambda x: self.parser_usage_stats[x]) if self.parser_usage_stats else None
        })
        
        return base_stats
    
    def get_channel_info(self) -> Dict[str, Any]:
        """Return multi-parser channel information"""
        base_info = super().get_channel_info()
        base_info.update({
            'parser_type': 'multi_parser',
            'supported_formats': [
                'TeeBinary Premium: PAIR CALL/PUT 5MIN',
                'Binary Trading Club: 2-message format',
                'Generic: 🎯 PAIR DIRECTION DURATION'
            ],
            'sub_parsers_count': len(self.sub_parsers),
            'parser_priority': self.parser_priority,
            'testing_capabilities': [
                'Forwarded message testing',
                'Multi-format signal detection',
                'Real demo trading validation'
            ]
        })
        return base_info
