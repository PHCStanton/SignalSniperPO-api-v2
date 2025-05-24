# src/websocket_client.py
import json
import asyncio
import websockets
from datetime import datetime, timedelta
import logging
from typing import Optional, Dict, Any

class WebSocketClient:
    def __init__(self, uri: str = "wss://po.trade/ws"):
        self.uri = uri
        self.ssid: Optional[str] = None
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.last_ssid_update = datetime.now()
        self.connected = False
        self.logger = logging.getLogger(__name__)

    async def connect(self, ssid: str) -> bool:
        """Connect to PocketOption WebSocket with SSID."""
        self.ssid = ssid
        try:
            self.ws = await websockets.connect(self.uri)
            auth_message = {
                "action": "auth",
                "ssid": self.ssid
            }
            await self.ws.send(json.dumps(auth_message))
            response = await self.ws.recv()
            auth_response = json.loads(response)
            
            if auth_response.get("status") == "success":
                self.connected = True
                self.last_ssid_update = datetime.now()
                self.logger.info("Successfully connected to PocketOption WebSocket")
                return True
            return False
        except Exception as e:
            self.logger.error(f"WebSocket connection failed: {str(e)}")
            return False

    async def subscribe_to_price(self, symbol: str = "EUR/USD"):
        """Subscribe to price updates for a specific symbol."""
        if not self.ws or not self.connected:
            return False
        
        subscribe_message = {
            "action": "subscribe",
            "symbol": symbol,
            "timeframe": "M1"
        }
        await self.ws.send(json.dumps(subscribe_message))

    async def place_trade(self, direction: str, amount: float, expiry: int = 60) -> bool:
        """Place a trade through WebSocket."""
        if not self.ws or not self.connected:
            return False
        
        trade_message = {
            "action": "trade",
            "type": direction,  # "call" or "put"
            "amount": amount,
            "expiry": expiry,
            "asset": "EUR/USD"
        }
        try:
            await self.ws.send(json.dumps(trade_message))
            response = await self.ws.recv()
            trade_response = json.loads(response)
            return trade_response.get("status") == "success"
        except Exception as e:
            self.logger.error(f"Trade placement failed: {str(e)}")
            return False

    async def check_ssid_validity(self) -> bool:
        """Check if SSID needs refresh (older than 20 hours)."""
        if not self.last_ssid_update:
            return False
        time_diff = datetime.now() - self.last_ssid_update
        return time_diff < timedelta(hours=20)

    async def receive_price_updates(self):
        """Receive and handle price updates."""
        if not self.ws or not self.connected:
            return None
        
        try:
            message = await self.ws.recv()
            return json.loads(message)
        except Exception as e:
            self.logger.error(f"Error receiving price updates: {str(e)}")
            return None

    async def close(self):
        """Close WebSocket connection."""
        if self.ws:
            await self.ws.close()
            self.connected = False