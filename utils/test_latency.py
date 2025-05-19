#!/usr/bin/env python3
"""
test_latency.py - Tests latency to Pocket Option servers from different regions.

This script measures the latency to Pocket Option WebSocket servers from the current
location to identify the optimal region for deployment, particularly for South Africa (SAST).
"""

import asyncio
import time
import statistics
import websockets
import ssl
import json
import argparse
from datetime import datetime
import sys
import os

# Add the parent directory to the path so we can import from pocketoptionapi
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import constants from the Pocket Option API
try:
    from pocketoptionapi.constants import WEBSOCKET_URL
except ImportError:
    # Default WebSocket URL if import fails
    WEBSOCKET_URL = "wss://api.pocketoption.com/v2"

# European server regions to test
REGIONS = {
    "Default": WEBSOCKET_URL,
    "Frankfurt": "wss://eu-fra.api.pocketoption.com/v2",  # Frankfurt, Germany
    "London": "wss://eu-lon.api.pocketoption.com/v2",     # London, UK
    "Paris": "wss://eu-par.api.pocketoption.com/v2",      # Paris, France
    "Amsterdam": "wss://eu-ams.api.pocketoption.com/v2",  # Amsterdam, Netherlands
    "Dublin": "wss://eu-dub.api.pocketoption.com/v2",     # Dublin, Ireland
}

# Number of ping tests to run per region
DEFAULT_NUM_TESTS = 10

class LatencyTester:
    def __init__(self, num_tests=DEFAULT_NUM_TESTS, verbose=False):
        self.num_tests = num_tests
        self.verbose = verbose
        self.results = {}
        
    async def test_region_latency(self, region_name, websocket_url):
        """Test the latency to a specific region's WebSocket server."""
        latencies = []
        connection_errors = 0
        
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
                        response = await asyncio.wait_for(websocket.recv(), timeout=5)
                        end_time = time.time()
                        latency = (end_time - start_time) * 1000  # Convert to milliseconds
                        latencies.append(latency)
                        
                        if self.verbose:
                            print(f"  Test {i+1}/{self.num_tests} for {region_name}: {latency:.2f}ms")
                    except asyncio.TimeoutError:
                        if self.verbose:
                            print(f"  Test {i+1}/{self.num_tests} for {region_name}: Timeout")
                        connection_errors += 1
                        
            except Exception as e:
                if self.verbose:
                    print(f"  Test {i+1}/{self.num_tests} for {region_name}: Error - {str(e)}")
                connection_errors += 1
                
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
                "region": region_name,
                "url": websocket_url,
                "avg_latency": avg_latency,
                "min_latency": min_latency,
                "max_latency": max_latency,
                "median_latency": median_latency,
                "stdev_latency": stdev_latency,
                "success_rate": (len(latencies) / self.num_tests) * 100,
                "connection_errors": connection_errors
            }
        else:
            # All tests failed
            result = {
                "region": region_name,
                "url": websocket_url,
                "avg_latency": float('inf'),
                "min_latency": float('inf'),
                "max_latency": float('inf'),
                "median_latency": float('inf'),
                "stdev_latency": float('inf'),
                "success_rate": 0,
                "connection_errors": connection_errors
            }
            
        self.results[region_name] = result
        return result
    
    async def test_all_regions(self):
        """Test latency to all defined regions."""
        print(f"Starting latency tests to {len(REGIONS)} Pocket Option server regions...")
        print(f"Running {self.num_tests} tests per region...\n")
        
        for region_name, websocket_url in REGIONS.items():
            print(f"Testing region: {region_name} ({websocket_url})")
            await self.test_region_latency(region_name, websocket_url)
            print(f"Completed testing for {region_name}\n")
            
        return self.results
    
    def print_results(self):
        """Print the latency test results in a formatted table."""
        if not self.results:
            print("No results to display. Run tests first.")
            return
        
        # Sort results by average latency
        sorted_results = sorted(
            self.results.values(), 
            key=lambda x: (
                # First sort by success rate (higher is better)
                -x["success_rate"],
                # Then by average latency (lower is better)
                x["avg_latency"] if x["avg_latency"] != float('inf') else sys.float_info.max
            )
        )
        
        # Print header
        print("\n" + "="*100)
        print(f"LATENCY TEST RESULTS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (SAST)")
        print("="*100)
        
        # Print table header
        header = f"{'Region':<12} | {'Success':<8} | {'Avg (ms)':<10} | {'Min (ms)':<10} | {'Max (ms)':<10} | {'Median (ms)':<12} | {'StdDev':<8} | {'Errors':<6}"
        print(header)
        print("-"*100)
        
        # Print each result row
        for result in sorted_results:
            if result["avg_latency"] == float('inf'):
                row = f"{result['region']:<12} | {result['success_rate']:>7.1f}% | {'TIMEOUT':<10} | {'TIMEOUT':<10} | {'TIMEOUT':<10} | {'TIMEOUT':<12} | {'N/A':<8} | {result['connection_errors']:<6}"
            else:
                row = f"{result['region']:<12} | {result['success_rate']:>7.1f}% | {result['avg_latency']:>9.2f} | {result['min_latency']:>9.2f} | {result['max_latency']:>9.2f} | {result['median_latency']:>11.2f} | {result['stdev_latency']:>7.2f} | {result['connection_errors']:<6}"
            print(row)
        
        print("-"*100)
        
        # Print recommendation
        best_region = sorted_results[0]['region']
        if sorted_results[0]["avg_latency"] == float('inf'):
            print("\nRECOMMENDATION: All regions failed to connect. Please check your internet connection and try again.")
        else:
            print(f"\nRECOMMENDATION: The optimal region for South Africa (SAST) appears to be {best_region}")
            print(f"                WebSocket URL: {sorted_results[0]['url']}")
            print(f"                Average Latency: {sorted_results[0]['avg_latency']:.2f}ms")
            print(f"                Success Rate: {sorted_results[0]['success_rate']:.1f}%")
        
        print("="*100)
        print("Note: Lower latency is better for executing time-sensitive trades.")
        print("      For optimal performance, deploy your EC2 instance in the recommended region.")
        print("="*100 + "\n")

async def main():
    parser = argparse.ArgumentParser(description='Test latency to Pocket Option servers from different regions.')
    parser.add_argument('-n', '--num-tests', type=int, default=DEFAULT_NUM_TESTS,
                        help=f'Number of tests to run per region (default: {DEFAULT_NUM_TESTS})')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Enable verbose output')
    args = parser.parse_args()
    
    tester = LatencyTester(num_tests=args.num_tests, verbose=args.verbose)
    await tester.test_all_regions()
    tester.print_results()

if __name__ == "__main__":
    print("Pocket Option Latency Tester")
    print("----------------------------")
    print("Testing latency from South Africa (SAST) to Pocket Option servers...")
    print("This will help determine the optimal region for EC2 deployment.\n")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nLatency test interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nError during latency test: {str(e)}")
        sys.exit(1)
