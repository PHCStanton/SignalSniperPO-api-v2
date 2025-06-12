import asyncio
import time
import json
import statistics
from datetime import datetime, timedelta
from typing import List, Dict, Tuple

from BinaryOptionsToolsV2.pocketoption.asyncronous import PocketOptionAsync

class TradingLatencyAnalyzer:
    def __init__(self, ssid: str):
        self.ssid = ssid
        self.client = None
        self.trade_latencies = []
        
    async def initialize(self):
        """Initialize the PocketOption client"""
        self.client = PocketOptionAsync(self.ssid)
        print("✅ Connected to Pocket Option")
        
        # Get current balance
        try:
            balance = await self.client.balance()
            print(f"💰 Current Balance: ${balance:.2f}")
        except Exception as e:
            print(f"⚠️  Could not fetch balance: {e}")
        
    async def measure_trade_execution_latency(self, asset: str = "EURUSD_otc", amount: float = 1.0) -> Dict:
        """Measure the complete trade execution latency"""
        print(f"\n🎯 Testing trade execution latency for {asset}")
        
        # Step 1: Get payout information
        payout_start = time.perf_counter()
        payout_info = await self.client.payout(asset)
        payout_time = (time.perf_counter() - payout_start) * 1000
        
        print(f"📈 Payout for {asset}: {payout_info}%")
        print(f"⏱️  Payout fetch time: {payout_time:.2f} ms")
        
        # Step 2: Simulate trade placement (buy order)
        trade_start = time.perf_counter()
        try:
            trade_id, trade_details = await self.client.buy(asset, amount, 60, check_win=False)
            trade_time = (time.perf_counter() - trade_start) * 1000
            
            print(f"✅ Trade placed successfully")
            print(f"🆔 Trade ID: {trade_id}")
            print(f"⏱️  Trade execution time: {trade_time:.2f} ms")
            
            return {
                "success": True,
                "trade_id": trade_id,
                "payout_latency": payout_time,
                "trade_latency": trade_time,
                "total_latency": payout_time + trade_time,
                "trade_details": trade_details
            }
            
        except Exception as e:
            trade_time = (time.perf_counter() - trade_start) * 1000
            print(f"❌ Trade failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "payout_latency": payout_time,
                "trade_latency": trade_time,
                "total_latency": payout_time + trade_time
            }
    
    async def analyze_signal_to_trade_latency(self, iterations: int = 5) -> Dict:
        """Analyze the complete signal-to-trade execution pipeline"""
        print(f"\n🔍 Analyzing Signal-to-Trade Latency Pipeline")
        print(f"📊 Running {iterations} iterations...")
        print("=" * 60)
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "iterations": iterations,
            "successful_trades": 0,
            "failed_trades": 0,
            "latencies": {
                "payout_fetch": [],
                "trade_execution": [],
                "total_pipeline": []
            },
            "trade_details": []
        }
        
        for i in range(iterations):
            print(f"\n📍 Iteration {i+1}/{iterations}")
            
            # Simulate signal reception time
            signal_time = time.perf_counter()
            
            # Measure complete trade execution
            trade_result = await self.measure_trade_execution_latency()
            
            if trade_result["success"]:
                results["successful_trades"] += 1
                results["latencies"]["payout_fetch"].append(trade_result["payout_latency"])
                results["latencies"]["trade_execution"].append(trade_result["trade_latency"])
                results["latencies"]["total_pipeline"].append(trade_result["total_latency"])
                results["trade_details"].append(trade_result["trade_details"])
            else:
                results["failed_trades"] += 1
            
            # Wait between iterations to avoid rate limiting
            if i < iterations - 1:
                print("⏳ Waiting 3 seconds before next iteration...")
                await asyncio.sleep(3)
        
        return results
    
    async def test_1_minute_signal_optimization(self) -> Dict:
        """Test optimization for 1-minute trading signals"""
        print("\n🚀 1-MINUTE SIGNAL OPTIMIZATION TEST")
        print("=" * 60)
        
        # Test different assets for latency comparison
        assets = ["EURUSD_otc", "GBPUSD_otc", "USDJPY_otc"]
        asset_results = {}
        
        for asset in assets:
            print(f"\n🎯 Testing {asset}")
            
            # Quick latency test for this asset
            start_time = time.perf_counter()
            
            try:
                # Get payout
                payout = await self.client.payout(asset)
                payout_time = time.perf_counter()
                
                # Get recent candles
                candles = await self.client.get_candles(asset, 60, 5)
                candles_time = time.perf_counter()
                
                asset_results[asset] = {
                    "payout": payout,
                    "payout_latency": (payout_time - start_time) * 1000,
                    "candles_latency": (candles_time - payout_time) * 1000,
                    "total_latency": (candles_time - start_time) * 1000,
                    "candles_count": len(candles) if candles else 0
                }
                
                print(f"  📈 Payout: {payout}%")
                print(f"  ⏱️  Total latency: {asset_results[asset]['total_latency']:.2f} ms")
                
            except Exception as e:
                asset_results[asset] = {"error": str(e)}
                print(f"  ❌ Error: {e}")
        
        return asset_results
    
    def print_analysis_results(self, results: Dict):
        """Print detailed analysis results"""
        print("\n" + "=" * 60)
        print("📊 TRADING LATENCY ANALYSIS RESULTS")
        print("=" * 60)
        
        print(f"🕐 Test completed at: {results['timestamp']}")
        print(f"🔄 Total iterations: {results['iterations']}")
        print(f"✅ Successful trades: {results['successful_trades']}")
        print(f"❌ Failed trades: {results['failed_trades']}")
        
        if results['successful_trades'] > 0:
            print(f"\n📈 SUCCESS RATE: {(results['successful_trades']/results['iterations']*100):.1f}%")
            
            for metric, values in results['latencies'].items():
                if values:
                    print(f"\n{metric.replace('_', ' ').title()}:")
                    print(f"  📊 Count: {len(values)}")
                    print(f"  ⚡ Min: {min(values):.2f} ms")
                    print(f"  🐌 Max: {max(values):.2f} ms")
                    print(f"  📊 Average: {statistics.mean(values):.2f} ms")
                    print(f"  📊 Median: {statistics.median(values):.2f} ms")
                    
                    if len(values) > 1:
                        print(f"  📊 Std Dev: {statistics.stdev(values):.2f} ms")
        
        # Performance recommendations
        print(f"\n🎯 PERFORMANCE ANALYSIS FOR 1-MINUTE TRADES:")
        if results['successful_trades'] > 0:
            avg_total = statistics.mean(results['latencies']['total_pipeline'])
            
            if avg_total < 100:
                print("  🟢 EXCELLENT: Latency under 100ms - Optimal for 1-minute signals")
            elif avg_total < 500:
                print("  🟡 GOOD: Latency under 500ms - Acceptable for 1-minute signals")
            elif avg_total < 1000:
                print("  🟠 FAIR: Latency under 1s - May impact 1-minute signal effectiveness")
            else:
                print("  🔴 POOR: Latency over 1s - Significant impact on 1-minute signals")
                
            print(f"  📊 Average total latency: {avg_total:.2f} ms")
            print(f"  ⏰ Time remaining for 60s signal: {60000 - avg_total:.0f} ms")

