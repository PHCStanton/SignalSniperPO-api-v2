#!/usr/bin/env python3
"""
Quick Latency Test for Pocket Option
====================================

This script provides a fast way to test the latency of your Pocket Option connection
for 1-minute trading signals. It's optimized for quick results and minimal setup.

Usage: python quick_latency_test.py
"""

import asyncio
import time
import json
from datetime import datetime

from BinaryOptionsToolsV2.pocketoption.asyncronous import PocketOptionAsync

async def quick_test():
    """Run a quick latency test"""
    print("🚀 POCKET OPTION QUICK LATENCY TEST")
    print("=" * 50)
    
    try:
        # Load configuration
        with open("config/pocket_option_config.json", "r") as f:
            config = json.load(f)
        ssid = config.get("ssid")

        if not ssid:
            print("❌ SSID not found in config/pocket_option_config.json")
            return

        # Initialize client
        client = PocketOptionAsync(ssid)
        print("✅ Connected to Pocket Option")
        
        # Get balance
        balance = await client.balance()
        print(f"💰 Balance: ${balance:.2f}")
        
        # Test primary assets for 1-minute signals
        assets = ["GBPUSD_otc", "EURUSD_otc", "USDJPY_otc"]
        
        print(f"\n📊 Testing {len(assets)} assets for 1-minute signal optimization...")
        print("-" * 50)
        
        best_asset = None
        best_latency = float('inf')
        results = []
        
        for asset in assets:
            start_time = time.perf_counter()
            
            try:
                # Get payout (most critical for trading decisions)
                payout = await client.payout(asset)
                latency = (time.perf_counter() - start_time) * 1000
                
                results.append({
                    'asset': asset,
                    'payout': payout,
                    'latency': latency
                })
                
                if latency < best_latency:
                    best_latency = latency
                    best_asset = asset
                
                # Performance indicator
                if latency < 50:
                    indicator = "🟢 EXCELLENT"
                elif latency < 100:
                    indicator = "🟡 GOOD"
                elif latency < 200:
                    indicator = "🟠 FAIR"
                else:
                    indicator = "🔴 POOR"
                
                print(f"{asset:12} | {payout:3}% | {latency:6.2f}ms | {indicator}")
                
            except Exception as e:
                print(f"{asset:12} | ERROR: {str(e)[:30]}...")
        
        # Summary
        print("-" * 50)
        if best_asset:
            print(f"🏆 FASTEST: {best_asset} ({best_latency:.2f}ms)")
            
            # Find best payout
            best_payout_asset = max(results, key=lambda x: x['payout'] if x['payout'] else 0)
            print(f"💰 BEST PAYOUT: {best_payout_asset['asset']} ({best_payout_asset['payout']}%)")
            
            # Recommendation
            balanced = min(results, key=lambda x: x['latency'] / (x['payout'] if x['payout'] else 1))
            print(f"⚖️  RECOMMENDED: {balanced['asset']} (Best speed/profit ratio)")
        
        # Performance assessment
        avg_latency = sum(r['latency'] for r in results) / len(results)
        print(f"\n📈 AVERAGE LATENCY: {avg_latency:.2f}ms")
        
        if avg_latency < 100:
            print("🎯 VERDICT: EXCELLENT - Optimal for 1-minute signals!")
            print(f"   Time available for signal processing: {60000 - avg_latency:.0f}ms")
        elif avg_latency < 500:
            print("🎯 VERDICT: GOOD - Suitable for 1-minute signals")
        else:
            print("🎯 VERDICT: NEEDS OPTIMIZATION - May impact 1-minute signal effectiveness")
        
        print(f"\n⏰ Test completed at: {datetime.now().strftime('%H:%M:%S')}")
        print("📋 For detailed analysis, run: python trading_latency_analyzer.py")
        
    except FileNotFoundError:
        print("❌ Error: config/pocket_option_config.json not found.")
        print("   Make sure your SSID is configured in the config file.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(quick_test())
