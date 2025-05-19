#!/usr/bin/env python3
"""
simulate_signals.py - Simulates trading signals for testing the Pocket Option trading bot.

This script generates simulated trading signals in the two-message format used by
Simon in the "BINARY TRADING CLUB" channel. It can be used to test the signal parsing
and execution logic of the trading bot without needing actual signals from the channel.
"""

import os
import sys
import json
import random
import asyncio
import logging
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("simulate_signals.log")
    ]
)
logger = logging.getLogger(__name__)

# Default assets to use for simulated signals
DEFAULT_ASSETS = [
    "EUR/USD",
    "GBP/USD",
    "USD/JPY",
    "EUR/JPY",
    "AUD/USD",
    "USD/CAD",
    "NZD/USD",
    "EUR/GBP"
]

# Default OTC assets (some assets may be marked as OTC)
DEFAULT_OTC_ASSETS = [
    "EUR/USD",
    "GBP/USD",
    "USD/JPY"
]

# Default expiry times in minutes
DEFAULT_EXPIRY_TIMES = [1, 2, 3, 5]

# Default signal count
DEFAULT_SIGNAL_COUNT = 5

class SignalSimulator:
    def __init__(
        self,
        assets: Optional[List[str]] = None,
        otc_assets: Optional[List[str]] = None,
        expiry_times: Optional[List[int]] = None,
        signal_count: int = DEFAULT_SIGNAL_COUNT,
        delay_between_signals: int = 60,
        delay_between_messages: int = 5,
        output_file: Optional[str] = None,
        verbose: bool = False
    ):
        """
        Initialize the signal simulator.
        
        Args:
            assets: List of assets to use for simulated signals
            otc_assets: List of assets that can be marked as OTC
            expiry_times: List of expiry times in minutes
            signal_count: Number of signals to generate
            delay_between_signals: Delay between signals in seconds
            delay_between_messages: Delay between first and second message in seconds
            output_file: File to write signals to (optional)
            verbose: Enable verbose output
        """
        self.assets = assets or DEFAULT_ASSETS
        self.otc_assets = otc_assets or DEFAULT_OTC_ASSETS
        self.expiry_times = expiry_times or DEFAULT_EXPIRY_TIMES
        self.signal_count = signal_count
        self.delay_between_signals = delay_between_signals
        self.delay_between_messages = delay_between_messages
        self.output_file = output_file
        self.verbose = verbose
        
        # Set logging level
        if verbose:
            logger.setLevel(logging.DEBUG)
            
        # Signal tracking
        self.signals = []
        
    def generate_signal(self) -> Dict:
        """
        Generate a random trading signal.
        
        Returns:
            Dictionary with signal details
        """
        # Select random asset
        asset = random.choice(self.assets)
        
        # Determine if asset is OTC
        is_otc = asset in self.otc_assets and random.random() < 0.5
        
        # Select random direction
        direction = random.choice(["HIGHER", "LOWER"])
        
        # Select random expiry time
        expiry = random.choice(self.expiry_times)
        
        # Generate random timer (within next 5 minutes)
        now = datetime.now()
        timer_time = now + timedelta(minutes=random.randint(1, 5))
        timer = timer_time.strftime("%H:%M:%S")
        
        # Generate signal number (e.g., "First", "Second", etc.)
        signal_numbers = ["First", "Second", "Third", "Fourth", "Fifth", "Sixth", "Seventh", "Eighth", "Ninth", "Tenth"]
        signal_number = signal_numbers[min(len(self.signals), len(signal_numbers) - 1)]
        
        # Create signal
        signal = {
            "asset": asset,
            "is_otc": is_otc,
            "direction": direction,
            "expiry": expiry,
            "timer": timer,
            "signal_number": signal_number,
            "timestamp": datetime.now().isoformat()
        }
        
        return signal
    
    def format_first_message(self, signal: Dict) -> str:
        """
        Format the first message of the signal.
        
        Args:
            signal: Signal details
            
        Returns:
            Formatted message
        """
        asset_display = f"{signal['asset']}{' (OTC)' if signal['is_otc'] else ''}"
        return f"Trading Pair: {asset_display}"
    
    def format_second_message(self, signal: Dict) -> str:
        """
        Format the second message of the signal.
        
        Args:
            signal: Signal details
            
        Returns:
            Formatted message
        """
        direction_arrow = "⬆" if signal["direction"] == "HIGHER" else "⬇"
        return (
            f"SET THE TIMER TO {signal['timer']}! "
            f"{signal['signal_number']} signal: "
            f"Currency pair {signal['asset']} {signal['direction']} {direction_arrow} "
            f"Trade time: {signal['expiry']} MIN"
        )
    
    async def simulate_signals(self) -> List[Dict]:
        """
        Simulate trading signals.
        
        Returns:
            List of simulated signals
        """
        logger.info(f"Simulating {self.signal_count} trading signals...")
        
        for i in range(self.signal_count):
            # Generate signal
            signal = self.generate_signal()
            self.signals.append(signal)
            
            # Format messages
            first_message = self.format_first_message(signal)
            second_message = self.format_second_message(signal)
            
            # Print first message
            logger.info(f"Signal {i+1}/{self.signal_count} - First Message:")
            print(f"\n{first_message}")
            
            # Wait between messages
            await asyncio.sleep(self.delay_between_messages)
            
            # Print second message
            logger.info(f"Signal {i+1}/{self.signal_count} - Second Message:")
            print(f"\n{second_message}")
            
            # Wait between signals
            if i < self.signal_count - 1:
                logger.info(f"Waiting {self.delay_between_signals} seconds until next signal...")
                await asyncio.sleep(self.delay_between_signals)
        
        # Save signals to file if specified
        if self.output_file:
            self.save_signals()
            
        return self.signals
    
    def save_signals(self) -> None:
        """Save signals to file."""
        if not self.signals:
            logger.warning("No signals to save.")
            return
            
        try:
            with open(self.output_file, 'w') as f:
                json.dump(self.signals, f, indent=2)
            logger.info(f"Signals saved to {self.output_file}")
        except Exception as e:
            logger.error(f"Error saving signals to {self.output_file}: {str(e)}")

