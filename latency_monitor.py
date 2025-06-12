import asyncio
import time
import json
import statistics
from datetime import datetime
from typing import List, Dict

from BinaryOptionsToolsV2.pocketoption.asyncronous import PocketOptionAsync

class LatencyMonitor:
    def __init__(self, ssid: str):
        self.ssid = ssid
        self.client = None
        self.latency_data = []
        
    async def initialize(self):
        """Initialize the PocketOption client"""
        self.client = PocketOptionAsync(self.ssid)
        
    async def measure_balance_latency(self) -> float:
        """Measure latency using balance request"""
        start_time = time.perf_counter()
        try:
            await self.client.balance()
            end_time = time.perf_counter()
            return (end_time - start_time) * 1000  # Convert to milliseconds
        except Exception as e:
            print(f"Balance request failed: {e}")
            return -1
            
    async def measure_payout_latency(self) -> float:
        """Measure latency using payout request"""
        start_time = time.perf_counter()
        try:
            await self.client.payout()
            end_time = time.perf_counter()
            return (end_time - start_time) * 1000  # Convert to milliseconds
        except Exception as e:
            print(f"Payout request failed: {e}")
            return -1
            
    async def measure_candles_latency(self, asset: str = "EURUSD_otc") -> float:
        """Measure latency using candles request"""
        start_time = time.perf_counter()
        try:
            await self.client.get_candles(asset, 60, 10)  # 1-minute candles, 10 periods
            end_time = time.perf_counter()
            return (end_time - start_time) * 1000  # Convert to milliseconds
        except Exception as e:
            print(f"Candles request failed: {e}")
            return -1
            
    async def run_comprehensive_test(self, iterations: int = 10) -> Dict:
        """Run comprehensive latency tests"""
        print(f"Starting comprehensive latency test with {iterations} iterations...")
        print("=" * 60)
        
        balance_latencies = []
        payout_latencies = []
        candles_latencies = []
        
        for i in range(iterations):
            print(f"Iteration {i+1}/{iterations}")
            
            # Test balance latency
            balance_lat = await self.measure_balance_latency()
            if balance_lat > 0:
                balance_latencies.append(balance_lat)
                print(f"  Balance latency: {balance_lat:.2f} ms")
            
            # Test payout latency
            payout_lat = await self.measure_payout_latency()
            if payout_lat > 0:
                payout_latencies.append(payout_lat)
                print(f"  Payout latency: {payout_lat:.2f} ms")
            
            # Test candles latency
            candles_lat = await self.measure_candles_latency()
            if candles_lat > 0:
                candles_latencies.append(candles_lat)
                print(f"  Candles latency: {candles_lat:.2f} ms")
            
            # Wait between iterations
            if i < iterations - 1:
                await asyncio.sleep(1)
            print()
        
        # Calculate statistics
        results = {
            "timestamp": datetime.now().isoformat(),
            "iterations": iterations,
            "balance": self._calculate_stats(balance_latencies, "Balance"),
            "payout": self._calculate_stats(payout_latencies, "Payout"),
            "candles": self._calculate_stats(candles_latencies, "Candles")
        }
        
        return results
    
    def _calculate_stats(self, latencies: List[float], operation: str) -> Dict:
        """Calculate statistics for latency measurements"""
        if not latencies:
            return {"error": f"No successful {operation} measurements"}
        
        stats = {
            "count": len(latencies),
            "min": min(latencies),
            "max": max(latencies),
            "mean": statistics.mean(latencies),
            "median": statistics.median(latencies),
            "std_dev": statistics.stdev(latencies) if len(latencies) > 1 else 0
        }
        
        return stats
    
    def print_results(self, results: Dict):
        """Print formatted results"""
        print("=" * 60)
        print("LATENCY TEST RESULTS")
        print("=" * 60)
        print(f"Test completed at: {results['timestamp']}")
        print(f"Total iterations: {results['iterations']}")
        print()
        
        for operation, stats in results.items():
            if operation in ["timestamp", "iterations"]:
                continue
                
            print(f"{operation.upper()} LATENCY:")
            if "error" in stats:
                print(f"  {stats['error']}")
            else:
                print(f"  Successful measurements: {stats['count']}")
                print(f"  Minimum: {stats['min']:.2f} ms")
                print(f"  Maximum: {stats['max']:.2f} ms")
                print(f"  Average: {stats['mean']:.2f} ms")
                print(f"  Median: {stats['median']:.2f} ms")
                print(f"  Std Deviation: {stats['std_dev']:.2f} ms")
            print()
    
    async def continuous_monitoring(self, duration_minutes: int = 5):
        """Run continuous latency monitoring"""
        print(f"Starting continuous monitoring for {duration_minutes} minutes...")
        print("Press Ctrl+C to stop early")
        print("=" * 60)
        
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        
        measurements = []
        
        try:
            while time.time() < end_time:
                timestamp = datetime.now()
                
                # Quick balance check for latency
                latency = await self.measure_balance_latency()
                
                if latency > 0:
                    measurements.append({
                        "timestamp": timestamp.isoformat(),
                        "latency": latency
                    })
                    print(f"{timestamp.strftime('%H:%M:%S')} - Latency: {latency:.2f} ms")
                
                await asyncio.sleep(10)  # Check every 10 seconds
                
        except KeyboardInterrupt:
            print("\nMonitoring stopped by user")
        
        # Save results
        if measurements:
            with open(f"latency_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w") as f:
                json.dump(measurements, f, indent=2)
            
            latencies = [m["latency"] for m in measurements]
            print(f"\nContinuous monitoring results:")
            print(f"Total measurements: {len(latencies)}")
            print(f"Average latency: {statistics.mean(latencies):.2f} ms")
            print(f"Min latency: {min(latencies):.2f} ms")
            print(f"Max latency: {max(latencies):.2f} ms")

async def main():
    """Main function to run latency tests"""
    try:
        # Load configuration
        with open("config/pocket_option_config.json", "r") as f:
            config = json.load(f)
        ssid = config.get("ssid")

        if not ssid:
            print("SSID not found in config/pocket_option_config.json")
            return

        # Initialize monitor
        monitor = LatencyMonitor(ssid)
        await monitor.initialize()
        
        print("Pocket Option Latency Monitor")
        print("=" * 60)
        print("1. Quick Test (5 iterations)")
        print("2. Comprehensive Test (20 iterations)")
        print("3. Continuous Monitoring (5 minutes)")
        print("4. Custom Test")
        
        choice = input("\nSelect test type (1-4): ").strip()
        
        if choice == "1":
            results = await monitor.run_comprehensive_test(5)
            monitor.print_results(results)
            
        elif choice == "2":
            results = await monitor.run_comprehensive_test(20)
            monitor.print_results(results)
            
        elif choice == "3":
            await monitor.continuous_monitoring(5)
            
        elif choice == "4":
            iterations = int(input("Enter number of iterations: "))
            results = await monitor.run_comprehensive_test(iterations)
            monitor.print_results(results)
            
        else:
            print("Invalid choice. Running quick test...")
            results = await monitor.run_comprehensive_test(5)
            monitor.print_results(results)

    except FileNotFoundError:
        print("Error: config/pocket_option_config.json not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())
