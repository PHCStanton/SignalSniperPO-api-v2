#!/usr/bin/env python3
"""
Trading Client Manager - Dual Implementation Support

This module provides a unified interface for both the existing PocketOptionAPI-v2
and the new optimized headless client, allowing seamless switching between
implementations for latency optimization.
"""

import time
import logging
import threading
from typing import Optional, Dict, Any, Union, Tuple
from datetime import datetime
from enum import Enum

# Configure logging
logger = logging.getLogger(__name__)

class ClientType(Enum):
    """Enumeration of available client types."""
    POCKETOPTION_V2 = "pocketoption_v2"
    HEADLESS_OPTIMIZED = "headless_optimized"

class TradingClientManager:
    """
    Unified interface for managing different Pocket Option client implementations.
    Provides seamless switching between PocketOptionAPI-v2 and optimized headless client.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the trading client manager.
        
        Args:
            config: Configuration dictionary containing client settings
        """
        self.config = config
        self.client_type = ClientType(config.get("client_type", "pocketoption_v2"))
        self.client = None
        self.is_connected = False
        self.connection_time = None
        self.last_error = None
        
        # Performance tracking
        self.execution_times = []
        self.connection_attempts = 0
        self.successful_connections = 0
        
        # Import clients based on availability
        self._import_clients()
    
    def _import_clients(self):
        """Import available client implementations."""
        # Try to import PocketOptionAPI-v2
        try:
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'PocketOptionAPI-v2'))
            from pocketoptionapi.stable_api import PocketOption
            self.PocketOption = PocketOption
            self.pocketoption_v2_available = True
            logger.debug("PocketOptionAPI-v2 imported successfully")
        except ImportError as e:
            self.PocketOption = None
            self.pocketoption_v2_available = False
            logger.warning(f"PocketOptionAPI-v2 not available: {e}")
        
        # Try to import headless client
        try:
            from Headless_Login.optimized_headless_login import OptimizedPocketOptionClient, HeadlessLoginManager
            self.OptimizedPocketOptionClient = OptimizedPocketOptionClient
            self.HeadlessLoginManager = HeadlessLoginManager
            self.headless_client_available = True
            logger.debug("Headless client imported successfully")
        except ImportError as e:
            self.OptimizedPocketOptionClient = None
            self.HeadlessLoginManager = None
            self.headless_client_available = False
            logger.warning(f"Headless client not available: {e}")
    
    def get_available_clients(self) -> Dict[str, bool]:
        """Get availability status of client implementations."""
        return {
            "pocketoption_v2": self.pocketoption_v2_available,
            "headless_optimized": self.headless_client_available
        }
    
    def set_client_type(self, client_type: Union[str, ClientType]) -> bool:
        """
        Set the client type to use.
        
        Args:
            client_type: Client type to use
            
        Returns:
            bool: True if client type is available and set successfully
        """
        if isinstance(client_type, str):
            try:
                client_type = ClientType(client_type)
            except ValueError:
                logger.error(f"Invalid client type: {client_type}")
                return False
        
        # Check availability
        if client_type == ClientType.POCKETOPTION_V2 and not self.pocketoption_v2_available:
            logger.error("PocketOptionAPI-v2 is not available")
            return False
        elif client_type == ClientType.HEADLESS_OPTIMIZED and not self.headless_client_available:
            logger.error("Headless optimized client is not available")
            return False
        
        # Disconnect current client if connected
        if self.is_connected:
            self.disconnect()
        
        self.client_type = client_type
        logger.info(f"Client type set to: {client_type.value}")
        return True
    
    def connect(self) -> bool:
        """
        Connect using the selected client type.
        
        Returns:
            bool: True if connection successful
        """
        start_time = time.time()
        self.connection_attempts += 1
        
        try:
            if self.client_type == ClientType.POCKETOPTION_V2:
                return self._connect_pocketoption_v2()
            elif self.client_type == ClientType.HEADLESS_OPTIMIZED:
                return self._connect_headless_optimized()
            else:
                logger.error(f"Unsupported client type: {self.client_type}")
                return False
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Connection failed: {e}")
            return False
        finally:
            self.connection_time = time.time() - start_time
            if self.is_connected:
                self.successful_connections += 1
    
    def _connect_pocketoption_v2(self) -> bool:
        """Connect using PocketOptionAPI-v2."""
        if not self.pocketoption_v2_available:
            logger.error("PocketOptionAPI-v2 is not available")
            return False
        
        try:
            ssid = self.config.get("ssid")
            is_demo = self.config.get("is_demo", False)
            
            if not ssid:
                logger.error("SSID not provided for PocketOptionAPI-v2")
                return False
            
            logger.info("Connecting using PocketOptionAPI-v2...")
            self.client = self.PocketOption(ssid, is_demo)
            
            connection_result = self.client.connect()
            if connection_result:
                self.is_connected = True
                logger.info("✅ PocketOptionAPI-v2 connected successfully")
                return True
            else:
                logger.error("❌ PocketOptionAPI-v2 connection failed")
                return False
                
        except Exception as e:
            logger.error(f"Error connecting PocketOptionAPI-v2: {e}")
            return False
    
    def _connect_headless_optimized(self) -> bool:
        """Connect using headless optimized client."""
        if not self.headless_client_available:
            logger.error("Headless optimized client is not available")
            return False
        
        try:
            ssid = self.config.get("ssid")
            is_demo = self.config.get("is_demo", False)
            
            if not ssid:
                logger.error("SSID not provided for headless client")
                return False
            
            logger.info("Connecting using headless optimized client...")
            login_manager = self.HeadlessLoginManager()
            self.client = login_manager.create_client(ssid, is_demo)
            
            if self.client and self.client.is_connected():
                self.is_connected = True
                logger.info("✅ Headless optimized client connected successfully")
                return True
            else:
                logger.error("❌ Headless optimized client connection failed")
                return False
                
        except Exception as e:
            logger.error(f"Error connecting headless optimized client: {e}")
            return False
    
    def disconnect(self) -> None:
        """Disconnect the current client."""
        try:
            if self.client:
                if hasattr(self.client, 'disconnect'):
                    self.client.disconnect()
                elif hasattr(self.client, 'close'):
                    self.client.close()
                
                self.client = None
                self.is_connected = False
                logger.info("Client disconnected")
        except Exception as e:
            logger.error(f"Error during disconnect: {e}")
    
    def get_balance(self) -> Optional[float]:
        """Get account balance."""
        if not self.is_connected or not self.client:
            logger.error("Client not connected")
            return None
        
        try:
            return self.client.get_balance()
        except Exception as e:
            logger.error(f"Error getting balance: {e}")
            return None
    
    def execute_trade(self, asset: str, direction: str, amount: float, expiry: int) -> Tuple[bool, Optional[str]]:
        """
        Execute a trade with performance tracking.
        
        Args:
            asset: Trading asset
            direction: "call" or "put"
            amount: Trade amount
            expiry: Expiry time in seconds
            
        Returns:
            Tuple[bool, Optional[str]]: (success, trade_id)
        """
        if not self.is_connected or not self.client:
            logger.error("Client not connected")
            return False, None
        
        start_time = time.time()
        
        try:
            if self.client_type == ClientType.POCKETOPTION_V2:
                result = self._execute_trade_v2(asset, direction, amount, expiry)
            elif self.client_type == ClientType.HEADLESS_OPTIMIZED:
                result = self._execute_trade_headless(asset, direction, amount, expiry)
            else:
                logger.error(f"Unsupported client type for trading: {self.client_type}")
                return False, None
            
            execution_time = (time.time() - start_time) * 1000
            self.execution_times.append(execution_time)
            
            # Keep only last 100 execution times for performance tracking
            if len(self.execution_times) > 100:
                self.execution_times = self.execution_times[-100:]
            
            logger.info(f"Trade execution completed in {execution_time:.1f}ms")
            return result
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(f"Trade execution failed after {execution_time:.1f}ms: {e}")
            return False, None
    
    def _execute_trade_v2(self, asset: str, direction: str, amount: float, expiry: int) -> Tuple[bool, Optional[str]]:
        """Execute trade using PocketOptionAPI-v2."""
        try:
            result, trade_id = self.client.buy(amount, asset, direction, expiry)
            return result, trade_id
        except Exception as e:
            logger.error(f"PocketOptionAPI-v2 trade execution error: {e}")
            return False, None
    
    def _execute_trade_headless(self, asset: str, direction: str, amount: float, expiry: int) -> Tuple[bool, Optional[str]]:
        """Execute trade using headless optimized client."""
        try:
            trade_id = self.client.execute_trade(asset, direction, amount, expiry)
            return trade_id is not None, trade_id
        except Exception as e:
            logger.error(f"Headless client trade execution error: {e}")
            return False, None
    
    def check_trade_result(self, trade_id: str) -> Optional[Dict[str, Any]]:
        """Check trade result."""
        if not self.is_connected or not self.client:
            logger.error("Client not connected")
            return None
        
        try:
            if self.client_type == ClientType.POCKETOPTION_V2:
                return self.client.check_win(trade_id)
            elif self.client_type == ClientType.HEADLESS_OPTIMIZED:
                # Headless client handles results via callbacks
                return self.client.last_trade_result
            else:
                logger.error(f"Unsupported client type for result checking: {self.client_type}")
                return None
        except Exception as e:
            logger.error(f"Error checking trade result: {e}")
            return None
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        if not self.execution_times:
            return {
                "avg_execution_time": 0,
                "min_execution_time": 0,
                "max_execution_time": 0,
                "total_executions": 0,
                "connection_success_rate": 0,
                "client_type": self.client_type.value
            }
        
        return {
            "avg_execution_time": sum(self.execution_times) / len(self.execution_times),
            "min_execution_time": min(self.execution_times),
            "max_execution_time": max(self.execution_times),
            "total_executions": len(self.execution_times),
            "connection_success_rate": (self.successful_connections / self.connection_attempts) * 100 if self.connection_attempts > 0 else 0,
            "client_type": self.client_type.value,
            "last_connection_time": self.connection_time,
            "last_error": self.last_error
        }
    
    def get_recommended_client(self) -> ClientType:
        """
        Get recommended client type based on availability and performance.
        
        Returns:
            ClientType: Recommended client type
        """
        # If only one client is available, recommend that one
        if self.headless_client_available and not self.pocketoption_v2_available:
            return ClientType.HEADLESS_OPTIMIZED
        elif self.pocketoption_v2_available and not self.headless_client_available:
            return ClientType.POCKETOPTION_V2
        elif not self.headless_client_available and not self.pocketoption_v2_available:
            logger.error("No clients available")
            return ClientType.POCKETOPTION_V2  # Default fallback
        
        # Both clients available - recommend based on performance requirements
        # For latency-critical trading, recommend headless optimized
        return ClientType.HEADLESS_OPTIMIZED
    
    def auto_select_client(self) -> bool:
        """
        Automatically select the best available client.
        
        Returns:
            bool: True if client selected and connected successfully
        """
        recommended_client = self.get_recommended_client()
        
        if self.set_client_type(recommended_client):
            logger.info(f"Auto-selected client: {recommended_client.value}")
            return self.connect()
        else:
            logger.error("Failed to auto-select client")
            return False


