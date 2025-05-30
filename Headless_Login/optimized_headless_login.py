#!/usr/bin/env python3
"""
Optimized Headless Login for Pocket Option - Raw WebSocket Implementation

This implementation uses raw WebSocket connection (like PocketOptionAPI-v2) instead of 
Socket.IO client library to avoid protocol negotiation issues.

Key optimizations:
- Raw WebSocket connection without Socket.IO client overhead
- Manual Socket.IO message handling
- Pre-authenticated session reuse
- Optimized for speed over features
"""

try:
    import websocket
except ImportError:
    print("Error: websocket-client package is not installed.")
    print("Please install it using: pip install websocket-client")
    exit(1)
import json
import time
import threading
import logging
from datetime import datetime
from typing import Optional, Dict, Any, Callable
import ssl

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OptimizedPocketOptionClient:
    """
    High-performance, minimal overhead Pocket Option client using raw WebSocket.
    Based on PocketOptionAPI-v2 connection method but optimized for latency.
    """
    
    def __init__(self, auth_payload: str, is_demo: bool = False):
        """
        Initialize the optimized client.
        
        Args:
            auth_payload: Pre-authenticated session string from login process
            is_demo: Whether to use demo mode (default: False for real trading)
        """
        self.auth_payload = auth_payload
        self.is_demo = is_demo
        self.ws = None
        
        # Connection state
        self.connected = False
        self.authenticated = False
        self.sid_received = False
        
        # Trading state
        self.balance = None
        self.last_trade_result = None
        self.pending_trades = {}
        
        # Performance tracking
        self.connection_time = None
        self.auth_time = None
        
        # Event callbacks
        self.on_trade_result_callback: Optional[Callable] = None
        self.on_balance_update_callback: Optional[Callable] = None
        
        # Threading
        self.ws_thread = None
        self.running = False
    
    def _on_message(self, ws, message):
        """Handle incoming WebSocket messages."""
        try:
            # Handle Socket.IO protocol messages (like PocketOptionAPI-v2)
            # Convert bytes to string if needed
            if isinstance(message, bytes):
                message = message.decode('utf-8')
            
            if message.startswith('0{"sid":"'):
                logger.debug("📨 Received SID, sending 40")
                ws.send("40")
                
            elif message == "2":
                # Ping-pong
                logger.debug("📨 Ping received, sending pong")
                ws.send("3")
                
            elif message.startswith('40{"sid":"'):
                logger.debug("📨 Ready for auth, sending session")
                ws.send(self.auth_payload)
                self.sid_received = True
                logger.info("🔐 Authentication sent")
                
            elif "successauth" in message or "auth" in message.lower():
                self.auth_time = time.time()
                self.authenticated = True
                if self.connection_time:
                    auth_latency = (self.auth_time - self.connection_time) * 1000
                    logger.info(f"✅ Authenticated successfully (latency: {auth_latency:.1f}ms)")
                
            elif "balance" in message.lower():
                # Extract balance quickly
                try:
                    if '"balance":' in message:
                        # Quick regex-free extraction
                        balance_start = message.find('"balance":') + 10
                        balance_end = message.find(',', balance_start)
                        if balance_end == -1:
                            balance_end = message.find('}', balance_start)
                        if balance_end > balance_start:
                            balance_str = message[balance_start:balance_end].strip('"')
                            self.balance = float(balance_str)
                            if self.on_balance_update_callback:
                                self.on_balance_update_callback(self.balance)
                except:
                    pass
                    
            elif "profit" in message.lower() or "trade_result" in message.lower():
                # Handle trade results
                try:
                    # Quick parsing for trade results
                    if '"id":' in message:
                        self.last_trade_result = message
                        if self.on_trade_result_callback:
                            self.on_trade_result_callback(message)
                except:
                    pass
            
            # Log only in debug mode to reduce overhead
            if logger.level <= logging.DEBUG:
                logger.debug(f"📨 Message: {message[:100]}...")
                
        except Exception as e:
            logger.error(f"❌ Error processing message: {e}")
    
    def _on_error(self, ws, error):
        """Handle WebSocket errors."""
        logger.error(f"❌ WebSocket error: {error}")
    
    def _on_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket close."""
        self.connected = False
        self.authenticated = False
        logger.warning("❌ WebSocket connection closed")
    
    def _on_open(self, ws):
        """Handle WebSocket open."""
        self.connection_time = time.time()
        self.connected = True
        logger.info("✅ Connected to Pocket Option WebSocket")
    
    def connect(self, timeout: int = 10) -> bool:
        """
        Connect to Pocket Option with timeout.
        
        Args:
            timeout: Connection timeout in seconds
            
        Returns:
            bool: True if connected and authenticated successfully
        """
        try:
            start_time = time.time()
            
            # Create WebSocket connection (same as PocketOptionAPI-v2)
            websocket.enableTrace(False)  # Disable debug traces for performance
            self.ws = websocket.WebSocketApp(
                "wss://api-eu.po.market/socket.io/?EIO=4&transport=websocket",
                header=["Origin: https://po.trade/"],  # Same origin as PocketOptionAPI-v2
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close,
                on_open=self._on_open
            )
            
            # Start WebSocket in thread
            self.running = True
            self.ws_thread = threading.Thread(
                target=self.ws.run_forever,
                kwargs={
                    'sslopt': {
                        "check_hostname": False,
                        "cert_reqs": ssl.CERT_NONE
                    },
                    "ping_interval": 0,
                    "skip_utf8_validation": True,
                    "origin": "https://po.trade/"
                }
            )
            self.ws_thread.daemon = True
            self.ws_thread.start()
            
            # Wait for authentication
            auth_timeout = start_time + timeout
            while time.time() < auth_timeout:
                if self.authenticated:
                    total_time = (time.time() - start_time) * 1000
                    logger.info(f"🚀 Ready for trading (total setup: {total_time:.1f}ms)")
                    return True
                time.sleep(0.01)  # 10ms polling
            
            logger.error("❌ Authentication timeout")
            return False
            
        except Exception as e:
            logger.error(f"❌ Connection failed: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from Pocket Option."""
        try:
            self.running = False
            if self.ws:
                self.ws.close()
                logger.info("👋 Disconnected from Pocket Option")
        except Exception as e:
            logger.error(f"Error during disconnect: {e}")
    
    def execute_trade(self, asset: str, direction: str, amount: float, expiry: int) -> Optional[str]:
        """
        Execute a trade with minimal latency.
        
        Args:
            asset: Trading asset (e.g., "EURUSD_otc")
            direction: "call" or "put"
            amount: Trade amount
            expiry: Expiry time in seconds
            
        Returns:
            str: Trade ID if successful, None if failed
        """
        if not self.authenticated or not self.ws:
            logger.error("❌ Not authenticated or connected")
            return None
        
        try:
            # Create minimal trade payload (same format as PocketOptionAPI-v2)
            trade_payload = f'42["buy",{{"asset":"{asset}","direction":"{direction}","amount":{amount},"expiry":{expiry}}}]'
            
            # Record execution timestamp
            execution_start = time.time()
            
            # Send trade immediately
            self.ws.send(trade_payload)
            
            # Generate trade ID for tracking
            trade_id = f"trade_{int(execution_start * 1000)}"
            self.pending_trades[trade_id] = {
                "asset": asset,
                "direction": direction,
                "amount": amount,
                "expiry": expiry,
                "timestamp": execution_start
            }
            
            execution_time = (time.time() - execution_start) * 1000
            logger.info(f"🚀 Trade executed: {asset} {direction.upper()} ${amount} (latency: {execution_time:.1f}ms)")
            
            return trade_id
            
        except Exception as e:
            logger.error(f"❌ Trade execution failed: {e}")
            return None
    
    def get_balance(self) -> Optional[float]:
        """Get current account balance."""
        return self.balance
    
    def is_connected(self) -> bool:
        """Check if connected and authenticated."""
        return self.connected and self.authenticated
    
    def set_trade_result_callback(self, callback: Callable):
        """Set callback for trade results."""
        self.on_trade_result_callback = callback
    
    def set_balance_update_callback(self, callback: Callable):
        """Set callback for balance updates."""
        self.on_balance_update_callback = callback


