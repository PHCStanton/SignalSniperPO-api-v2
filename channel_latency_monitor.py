#!/usr/bin/env python3
"""
Channel-Specific Latency Monitor for BINARY TRADING CLUB
========================================================

This script measures the delays between the bot and the 'BINARY TRADING CLUB' channel
specifically for receiving, parsing, and executing messages. It helps determine if
optimization is needed for the signal processing pipeline.

Key Measurements:
- Message reception delays from the channel
- Signal parsing latency for channel-specific message formats
- End-to-end processing time for BINARY TRADING CLUB signals
- Channel-specific performance metrics and recommendations
"""

import asyncio
import time
import json
import statistics
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

from telethon import TelegramClient, events
from BinaryOptionsToolsV2.pocketoption.asyncronous import PocketOptionAsync

@dataclass
class ChannelLatencyMeasurement:
    """Data class for storing channel latency measurements"""
    timestamp: str
    message_id: int
    channel_id: int
    channel_name: str
    message_length: int
    reception_latency: float
    parsing_latency: float
    validation_latency: float
    total_processing_latency: float
    signal_detected: bool
    signal_valid: bool
    parsing_success: bool
    error_message: Optional[str] = None

class BinaryTradingClubLatencyMonitor:
    """Specialized latency monitor for the BINARY TRADING CLUB channel"""
    
    def __init__(self):
        self.telegram_config = None
        self.pocket_config = None
        self.telegram_client = None
        self.pocket_client = None
        self.measurements = []
        self.channel_id = None
        self.channel_name = "BINARY TRADING CLUB"
        
        # Signal parsing patterns (from telegram_config.json)
        self.first_message_pattern = r"Trading Pair: (\w+/\w+)(?:\s*\(OTC\))?"
        self.second_message_patterns = {
            "timer": r"SET THE TIMER TO (\d{2}:\d{2}:\d{2})",
            "pair": r"Currency pair (\w+/\w+)",
            "direction": r"(HIGHER|LOWER)",
            "expiry": r"Trade time: (\d+) MIN"
        }
        
        # Performance thresholds (in milliseconds)
        self.thresholds = {
            "excellent": 50,
            "good": 100,
            "fair": 200,
            "poor": 500
        }
    
    async def initialize(self) -> bool:
        """Initialize Telegram and Pocket Option clients"""
        print("🚀 BINARY TRADING CLUB LATENCY MONITOR")
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
        
        # Get channel information
        self.channel_id = self.telegram_config.get("channel_id", -1002412213735)
        self.channel_name = self.telegram_config.get("channel_name", "BINARY TRADING CLUB")
        
        # Initialize Telegram client
        try:
            self.telegram_client = TelegramClient(
                self.telegram_config["session_name"],
                self.telegram_config["api_id"],
                self.telegram_config["api_hash"]
            )
            await self.telegram_client.start()
            print(f"✅ Connected to Telegram")
            
            # Verify channel access
            try:
                channel = await self.telegram_client.get_entity(self.channel_id)
                print(f"✅ Channel access verified: {getattr(channel, 'title', self.channel_name)}")
            except Exception as e:
                print(f"⚠️  Channel access warning: {e}")
                
        except Exception as e:
            print(f"❌ Telegram connection failed: {e}")
            return False
        
        # Initialize Pocket Option client (optional for parsing tests)
        try:
            self.pocket_client = PocketOptionAsync(self.pocket_config["ssid"])
            balance = await self.pocket_client.balance()
            print(f"✅ Connected to Pocket Option (Balance: ${balance:.2f})")
        except Exception as e:
            print(f"⚠️  Pocket Option connection failed: {e}")
            print("   Continuing with Telegram-only monitoring...")
        
        return True
    
    def parse_signal_message(self, message_text: str) -> Tuple[Dict, float]:
        """
        Parse a signal message and measure parsing latency
        Returns: (parsed_signal_dict, parsing_time_ms)
        """
        start_time = time.perf_counter()
        
        try:
            # Clean the message text
            text = message_text.strip()
            
            # Try single-message format first
            signal = self._parse_complete_signal(text)
            if signal:
                parsing_time = (time.perf_counter() - start_time) * 1000
                return signal, parsing_time
            
            # Try two-message format
            signal = self._parse_partial_signal(text)
            parsing_time = (time.perf_counter() - start_time) * 1000
            return signal, parsing_time
            
        except Exception as e:
            parsing_time = (time.perf_counter() - start_time) * 1000
            return {"error": str(e)}, parsing_time
    
    def _parse_complete_signal(self, text: str) -> Optional[Dict]:
        """Parse complete signal from single message"""
        try:
            # Extract timer
            timer_match = re.search(self.second_message_patterns["timer"], text)
            if not timer_match:
                return None
            timer = timer_match.group(1)
            
            # Extract currency pair
            pair_match = re.search(self.second_message_patterns["pair"], text)
            if not pair_match:
                return None
            pair = pair_match.group(1)
            
            # Extract direction
            direction = None
            if "HIGHER" in text or "⬆️" in text:
                direction = "HIGHER"
            elif "LOWER" in text or "⬇️" in text:
                direction = "LOWER"
            
            if not direction:
                return None
            
            # Extract expiry
            expiry_match = re.search(self.second_message_patterns["expiry"], text)
            if not expiry_match:
                return None
            expiry = int(expiry_match.group(1))
            
            return {
                "type": "complete_signal",
                "timer": timer,
                "pair": pair,
                "direction": direction,
                "expiry": expiry,
                "valid": True
            }
            
        except Exception:
            return None
    
    def _parse_partial_signal(self, text: str) -> Dict:
        """Parse partial signal components"""
        components = {}
        
        # Check for first message pattern
        first_match = re.search(self.first_message_pattern, text)
        if first_match:
            components["first_message"] = {
                "trading_pair": first_match.group(1),
                "type": "first_message"
            }
        
        # Check for second message components
        for component, pattern in self.second_message_patterns.items():
            match = re.search(pattern, text)
            if match:
                components[component] = match.group(1)
        
        if components:
            components["type"] = "partial_signal"
            components["valid"] = len(components) > 1
        else:
            components = {"type": "no_signal", "valid": False}
        
        return components
    
    def validate_signal(self, signal: Dict) -> Tuple[bool, float, str]:
        """
        Validate a parsed signal and measure validation latency
        Returns: (is_valid, validation_time_ms, validation_message)
        """
        start_time = time.perf_counter()
        
        try:
            if signal.get("error"):
                validation_time = (time.perf_counter() - start_time) * 1000
                return False, validation_time, f"Parsing error: {signal['error']}"
            
            if signal.get("type") == "complete_signal":
                # Validate complete signal
                required_fields = ["timer", "pair", "direction", "expiry"]
                missing_fields = [field for field in required_fields if not signal.get(field)]
                
                if missing_fields:
                    validation_time = (time.perf_counter() - start_time) * 1000
                    return False, validation_time, f"Missing fields: {missing_fields}"
                
                # Validate timer format
                timer = signal["timer"]
                if not re.match(r"\d{2}:\d{2}:\d{2}", timer):
                    validation_time = (time.perf_counter() - start_time) * 1000
                    return False, validation_time, "Invalid timer format"
                
                # Validate direction
                if signal["direction"] not in ["HIGHER", "LOWER"]:
                    validation_time = (time.perf_counter() - start_time) * 1000
                    return False, validation_time, "Invalid direction"
                
                # Validate expiry
                if not isinstance(signal["expiry"], int) or signal["expiry"] <= 0:
                    validation_time = (time.perf_counter() - start_time) * 1000
                    return False, validation_time, "Invalid expiry"
                
                validation_time = (time.perf_counter() - start_time) * 1000
                return True, validation_time, "Valid complete signal"
            
            elif signal.get("type") == "partial_signal":
                validation_time = (time.perf_counter() - start_time) * 1000
                return True, validation_time, "Valid partial signal"
            
            else:
                validation_time = (time.perf_counter() - start_time) * 1000
                return False, validation_time, "No signal detected"
                
        except Exception as e:
            validation_time = (time.perf_counter() - start_time) * 1000
            return False, validation_time, f"Validation error: {str(e)}"
    
    async def measure_message_reception_latency(self, iterations: int = 10) -> Dict:
        """Measure latency of receiving messages from the channel"""
        print(f"\n📱 Testing message reception latency from {self.channel_name}...")
        
        latencies = []
        
        for i in range(iterations):
            start_time = time.perf_counter()
            try:
                # Fetch recent messages from the specific channel
                messages = await self.telegram_client.get_messages(self.channel_id, limit=5)
                end_time = time.perf_counter()
                
                latency = (end_time - start_time) * 1000
                latencies.append(latency)
                print(f"  Reception #{i+1}: {latency:.2f}ms ({len(messages)} messages)")
                
            except Exception as e:
                print(f"  Reception #{i+1}: ERROR - {e}")
            
            await asyncio.sleep(0.5)
        
        if latencies:
            return {
                "success": True,
                "channel_name": self.channel_name,
                "channel_id": self.channel_id,
                "iterations": len(latencies),
                "min": min(latencies),
                "max": max(latencies),
                "avg": statistics.mean(latencies),
                "median": statistics.median(latencies),
                "std_dev": statistics.stdev(latencies) if len(latencies) > 1 else 0
            }
        else:
            return {"success": False, "error": "No successful message receptions"}
    
    async def test_signal_parsing_performance(self, test_messages: List[str] = None) -> Dict:
        """Test signal parsing performance with sample messages"""
        print(f"\n🔍 Testing signal parsing performance for {self.channel_name} format...")
        
        if not test_messages:
            test_messages = [
                """❗️SET THE TIMER TO 00:01:00❗️

First signal: Currency pair AUD/USD 
HIGHER ⬆️ 
Trade time: 1 MIN""",
                """Trading Pair: EUR/USD (OTC)
SET THE TIMER TO 13:45:30
Currency pair EUR/USD
LOWER
Trade time: 1 MIN""",
                """❗️SET THE TIMER TO 00:02:00❗️

Currency pair GBP/USD 
HIGHER ⬆️ 
Trade time: 1 MIN""",
                "Invalid message without signal format",
                """SET THE TIMER TO 14:30:15
Currency pair USD/JPY
LOWER ⬇️
Trade time: 1 MIN"""
            ]
        
        results = {
            "total_tests": len(test_messages),
            "successful_parses": 0,
            "failed_parses": 0,
            "valid_signals": 0,
            "invalid_signals": 0,
            "parsing_times": [],
            "validation_times": [],
            "test_results": []
        }
        
        for i, message in enumerate(test_messages):
            print(f"\n  Test #{i+1}: {message[:50]}...")
            
            # Parse the message
            signal, parsing_time = self.parse_signal_message(message)
            results["parsing_times"].append(parsing_time)
            
            # Validate the signal
            is_valid, validation_time, validation_msg = self.validate_signal(signal)
            results["validation_times"].append(validation_time)
            
            # Record results
            test_result = {
                "test_id": i + 1,
                "message_length": len(message),
                "parsing_time": parsing_time,
                "validation_time": validation_time,
                "total_time": parsing_time + validation_time,
                "signal_detected": signal.get("type") != "no_signal",
                "signal_valid": is_valid,
                "validation_message": validation_msg,
                "signal_data": signal
            }
            
            results["test_results"].append(test_result)
            
            if signal.get("type") != "no_signal":
                results["successful_parses"] += 1
                if is_valid:
                    results["valid_signals"] += 1
                    print(f"    ✅ Valid signal: {parsing_time:.2f}ms parse + {validation_time:.2f}ms validation")
                else:
                    results["invalid_signals"] += 1
                    print(f"    ⚠️  Invalid signal: {validation_msg}")
            else:
                results["failed_parses"] += 1
                print(f"    ❌ No signal detected: {parsing_time:.2f}ms")
        
        # Calculate statistics
        if results["parsing_times"]:
            results["avg_parsing_time"] = statistics.mean(results["parsing_times"])
            results["avg_validation_time"] = statistics.mean(results["validation_times"])
            results["avg_total_time"] = results["avg_parsing_time"] + results["avg_validation_time"]
        
        return results
    
    async def monitor_live_channel_performance(self, duration_minutes: int = 15) -> Dict:
        """Monitor live performance of the BINARY TRADING CLUB channel"""
        print(f"\n📡 Live monitoring of {self.channel_name} ({duration_minutes} minutes)")
        print("Press Ctrl+C to stop early")
        print("=" * 60)
        
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        
        live_measurements = []
        message_count = 0
        signal_count = 0
        
        try:
            while time.time() < end_time:
                try:
                    # Check for new messages
                    reception_start = time.perf_counter()
                    messages = await self.telegram_client.get_messages(self.channel_id, limit=3)
                    reception_time = (time.perf_counter() - reception_start) * 1000
                    
                    # Process each message
                    for message in messages:
                        if message.text:
                            message_count += 1
                            
                            # Parse the message
                            signal, parsing_time = self.parse_signal_message(message.text)
                            
                            # Validate the signal
                            is_valid, validation_time, validation_msg = self.validate_signal(signal)
                            
                            # Create measurement record
                            measurement = ChannelLatencyMeasurement(
                                timestamp=datetime.now().isoformat(),
                                message_id=message.id,
                                channel_id=self.channel_id,
                                channel_name=self.channel_name,
                                message_length=len(message.text),
                                reception_latency=reception_time,
                                parsing_latency=parsing_time,
                                validation_latency=validation_time,
                                total_processing_latency=reception_time + parsing_time + validation_time,
                                signal_detected=signal.get("type") != "no_signal",
                                signal_valid=is_valid,
                                parsing_success=not signal.get("error"),
                                error_message=validation_msg if not is_valid else None
                            )
                            
                            live_measurements.append(measurement)
                            
                            if signal.get("type") == "complete_signal" and is_valid:
                                signal_count += 1
                                print(f"📊 Signal #{signal_count}: {measurement.total_processing_latency:.2f}ms total")
                                print(f"   Reception: {reception_time:.2f}ms | Parsing: {parsing_time:.2f}ms | Validation: {validation_time:.2f}ms")
                                print(f"   Signal: {signal['pair']} {signal['direction']} {signal['expiry']}min")
                    
                    # Wait before next check
                    await asyncio.sleep(10)
                    
                except Exception as e:
                    print(f"⚠️  Monitoring error: {e}")
                    await asyncio.sleep(5)
                    
        except KeyboardInterrupt:
            print("\n⏹️  Monitoring stopped by user")
        
        # Compile results
        results = {
            "monitoring_duration": duration_minutes,
            "channel_name": self.channel_name,
            "channel_id": self.channel_id,
            "total_messages": message_count,
            "total_signals": signal_count,
            "measurements": [
                {
                    "timestamp": m.timestamp,
                    "message_id": m.message_id,
                    "reception_latency": m.reception_latency,
                    "parsing_latency": m.parsing_latency,
                    "validation_latency": m.validation_latency,
                    "total_latency": m.total_processing_latency,
                    "signal_detected": m.signal_detected,
                    "signal_valid": m.signal_valid
                }
                for m in live_measurements
            ]
        }
        
        # Calculate performance statistics
        if live_measurements:
            total_latencies = [m.total_processing_latency for m in live_measurements]
            reception_latencies = [m.reception_latency for m in live_measurements]
            parsing_latencies = [m.parsing_latency for m in live_measurements]
            validation_latencies = [m.validation_latency for m in live_measurements]
            
            results["performance_stats"] = {
                "avg_total_latency": statistics.mean(total_latencies),
                "avg_reception_latency": statistics.mean(reception_latencies),
                "avg_parsing_latency": statistics.mean(parsing_latencies),
                "avg_validation_latency": statistics.mean(validation_latencies),
                "min_total_latency": min(total_latencies),
                "max_total_latency": max(total_latencies),
                "signal_detection_rate": (signal_count / message_count * 100) if message_count > 0 else 0
            }
            
            # Save detailed results
            filename = f"channel_latency_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, "w") as f:
                json.dump(results, f, indent=2)
            print(f"\n📊 Results saved to: {filename}")
        
        return results
    
    def assess_performance(self, avg_latency: float) -> Tuple[str, str, str]:
        """Assess performance based on average latency"""
        if avg_latency <= self.thresholds["excellent"]:
            return "🟢 EXCELLENT", "Optimal for high-frequency trading", "No optimization needed"
        elif avg_latency <= self.thresholds["good"]:
            return "🟡 GOOD", "Suitable for 1-minute signals", "Minor optimizations possible"
        elif avg_latency <= self.thresholds["fair"]:
            return "🟠 FAIR", "May impact signal effectiveness", "Optimization recommended"
        else:
            return "🔴 POOR", "Significant impact on trading", "Immediate optimization required"
    
    def print_performance_report(self, results: Dict):
        """Print a comprehensive performance report"""
        print("\n" + "=" * 70)
        print(f"📊 {self.channel_name.upper()} LATENCY PERFORMANCE REPORT")
        print("=" * 70)
        
        if "performance_stats" in results:
            stats = results["performance_stats"]
            
            print(f"🕐 Monitoring Duration: {results['monitoring_duration']} minutes")
            print(f"📨 Total Messages: {results['total_messages']}")
            print(f"🎯 Signals Detected: {results['total_signals']}")
            print(f"📈 Signal Detection Rate: {stats['signal_detection_rate']:.1f}%")
            
            print(f"\n📊 LATENCY BREAKDOWN:")
            print(f"   Message Reception: {stats['avg_reception_latency']:.2f}ms avg")
            print(f"   Signal Parsing: {stats['avg_parsing_latency']:.2f}ms avg")
            print(f"   Signal Validation: {stats['avg_validation_latency']:.2f}ms avg")
            print(f"   TOTAL PROCESSING: {stats['avg_total_latency']:.2f}ms avg")
            
            print(f"\n🎯 LATENCY RANGE:")
            print(f"   Minimum: {stats['min_total_latency']:.2f}ms")
            print(f"   Maximum: {stats['max_total_latency']:.2f}ms")
            
            # Performance assessment
            rating, verdict, recommendation = self.assess_performance(stats['avg_total_latency'])
            print(f"\n🏆 PERFORMANCE ASSESSMENT:")
            print(f"   Rating: {rating}")
            print(f"   Verdict: {verdict}")
            print(f"   Recommendation: {recommendation}")
            
            # Time remaining for 1-minute signals
            remaining_time = 60000 - stats['avg_total_latency']
            print(f"   Time remaining in 60s window: {remaining_time:.0f}ms ({remaining_time/600:.1f}%)")
            
        elif "avg_total_time" in results:
            # Parsing test results
            print(f"🧪 Signal Parsing Test Results:")
            print(f"   Total Tests: {results['total_tests']}")
            print(f"   Successful Parses: {results['successful_parses']}")
            print(f"   Valid Signals: {results['valid_signals']}")
            print(f"   Average Parsing Time: {results['avg_parsing_time']:.2f}ms")
            print(f"   Average Validation Time: {results['avg_validation_time']:.2f}ms")
            print(f"   Average Total Time: {results['avg_total_time']:.2f}ms")
            
            rating, verdict, recommendation = self.assess_performance(results['avg_total_time'])
            print(f"\n🏆 PARSING PERFORMANCE:")
            print(f"   Rating: {rating}")
            print(f"   Recommendation: {recommendation}")
    
    async def run_comprehensive_channel_analysis(self) -> Dict:
        """Run comprehensive analysis of channel performance"""
        print(f"\n🔍 COMPREHENSIVE CHANNEL ANALYSIS: {self.channel_name}")
        print("=" * 70)
        
        comprehensive_results = {
            "channel_name": self.channel_name,
            "channel_id": self.channel_id,
            "timestamp": datetime.now().isoformat(),
            "tests": {}
        }
        
        # Test 1: Message reception latency
        print("\n1️⃣ Testing message reception latency...")
        reception_results = await self.measure_message_reception_latency(10)
        comprehensive_results["tests"]["message_reception"] = reception_results
        
        if reception_results["success"]:
            print(f"   ✅ Average reception latency: {reception_results['avg']:.2f}ms")
        
        # Test 2: Signal parsing performance
        print("\n2️⃣ Testing signal parsing performance...")
        parsing_results = await self.test_signal_parsing_performance()
        comprehensive_results["tests"]["signal_parsing"] = parsing_results
        print(f"   ✅ Average parsing latency: {parsing_results.get('avg_total_time', 0):.2f}ms")
        
        # Test 3: Live monitoring (short duration for testing)
        print("\n3️⃣ Running live monitoring test (2 minutes)...")
        live_results = await self.monitor_live_channel_performance(2)
        comprehensive_results["tests"]["live_monitoring"] = live_results
        
        # Calculate overall performance
        total_avg_latency = 0
        component_count = 0
        
        if reception_results["success"]:
            total_avg_latency += reception_results["avg"]
            component_count += 1
        
        if "avg_total_time" in parsing_results:
            total_avg_latency += parsing_results["avg_total_time"]
            component_count += 1
        
        if component_count > 0:
            overall_avg = total_avg_latency / component_count
            comprehensive_results["overall_performance"] = {
                "average_latency": overall_avg,
                "component_count": component_count
            }
            
            rating, verdict, recommendation = self.assess_performance(overall_avg)
            comprehensive_results["assessment"] = {
                "rating": rating,
                "verdict": verdict,
                "recommendation": recommendation
            }
        
        # Save comprehensive results
        filename = f"channel_analysis_{self.channel_name.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, "w") as f:
            json.dump(comprehensive_results, f, indent=2)
        
        print(f"\n💾 Comprehensive analysis saved to: {filename}")
        return comprehensive_results
    
    async def cleanup(self):
        """Clean up connections"""
        if self.telegram_client:
            await self.telegram_client.disconnect()
        print("🔌 Connections closed")

