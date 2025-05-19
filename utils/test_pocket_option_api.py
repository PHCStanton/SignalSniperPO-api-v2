#!/usr/bin/env python3
"""
test_pocket_option_api.py - Tests connection and authentication with Pocket Option API.

This script tests the connection to the Pocket Option API, authenticates with the API,
retrieves basic account information, and tests basic trading functionality.
"""

import os
import sys
import json
import time
import asyncio
import logging
import argparse
from datetime import datetime
from typing import Dict, List, Optional, Union, Any

# Add the parent directory to the path so we can import from pocketoptionapi
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from pocketoptionapi.api import PocketOption
except ImportError:
    print("Error: pocketoptionapi package not found or cannot be imported.")
    print("Make sure you're running this script from the correct directory.")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("pocket_option_api_test.log")
    ]
)
logger = logging.getLogger(__name__)

class PocketOptionAPITester:
    def __init__(
        self,
        email: str,
        password: str,
        config_file: str = "pocket_option_config.json",
        verbose: bool = False
    ):
        """
        Initialize the Pocket Option API tester.
        
        Args:
            email: Pocket Option account email
            password: Pocket Option account password
            config_file: Configuration file path
            verbose: Enable verbose logging
        """
        self.email = email
        self.password = password
        self.config_file = config_file
        self.verbose = verbose
        self.api = None
        self.config = self._load_config()
        
        # Set logging level
        if verbose:
            logger.setLevel(logging.DEBUG)
        
    def _load_config(self) -> Dict:
        """Load configuration from file or create default."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.error(f"Error parsing config file: {self.config_file}")
                
        # Default configuration
        return {
            "api": {
                "websocket_url": None,  # Will use default from PocketOption class
                "connection_timeout": 30,
                "ping_interval": 30
            },
            "trading": {
                "default_asset": "EUR/USD",
                "default_amount": 1,  # Minimum trade amount
                "default_expiry": 60,  # 1 minute expiry
                "test_mode": True     # Use practice account
            },
            "tests": {
                "assets_to_check": ["EUR/USD", "GBP/USD", "USD/JPY", "EUR/JPY", "AUD/USD"],
                "run_balance_check": True,
                "run_asset_check": True,
                "run_trade_test": False  # Set to True to test actual trading
            }
        }
    
    def _save_config(self) -> None:
        """Save configuration to file."""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=4)
        logger.info(f"Configuration saved to {self.config_file}")
    
    async def initialize(self) -> bool:
        """
        Initialize the Pocket Option API.
        
        Returns:
            True if initialized successfully, False otherwise
        """
        try:
            logger.info("Initializing Pocket Option API...")
            
            # Create API instance
            self.api = PocketOption(
                email=self.email,
                password=self.password
            )
            
            # Connect to API
            logger.info("Connecting to Pocket Option API...")
            await self.api.connect()
            
            # Check if connected
            if self.api.connected:
                logger.info("Successfully connected to Pocket Option API")
                return True
            else:
                logger.error("Failed to connect to Pocket Option API")
                return False
                
        except Exception as e:
            logger.error(f"Error initializing Pocket Option API: {str(e)}")
            return False
    
    async def authenticate(self) -> bool:
        """
        Authenticate with the Pocket Option API.
        
        Returns:
            True if authenticated successfully, False otherwise
        """
        if not self.api or not self.api.connected:
            logger.error("API not initialized or not connected. Call initialize() first.")
            return False
            
        try:
            logger.info("Authenticating with Pocket Option API...")
            
            # Authenticate
            result = await self.api.login()
            
            if result:
                logger.info("Successfully authenticated with Pocket Option API")
                return True
            else:
                logger.error("Failed to authenticate with Pocket Option API")
                return False
                
        except Exception as e:
            logger.error(f"Error authenticating with Pocket Option API: {str(e)}")
            return False
    
    async def check_balance(self) -> Optional[float]:
        """
        Check account balance.
        
        Returns:
            Account balance if successful, None otherwise
        """
        if not self.api or not self.api.connected:
            logger.error("API not initialized or not connected. Call initialize() first.")
            return None
            
        try:
            logger.info("Checking account balance...")
            
            # Get balance
            balance = await self.api.get_balance()
            
            if balance is not None:
                logger.info(f"Account balance: {balance}")
                return balance
            else:
                logger.error("Failed to get account balance")
                return None
                
        except Exception as e:
            logger.error(f"Error checking account balance: {str(e)}")
            return None
    
    async def check_assets(self) -> Optional[List[Dict]]:
        """
        Check available assets.
        
        Returns:
            List of assets if successful, None otherwise
        """
        if not self.api or not self.api.connected:
            logger.error("API not initialized or not connected. Call initialize() first.")
            return None
            
        try:
            logger.info("Checking available assets...")
            
            # Get assets
            assets = await self.api.get_all_assets()
            
            if assets:
                # Check if specific assets are available
                assets_to_check = self.config["tests"]["assets_to_check"]
                available_assets = []
                
                for asset_name in assets_to_check:
                    asset_available = any(asset["name"] == asset_name for asset in assets)
                    status = "✅ Available" if asset_available else "❌ Not available"
                    logger.info(f"Asset {asset_name}: {status}")
                    
                    if asset_available:
                        asset_data = next(asset for asset in assets if asset["name"] == asset_name)
                        available_assets.append(asset_data)
                
                logger.info(f"Found {len(assets)} total assets, {len(available_assets)} requested assets available")
                return available_assets
            else:
                logger.error("Failed to get assets")
                return None
                
        except Exception as e:
            logger.error(f"Error checking assets: {str(e)}")
            return None
    
    async def test_trade(self, asset: str, amount: float, direction: str, expiry: int) -> bool:
        """
        Test trading functionality.
        
        Args:
            asset: Asset to trade
            amount: Trade amount
            direction: Trade direction ('call' for UP/HIGHER or 'put' for DOWN/LOWER)
            expiry: Expiry time in seconds
            
        Returns:
            True if trade executed successfully, False otherwise
        """
        if not self.api or not self.api.connected:
            logger.error("API not initialized or not connected. Call initialize() first.")
            return False
            
        try:
            logger.info(f"Testing trade: {asset} {direction.upper()} {amount} (expiry: {expiry}s)")
            
            # Execute trade
            result = await self.api.buy(
                price=amount,
                asset=asset,
                direction=direction,
                expired=expiry
            )
            
            if result and "id" in result:
                logger.info(f"Trade executed successfully: ID {result['id']}")
                
                # Wait for trade to complete
                logger.info(f"Waiting {expiry} seconds for trade to complete...")
                await asyncio.sleep(expiry + 2)  # Add 2 seconds buffer
                
                # Check trade result
                # Note: In a real implementation, we would check the trade result
                # For this test, we just log that we would check it
                logger.info("Trade completed. In a real implementation, we would check the result.")
                
                return True
            else:
                logger.error(f"Failed to execute trade: {result}")
                return False
                
        except Exception as e:
            logger.error(f"Error testing trade: {str(e)}")
            return False
    
    async def run_tests(self) -> Dict[str, bool]:
        """
        Run all tests.
        
        Returns:
            Dictionary with test results
        """
        results = {
            "connection": False,
            "authentication": False,
            "balance_check": False,
            "asset_check": False,
            "trade_test": False
        }
        
        # Initialize and connect
        results["connection"] = await self.initialize()
        if not results["connection"]:
            logger.error("Connection test failed. Aborting remaining tests.")
            return results
            
        # Authenticate
        results["authentication"] = await self.authenticate()
        if not results["authentication"]:
            logger.error("Authentication test failed. Aborting remaining tests.")
            return results
            
        # Check balance
        if self.config["tests"]["run_balance_check"]:
            balance = await self.check_balance()
            results["balance_check"] = balance is not None
        else:
            logger.info("Skipping balance check test")
            
        # Check assets
        if self.config["tests"]["run_asset_check"]:
            assets = await self.check_assets()
            results["asset_check"] = assets is not None and len(assets) > 0
        else:
            logger.info("Skipping asset check test")
            
        # Test trade
        if self.config["tests"]["run_trade_test"]:
            # Use default values from config
            asset = self.config["trading"]["default_asset"]
            amount = self.config["trading"]["default_amount"]
            expiry = self.config["trading"]["default_expiry"]
            
            # Execute a test trade (call/HIGHER)
            results["trade_test"] = await self.test_trade(
                asset=asset,
                amount=amount,
                direction="call",  # 'call' for UP/HIGHER
                expiry=expiry
            )
        else:
            logger.info("Skipping trade test")
            
        return results
    
    async def close(self) -> None:
        """Close the Pocket Option API connection."""
        if self.api and self.api.connected:
            await self.api.close()
            logger.info("Pocket Option API connection closed")

async def main():
    parser = argparse.ArgumentParser(description='Test Pocket Option API connection and functionality')
    parser.add_argument('--email', type=str, help='Pocket Option account email')
    parser.add_argument('--password', type=str, help='Pocket Option account password')
    parser.add_argument('--config', type=str, default='pocket_option_config.json', help='Configuration file path')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    parser.add_argument('--test-trade', action='store_true', help='Test trading functionality')
    
    args = parser.parse_args()
    
    # Check for required arguments
    if not args.email or not args.password:
        # Try to load from environment variables
        email = os.environ.get('POCKET_OPTION_EMAIL')
        password = os.environ.get('POCKET_OPTION_PASSWORD')
        
        if not email or not password:
            parser.error("Email and password are required. Provide them as arguments or set POCKET_OPTION_EMAIL and POCKET_OPTION_PASSWORD environment variables.")
    else:
        email = args.email
        password = args.password
    
    # Create tester
    tester = PocketOptionAPITester(
        email=email,
        password=password,
        config_file=args.config,
        verbose=args.verbose
    )
    
    # Update config if test-trade flag is set
    if args.test_trade:
        tester.config["tests"]["run_trade_test"] = True
    
    try:
        # Run tests
        results = await tester.run_tests()
        
        # Print results
        print("\n" + "="*50)
        print("POCKET OPTION API TEST RESULTS")
        print("="*50)
        
        for test_name, result in results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{test_name.replace('_', ' ').title()}: {status}")
            
        print("="*50)
        
        # Overall result
        if all(results.values()):
            print("\n✅ All tests passed successfully!")
        else:
            print("\n❌ Some tests failed. Check the log for details.")
            
    except Exception as e:
        logger.error(f"Error during tests: {str(e)}")
    finally:
        # Close connection
        await tester.close()

if __name__ == "__main__":
    print("Pocket Option API Tester")
    print("------------------------")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nTests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError during tests: {str(e)}")
        sys.exit(1)
