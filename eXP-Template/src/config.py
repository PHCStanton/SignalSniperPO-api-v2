# src/config.py
import json
import os
from typing import Dict, Any
from datetime import datetime

class Config:
    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self.config: Dict[str, Any] = {}
        self.load_config()

    def load_config(self) -> None:
        """Load configuration from file."""
        try:
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
        except FileNotFoundError:
            # Load default configuration
            self.config = {
                "websocket": {
                    "uri": "wss://po.trade/ws",
                    "ssid_refresh_hours": 20
                },
                "trading": {
                    "symbol": "EUR/USD",
                    "timeframe": "1 minute",
                    "position_size_percent": 1,
                    "daily_loss_limit_percent": 5
                },
                "backtesting": {
                    "enabled": False,
                    "data_file": "backtest_data.csv"
                }
            }
            self.save_config()

    def save_config(self) -> None:
        """Save current configuration to file."""
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=4)

    def update_ssid(self, ssid: str) -> None:
        """Update SSID in configuration."""
        self.config["websocket"]["ssid"] = ssid
        self.config["websocket"]["last_update"] = datetime.now().isoformat()
        self.save_config()

    def get_ssid(self) -> str:
        """Get current SSID."""
        return self.config["websocket"].get("ssid", "")

    def get_trading_rules(self) -> Dict:
        """Get trading rules from configuration."""
        rules_path = os.path.join(os.path.dirname(__file__), "..", "docs", "trading_rules.json")
        try:
            with open(rules_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def __getitem__(self, key: str) -> Any:
        """Get configuration value."""
        return self.config.get(key, {})