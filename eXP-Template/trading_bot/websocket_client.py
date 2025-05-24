# trading_bot/websocket_client.py
import json
import logging
import time
import urllib.request
import urllib.error
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class WebSocketClient:
    def __init__(self, base_url: str = "https://po.trade/api"):
        self.base_url = base_url
        self.ssid: Optional[str] = None
        self.last_ssid_update = time.time()
        self.connected = False
        self.headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0'
        }

    def connect(self, ssid: str) -> bool:
        """Connect to PocketOption API with SSID."""
        self.ssid = ssid
        try:
            auth_data = {
                "action": "auth",
                "ssid": self.ssid
            }
            req = urllib.request.Request(
                f"{self.base_url}/auth",
                data=json.dumps(auth_data).encode(),
                headers=self.headers,
                method='POST'
            )
            with urllib.request.urlopen(req) as response:
                auth_response = json.loads(response.read().decode())
                
                if auth_response.get("status") == "success":
                    self.connected = True
                    self.last_ssid_update = time.time()
                    self.headers['Authorization'] = f'Bearer {self.ssid}'
                    logger.info("Successfully connected to PocketOption API")
                    return True
            return False
        except Exception as e:
            logger.error(f"API connection failed: {str(e)}")
            return False

    def subscribe_to_price(self, symbol: str = "EUR/USD") -> bool:
        """Subscribe to price updates for a specific symbol."""
        if not self.connected:
            return False
        
        try:
            subscribe_data = {
                "action": "subscribe",
                "symbol": symbol,
                "timeframe": "M1"
            }
            req = urllib.request.Request(
                f"{self.base_url}/subscribe",
                data=json.dumps(subscribe_data).encode(),
                headers=self.headers,
                method='POST'
            )
            with urllib.request.urlopen(req) as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"Price subscription failed: {str(e)}")
            return False

    def place_trade(self, direction: str, amount: float, expiry: int = 60) -> bool:
        """Place a trade through API."""
        if not self.connected:
            return False
        
        try:
            trade_data = {
                "action": "trade",
                "type": direction,  # "call" or "put"
                "amount": amount,
                "expiry": expiry,
                "asset": "EUR/USD"
            }
            req = urllib.request.Request(
                f"{self.base_url}/trade",
                data=json.dumps(trade_data).encode(),
                headers=self.headers,
                method='POST'
            )
            with urllib.request.urlopen(req) as response:
                trade_response = json.loads(response.read().decode())
                return trade_response.get("status") == "success"
        except Exception as e:
            logger.error(f"Trade placement failed: {str(e)}")
            return False

    def receive_price_updates(self) -> Optional[Dict[str, Any]]:
        """Receive price updates through polling."""
        if not self.connected:
            return None
        
        try:
            req = urllib.request.Request(
                f"{self.base_url}/price",
                headers=self.headers,
                method='GET'
            )
            with urllib.request.urlopen(req) as response:
                return json.loads(response.read().decode())
        except Exception as e:
            logger.error(f"Error receiving price updates: {str(e)}")
            return None

    def close(self):
        """Close API connection."""
        self.connected = False
        self.ssid = None