async def main():
    """Main function"""
    monitor = BinaryTradingClubLatencyMonitor()
    
    try:
        # Initialize connections
        if not await monitor.initialize():
            return
        
        print(f"\n🎯 {monitor.channel_name.upper()} LATENCY MONITORING OPTIONS")
        print("=" * 70)
        print("1. Message Reception Latency Test")
        print("2. Signal Parsing Performance Test")
        print("3. Live Channel Monitoring (15 minutes)")
        print("4. Quick Live Test (2 minutes)")
        print("5. Comprehensive Channel Analysis")
        print("6. Custom Live Monitoring Duration")
        
        choice = input("\nSelect test type (1-6): ").strip()
        
        if choice == "1":
            result = await monitor.measure_message_reception_latency(15)
            if result["success"]:
                print(f"\n📊 Message Reception Results:")
                print(f"   Channel: {result['channel_name']}")
                print(f"   Average: {result['avg']:.2f}ms")
                print(f"   Min: {result['min']:.2f}ms")
                print(f"   Max: {result['max']:.2f}ms")
                print(f"   Std Dev: {result['std_dev']:.2f}ms")
                
                rating, verdict, recommendation = monitor.assess_performance(result['avg'])
                print(f"\n🏆 Performance: {rating}")
                print(f"   {recommendation}")
            
        elif choice == "2":
            results = await monitor.test_signal_parsing_performance()
            monitor.print_performance_report(results)
            
        elif choice == "3":
            results = await monitor.monitor_live_channel_performance(15)
            monitor.print_performance_report(results)
            
        elif choice == "4":
            results = await monitor.monitor_live_channel_performance(2)
            monitor.print_performance_report(results)
            
        elif choice == "5":
            results = await monitor.run_comprehensive_channel_analysis()
            print(f"\n🎯 COMPREHENSIVE ANALYSIS COMPLETE")
            if "assessment" in results:
                print(f"   Overall Rating: {results['assessment']['rating']}")
                print(f"   Recommendation: {results['assessment']['recommendation']}")
            
        elif choice == "6":
            try:
                duration = int(input("Enter monitoring duration in minutes: "))
                if duration > 0:
                    results = await monitor.monitor_live_channel_performance(duration)
                    monitor.print_performance_report(results)
                else:
                    print("❌ Duration must be positive")
            except ValueError:
                print("❌ Invalid duration")
            
        else:
            print("❌ Invalid choice. Running quick test...")
            results = await monitor.monitor_live_channel_performance(2)
            monitor.print_performance_report(results)
    
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        await monitor.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
