# src/main.py
import asyncio
import logging
from datetime import datetime
from typing import Optional
import json

from .websocket_client import WebSocketClient
from .strategy import TradingStrategy
from .config import Config
from .tui import TradingBotTUI

class TradingBot:
    def __init__(self):
        self.config = Config()
        self.trading_rules = self.config.get_trading_rules()
        self.ws_client = WebSocketClient()
        self.strategy = TradingStrategy(self.trading_rules)
        self.tui = TradingBotTUI()
        self.trading_active = False
        self.logger = self.setup_logger()

    def setup_logger(self):
        """Setup logging configuration."""
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        handler = logging.FileHandler('trading_bot.log')
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    async def connect(self, ssid: str) -> bool:
        """Connect to WebSocket with provided SSID."""
        success = await self.ws_client.connect(ssid)
        if success:
            self.config.update_ssid(ssid)
            await self.ws_client.subscribe_to_price(self.trading_rules['asset'])
            self.tui.update_connection_status("Connected")
            self.logger.info("Successfully connected to WebSocket")
        else:
            self.tui.update_connection_status("Connection Failed")
            self.logger.error("Failed to connect to WebSocket")
        return success

    async def check_ssid_refresh(self):
        """Check and refresh SSID if needed."""
        while True:
            if not await self.ws_client.check_ssid_validity():
                self.tui.add_log_message("SSID expired. Please refresh SSID.")
                self.trading_active = False
            await asyncio.sleep(3600)  # Check every hour

    async def process_market_data(self, data: dict):
        """Process incoming market data."""
        if not self.trading_active:
            return

        self.strategy.update_price_history(data)
        self.tui.update_price(data['close'])

        if not self.strategy.check_trading_hours():
            return

        if not self.strategy.can_place_trade():
            return

        account_balance = float(data.get('account_balance', 0))
        self.tui.update_balance(account_balance)

        if not self.strategy.check_risk_parameters(account_balance):
            return

        signal = self.strategy.analyze_entry_signal()
        if signal:
            position_size = account_balance * 0.01  # 1% of account balance
            success = await self.ws_client.place_trade(
                signal,
                position_size,
                self.trading_rules['trade_parameters']['expiry']
            )
            
            if success:
                self.tui.add_log_message(f"Placed {signal.upper()} trade: ${position_size:.2f}")
                self.strategy.last_trade_time = datetime.now()

    async def run(self):
        """Main running loop."""
        ssid_refresh_task = asyncio.create_task(self.check_ssid_refresh())
        
        try:
            while True:
                if self.ws_client.connected and self.trading_active:
                    price_data = await self.ws_client.receive_price_updates()
                    if price_data:
                        await self.process_market_data(price_data)
                await asyncio.sleep(0.1)
        except Exception as e:
            self.logger.error(f"Error in main loop: {str(e)}")
        finally:
            ssid_refresh_task.cancel()
            await self.ws_client.close()

    def start(self):
        """Start the trading bot."""
        self.tui.run()

if __name__ == "__main__":
    bot = TradingBot()
    bot.start()