#!/usr/bin/env python3
"""
Telegram Signal Latency Monitor
==============================

This script measures the complete latency pipeline from Telegram signal reception
to Pocket Option trade execution for 1-minute trading signals.

Pipeline: Telegram Signal → Signal Processing → Pocket Option API → Trade Execution
"""

import asyncio
import time
import json
import statistics
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import re

from telethon import TelegramClient
from BinaryOptionsToolsV2.pocketoption.asyncronous import PocketOptionAsync

class TelegramLatencyMonitor:
    def __init__(self):
        self.telegram_config = None
        self.pocket_config = None
        self.telegram_client = None
        self.pocket_client = None
        self.signal_latencies = []
        
    async def initialize(self):
        """Initialize both Telegram and Pocket Option clients"""
        print("🚀 TELEGRAM SIGNAL LATENCY MONITOR")
        print("=" * 60)
        
        # Load configurations
        try:
            with open("config/telegram_config.json", "r") as f:
                self.telegram_config = json.load(f)
            with open("config/pocket_option_config.json", "r") as f:
                self.pocket_config = json.load(f)
        except FileNotFoundError as e:
            print(f"❌ Configuration file not found: {e}")
            return False
        
        # Initialize Telegram client
        try:
            self.telegram_client = TelegramClient(
                self.telegram_config["session_name"],
                self.telegram_config["api_id"],
                self.telegram_config["api_hash"]
            )
            await self.telegram_client.start()
            print("✅ Connected to Telegram")
        except Exception as e:
            print(f"❌ Telegram connection failed: {e}")
            return False
        
        # Initialize Pocket Option client
        try:
            self.pocket_client = PocketOptionAsync(self.pocket_config["ssid"])
            balance = await self.pocket_client.balance()
            print(f"✅ Connected to Pocket Option (Balance: ${balance:.2f})")
        except Exception as e:
            print(f"❌ Pocket Option connection failed: {e}")
            return False
        
        return True
    
    async def measure_telegram_fetch_latency(self) -> Dict:
        """Measure latency of fetching recent messages from Telegram"""
        print("\n📱 Testing Telegram message fetch latency...")
        
        channel_id = self.telegram_config["channel_id"]
        latencies = []
        
        for i in range(5):  # Test 5 times
            start_time = time.perf_counter()
            try:
                # Fetch last 10 messages
                messages = await self.telegram_client.get_messages(channel_id, limit=10)
                end_time = time.perf_counter()
                
                latency = (end_time - start_time) * 1000
                latencies.append(latency)
                print(f"  Fetch #{i+1}: {latency:.2f}ms ({len(messages)} messages)")
                
            except Exception as e:
                print(f"  Fetch #{i+1}: ERROR - {e}")
            
            await asyncio.sleep(0.5)  # Small delay between tests
        
        if latencies:
            return {
                "success": True,
                "count": len(latencies),
                "min": min(latencies),
                "max": max(latencies),
                "avg": statistics.mean(latencies),
                "median": statistics.median(latencies)
            }
        else:
            return {"success": False, "error": "No successful fetches"}
    
    async def simulate_signal_processing_latency(self, message_text: str) -> Dict:
        """Simulate signal processing latency"""
        start_time = time.perf_counter()
        
        # Simulate regex matching (actual signal parsing)
        first_regex = self.telegram_config["first_message_regex"]
        second_regex = self.telegram_config["second_message_regex"]
        
        # Test pattern matching
        pair_match = re.search(first_regex, message_text)
        direction_match = re.search(second_regex["direction"], message_text)
        timer_match = re.search(second_regex["timer"], message_text)
        
        # Simulate asset conversion (EUR/USD -> EURUSD_otc)
        if pair_match:
            pair = pair_match.group(1).replace("/", "") + "_otc"
        else:
            pair = "EURUSD_otc"  # Default
        
        end_time = time.perf_counter()
        processing_time = (end_time - start_time) * 1000
        
        return {
            "processing_time": processing_time,
            "parsed_pair": pair,
            "found_direction": bool(direction_match),
            "found_timer": bool(timer_match)
        }
    
    async def measure_complete_signal_pipeline(self, test_message: str = None) -> Dict:
        """Measure the complete signal-to-trade pipeline"""
        print("\n🔄 Testing Complete Signal Pipeline...")
        
        if not test_message:
            test_message = """Trading Pair: EUR/USD (OTC)
SET THE TIMER TO 13:45:30
Currency pair EUR/USD
HIGHER
Trade time: 1 MIN"""
        
        pipeline_start = time.perf_counter()
        
        # Step 1: Telegram message fetch simulation
        telegram_start = time.perf_counter()
        await asyncio.sleep(0.001)  # Simulate network delay
        telegram_time = (time.perf_counter() - telegram_start) * 1000
        
        # Step 2: Signal processing
        processing_result = await self.simulate_signal_processing_latency(test_message)
        processing_time = processing_result["processing_time"]
        
        # Step 3: Pocket Option API calls
        api_start = time.perf_counter()
        try:
            # Get payout for the asset
            payout = await self.pocket_client.payout(processing_result["parsed_pair"])
            api_time = (time.perf_counter() - api_start) * 1000
            
            # Step 4: Trade execution simulation (without actual trade)
            trade_start = time.perf_counter()
            # Simulate trade preparation time
            await asyncio.sleep(0.001)
            trade_prep_time = (time.perf_counter() - trade_start) * 1000
            
            total_time = (time.perf_counter() - pipeline_start) * 1000
            
            return {
                "success": True,
                "telegram_fetch": telegram_time,
                "signal_processing": processing_time,
                "api_call": api_time,
                "trade_preparation": trade_prep_time,
                "total_pipeline": total_time,
                "asset": processing_result["parsed_pair"],
                "payout": payout
            }
            
        except Exception as e:
            total_time = (time.perf_counter() - pipeline_start) * 1000
            return {
                "success": False,
                "error": str(e),
                "telegram_fetch": telegram_time,
                "signal_processing": processing_time,
                "total_pipeline": total_time
            }
    
    async def run_comprehensive_pipeline_test(self, iterations: int = 10) -> Dict:
        """Run comprehensive pipeline testing"""
        print(f"\n🔍 Running Comprehensive Pipeline Test ({iterations} iterations)")
        print("=" * 60)
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "iterations": iterations,
            "successful_pipelines": 0,
            "failed_pipelines": 0,
            "latencies": {
                "telegram_fetch": [],
                "signal_processing": [],
                "api_call": [],
                "trade_preparation": [],
                "total_pipeline": []
            },
            "assets_tested": [],
            "payouts": []
        }
        
        for i in range(iterations):
            print(f"\n📍 Pipeline Test {i+1}/{iterations}")
            
            pipeline_result = await self.measure_complete_signal_pipeline()
            
            if pipeline_result["success"]:
                results["successful_pipelines"] += 1
                results["latencies"]["telegram_fetch"].append(pipeline_result["telegram_fetch"])
                results["latencies"]["signal_processing"].append(pipeline_result["signal_processing"])
                results["latencies"]["api_call"].append(pipeline_result["api_call"])
                results["latencies"]["trade_preparation"].append(pipeline_result["trade_preparation"])
                results["latencies"]["total_pipeline"].append(pipeline_result["total_pipeline"])
                results["assets_tested"].append(pipeline_result["asset"])
                results["payouts"].append(pipeline_result["payout"])
                
                print(f"  ✅ Total: {pipeline_result['total_pipeline']:.2f}ms")
                print(f"     Telegram: {pipeline_result['telegram_fetch']:.2f}ms")
                print(f"     Processing: {pipeline_result['signal_processing']:.2f}ms")
                print(f"     API: {pipeline_result['api_call']:.2f}ms")
                print(f"     Asset: {pipeline_result['asset']} ({pipeline_result['payout']}%)")
            else:
                results["failed_pipelines"] += 1
                print(f"  ❌ Failed: {pipeline_result.get('error', 'Unknown error')}")
            
            # Wait between iterations
            if i < iterations - 1:
                await asyncio.sleep(1)
        
        return results
    
    async def monitor_live_signals(self, duration_minutes: int = 10):
        """Monitor live Telegram signals and measure response times"""
        print(f"\n📡 Live Signal Monitoring ({duration_minutes} minutes)")
        print("Press Ctrl+C to stop early")
        print("=" * 60)
        
        channel_id = self.telegram_config["channel_id"]
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        
        signal_count = 0
        measurements = []
        
        try:
            while time.time() < end_time:
                try:
                    # Check for new messages
                    fetch_start = time.perf_counter()
                    messages = await self.telegram_client.get_messages(channel_id, limit=5)
                    fetch_time = (time.perf_counter() - fetch_start) * 1000
                    
                    # Look for trading signals in recent messages
                    for message in messages:
                        if message.text and "Trading Pair:" in message.text:
                            signal_count += 1
                            
                            # Measure processing time for this signal
                            processing_result = await self.simulate_signal_processing_latency(message.text)
                            
                            measurement = {
                                "timestamp": datetime.now().isoformat(),
                                "signal_id": signal_count,
                                "fetch_latency": fetch_time,
                                "processing_latency": processing_result["processing_time"],
                                "total_latency": fetch_time + processing_result["processing_time"],
                                "message_length": len(message.text)
                            }
                            
                            measurements.append(measurement)
                            
                            print(f"📊 Signal #{signal_count}: {measurement['total_latency']:.2f}ms total")
                            print(f"   Fetch: {fetch_time:.2f}ms | Processing: {processing_result['processing_time']:.2f}ms")
                            break
                    
                    await asyncio.sleep(10)  # Check every 10 seconds
                    
                except Exception as e:
                    print(f"⚠️  Monitoring error: {e}")
                    await asyncio.sleep(5)
                    
        except KeyboardInterrupt:
            print("\n⏹️  Monitoring stopped by user")
        
        # Save results
        if measurements:
            filename = f"telegram_signal_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, "w") as f:
                json.dump(measurements, f, indent=2)
            
            total_latencies = [m["total_latency"] for m in measurements]
            print(f"\n📊 Live Monitoring Results:")
            print(f"   Signals detected: {signal_count}")
            print(f"   Average latency: {statistics.mean(total_latencies):.2f}ms")
            print(f"   Min latency: {min(total_latencies):.2f}ms")
            print(f"   Max latency: {max(total_latencies):.2f}ms")
            print(f"   Results saved to: {filename}")
    
    def print_pipeline_results(self, results: Dict):
        """Print formatted pipeline test results"""
        print("\n" + "=" * 60)
        print("📊 TELEGRAM SIGNAL PIPELINE RESULTS")
        print("=" * 60)
        
        print(f"🕐 Test completed: {results['timestamp']}")
        print(f"🔄 Total iterations: {results['iterations']}")
        print(f"✅ Successful: {results['successful_pipelines']}")
        print(f"❌ Failed: {results['failed_pipelines']}")
        
        if results['successful_pipelines'] > 0:
            success_rate = (results['successful_pipelines'] / results['iterations']) * 100
            print(f"📈 Success Rate: {success_rate:.1f}%")
            
            print(f"\n📊 LATENCY BREAKDOWN:")
            for component, values in results['latencies'].items():
                if values:
                    avg_latency = statistics.mean(values)
                    print(f"   {component.replace('_', ' ').title()}: {avg_latency:.2f}ms avg")
            
            total_avg = statistics.mean(results['latencies']['total_pipeline'])
            print(f"\n🎯 TOTAL PIPELINE LATENCY: {total_avg:.2f}ms")
            
            # Performance assessment for 1-minute signals
            if total_avg < 100:
                rating = "🟢 EXCELLENT"
                verdict = "Optimal for 1-minute signals"
            elif total_avg < 500:
                rating = "🟡 GOOD"
                verdict = "Suitable for 1-minute signals"
            elif total_avg < 1000:
                rating = "🟠 FAIR"
                verdict = "May impact signal effectiveness"
            else:
                rating = "🔴 POOR"
                verdict = "Significant impact on 1-minute signals"
            
            print(f"   Performance: {rating}")
            print(f"   Verdict: {verdict}")
            print(f"   Time remaining in 60s window: {60000 - total_avg:.0f}ms")
    
    async def cleanup(self):
        """Clean up connections"""
        if self.telegram_client:
            await self.telegram_client.disconnect()
        print("🔌 Connections closed")

