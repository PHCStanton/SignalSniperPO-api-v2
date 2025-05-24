# trading_bot/websocket_adapter.py
import logging
from typing import Optional, Dict, Any, Union, cast, TYPE_CHECKING

# Import both implementations
from .websocket_client import WebSocketClient
from .improved_websocket_client import ImprovedWebSocketClient

logger = logging.getLogger(__name__)

class WebSocketAdapter:
    """Adapter to provide unified interface for both WebSocket client implementations.
    
    This adapter allows the trading bot to easily switch between the original HTTP
    polling implementation and the new WebSocket-based implementation without
    changing the bot's code.
    """
    
    def __init__(self, use_improved: bool = True, base_url: str = "https://po.trade/api", ws_uri: str = "wss://po.trade/ws"):
        """Initialize the WebSocket adapter.
        
        Args:
            use_improved: Whether to use the improved WebSocket implementation
            base_url: Base URL for HTTP API (used by original implementation)
            ws_uri: WebSocket URI (used by improved implementation)
        """
        self.use_improved = use_improved
        
        # Ensure WebSocket URI is properly formatted
        if not ws_uri.startswith(('ws://', 'wss://')):
            if ws_uri.startswith(('http://', 'https://')):
                ws_uri = 'wss://' + ws_uri.split('://', 1)[1]
            else:
                ws_uri = 'wss://' + ws_uri
        
        if use_improved:
            self.client: Union[ImprovedWebSocketClient, WebSocketClient] = ImprovedWebSocketClient(uri=ws_uri)
            logger.info("Using improved WebSocket client with automatic reconnection")
        else:
            self.client: Union[ImprovedWebSocketClient, WebSocketClient] = WebSocketClient(base_url=base_url)
            logger.info("Using original HTTP polling client")

    def connect(self, ssid: str) -> bool:
        """Connect to PocketOption API/WebSocket with SSID."""
        if self.use_improved:
            # For the improved client, we need to use the sync methods
            improved_client = cast(ImprovedWebSocketClient, self.client)
            return improved_client.sync_connect(ssid)
        else:
            # For the original client, we use the direct methods
            original_client = cast(WebSocketClient, self.client)
            return original_client.connect(ssid)
            
    def subscribe_to_price(self, symbol: str = "EUR/USD") -> bool:
        """Subscribe to price updates for a specific symbol."""
        if self.use_improved:
            improved_client = cast(ImprovedWebSocketClient, self.client)
            return improved_client.sync_subscribe_to_price(symbol)
        else:
            original_client = cast(WebSocketClient, self.client)
            return original_client.subscribe_to_price(symbol)
            
    def place_trade(self, direction: str, amount: float, expiry: int = 60) -> bool:
        """Place a trade through API/WebSocket."""
        if self.use_improved:
            improved_client = cast(ImprovedWebSocketClient, self.client)
            return improved_client.sync_place_trade(direction, amount, expiry)
        else:
            original_client = cast(WebSocketClient, self.client)
            return original_client.place_trade(direction, amount, expiry)
            
    def receive_price_updates(self) -> Optional[Dict[str, Any]]:
        """Receive price updates."""
        if self.use_improved:
            improved_client = cast(ImprovedWebSocketClient, self.client)
            return improved_client.sync_receive_price_updates()
        else:
            original_client = cast(WebSocketClient, self.client)
            return original_client.receive_price_updates()
            
    def is_connected(self) -> bool:
        """Check if the client is connected.
        
        Returns:
            bool: True if connected, False otherwise
        """
        if self.use_improved:
            improved_client = cast(ImprovedWebSocketClient, self.client)
            return improved_client.connected
        else:
            original_client = cast(WebSocketClient, self.client)
            return original_client.connected
            
    def close(self):
        """Close connection."""
        try:
            if self.use_improved:
                improved_client = cast(ImprovedWebSocketClient, self.client)
                improved_client.sync_close()
            else:
                original_client = cast(WebSocketClient, self.client)
                original_client.close()
        except Exception as e:
            logger.error(f"Error closing WebSocket connection: {str(e)}")