async def main():
    """Main function to run trading latency analysis"""
    try:
        # Load configuration
        with open("config/pocket_option_config.json", "r") as f:
            config = json.load(f)
        ssid = config.get("ssid")

        if not ssid:
            print("❌ SSID not found in config/pocket_option_config.json")
            return

        # Initialize analyzer
        analyzer = TradingLatencyAnalyzer(ssid)
        await analyzer.initialize()
        
        print("\n🎯 POCKET OPTION TRADING LATENCY ANALYZER")
        print("=" * 60)
        print("1. Quick Signal-to-Trade Test (3 iterations)")
        print("2. Comprehensive Analysis (10 iterations)")
        print("3. 1-Minute Signal Optimization Test")
        print("4. Asset Comparison Test")
        print("5. Custom Test")
        
        choice = input("\nSelect test type (1-5): ").strip()
        
        if choice == "1":
            results = await analyzer.analyze_signal_to_trade_latency(3)
            analyzer.print_analysis_results(results)
            
        elif choice == "2":
            results = await analyzer.analyze_signal_to_trade_latency(10)
            analyzer.print_analysis_results(results)
            
        elif choice == "3":
            asset_results = await analyzer.test_1_minute_signal_optimization()
            print("\n📊 1-MINUTE SIGNAL OPTIMIZATION RESULTS:")
            for asset, data in asset_results.items():
                print(f"\n{asset}:")
                if "error" not in data:
                    print(f"  Payout: {data['payout']}%")
                    print(f"  Total Latency: {data['total_latency']:.2f} ms")
                else:
                    print(f"  Error: {data['error']}")
                    
        elif choice == "4":
            print("🔄 Running asset comparison...")
            asset_results = await analyzer.test_1_minute_signal_optimization()
            
            # Find best performing asset
            best_asset = None
            best_latency = float('inf')
            
            for asset, data in asset_results.items():
                if "error" not in data and data['total_latency'] < best_latency:
                    best_latency = data['total_latency']
                    best_asset = asset
            
            if best_asset:
                print(f"\n🏆 BEST PERFORMING ASSET: {best_asset}")
                print(f"⚡ Lowest latency: {best_latency:.2f} ms")
                
        elif choice == "5":
            iterations = int(input("Enter number of iterations: "))
            results = await analyzer.analyze_signal_to_trade_latency(iterations)
            analyzer.print_analysis_results(results)
            
        else:
            print("❌ Invalid choice. Running quick test...")
            results = await analyzer.analyze_signal_to_trade_latency(3)
            analyzer.print_analysis_results(results)

    except FileNotFoundError:
        print("❌ Error: config/pocket_option_config.json not found.")
    except Exception as e:
        print(f"❌ An error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())
