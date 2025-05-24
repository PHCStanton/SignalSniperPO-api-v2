"""Risk management for trading system.

This module provides the RiskManager class for implementing risk management
rules and position sizing.
"""
from typing import Dict
from models.trade import Trade
from models.signal import Signal


class RiskManager:
    """Class for managing trading risk parameters.

    This class implements risk management rules including position sizing,
    maximum losses, and concurrent trade limits.

    Attributes:
        config: Configuration object
        max_position_size: Maximum allowed position size
        max_daily_loss: Maximum allowed daily loss
        max_concurrent_trades: Maximum allowed concurrent trades
        current_daily_loss: Current daily loss amount
        active_trades_count: Current number of active trades
    """

    def __init__(self, config):
        """Initialize RiskManager with configuration.

        Args:
            config: Configuration object containing risk parameters
        """
        self.config = config
        self.max_position_size = config.get_config("max_position_size")
        self.max_daily_loss = config.get_config("max_daily_loss")
        self.max_concurrent_trades = config.get_config("max_concurrent_trades")
        self.current_daily_loss = 0
        self.active_trades_count = 0

    async def validate_trade(self, trade: Trade) -> bool:
        """Validate if a trade meets risk management criteria.

        Args:
            trade: Trade to validate

        Returns:
            bool: Whether trade meets risk criteria
        """
        if self.active_trades_count >= self.max_concurrent_trades:
            return False
        
        if trade.position_size > self.max_position_size:
            return False

        # Check if potential loss would exceed daily limit
        potential_loss = trade.position_size
        if self.current_daily_loss + potential_loss > self.max_daily_loss:
            return False

        return True

    async def update_risk_params(self, params: Dict):
        """Update risk management parameters.

        Args:
            params: Dictionary of parameters to update
        """
        if "max_position_size" in params:
            self.max_position_size = params["max_position_size"]
        if "max_daily_loss" in params:
            self.max_daily_loss = params["max_daily_loss"]
        if "max_concurrent_trades" in params:
            self.max_concurrent_trades = params["max_concurrent_trades"]

    async def calculate_position_size(self, signal: Signal) -> float:
        """Calculate appropriate position size for a signal.

        Args:
            signal: Signal to calculate position size for

        Returns:
            float: Calculated position size
        """
        account_balance = self.config.get_config("account_balance")
        risk_per_trade = self.config.get_config("risk_per_trade")
        
        position_size = account_balance * (risk_per_trade / 100)
        return min(position_size, self.max_position_size)