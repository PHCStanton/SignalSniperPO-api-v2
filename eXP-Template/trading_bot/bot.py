# trading_bot/bot.py
import logging
import time
from datetime import datetime
from typing import Optional, Dict, Any
import threading

from .websocket_adapter import WebSocketAdapter
from .strategy import TradingStrategy
from .config import Config
from .tui import TradingBotTUI

logger = logging.getLogger(__name__)

class TradingBot:
    def __init__(self, use_improved_websocket: bool = True):
        self.config = Config()
        self.trading_rules = self.config.get_trading_rules()
        self.ws_client = WebSocketAdapter(use_improved=use_improved_websocket)
        self.strategy = TradingStrategy(self.trading_rules)
        self.tui = TradingBotTUI()
        self.trading_active = False
        self.trading_thread = None
        self.setup_event_handlers()

    def setup_event_handlers(self):
        """Setup event handlers for TUI messages."""
        self.tui.on_message = self.handle_tui_message

    def handle_tui_message(self, message: Dict[str, Any]):
        """Handle messages from TUI."""
        if message["type"] == "connect":
            self._connect(message["ssid"])
        elif message["type"] == "refresh_ssid":
            self._refresh_ssid()
        elif message["type"] == "toggle_trading":
            self.trading_active = not self.trading_active
            status = "started" if self.trading_active else "stopped"
            self.tui.add_log_message(f"Trading {status}")

    def _connect(self, ssid: str) -> bool:
        """Connect with provided SSID."""
        success = self.ws_client.connect(ssid)
        if success:
            self.config.update_ssid(ssid)
            self.ws_client.subscribe_to_price(self.trading_rules['asset'])
            self.tui.update_connection_status("Connected")
            logger.info("Successfully connected to API")
            self.trading_thread = threading.Thread(target=self._trading_loop)
            self.trading_thread.daemon = True
            self.trading_thread.start()
        else:
            self.tui.update_connection_status("Connection Failed")
            logger.error("Failed to connect to API")
        return success

    def _refresh_ssid(self):
        """Refresh SSID connection."""
        current_ssid = self.config.get_ssid()
        if current_ssid:
            self.ws_client.close()
            self._connect(current_ssid)

    def _process_market_data(self, data: Dict[str, Any]):
        """Process incoming market data."""
        if not self.trading_active:
            return

        try:
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
                position_size = account_balance * float(self.trading_rules['risk_management']['position_size'].split('%')[0]) / 100
                success = self.ws_client.place_trade(
                    signal,
                    position_size,
                    int(self.trading_rules['trade_parameters']['expiry'].split()[0])
                )
                
                if success:
                    self.tui.add_log_message(f"Placed {signal.upper()} trade: ${position_size:.2f}")
                    self.strategy.last_trade_time = datetime.now()
        except Exception as e:
            logger.error(f"Error processing market data: {str(e)}")
            self.tui.add_log_message(f"Processing error: {str(e)}")

    def _trading_loop(self):
        """Main trading loop."""
        while True:
            try:
                if self.ws_client.is_connected() and self.trading_active:
                    price_data = self.ws_client.receive_price_updates()
                    if price_data:
                        self._process_market_data(price_data)
                time.sleep(1)  # Poll every second
            except Exception as e:
                logger.error(f"Error in trading loop: {str(e)}")
                self.tui.add_log_message(f"Trading error: {str(e)}")
                self.trading_active = False
                time.sleep(5)  # Wait before retrying

    def start(self):
        """Start the trading bot with TUI."""
        try:
            self.tui.run()
        except Exception as e:
            logger.error(f"Bot crashed: {str(e)}")
            raise
        finally:
            if self.ws_client.is_connected():
                self.ws_client.close()