async def main():
    parser = argparse.ArgumentParser(description='Simulate trading signals for testing the Pocket Option trading bot')
    parser.add_argument('-a', '--assets', type=str, nargs='+', help='Assets to use for simulated signals')
    parser.add_argument('--otc', type=str, nargs='+', help='Assets that can be marked as OTC')
    parser.add_argument('-e', '--expiry', type=int, nargs='+', help='Expiry times in minutes')
    parser.add_argument('-c', '--count', type=int, default=DEFAULT_SIGNAL_COUNT, help='Number of signals to generate')
    parser.add_argument('-d', '--delay', type=int, default=60, help='Delay between signals in seconds')
    parser.add_argument('-m', '--message-delay', type=int, default=5, help='Delay between first and second message in seconds')
    parser.add_argument('-o', '--output', type=str, help='File to write signals to')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
    
    args = parser.parse_args()
    
    # Create simulator
    simulator = SignalSimulator(
        assets=args.assets,
        otc_assets=args.otc,
        expiry_times=args.expiry,
        signal_count=args.count,
        delay_between_signals=args.delay,
        delay_between_messages=args.message_delay,
        output_file=args.output,
        verbose=args.verbose
    )
    
    # Simulate signals
    await simulator.simulate_signals()

if __name__ == "__main__":
    print("Pocket Option Trading Bot - Signal Simulator")
    print("-------------------------------------------")
    print("This script simulates trading signals in the format used by Simon in the BINARY TRADING CLUB channel.")
    print("It can be used to test the signal parsing and execution logic of the trading bot.")
    print("")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nSignal simulation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError during signal simulation: {str(e)}")
        sys.exit(1)
