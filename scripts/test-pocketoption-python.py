#!/usr/bin/env python3
"""
PocketOption Trading Latency Test using Official API
Tests real trading API latency with proper authentication
"""

import time
import json
import threading
from datetime import datetime
from pocketoptionapi.stable_api import PocketOption
import pocketoptionapi.global_value as global_value

# Configure logging
global_value.loglevel = 'INFO'

# Your session data from the browser
SSID = """42["auth",{"session":"a:4:{s:10:\\"session_id\\";s:32:\\"2666465456adc00252df90dd2da488d1\\";s:10:\\"ip_address\\";s:14:\\"63.178.193.220\\";s:10:\\"user_agent\\";s:111:\\"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36\\";s:13:\\"last_activity\\";i:" + str(int(time.time())) + ";}49178e83020b72682666eadb310670ec","isDemo":0,"uid":101002476,"platform":2}]"""
DEMO = False

class LatencyTester:
    def __init__(self, ssid, demo=False):
        self.api = PocketOption(ssid, demo)
        self.latency_results = []
        self.connection_time = 0
        self.test_duration = 30  # seconds
        self.test_interval = 2   # seconds between tests
        
    def connect(self):
        """Connect to PocketOption API and measure connection time"""
        print("[INFO] Connecting to PocketOption API...")
        start_time = time.time()
        
        self.api.connect()
        
        # Wait for connection to be established
        while not global_value.websocket_is_connected:
            time.sleep(0.1)
            if time.time() - start_time > 10:  # 10 second timeout
                print("[ERROR] Connection timeout")
                return False
                
        self.connection_time = (time.time() - start_time) * 1000
        print(f"[SUCCESS] Connected in {self.connection_time:.2f}ms")
        return True
        
    def test_balance_latency(self):
        """Test balance retrieval latency"""
        start_time = time.time()
        try:
            balance = self.api.get_balance()
            latency = (time.time() - start_time) * 1000
            print(f"Balance check: {latency:.2f}ms (Balance: {balance})")
            return latency
        except Exception as e:
            print(f"Balance check failed: {e}")
            return None
            
    def test_candles_latency(self, asset="EURUSD_otc", period=60):
        """Test candle data retrieval latency"""
        start_time = time.time()
        try:
            candles = self.api.get_candles(asset, period)
            latency = (time.time() - start_time) * 1000
            print(f"Candles request ({asset}): {latency:.2f}ms")
            return latency
        except Exception as e:
            print(f"Candles request failed: {e}")
            return None
            
    def test_payout_latency(self):
        """Test payout data retrieval latency"""
        start_time = time.time()
        try:
            # Access payout data from global value
            payout_data = global_value.PayoutData
            latency = (time.time() - start_time) * 1000
            print(f"Payout data: {latency:.2f}ms")
            return latency
        except Exception as e:
            print(f"Payout data failed: {e}")
            return None
            
    def test_buy_latency(self, amount=1, asset="EURUSD_otc", action="call", expiration=60):
        """Test trade execution latency (demo only for safety)"""
        if not DEMO:
            print("[WARNING] Skipping buy test on real account for safety")
            return None
            
        start_time = time.time()
        try:
            result = self.api.buy(amount=amount, active=asset, action=action, expirations=expiration)
            latency = (time.time() - start_time) * 1000
            print(f"Trade execution: {latency:.2f}ms (Result: {result})")
            return latency
        except Exception as e:
            print(f"Trade execution failed: {e}")
            return None
            
    def run_latency_tests(self):
        """Run comprehensive latency tests"""
        print(f"\n=== STARTING LATENCY TESTS FOR {self.test_duration} SECONDS ===")
        
        test_results = {
            'balance': [],
            'candles': [],
            'payout': [],
            'trades': []
        }
        
        start_time = time.time()
        test_count = 0
        
        while time.time() - start_time < self.test_duration:
            test_count += 1
            print(f"\n[TEST #{test_count}] Running latency tests...")
            
            # Test balance latency
            balance_latency = self.test_balance_latency()
            if balance_latency:
                test_results['balance'].append(balance_latency)
                
            # Test candles latency
            candles_latency = self.test_candles_latency()
            if candles_latency:
                test_results['candles'].append(candles_latency)
                
            # Test payout latency
            payout_latency = self.test_payout_latency()
            if payout_latency:
                test_results['payout'].append(payout_latency)
                
            # Test trade latency (demo only)
            if DEMO:
                trade_latency = self.test_buy_latency()
                if trade_latency:
                    test_results['trades'].append(trade_latency)
            
            # Wait before next test
            time.sleep(self.test_interval)
            
        return test_results
        
    def analyze_results(self, results):
        """Analyze and display latency test results"""
        print("\n" + "="*60)
        print("TRADING LATENCY ANALYSIS RESULTS")
        print("="*60)
        
        print(f"Connection time: {self.connection_time:.2f}ms")
        print(f"Test duration: {self.test_duration} seconds")
        print(f"Total test cycles: {len(results['balance'])}")
        
        for test_type, latencies in results.items():
            if latencies:
                avg_latency = sum(latencies) / len(latencies)
                min_latency = min(latencies)
                max_latency = max(latencies)
                variance = max_latency - min_latency
                
                print(f"\n{test_type.upper()} LATENCY:")
                print(f"  Average: {avg_latency:.2f}ms")
                print(f"  Minimum: {min_latency:.2f}ms")
                print(f"  Maximum: {max_latency:.2f}ms")
                print(f"  Variance: {variance:.2f}ms")
                print(f"  Tests: {len(latencies)}")
                
        # Overall performance assessment
        all_latencies = []
        for latencies in results.values():
            all_latencies.extend(latencies)
            
        if all_latencies:
            overall_avg = sum(all_latencies) / len(all_latencies)
            
            print(f"\nOVERALL AVERAGE LATENCY: {overall_avg:.2f}ms")
            print("\nTRADING PERFORMANCE ASSESSMENT:")
            
            if overall_avg < 30:
                print("🟢 EXCELLENT - Perfect for high-frequency trading")
            elif overall_avg < 50:
                print("🟢 VERY GOOD - Excellent for active trading")
            elif overall_avg < 100:
                print("🟡 GOOD - Suitable for most trading strategies")
            elif overall_avg < 200:
                print("🟡 ACCEPTABLE - May notice slight delays")
            else:
                print("🔴 POOR - May significantly affect trading performance")
                
            if max(all_latencies) - min(all_latencies) > 100:
                print("⚠️  WARNING: High latency variance detected")
                
        print("\n" + "="*60)
        
def main():
    print("PocketOption Trading Latency Test")
    print("Using Official PocketOption API v2")
    print("-" * 50)
    
    # Create latency tester
    tester = LatencyTester(SSID, DEMO)
    
    # Connect to API
    if not tester.connect():
        print("[ERROR] Failed to connect to PocketOption API")
        return
        
    # Wait a moment for full initialization
    time.sleep(2)
    
    # Get initial account info
    try:
        balance = tester.api.get_balance()
        print(f"[INFO] Account Balance: {balance}")
        print(f"[INFO] Demo Mode: {DEMO}")
    except Exception as e:
        print(f"[WARNING] Could not retrieve balance: {e}")
    
    # Run latency tests
    try:
        results = tester.run_latency_tests()
        tester.analyze_results(results)
    except KeyboardInterrupt:
        print("\n[INFO] Test interrupted by user")
    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
    finally:
        print("\n[INFO] Disconnecting...")
        # The API will disconnect automatically

if __name__ == "__main__":
    main()