# Configuration helper functions
def create_config_from_pocket_option_config(pocket_option_config: Dict[str, Any], client_type: str = "headless_optimized") -> Dict[str, Any]:
    """
    Create trading client manager config from existing pocket option config.
    
    Args:
        pocket_option_config: Existing pocket option configuration
        client_type: Preferred client type
        
    Returns:
        Dict: Configuration for trading client manager
    """
    return {
        "client_type": client_type,
        "ssid": pocket_option_config.get("ssid"),
        "is_demo": pocket_option_config.get("is_demo", False),
        "connection_timeout": pocket_option_config.get("connection_timeout", 30),
        "reconnect_attempts": pocket_option_config.get("reconnect_attempts", 5),
        "reconnect_delay": pocket_option_config.get("reconnect_delay", 5)
    }


# Example usage
if __name__ == "__main__":
    # Example configuration
    config = {
        "client_type": "headless_optimized",
        "ssid": '42["auth", {"session":"a:4:{s:10:\\"session_id\\";s:32:\\"09fe77a0ae78b1cad0b0f39fdcd860e1\\";s:10:\\"ip_address\\";s:12:\\"169.0.58.139\\";s:10:\\"user_agent\\";s:111:\\"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36\\";s:13:\\"last_activity\\";i:1748595569;}cf3adf2d4ba652d639fc10f3b8cf643b","isDemo":0,"uid":101002476,"platform":9,"isFastHistory":true}]',
        "is_demo": False
    }
    
    # Create manager
    manager = TradingClientManager(config)
    
    # Check available clients
    available = manager.get_available_clients()
    print(f"Available clients: {available}")
    
    # Auto-select and connect
    if manager.auto_select_client():
        print(f"Connected using: {manager.client_type.value}")
        print(f"Balance: ${manager.get_balance()}")
        
        # Example trade
        success, trade_id = manager.execute_trade("EURUSD_otc", "call", 1.0, 60)
        if success:
            print(f"Trade executed: {trade_id}")
        
        # Get performance stats
        stats = manager.get_performance_stats()
        print(f"Performance stats: {stats}")
        
        # Cleanup
        manager.disconnect()
    else:
        print("Failed to connect")
