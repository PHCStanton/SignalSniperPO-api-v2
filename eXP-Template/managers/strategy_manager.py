"""Strategy management for trading system.

This module provides classes for implementing and managing different
trading strategies.
"""
from typing import Dict, Optional
from models.signal import Signal
import pandas as pd


class Strategy:
    """Base class for implementing trading strategies.

    All trading strategies should inherit from this class and implement
    the required methods.

    Attributes:
        name: Strategy name
        parameters: Strategy parameters
    """

    def __init__(self, name: str, parameters: Dict):
        """Initialize strategy with name and parameters.

        Args:
            name: Strategy name
            parameters: Strategy parameters
        """
        self.name = name
        self.parameters = parameters

    async def validate_signal(self, signal: Signal) -> bool:
        """Validate if a signal meets the strategy criteria.

        Args:
            signal: Signal to validate

        Returns:
            bool: Whether signal is valid for this strategy
        """
        raise NotImplementedError

    async def calculate_entry(self, data: pd.DataFrame) -> Dict:
        """Calculate entry parameters based on historical data.

        Args:
            data: Historical price data

        Returns:
            Dict: Entry parameters
        """
        raise NotImplementedError


class StrategyManager:
    """Class for managing trading strategies.

    This class handles loading, switching between, and applying
    trading strategies.

    Attributes:
        config: Configuration object
        strategies: Dictionary of available strategies
        active_strategy: Currently active strategy
    """

    def __init__(self, config):
        """Initialize StrategyManager with configuration.

        Args:
            config: Configuration object
        """
        self.config = config
        self.strategies: Dict[str, Strategy] = {}
        self.active_strategy: Optional[Strategy] = None
        self._load_strategies()

    def _load_strategies(self):
        """Load strategies from configuration."""
        strategy_configs = self.config.get_config("strategies")
        for strategy_name, strategy_params in strategy_configs.items():
            self.add_strategy(Strategy(strategy_name, strategy_params))

    async def add_strategy(self, strategy: Strategy):
        """Add a new strategy.

        Args:
            strategy: Strategy instance to add
        """
        self.strategies[strategy.name] = strategy
        if not self.active_strategy:
            self.active_strategy = strategy

    async def remove_strategy(self, name: str):
        """Remove a strategy.

        Args:
            name: Name of strategy to remove
        """
        if name in self.strategies:
            if self.active_strategy == self.strategies[name]:
                self.active_strategy = None
            del self.strategies[name]

    async def switch_strategy(self, name: str) -> bool:
        """Switch to a different strategy.

        Args:
            name: Name of strategy to switch to

        Returns:
            bool: Whether switch was successful
        """
        if name in self.strategies:
            self.active_strategy = self.strategies[name]
            return True
        return False

    async def validate_signal(self, signal: Signal) -> bool:
        """Validate a signal using the active strategy.

        Args:
            signal: Signal to validate

        Returns:
            bool: Whether signal is valid
        """
        if not self.active_strategy:
            return False
        return await self.active_strategy.validate_signal(signal)