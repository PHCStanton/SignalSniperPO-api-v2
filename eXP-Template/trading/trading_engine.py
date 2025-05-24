"""Trading engine for trading system.

This module provides the TradingEngine class for executing and managing trades.
"""
from typing import Dict, List, Optional
import asyncio

from models.trade import Trade
from models.signal import Signal
from api.pocket_option_api import PocketOptionAPI


class TradingEngine:
    """Class for executing and managing trades.

    This class handles trade execution, monitoring, and status updates.

    Attributes:
        config: Configuration object
        pocket_option_api: PocketOption API client
        active_trades: Dictionary of active trades
        trade_history: List of completed trades
        monitoring_task: Task for monitoring trades
    """

    def __init__(self, config):
        """Initialize trading engine with configuration.

        Args:
            config: Configuration object
        """
        self.config = config
        self.pocket_option_api = PocketOptionAPI(config)
        self.active_trades: Dict[str, Trade] = {}
        self.trade_history: List[Trade] = []
        self.monitoring_task: Optional[asyncio.Task] = None

    async def execute_trade(self, signal: Signal) -> Optional[str]:
        """Execute a trade based on a signal.

        Args:
            signal: Signal to execute trade from

        Returns:
            Optional[str]: Trade ID if successful, None otherwise
        """
        try:
            trade_result = await self.pocket_option_api.place_trade(
                symbol=signal.symbol,
                direction=signal.direction,
                amount=signal.amount,
                expiry=signal.expiry
            )
            
            if trade_result and trade_result.get('success'):
                trade = Trade(
                    id=trade_result['trade_id'],
                    signal=signal,
                    position_size=signal.amount
                )
                self.active_trades[trade.id] = trade
                return trade.id
            return None
        except Exception as e:
            print(f"Error executing trade: {e}")
            return None

    async def close_trade(self, trade_id: str) -> bool:
        """Close a specific trade.

        Args:
            trade_id: ID of trade to close

        Returns:
            bool: Whether close was successful
        """
        if trade_id in self.active_trades:
            try:
                result = await self.pocket_option_api.close_trade(trade_id)
                if result.get('success'):
                    trade = self.active_trades.pop(trade_id)
                    trade.update_result(result)
                    self.trade_history.append(trade)
                    return True
            except Exception as e:
                print(f"Error closing trade: {e}")
        return False

    async def close_all_trades(self):
        """Close all active trades."""
        for trade_id in list(self.active_trades.keys()):
            await self.close_trade(trade_id)

    def get_active_trades(self) -> List[Trade]:
        """Get list of active trades.

        Returns:
            List[Trade]: List of active trades
        """
        return list(self.active_trades.values())

    def get_trade_history(self) -> List[Trade]:
        """Get trading history.

        Returns:
            List[Trade]: List of completed trades
        """
        return self.trade_history

    async def monitor_trades(self):
        """Monitor active trades for updates."""
        while True:
            try:
                updates = await self.pocket_option_api.get_active_trades()
                for update in updates:
                    trade_id = update['trade_id']
                    if trade_id in self.active_trades:
                        if update['status'] == 'closed':
                            await self.close_trade(trade_id)
            except Exception as e:
                print(f"Error monitoring trades: {e}")
            await asyncio.sleep(1)