"""Trade data model for trading system.

This module defines the Trade class which represents an executed trade
and its current status.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from models.signal import Signal


@dataclass
class Trade:
    """A class representing an executed trade.

    Attributes:
        id (str): Unique trade identifier
        signal (Signal): The signal that triggered this trade
        position_size (float): Trade amount
        entry_time (datetime): When the trade was opened
        exit_time (Optional[datetime]): When the trade was closed
        result (Optional[str]): Trade result (win/loss)
        pnl (Optional[float]): Profit/Loss amount
    """
    id: str
    signal: Signal
    position_size: float
    entry_time: datetime = None
    exit_time: Optional[datetime] = None
    result: Optional[str] = None
    pnl: Optional[float] = None
    
    def __post_init__(self):
        """Initialize entry time if not provided."""
        if self.entry_time is None:
            self.entry_time = datetime.now()

    def update_result(self, result_data: dict):
        """Update trade with result information.

        Args:
            result_data (dict): Dictionary containing trade result data
        """
        self.exit_time = datetime.now()
        self.result = result_data.get('result', 'unknown')
        self.pnl = result_data.get('pnl', 0.0)

    def to_dict(self) -> dict:
        """Convert Trade to dictionary format.

        Returns:
            dict: Trade data as dictionary
        """
        return {
            'id': self.id,
            'signal': self.signal.to_dict(),
            'position_size': self.position_size,
            'entry_time': self.entry_time.isoformat() if self.entry_time else None,
            'exit_time': self.exit_time.isoformat() if self.exit_time else None,
            'result': self.result,
            'pnl': self.pnl
        }