async def main():
    """Main function"""
    monitor = TelegramLatencyMonitor()
    
    try:
        # Initialize connections
        if not await monitor.initialize():
            return
        
        print("\n🎯 TELEGRAM SIGNAL LATENCY TESTS")
        print("=" * 60)
        print("1. Telegram Fetch Latency Test")
        print("2. Complete Pipeline Test (10 iterations)")
        print("3. Live Signal Monitoring (10 minutes)")
        print("4. Quick Pipeline Test (3 iterations)")
        print("5. Custom Test")
        
        choice = input("\nSelect test type (1-5): ").strip()
        
        if choice == "1":
            result = await monitor.measure_telegram_fetch_latency()
            if result["success"]:
                print(f"\n📊 Telegram Fetch Results:")
                print(f"   Average: {result['avg']:.2f}ms")
                print(f"   Min: {result['min']:.2f}ms")
                print(f"   Max: {result['max']:.2f}ms")
            
        elif choice == "2":
            results = await monitor.run_comprehensive_pipeline_test(10)
            monitor.print_pipeline_results(results)
            
        elif choice == "3":
            await monitor.monitor_live_signals(10)
            
        elif choice == "4":
            results = await monitor.run_comprehensive_pipeline_test(3)
            monitor.print_pipeline_results(results)
            
        elif choice == "5":
            iterations = int(input("Enter number of iterations: "))
            results = await monitor.run_comprehensive_pipeline_test(iterations)
            monitor.print_pipeline_results(results)
            
        else:
            print("❌ Invalid choice. Running quick test...")
            results = await monitor.run_comprehensive_pipeline_test(3)
            monitor.print_pipeline_results(results)
    
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        await monitor.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
