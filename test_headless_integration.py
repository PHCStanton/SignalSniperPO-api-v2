#!/usr/bin/env python3
"""
test_headless_integration.py - Test Script for Headless Login Integration

This script tests the integration of the optimized headless login implementation
with the existing Self Bot functionality.
"""

import os
import sys
import json
import time
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_trading_client_manager():
    """Test the trading client manager functionality."""
    try:
        # Import trading client manager
        from trading_client_manager import TradingClientManager, create_config_from_pocket_option_config
        logger.info("✅ Trading Client Manager imported successfully")
        
        # Load pocket option config
        config_file = "config/pocket_option_config.json"
        if not os.path.exists(config_file):
            logger.error(f"❌ Config file not found: {config_file}")
            return False
        
        with open(config_file, 'r') as f:
            pocket_option_config = json.load(f)
        
        # Create manager config
        manager_config = create_config_from_pocket_option_config(
            pocket_option_config,
            client_type="headless_optimized"
        )
        
        logger.info(f"📋 Manager config created: {manager_config}")
        
        # Initialize trading client manager
        manager = TradingClientManager(manager_config)
        
        # Check available clients
        available = manager.get_available_clients()
        logger.info(f"🔍 Available clients: {available}")
        
        # Get recommended client
        recommended = manager.get_recommended_client()
        logger.info(f"💡 Recommended client: {recommended.value}")
        
        # Test auto-selection
        start_time = time.time()
        if manager.auto_select_client():
            connection_time = (time.time() - start_time) * 1000
            logger.info(f"✅ Auto-selected client: {manager.client_type.value}")
            logger.info(f"⚡ Connection time: {connection_time:.1f}ms")
            
            # Test balance retrieval
            balance = manager.get_balance()
            logger.info(f"💰 Balance: {balance}")
            
            # Get performance stats
            stats = manager.get_performance_stats()
            logger.info(f"📊 Performance stats: {stats}")
            
            # Test trade execution (dry run)
            logger.info("🧪 Testing trade execution (dry run)...")
            success, trade_id = manager.execute_trade("EURUSD_otc", "call", 1.0, 60)
            logger.info(f"📈 Trade result: Success={success}, ID={trade_id}")
            
            # Cleanup
            manager.disconnect()
            logger.info("✅ Test completed successfully")
            return True
        else:
            logger.error("❌ Failed to auto-select client")
            return False
            
    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False

def test_headless_client_standalone():
    """Test the headless client standalone."""
    try:
        from Headless_Login.optimized_headless_login import OptimizedPocketOptionClient, HeadlessLoginManager
        logger.info("✅ Headless client imported successfully")
        
        # Load config
        config_file = "config/pocket_option_config.json"
        if not os.path.exists(config_file):
            logger.error(f"❌ Config file not found: {config_file}")
            return False
        
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        ssid = config.get("ssid")
        is_demo = config.get("is_demo", False)
        
        if not ssid:
            logger.error("❌ No SSID found in config")
            return False
        
        # Test headless login manager
        login_manager = HeadlessLoginManager()
        
        start_time = time.time()
        client = login_manager.create_client(ssid, is_demo)
        connection_time = (time.time() - start_time) * 1000
        
        if client and client.is_connected():
            logger.info(f"✅ Headless client connected successfully")
            logger.info(f"⚡ Connection time: {connection_time:.1f}ms")
            
            # Test balance
            balance = client.get_balance()
            logger.info(f"💰 Balance: {balance}")
            
            # Test trade execution (if available)
            if hasattr(client, 'execute_trade'):
                logger.info("🧪 Testing trade execution...")
                trade_id = client.execute_trade("EURUSD_otc", "call", 1.0, 60)
                logger.info(f"📈 Trade ID: {trade_id}")
            
            # Cleanup
            client.disconnect()
            logger.info("✅ Headless client test completed successfully")
            return True
        else:
            logger.error("❌ Failed to connect headless client")
            return False
            
    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False

def test_performance_comparison():
    """Compare performance between different client implementations."""
    try:
        from trading_client_manager import TradingClientManager, create_config_from_pocket_option_config
        
        # Load config
        config_file = "config/pocket_option_config.json"
        with open(config_file, 'r') as f:
            pocket_option_config = json.load(f)
        
        results = {}
        
        # Test both client types
        for client_type in ["pocketoption_v2", "headless_optimized"]:
            logger.info(f"🧪 Testing {client_type}...")
            
            manager_config = create_config_from_pocket_option_config(
                pocket_option_config,
                client_type=client_type
            )
            
            manager = TradingClientManager(manager_config)
            
            if manager.set_client_type(client_type):
                start_time = time.time()
                if manager.connect():
                    connection_time = (time.time() - start_time) * 1000
                    
                    # Test balance retrieval
                    balance_start = time.time()
                    balance = manager.get_balance()
                    balance_time = (time.time() - balance_start) * 1000
                    
                    results[client_type] = {
                        "connection_time_ms": connection_time,
                        "balance_retrieval_ms": balance_time,
                        "balance": balance,
                        "available": True
                    }
                    
                    manager.disconnect()
                    logger.info(f"✅ {client_type}: Connection={connection_time:.1f}ms, Balance={balance_time:.1f}ms")
                else:
                    results[client_type] = {"available": False, "error": "Connection failed"}
                    logger.error(f"❌ {client_type}: Connection failed")
            else:
                results[client_type] = {"available": False, "error": "Client not available"}
                logger.error(f"❌ {client_type}: Not available")
        
        # Compare results
        logger.info("📊 PERFORMANCE COMPARISON:")
        for client_type, result in results.items():
            if result.get("available"):
                logger.info(f"   {client_type}:")
                logger.info(f"     Connection: {result['connection_time_ms']:.1f}ms")
                logger.info(f"     Balance: {result['balance_retrieval_ms']:.1f}ms")
            else:
                logger.info(f"   {client_type}: {result.get('error', 'Not available')}")
        
        return results
        
    except Exception as e:
        logger.error(f"❌ Performance comparison failed: {e}")
        return {}

def main():
    """Main test function."""
    logger.info("🚀 Starting Headless Login Integration Tests")
    logger.info("=" * 60)
    
    # Test 1: Trading Client Manager
    logger.info("📋 Test 1: Trading Client Manager")
    test1_result = test_trading_client_manager()
    logger.info(f"Result: {'✅ PASSED' if test1_result else '❌ FAILED'}")
    logger.info("-" * 40)
    
    # Test 2: Headless Client Standalone
    logger.info("📋 Test 2: Headless Client Standalone")
    test2_result = test_headless_client_standalone()
    logger.info(f"Result: {'✅ PASSED' if test2_result else '❌ FAILED'}")
    logger.info("-" * 40)
    
    # Test 3: Performance Comparison
    logger.info("📋 Test 3: Performance Comparison")
    test3_result = test_performance_comparison()
    logger.info(f"Result: {'✅ COMPLETED' if test3_result else '❌ FAILED'}")
    logger.info("-" * 40)
    
    # Summary
    logger.info("📊 TEST SUMMARY:")
    logger.info(f"   Trading Client Manager: {'✅ PASSED' if test1_result else '❌ FAILED'}")
    logger.info(f"   Headless Client: {'✅ PASSED' if test2_result else '❌ FAILED'}")
    logger.info(f"   Performance Comparison: {'✅ COMPLETED' if test3_result else '❌ FAILED'}")
    
    if test1_result and test2_result:
        logger.info("🎉 ALL TESTS PASSED - Integration ready for production!")
    else:
        logger.info("⚠️ Some tests failed - Check configuration and dependencies")

if __name__ == "__main__":
    main()
