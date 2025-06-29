#!/usr/bin/env python3
"""
Parsers Module for Modular Channel Architecture

This module provides channel-specific parsers for different Telegram channels.
Each parser handles the unique message format and signal extraction logic
for its respective channel.
"""

from .base_parser import BaseChannelParser, Signal
from .generic_parser import GenericParser
from .binary_trading_club_parser import BinaryTradingClubParser
from .teebinary_premium_parser import TeeBinaryPremiumParser
from .multi_parser import MultiParser

__all__ = [
    'BaseChannelParser', 
    'Signal',
    'GenericParser',
    'BinaryTradingClubParser', 
    'TeeBinaryPremiumParser',
    'MultiParser'
]
