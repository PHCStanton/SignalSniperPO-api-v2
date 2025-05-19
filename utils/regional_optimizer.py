#!/usr/bin/env python3
"""
regional_optimizer.py - Optimizes the Pocket Option trading bot for specific regions.

This script analyzes latency to different Pocket Option servers, selects the optimal
server for the specified region (with focus on South Africa/SAST), and updates the
configuration accordingly. It also implements region-specific optimizations for
trading during optimal market hours and handling regional network conditions.
"""

import os
import sys
import json
import time
import asyncio
import statistics
import websockets
import ssl
import argparse
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import pytz

# Add the parent directory to the path so we can import from pocketoptionapi
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import constants from the Pocket Option API
try:
    from pocketoptionapi.constants import WEBSOCKET_URL
except ImportError:
    # Default WebSocket URL if import fails
    WEBSOCKET_URL = "wss://api.pocketoption.com/v2"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("regional_optimizer.log")
    ]
)
logger = logging.getLogger(__name__)

# European server regions to test
REGIONS = {
    "Default": WEBSOCKET_URL,
    "Frankfurt": "wss://eu-fra.api.pocketoption.com/v2",  # Frankfurt, Germany
    "London": "wss://eu-lon.api.pocketoption.com/v2",     # London, UK
    "Paris": "wss://eu-par.api.pocketoption.com/v2",      # Paris, France
    "Amsterdam": "wss://eu-ams.api.pocketoption.com/v2",  # Amsterdam, Netherlands
    "Dublin": "wss://eu-dub.api.pocketoption.com/v2",     # Dublin, Ireland
}

# Default thresholds
DEFAULT_WARNING_THRESHOLD = 200  # ms
DEFAULT_CRITICAL_THRESHOLD = 500  # ms
DEFAULT_TIMEOUT_THRESHOLD = 5000  # ms

# South Africa specific settings
SA_TIMEZONE = "Africa/Johannesburg"
SA_OPTIMAL_TRADING_HOURS = {
    "weekday": [(8, 0, 16, 0)],  # 8:00 AM to 4:00 PM on weekdays
    "weekend": [(10, 0, 14, 0)]  # 10:00 AM to 2:00 PM on weekends
}
SA_NETWORK_PEAK_HOURS = [(18, 0, 22, 0)]  # 6:00 PM to 10:00 PM daily

