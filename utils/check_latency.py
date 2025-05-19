#!/usr/bin/env python3
"""
check_latency.py - Continuously monitors latency to Pocket Option servers.

This script continuously monitors the latency to Pocket Option WebSocket servers
and reports any issues. It can be used to ensure optimal performance for the trading bot.
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
        logging.FileHandler("latency_monitor.log")
    ]
)
logger = logging.getLogger(__name__)

# Default regions to monitor
DEFAULT_REGIONS = {
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

class LatencyMonitor:
    def __init__(
        self,
        regions: Optional[Dict[str, str]] = None,
        interval: int = 60,
        warning_threshold: int = DEFAULT_WARNING_THRESHOLD,
        critical_threshold: int = DEFAULT_CRITICAL_THRESHOLD,
        timeout_threshold: int = DEFAULT_TIMEOUT_THRESHOLD,
        report_interval: int = 3600,
        output_file: Optional[str] = None,
        verbose: bool = False
    ):
        """
        Initialize the latency monitor.
        
        Args:
            regions: Dictionary of region names to WebSocket URLs
            interval: Interval between latency checks in seconds
            warning_threshold: Latency threshold for warnings in milliseconds
            critical_threshold: Latency threshold for critical alerts in milliseconds
            timeout_threshold: Timeout threshold in milliseconds
            report_interval: Interval between summary reports in seconds
            output_file: File to write latency data to (optional)
            verbose: Enable verbose output
        """
        self.regions = regions or DEFAULT_REGIONS
        self.interval = interval
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold
        self.timeout_threshold = timeout_threshold
        self.report_interval = report_interval
        self.output_file = output_file
        self.verbose = verbose
        
        # Set logging level
        if verbose:
            logger.setLevel(logging.DEBUG)
        
        # Latency tracking
        self.latency_data = {}
        self.last_report_time = datetime.now()
        
        # Initialize latency data
        for region in self.regions:
            self.latency_data[region] = {
                "latencies": [],
                "timeouts": 0,
                "errors": 0,
                "last_latency": None,
                "last_check_time": None
            }
    
    async def check_latency(self, region: str, url: str) -> Optional[float]:
        """
        Check latency to a specific region's WebSocket server.
        
        Args:
            region: Region name
            url: WebSocket URL
            
        Returns:
            Latency in milliseconds if successful, None otherwise
        """
        try:
            start_time = time.time()
            
            # Create SSL context with default verification
            ssl_context = ssl.create_default_context()
            
            # Connect to the WebSocket server with a timeout
            async with websockets.connect(
                url, 
                ssl=ssl_context,
                close_timeout=self.timeout_threshold / 1000,  # Convert to seconds
                ping_interval=None,  # Disable automatic pings
                ping_timeout=None    # Disable automatic pings
            ) as websocket:
                # Send a simple ping message
                ping_message = json.dumps({"action": "ping", "timestamp": time.time()})
                await websocket.send(ping_message)
                
                # Wait for response with a timeout
                try:
                    response = await asyncio.wait_for(
                        websocket.recv(), 
                        timeout=self.timeout_threshold / 1000  # Convert to seconds
                    )
                    end_time = time.time()
                    latency = (end_time - start_time) * 1000  # Convert to milliseconds
                    
                    logger.debug(f"Latency to {region}: {latency:.2f}ms")
                    return latency
                except asyncio.TimeoutError:
                    logger.warning(f"Timeout when checking latency to {region}")
                    self.latency_data[region]["timeouts"] += 1
                    return None
                
        except Exception as e:
            logger.error(f"Error checking latency to {region}: {str(e)}")
            self.latency_data[region]["errors"] += 1
            return None
    
    def update_latency_data(self, region: str, latency: Optional[float]) -> None:
        """
        Update latency data for a region.
        
        Args:
            region: Region name
            latency: Latency in milliseconds
        """
        self.latency_data[region]["last_check_time"] = datetime.now()
        
        if latency is not None:
            self.latency_data[region]["latencies"].append(latency)
            self.latency_data[region]["last_latency"] = latency
            
            # Check thresholds
            if latency > self.critical_threshold:
                logger.critical(f"Critical latency to {region}: {latency:.2f}ms (threshold: {self.critical_threshold}ms)")
            elif latency > self.warning_threshold:
                logger.warning(f"High latency to {region}: {latency:.2f}ms (threshold: {self.warning_threshold}ms)")
    
    def generate_report(self) -> Dict[str, Any]:
        """
        Generate a summary report of latency data.
        
        Returns:
            Dictionary with report data
        """
        report = {
            "timestamp": datetime.now().isoformat(),
            "regions": {}
        }
        
        # Find the best region
        best_region = None
        best_avg_latency = float('inf')
        
        for region, data in self.latency_data.items():
            latencies = data["latencies"]
            
            if not latencies:
                avg_latency = float('inf')
                min_latency = float('inf')
                max_latency = float('inf')
                median_latency = float('inf')
                stdev_latency = float('inf')
            else:
                avg_latency = statistics.mean(latencies)
                min_latency = min(latencies)
                max_latency = max(latencies)
                median_latency = statistics.median(latencies)
                stdev_latency = statistics.stdev(latencies) if len(latencies) > 1 else 0
            
            # Check if this is the best region
            if avg_latency < best_avg_latency and avg_latency != float('inf'):
                best_region = region
                best_avg_latency = avg_latency
            
            # Add region data to report
            report["regions"][region] = {
                "avg_latency": avg_latency,
                "min_latency": min_latency,
                "max_latency": max_latency,
                "median_latency": median_latency,
                "stdev_latency": stdev_latency,
                "timeouts": data["timeouts"],
                "errors": data["errors"],
                "checks": len(latencies) + data["timeouts"] + data["errors"],
                "success_rate": len(latencies) / (len(latencies) + data["timeouts"] + data["errors"]) * 100 if (len(latencies) + data["timeouts"] + data["errors"]) > 0 else 0
            }
        
        # Add best region to report
        report["best_region"] = best_region
        report["best_avg_latency"] = best_avg_latency
        
        return report
    
    def print_report(self, report: Dict[str, Any]) -> None:
        """
        Print a summary report of latency data.
        
        Args:
            report: Report data
        """
        print("\n" + "="*100)
        print(f"LATENCY MONITORING REPORT - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*100)
        
        # Print table header
        header = f"{'Region':<12} | {'Success':<8} | {'Avg (ms)':<10} | {'Min (ms)':<10} | {'Max (ms)':<10} | {'Median (ms)':<12} | {'StdDev':<8} | {'Timeouts':<8} | {'Errors':<6}"
        print(header)
        print("-"*100)
        
        # Sort regions by average latency
        sorted_regions = sorted(
            report["regions"].items(),
            key=lambda x: (
                # First sort by success rate (higher is better)
                -x[1]["success_rate"],
                # Then by average latency (lower is better)
                x[1]["avg_latency"] if x[1]["avg_latency"] != float('inf') else sys.float_info.max
            )
        )
        
        # Print each region
        for region, data in sorted_regions:
            if data["avg_latency"] == float('inf'):
                row = f"{region:<12} | {data['success_rate']:>7.1f}% | {'TIMEOUT':<10} | {'TIMEOUT':<10} | {'TIMEOUT':<10} | {'TIMEOUT':<12} | {'N/A':<8} | {data['timeouts']:<8} | {data['errors']:<6}"
            else:
                row = f"{region:<12} | {data['success_rate']:>7.1f}% | {data['avg_latency']:>9.2f} | {data['min_latency']:>9.2f} | {data['max_latency']:>9.2f} | {data['median_latency']:>11.2f} | {data['stdev_latency']:>7.2f} | {data['timeouts']:<8} | {data['errors']:<6}"
            print(row)
        
        print("-"*100)
        
        # Print best region
        if report["best_region"]:
            print(f"\nBest region: {report['best_region']} (Average latency: {report['best_avg_latency']:.2f}ms)")
        else:
            print("\nNo best region found. All regions may be experiencing issues.")
        
        print("="*100)
    
    def save_report(self, report: Dict[str, Any]) -> None:
        """
        Save a report to file.
        
        Args:
            report: Report data
        """
        if not self.output_file:
            return
            
        try:
            # Load existing data if file exists
            data = []
            if os.path.exists(self.output_file):
                with open(self.output_file, 'r') as f:
                    data = json.load(f)
            
            # Add new report
            data.append(report)
            
            # Save data
            with open(self.output_file, 'w') as f:
                json.dump(data, f, indent=2)
                
            logger.info(f"Report saved to {self.output_file}")
        except Exception as e:
            logger.error(f"Error saving report to {self.output_file}: {str(e)}")
    
    def reset_latency_data(self) -> None:
        """Reset latency data for all regions."""
        for region in self.regions:
            self.latency_data[region]["latencies"] = []
            self.latency_data[region]["timeouts"] = 0
            self.latency_data[region]["errors"] = 0
    
    async def monitor_latency(self, duration: Optional[int] = None) -> None:
        """
        Monitor latency to all regions.
        
        Args:
            duration: Duration to monitor in seconds (None for indefinite)
        """
        logger.info(f"Starting latency monitoring for {len(self.regions)} regions...")
        logger.info(f"Checking latency every {self.interval} seconds")
        logger.info(f"Warning threshold: {self.warning_threshold}ms")
        logger.info(f"Critical threshold: {self.critical_threshold}ms")
        logger.info(f"Timeout threshold: {self.timeout_threshold}ms")
        logger.info(f"Generating reports every {self.report_interval} seconds")
        
        start_time = datetime.now()
        end_time = start_time + timedelta(seconds=duration) if duration else None
        
        try:
            while True:
                # Check if monitoring duration has elapsed
                if end_time and datetime.now() >= end_time:
                    logger.info(f"Monitoring duration of {duration} seconds has elapsed")
                    break
                
                # Check latency for each region
                for region, url in self.regions.items():
                    latency = await self.check_latency(region, url)
                    self.update_latency_data(region, latency)
                
                # Check if it's time to generate a report
                if (datetime.now() - self.last_report_time).total_seconds() >= self.report_interval:
                    report = self.generate_report()
                    self.print_report(report)
                    self.save_report(report)
                    self.reset_latency_data()
                    self.last_report_time = datetime.now()
                
                # Wait for the next check
                await asyncio.sleep(self.interval)
                
        except KeyboardInterrupt:
            logger.info("Latency monitoring interrupted by user")
        except Exception as e:
            logger.error(f"Error during latency monitoring: {str(e)}")
        finally:
            # Generate final report
            report = self.generate_report()
            self.print_report(report)
            self.save_report(report)
            
            logger.info("Latency monitoring stopped")

async def main():
    parser = argparse.ArgumentParser(description='Monitor latency to Pocket Option servers')
    parser.add_argument('-i', '--interval', type=int, default=60, help='Interval between latency checks in seconds')
    parser.add_argument('-d', '--duration', type=int, help='Duration to monitor in seconds (default: indefinite)')
    parser.add_argument('-w', '--warning', type=int, default=DEFAULT_WARNING_THRESHOLD, help=f'Warning threshold in milliseconds (default: {DEFAULT_WARNING_THRESHOLD})')
    parser.add_argument('-c', '--critical', type=int, default=DEFAULT_CRITICAL_THRESHOLD, help=f'Critical threshold in milliseconds (default: {DEFAULT_CRITICAL_THRESHOLD})')
    parser.add_argument('-t', '--timeout', type=int, default=DEFAULT_TIMEOUT_THRESHOLD, help=f'Timeout threshold in milliseconds (default: {DEFAULT_TIMEOUT_THRESHOLD})')
    parser.add_argument('-r', '--report', type=int, default=3600, help='Interval between summary reports in seconds (default: 3600)')
    parser.add_argument('-o', '--output', type=str, help='File to write latency data to')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
    
    args = parser.parse_args()
    
    # Create monitor
    monitor = LatencyMonitor(
        interval=args.interval,
        warning_threshold=args.warning,
        critical_threshold=args.critical,
        timeout_threshold=args.timeout,
        report_interval=args.report,
        output_file=args.output,
        verbose=args.verbose
    )
    
    # Start monitoring
    await monitor.monitor_latency(args.duration)

if __name__ == "__main__":
    print("Pocket Option Latency Monitor")
    print("----------------------------")
    print("This script continuously monitors latency to Pocket Option servers.")
    print("Press Ctrl+C to stop monitoring.")
    print("")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nLatency monitoring interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError during latency monitoring: {str(e)}")
        sys.exit(1)
