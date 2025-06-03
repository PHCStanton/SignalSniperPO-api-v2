#!/usr/bin/env python3
"""
Final Optimized Pocket Option Latency Test
Provides accurate real-world latency measurements for trading assessment
"""

import time
import json
import logging
import statistics
import socket
import subprocess
import platform
from datetime import datetime
from pocketoptionapi.stable_api import PocketOption
import pocketoptionapi.global_value as global_value

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FinalPocketOptionLatencyTester:
    def __init__(self, config_path="config/pocket_option_config.json"):
        self.config_path = config_path
        self.api = None
        self.latency_results = []
        self.connection_start_time = None
        self.server_host = "api-eu.po.market"
        self.server_port = 443
        
    def load_config(self):
        """Load configuration from JSON file"""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            logger.info(f"Loaded configuration from {self.config_path}")
            return config
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return None
    
    def precise_timer(self):
        """Get high-precision timestamp"""
        return time.perf_counter()
    
    def test_network_ping(self, iterations=5):
        """Test raw network ping to the server"""
        logger.info(f"Testing raw network ping to {self.server_host}...")
        
        latencies = []
        
        for i in range(iterations):
            try:
                if platform.system().lower() == "windows":
                    # Windows ping command
                    result = subprocess.run(
                        ["ping", "-n", "1", self.server_host],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    
                    # Parse Windows ping output
                    if "time=" in result.stdout:
                        for line in result.stdout.split('\n'):
                            if "time=" in line:
                                time_str = line.split("time=")[1].split("ms")[0]
                                latency = float(time_str)
                                latencies.append(latency)
                                logger.info(f"  Network ping {i+1}/{iterations}: {latency:.1f}ms")
                                break
                    else:
                        logger.warning(f"  Network ping {i+1}/{iterations}: Failed")
                else:
                    # Unix/Linux ping command
                    result = subprocess.run(
                        ["ping", "-c", "1", self.server_host],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    
                    # Parse Unix ping output
                    if "time=" in result.stdout:
                        for line in result.stdout.split('\n'):
                            if "time=" in line:
                                time_str = line.split("time=")[1].split(" ")[0]
                                latency = float(time_str)
                                latencies.append(latency)
                                logger.info(f"  Network ping {i+1}/{iterations}: {latency:.1f}ms")
                                break
                    else:
                        logger.warning(f"  Network ping {i+1}/{iterations}: Failed")
                
                time.sleep(0.2)
                
            except Exception as e:
                logger.error(f"  Network ping {i+1}/{iterations}: Error - {e}")
        
        return latencies
    
    def test_tcp_connection_latency(self, iterations=5):
        """Test TCP connection latency to the server"""
        logger.info(f"Testing TCP connection latency to {self.server_host}:{self.server_port}...")
        
        latencies = []
        
        for i in range(iterations):
            try:
                start_time = self.precise_timer()
                
                # Create TCP socket and connect
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                
                result = sock.connect_ex((self.server_host, self.server_port))
                
                end_time = self.precise_timer()
                latency = (end_time - start_time) * 1000
                
                sock.close()
                
                if result == 0:  # Connection successful
                    latencies.append(latency)
                    logger.info(f"  TCP connect {i+1}/{iterations}: {latency:.2f}ms")
                else:
                    logger.warning(f"  TCP connect {i+1}/{iterations}: Failed")
                
                time.sleep(0.3)
                
            except Exception as e:
                logger.error(f"  TCP connect {i+1}/{iterations}: Error - {e}")
        
        return latencies
    
    def connect_to_api(self, ssid, is_demo=False):
        """Connect to PocketOption API with precise timing"""
        try:
            # Reset global values for a clean test
            global_value.websocket_is_connected = False
            global_value.balance = None
            global_value.balance_updated = False
            
            logger.info("Creating PocketOption API instance...")
            self.connection_start_time = self.precise_timer()
            
            self.api = PocketOption(ssid, is_demo)
            
            logger.info("Attempting to connect to Pocket Option API...")
            # Connect using proper method
            connection_result = self.api.connect()
            if not connection_result:
                logger.error("Failed to start connection")
                return False, None, None
            
            logger.info("Waiting for connection to establish...")
            # Wait for connection to establish properly
            start_time = self.precise_timer()
            connection_established = False
            
            while self.precise_timer() - start_time < 15:  # Wait up to 15 seconds
                if self.api.check_connect():
                    connection_established = True
                    connect_end = self.precise_timer()
                    connection_latency = (connect_end - self.connection_start_time) * 1000
                    logger.info("Successfully connected to Pocket Option API")
                    break
                time.sleep(0.1)
            
            if not connection_established:
                logger.error("Connection timeout - could not establish websocket connection")
                return False, None, None
            
            logger.info("Testing authentication with balance retrieval...")
            
            # Test authentication by getting balance with precise timing
            auth_start = self.precise_timer()
            balance = None
            start_time = self.precise_timer()
            
            while self.precise_timer() - start_time < 10:  # Wait up to 10 seconds
                balance = self.api.get_balance()
                if balance is not None:
                    auth_end = self.precise_timer()
                    auth_latency = (auth_end - auth_start) * 1000
                    logger.info(f"Successfully authenticated. Balance: {balance}")
                    logger.info(f"Connection latency: {connection_latency:.2f}ms")
                    logger.info(f"Authentication latency: {auth_latency:.2f}ms")
                    return True, connection_latency, auth_latency
                time.sleep(0.05)
            
            logger.error("Failed to authenticate - balance is None")
            return False, None, None
                
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return False, None, None
    
    def test_api_round_trip_latency(self, iterations=10):
        """Test API round-trip latency with forced server requests"""
        logger.info(f"Testing API round-trip latency with {iterations} iterations...")
        
        latencies = []
        successful_requests = 0
        
        for i in range(iterations):
            try:
                # Clear cached values to force server request
                old_balance = global_value.balance
                
                start_time = self.precise_timer()
                
                # Force a fresh balance request by temporarily clearing cache
                global_value.balance = None
                balance = self.api.get_balance()
                
                # If balance is still None, try to get server timestamp instead
                if balance is None:
                    server_time = self.api.get_server_timestamp()
                    end_time = self.precise_timer()
                    
                    if server_time is not None:
                        latency = (end_time - start_time) * 1000
                        latencies.append(latency)
                        successful_requests += 1
                        logger.info(f"  API request {i+1}/{iterations}: {latency:.2f}ms (timestamp)")
                    else:
                        logger.warning(f"  API request {i+1}/{iterations}: Failed")
                else:
                    end_time = self.precise_timer()
                    latency = (end_time - start_time) * 1000
                    latencies.append(latency)
                    successful_requests += 1
                    logger.info(f"  API request {i+1}/{iterations}: {latency:.2f}ms (balance)")
                
                # Restore balance if it was cleared
                if balance is not None:
                    global_value.balance = balance
                
                time.sleep(0.2)
                
            except Exception as e:
                logger.error(f"  API request {i+1}/{iterations}: Error - {e}")
        
        return latencies, successful_requests
    
    def calculate_statistics(self, latencies, test_name):
        """Calculate and display latency statistics"""
        if not latencies:
            logger.warning(f"No successful {test_name} measurements")
            return None
        
        stats = {
            'count': len(latencies),
            'min': min(latencies),
            'max': max(latencies),
            'mean': statistics.mean(latencies),
            'median': statistics.median(latencies),
            'stdev': statistics.stdev(latencies) if len(latencies) > 1 else 0,
            'p95': sorted(latencies)[int(len(latencies) * 0.95)] if len(latencies) > 1 else latencies[0]
        }
        
        logger.info(f"\n{test_name} Statistics:")
        logger.info(f"  Successful tests: {stats['count']}")
        logger.info(f"  Minimum latency: {stats['min']:.2f}ms")
        logger.info(f"  Maximum latency: {stats['max']:.2f}ms")
        logger.info(f"  Average latency: {stats['mean']:.2f}ms")
        logger.info(f"  Median latency: {stats['median']:.2f}ms")
        logger.info(f"  95th percentile: {stats['p95']:.2f}ms")
        logger.info(f"  Standard deviation: {stats['stdev']:.2f}ms")
        
        return stats
    
    def assess_trading_performance(self, network_stats, tcp_stats, api_stats):
        """Assess trading performance based on latency measurements"""
        print(f"\n🎯 TRADING PERFORMANCE ASSESSMENT:")
        
        # Use the most relevant latency measurement
        if api_stats:
            primary_latency = api_stats['mean']
            primary_p95 = api_stats['p95']
            primary_source = "API"
        elif tcp_stats:
            primary_latency = tcp_stats['mean']
            primary_p95 = tcp_stats['p95']
            primary_source = "TCP"
        elif network_stats:
            primary_latency = network_stats['mean']
            primary_p95 = network_stats['p95']
            primary_source = "Network"
        else:
            print("   ❌ No latency data available for assessment")
            return
        
        print(f"   Primary measurement source: {primary_source}")
        print(f"   Average latency: {primary_latency:.2f}ms")
        print(f"   95th percentile: {primary_p95:.2f}ms")
        
        # Trading strategy suitability
        print(f"\n   📊 Trading Strategy Suitability:")
        
        if primary_latency < 30 and primary_p95 < 50:
            print("   • Scalping (1-5min): ✅ EXCELLENT - Ultra-low latency")
            print("   • Day trading (5-60min): ✅ EXCELLENT")
            print("   • Swing trading (1hr+): ✅ EXCELLENT")
            overall_rating = "🟢 EXCELLENT"
        elif primary_latency < 50 and primary_p95 < 100:
            print("   • Scalping (1-5min): ✅ GOOD - Suitable for most strategies")
            print("   • Day trading (5-60min): ✅ EXCELLENT")
            print("   • Swing trading (1hr+): ✅ EXCELLENT")
            overall_rating = "🟢 GOOD"
        elif primary_latency < 100 and primary_p95 < 200:
            print("   • Scalping (1-5min): ⚠️ CAUTION - May miss fast opportunities")
            print("   • Day trading (5-60min): ✅ GOOD")
            print("   • Swing trading (1hr+): ✅ EXCELLENT")
            overall_rating = "🟡 ACCEPTABLE"
        elif primary_latency < 200 and primary_p95 < 400:
            print("   • Scalping (1-5min): ❌ NOT RECOMMENDED")
            print("   • Day trading (5-60min): ⚠️ CAUTION - Limited strategies")
            print("   • Swing trading (1hr+): ✅ GOOD")
            overall_rating = "🟠 POOR"
        else:
            print("   • Scalping (1-5min): ❌ NOT RECOMMENDED")
            print("   • Day trading (5-60min): ❌ NOT RECOMMENDED")
            print("   • Swing trading (1hr+): ⚠️ CAUTION")
            overall_rating = "🔴 VERY POOR"
        
        # Slippage estimation
        if primary_latency < 30:
            slippage = "Minimal (<0.1 pips)"
        elif primary_latency < 50:
            slippage = "Very Low (0.1-0.2 pips)"
        elif primary_latency < 100:
            slippage = "Low (0.2-0.5 pips)"
        elif primary_latency < 200:
            slippage = "Moderate (0.5-1 pips)"
        else:
            slippage = "High (>1 pip)"
        
        print(f"\n   💰 Expected Slippage: {slippage}")
        print(f"   🏆 Overall Rating: {overall_rating}")
        
        return overall_rating
    
    def run_comprehensive_test(self):
        """Run comprehensive latency testing"""
        print("\n" + "="*80)
        print("🚀 FINAL POCKET OPTION LATENCY TEST - COMPREHENSIVE ANALYSIS")
        print("="*80)
        
        # Load configuration
        config = self.load_config()
        if not config:
            print("❌ Failed to load configuration")
            return False
        
        ssid = config.get('ssid')
        is_demo = config.get('is_demo', False)
        
        if not ssid:
            print("❌ No SSID found in configuration")
            return False
        
        print(f"🎯 Testing with {'DEMO' if is_demo else 'REAL'} account")
        print(f"🌐 Target server: {self.server_host}")
        print(f"📡 SSID: {ssid[:30]}... (truncated)")
        
        # Test 1: Network ping
        print(f"\n1. 🌐 Testing Network Ping Latency...")
        network_latencies = self.test_network_ping(5)
        network_stats = self.calculate_statistics(network_latencies, "Network Ping")
        
        # Test 2: TCP connection
        print(f"\n2. 🔌 Testing TCP Connection Latency...")
        tcp_latencies = self.test_tcp_connection_latency(5)
        tcp_stats = self.calculate_statistics(tcp_latencies, "TCP Connection")
        
        # Test 3: WebSocket connection
        print(f"\n3. 🔗 Testing WebSocket Connection...")
        success, conn_latency, auth_latency = self.connect_to_api(ssid, is_demo)
        
        if not success:
            print("❌ Failed to connect to Pocket Option API")
            return False
        
        print(f"✅ WebSocket connection established!")
        print(f"   Connection time: {conn_latency:.2f}ms")
        print(f"   Authentication time: {auth_latency:.2f}ms")
        
        # Test 4: API round-trip latency
        print(f"\n4. ⚡ Testing API Round-Trip Latency...")
        api_latencies, successful_requests = self.test_api_round_trip_latency(10)
        api_stats = self.calculate_statistics(api_latencies, "API Round-Trip")
        
        # Comprehensive analysis
        print(f"\n" + "="*80)
        print("📊 COMPREHENSIVE LATENCY ANALYSIS")
        print("="*80)
        
        if network_stats:
            print(f"🌐 Network ping: {network_stats['mean']:.1f}ms (min: {network_stats['min']:.1f}ms, max: {network_stats['max']:.1f}ms)")
        
        if tcp_stats:
            print(f"🔌 TCP connection: {tcp_stats['mean']:.1f}ms (min: {tcp_stats['min']:.1f}ms, max: {tcp_stats['max']:.1f}ms)")
        
        print(f"🔗 WebSocket setup: {conn_latency:.1f}ms")
        print(f"🔐 Authentication: {auth_latency:.1f}ms")
        
        if api_stats:
            print(f"⚡ API round-trip: {api_stats['mean']:.1f}ms (min: {api_stats['min']:.1f}ms, max: {api_stats['max']:.1f}ms)")
        
        # Trading performance assessment
        overall_rating = self.assess_trading_performance(network_stats, tcp_stats, api_stats)
        
        # Optimization recommendations
        print(f"\n💡 OPTIMIZATION RECOMMENDATIONS:")
        
        if network_stats and network_stats['mean'] > 100:
            print("   • Consider using a VPS closer to European servers")
            print("   • Check your internet connection quality")
        
        if tcp_stats and tcp_stats['stdev'] > 50:
            print("   • Network stability issues detected")
            print("   • Consider switching to a more stable internet provider")
        
        if conn_latency > 500:
            print("   • WebSocket connection is slow - check firewall/proxy settings")
        
        if api_stats and api_stats['mean'] > 100:
            print("   • API responses are slow - consider optimizing your code")
        
        print("   • Test during different times of day to identify peak hours")
        print("   • Monitor latency during live trading sessions")
        
        # Disconnect safely
        try:
            if self.api:
                logger.info("Disconnecting from API...")
                self.api.disconnect()
                time.sleep(1)
        except Exception as e:
            logger.warning(f"Disconnect warning: {e}")
        
        print(f"\n✅ Comprehensive latency testing completed!")
        print(f"🎯 Your connection rating: {overall_rating}")
        return True

def main():
    """Main function"""
    tester = FinalPocketOptionLatencyTester()
    success = tester.run_comprehensive_test()
    
    if success:
        print(f"\n🎉 Latency analysis complete! Check the assessment above for trading recommendations.")
    else:
        print(f"\n❌ Latency test failed. Please check your configuration and connection.")

if __name__ == "__main__":
    main()
