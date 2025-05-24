"""Signal model for trading signals.

This module defines the Signal class, which represents a trading signal
with attributes like symbol, direction, expiry, etc.
"""
from datetime import datetime
from typing import Optional, Dict, Any

class Signal:
    """Class representing a trading signal.
    
    This class represents a trading signal with attributes like symbol,
    direction, expiry, etc. It is used to pass signals between components
    of the trading bot.
    
    Attributes:
        timestamp: When the signal was generated
        symbol: Trading pair (e.g., "EUR/USD")
        direction: Trade direction ("CALL" or "PUT")
        expiry: Expiry time in seconds
        confidence: Confidence level (0.0 to 1.0)
        source: Source of the signal (e.g., "telegram", "test")
        amount: Trade amount (optional)
    """
    
    def __init__(self, 
                 timestamp: datetime,
                 symbol: str,
                 direction: str,
                 expiry: int,
                 confidence: float,
                 source: str,
                 amount: Optional[float] = None):
        """Initialize a Signal object.
        
        Args:
            timestamp: When the signal was generated
            symbol: Trading pair (e.g., "EUR/USD")
            direction: Trade direction ("CALL" or "PUT")
            expiry: Expiry time in seconds
            confidence: Confidence level (0.0 to 1.0)
            source: Source of the signal (e.g., "telegram", "test")
            amount: Trade amount (optional)
        """
        self.timestamp = timestamp
        self.symbol = symbol
        self.direction = direction
        self.expiry = expiry
        self.confidence = confidence
        self.source = source
        self.amount = amount
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the signal to a dictionary.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the signal
        """
        return {
            "timestamp": self.timestamp.isoformat(),
            "symbol": self.symbol,
            "direction": self.direction,
            "expiry": self.expiry,
            "confidence": self.confidence,
            "source": self.source,
            "amount": self.amount
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Signal':
        """Create a Signal object from a dictionary.
        
        Args:
            data: Dictionary representation of the signal
            
        Returns:
            Signal: Signal object
        """
        return cls(
            timestamp=datetime.fromisoformat(data["timestamp"]),
            symbol=data["symbol"],
            direction=data["direction"],
            expiry=data["expiry"],
            confidence=data["confidence"],
            source=data["source"],
            amount=data.get("amount")
        )
    
    def __str__(self) -> str:
        """Return a string representation of the signal.
        
        Returns:
            str: String representation of the signal
        """
        return f"Signal({self.symbol}, {self.direction}, {self.expiry}s, {self.confidence:.2f}, {self.source})"
    
    def __repr__(self) -> str:
        """Return a string representation of the signal.
        
        Returns:
            str: String representation of the signal
        """
        return self.__str__()