class HeadlessLoginManager:
    """
    Manages session authentication and client lifecycle for optimal performance.
    """
    
    def __init__(self, session_file: str = "session.txt"):
        self.session_file = session_file
        self.client: Optional[OptimizedPocketOptionClient] = None
    
    def load_session(self) -> Optional[str]:
        """Load session from file."""
        try:
            with open(self.session_file, "r") as f:
                return f.read().strip()
        except FileNotFoundError:
            logger.error(f"Session file not found: {self.session_file}")
            return None
        except Exception as e:
            logger.error(f"Error loading session: {e}")
            return None
    
    def save_session(self, session: str) -> bool:
        """Save session to file."""
        try:
            with open(self.session_file, "w") as f:
                f.write(session)
            return True
        except Exception as e:
            logger.error(f"Error saving session: {e}")
            return False
    
    def create_client(self, auth_payload: Optional[str] = None, is_demo: bool = False) -> Optional[OptimizedPocketOptionClient]:
        """
        Create optimized client with session.
        
        Args:
            auth_payload: Optional auth payload, will load from file if not provided
            is_demo: Demo mode flag
            
        Returns:
            OptimizedPocketOptionClient: Ready-to-use client or None if failed
        """
        if not auth_payload:
            auth_payload = self.load_session()
            if not auth_payload:
                logger.error("No valid session available")
                return None
        
        try:
            self.client = OptimizedPocketOptionClient(auth_payload, is_demo)
            
            if self.client.connect():
                logger.info("✅ Headless client ready for trading")
                return self.client
            else:
                logger.error("❌ Failed to connect headless client")
                return None
                
        except Exception as e:
            logger.error(f"Error creating client: {e}")
            return None
    
    def cleanup(self):
        """Clean up client connection."""
        if self.client:
            self.client.disconnect()
            self.client = None


# Example usage and testing
if __name__ == "__main__":
    # Example session string (replace with your actual session)
    AUTH_PAYLOAD = '42["auth", {"session":"a:4:{s:10:\\"session_id\\";s:32:\\"09fe77a0ae78b1cad0b0f39fdcd860e1\\";s:10:\\"ip_address\\";s:12:\\"169.0.58.139\\";s:10:\\"user_agent\\";s:111:\\"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36\\";s:13:\\"last_activity\\";i:1748595569;}cf3adf2d4ba652d639fc10f3b8cf643b","isDemo":0,"uid":101002476,"platform":9,"isFastHistory":true}]'
    
    # Create login manager
    login_manager = HeadlessLoginManager()
    
    # Create and test client
    client = login_manager.create_client(AUTH_PAYLOAD, is_demo=False)
    
    if client:
        print(f"Balance: ${client.get_balance()}")
        
        # Example trade execution
        trade_id = client.execute_trade("EURUSD_otc", "call", 1.0, 60)
        if trade_id:
            print(f"Trade executed: {trade_id}")
        
        # Keep connection alive for testing
        try:
            input("Press Enter to disconnect...")
        except KeyboardInterrupt:
            pass
        
        # Cleanup
        login_manager.cleanup()
    else:
        print("Failed to create client")