class RegionalOptimizer:
    def __init__(
        self,
        region: str = "South Africa",
        timezone: str = SA_TIMEZONE,
        config_file: str = "../config/pocket_option_config.json",
        num_tests: int = 10,
        warning_threshold: int = DEFAULT_WARNING_THRESHOLD,
        critical_threshold: int = DEFAULT_CRITICAL_THRESHOLD,
        timeout_threshold: int = DEFAULT_TIMEOUT_THRESHOLD,
        verbose: bool = False
    ):
        """
        Initialize the regional optimizer.
        
        Args:
            region: Region name (default: South Africa)
            timezone: Timezone for the region (default: Africa/Johannesburg)
            config_file: Path to Pocket Option configuration file
            num_tests: Number of latency tests to run per server
            warning_threshold: Latency threshold for warnings in milliseconds
            critical_threshold: Latency threshold for critical alerts in milliseconds
            timeout_threshold: Timeout threshold in milliseconds
            verbose: Enable verbose output
        """
        self.region = region
        self.timezone = timezone
        self.config_file = config_file
        self.num_tests = num_tests
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold
        self.timeout_threshold = timeout_threshold
        self.verbose = verbose
        
        # Set logging level
        if verbose:
            logger.setLevel(logging.DEBUG)
        
        # Latency data
        self.latency_data = {}
        self.best_server = None
        self.best_avg_latency = float('inf')
        
        # Load configuration
        self.config = self._load_config()
    
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
            "email": "",
            "password": "",
            "use_practice_account": True,
            "api": {
                "websocket_url": None,
                "connection_timeout": 30,
                "ping_interval": 30,
                "reconnect_attempts": 3,
                "reconnect_delay": 5
            },
            "trading": {
                "default_asset": "EUR/USD",
                "default_amount": 1,
                "default_expiry": 60,
                "preferred_assets": [
                    "EUR/USD",
                    "GBP/USD",
                    "USD/JPY",
                    "EUR/JPY",
                    "AUD/USD"
                ],
                "excluded_assets": []
            },
            "regional": {
                "preferred_region": "Frankfurt",
                "use_optimal_region": True,
                "latency_threshold": 200,
                "optimal_trading_hours": SA_OPTIMAL_TRADING_HOURS,
                "network_peak_hours": SA_NETWORK_PEAK_HOURS
            },
            "advanced": {
                "time_sync_interval": 300,
                "balance_check_interval": 60,
                "asset_check_interval": 300,
                "trade_history_days": 30,
                "debug_mode": False
            }
        }
    
    def _save_config(self) -> None:
        """Save configuration to file."""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            logger.info(f"Configuration saved to {self.config_file}")
        except Exception as e:
            logger.error(f"Error saving configuration: {str(e)}")
    
    async def test_server_latency(self, server_name: str, websocket_url: str) -> Optional[Dict]:
        """
        Test latency to a specific server.
        
        Args:
            server_name: Server name
            websocket_url: WebSocket URL
            
        Returns:
            Dictionary with latency data if successful, None otherwise
        """
        logger.info(f"Testing latency to {server_name} ({websocket_url})...")
        
        latencies = []
        timeouts = 0
        errors = 0
        
        for i in range(self.num_tests):
            try:
                start_time = time.time()
                
                # Create SSL context with default verification
                ssl_context = ssl.create_default_context()
                
                # Connect to the WebSocket server
                async with websockets.connect(
                    websocket_url, 
                    ssl=ssl_context,
                    close_timeout=5
                ) as websocket:
                    # Send a simple ping message
                    ping_message = json.dumps({"action": "ping", "timestamp": time.time()})
                    await websocket.send(ping_message)
                    
                    # Wait for response with a timeout
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=self.timeout_threshold / 1000)
                        end_time = time.time()
                        latency = (end_time - start_time) * 1000  # Convert to milliseconds
                        latencies.append(latency)
                        
                        if self.verbose:
                            logger.debug(f"Test {i+1}/{self.num_tests} for {server_name}: {latency:.2f}ms")
                    except asyncio.TimeoutError:
                        if self.verbose:
                            logger.debug(f"Test {i+1}/{self.num_tests} for {server_name}: Timeout")
                        timeouts += 1
                        
            except Exception as e:
                if self.verbose:
                    logger.debug(f"Test {i+1}/{self.num_tests} for {server_name}: Error - {str(e)}")
                errors += 1
                
            # Add a small delay between tests
            await asyncio.sleep(0.5)
        
        # Calculate statistics if we have any successful tests
        if latencies:
            avg_latency = statistics.mean(latencies)
            min_latency = min(latencies)
            max_latency = max(latencies)
            median_latency = statistics.median(latencies)
            stdev_latency = statistics.stdev(latencies) if len(latencies) > 1 else 0
            
            result = {
                "server": server_name,
                "url": websocket_url,
                "avg_latency": avg_latency,
                "min_latency": min_latency,
                "max_latency": max_latency,
                "median_latency": median_latency,
                "stdev_latency": stdev_latency,
                "success_rate": (len(latencies) / self.num_tests) * 100,
                "timeouts": timeouts,
                "errors": errors
            }
            
            # Check if this is the best server so far
            if avg_latency < self.best_avg_latency:
                self.best_server = server_name
                self.best_avg_latency = avg_latency
            
            return result
        else:
            # All tests failed
            logger.warning(f"All latency tests to {server_name} failed")
            return None
    
    async def test_all_servers(self) -> Dict[str, Dict]:
        """
        Test latency to all servers.
        
        Returns:
            Dictionary with server names as keys and latency data as values
        """
        logger.info(f"Testing latency to {len(REGIONS)} Pocket Option servers...")
        
        results = {}
        
        for server_name, websocket_url in REGIONS.items():
            result = await self.test_server_latency(server_name, websocket_url)
            if result:
                results[server_name] = result
        
        return results
    
    def update_config_with_best_server(self) -> None:
        """Update configuration with the best server."""
        if not self.best_server:
            logger.warning("No best server found. Configuration not updated.")
            return
        
        logger.info(f"Updating configuration with best server: {self.best_server} ({self.best_avg_latency:.2f}ms)")
        
        # Update configuration
        self.config["regional"]["preferred_region"] = self.best_server
        self.config["api"]["websocket_url"] = REGIONS[self.best_server]
        
        # Save configuration
        self._save_config()
    
    def is_optimal_trading_time(self) -> bool:
        """
        Check if the current time is within optimal trading hours for the region.
        
        Returns:
            True if current time is within optimal trading hours, False otherwise
        """
        now = datetime.now(pytz.timezone(self.timezone))
        is_weekend = now.weekday() >= 5  # 5 = Saturday, 6 = Sunday
        
        # Get optimal trading hours for the current day
        optimal_hours = SA_OPTIMAL_TRADING_HOURS["weekend" if is_weekend else "weekday"]
        
        # Check if current time is within any of the optimal trading periods
        for start_hour, start_minute, end_hour, end_minute in optimal_hours:
            start_time = now.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
            end_time = now.replace(hour=end_hour, minute=end_minute, second=0, microsecond=0)
            
            if start_time <= now <= end_time:
                return True
        
        return False
    
    def is_network_peak_time(self) -> bool:
        """
        Check if the current time is within network peak hours for the region.
        
        Returns:
            True if current time is within network peak hours, False otherwise
        """
        now = datetime.now(pytz.timezone(self.timezone))
        
        # Check if current time is within any of the network peak periods
        for start_hour, start_minute, end_hour, end_minute in SA_NETWORK_PEAK_HOURS:
            start_time = now.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
            end_time = now.replace(hour=end_hour, minute=end_minute, second=0, microsecond=0)
            
            if start_time <= now <= end_time:
                return True
        
        return False
    
    def get_regional_recommendations(self) -> Dict:
        """
        Get region-specific recommendations for trading.
        
        Returns:
            Dictionary with recommendations
        """
        now = datetime.now(pytz.timezone(self.timezone))
        is_weekend = now.weekday() >= 5  # 5 = Saturday, 6 = Sunday
        is_optimal_time = self.is_optimal_trading_time()
        is_peak_time = self.is_network_peak_time()
        
        recommendations = {
            "timestamp": now.isoformat(),
            "region": self.region,
            "timezone": self.timezone,
            "is_weekend": is_weekend,
            "is_optimal_trading_time": is_optimal_time,
            "is_network_peak_time": is_peak_time,
            "best_server": self.best_server,
            "best_server_latency": self.best_avg_latency,
            "recommendations": []
        }
        
        # Add recommendations based on current conditions
        if is_optimal_time:
            recommendations["recommendations"].append({
                "type": "trading_time",
                "message": "Current time is within optimal trading hours for South Africa.",
                "action": "Continue trading normally."
            })
        else:
            recommendations["recommendations"].append({
                "type": "trading_time",
                "message": "Current time is outside optimal trading hours for South Africa.",
                "action": "Consider reducing trade frequency or amount."
            })
        
        if is_peak_time:
            recommendations["recommendations"].append({
                "type": "network_condition",
                "message": "Current time is within network peak hours for South Africa.",
                "action": "Expect higher latency. Consider increasing min_seconds_before_timer setting."
            })
        
        if is_weekend:
            recommendations["recommendations"].append({
                "type": "market_condition",
                "message": "It's currently weekend in South Africa.",
                "action": "Market volatility may be lower. Consider focusing on major currency pairs."
            })
        
        if self.best_avg_latency > self.warning_threshold:
            recommendations["recommendations"].append({
                "type": "latency",
                "message": f"Latency to best server ({self.best_server}) is high: {self.best_avg_latency:.2f}ms.",
                "action": "Consider increasing min_seconds_before_timer setting to compensate for latency."
            })
        
        return recommendations
    
    def print_recommendations(self, recommendations: Dict) -> None:
        """
        Print region-specific recommendations.
        
        Args:
            recommendations: Dictionary with recommendations
        """
        print("\n" + "="*80)
        print(f"REGIONAL OPTIMIZATION RECOMMENDATIONS FOR {recommendations['region'].upper()}")
        print("="*80)
        
        print(f"Timestamp: {recommendations['timestamp']}")
        print(f"Timezone: {recommendations['timezone']}")
        print(f"Weekend: {'Yes' if recommendations['is_weekend'] else 'No'}")
        print(f"Optimal Trading Time: {'Yes' if recommendations['is_optimal_trading_time'] else 'No'}")
        print(f"Network Peak Time: {'Yes' if recommendations['is_network_peak_time'] else 'No'}")
        print(f"Best Server: {recommendations['best_server']} ({recommendations['best_server_latency']:.2f}ms)")
        
        print("\nRecommendations:")
        for i, rec in enumerate(recommendations['recommendations'], 1):
            print(f"{i}. {rec['message']}")
            print(f"   Action: {rec['action']}")
        
        print("="*80)
    
    def save_recommendations(self, recommendations: Dict, output_file: str) -> None:
        """
        Save region-specific recommendations to a file.
        
        Args:
            recommendations: Dictionary with recommendations
            output_file: Output file path
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            
            # Load existing data if file exists
            data = []
            if os.path.exists(output_file):
                with open(output_file, 'r') as f:
                    data = json.load(f)
            
            # Add new recommendations
            data.append(recommendations)
            
            # Save data
            with open(output_file, 'w') as f:
                json.dump(data, f, indent=2)
                
            logger.info(f"Recommendations saved to {output_file}")
        except Exception as e:
            logger.error(f"Error saving recommendations: {str(e)}")
    
    async def optimize(self, output_file: Optional[str] = None) -> Dict:
        """
        Run the regional optimization process.
        
        Args:
            output_file: Output file path for recommendations
            
        Returns:
            Dictionary with optimization results
        """
        # Test latency to all servers
        self.latency_data = await self.test_all_servers()
        
        # Update configuration with best server
        self.update_config_with_best_server()
        
        # Get regional recommendations
        recommendations = self.get_regional_recommendations()
        
        # Print recommendations
        self.print_recommendations(recommendations)
        
        # Save recommendations if output file is specified
        if output_file:
            self.save_recommendations(recommendations, output_file)
        
        return {
            "latency_data": self.latency_data,
            "best_server": self.best_server,
            "best_avg_latency": self.best_avg_latency,
            "recommendations": recommendations
        }

async def main():
    parser = argparse.ArgumentParser(description='Optimize Pocket Option trading bot for specific regions')
    parser.add_argument('-r', '--region', type=str, default="South Africa", help='Region name')
    parser.add_argument('-t', '--timezone', type=str, default=SA_TIMEZONE, help='Timezone for the region')
    parser.add_argument('-c', '--config', type=str, default="../config/pocket_option_config.json", help='Path to Pocket Option configuration file')
    parser.add_argument('-n', '--num-tests', type=int, default=10, help='Number of latency tests to run per server')
    parser.add_argument('-w', '--warning', type=int, default=DEFAULT_WARNING_THRESHOLD, help='Warning threshold in milliseconds')
    parser.add_argument('-C', '--critical', type=int, default=DEFAULT_CRITICAL_THRESHOLD, help='Critical threshold in milliseconds')
    parser.add_argument('-T', '--timeout', type=int, default=DEFAULT_TIMEOUT_THRESHOLD, help='Timeout threshold in milliseconds')
    parser.add_argument('-o', '--output', type=str, help='Output file path for recommendations')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
    
    args = parser.parse_args()
    
    # Create optimizer
    optimizer = RegionalOptimizer(
        region=args.region,
        timezone=args.timezone,
        config_file=args.config,
        num_tests=args.num_tests,
        warning_threshold=args.warning,
        critical_threshold=args.critical,
        timeout_threshold=args.timeout,
        verbose=args.verbose
    )
    
    # Run optimization
    await optimizer.optimize(args.output)

if __name__ == "__main__":
    print("Pocket Option Regional Optimizer")
    print("--------------------------------")
    print("This script optimizes the Pocket Option trading bot for specific regions.")
    print("It focuses on South Africa (SAST) by default.")
    print("")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nOptimization interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError during optimization: {str(e)}")
        sys.exit(1)
