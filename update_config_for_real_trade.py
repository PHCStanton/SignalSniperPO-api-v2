#!/usr/bin/env python3
"""
update_config_for_real_trade.py - Update configuration for real trade execution

This script updates the bot_config.json file to prepare for real trade execution.
It sets test_mode to false and adjusts the trade_amount to a minimal value for safety.
"""

import os
import json
import argparse
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def update_config(config_file, test_mode=False, trade_amount=1):
    """
    Update the configuration file for real trade execution.
    
    Args:
        config_file: Path to the configuration file
        test_mode: Whether to enable test mode
        trade_amount: Amount to trade
    """
    try:
        # Check if file exists
        if not os.path.exists(config_file):
            logger.error(f"Configuration file not found: {config_file}")
            return False
        
        # Read current configuration
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        # Save original values
        original_test_mode = config.get('test_mode', True)
        original_trade_amount = config.get('trade_amount', 10)
        
        # Update configuration
        config['test_mode'] = test_mode
        config['trade_amount'] = trade_amount
        
        # Write updated configuration
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=4)
        
        logger.info(f"Configuration updated successfully:")
        logger.info(f"  test_mode: {original_test_mode} -> {test_mode}")
        logger.info(f"  trade_amount: {original_trade_amount} -> {trade_amount}")
        
        return True
    except Exception as e:
        logger.error(f"Error updating configuration: {str(e)}")
        return False

def main():
    """Main function to parse arguments and update configuration."""
    parser = argparse.ArgumentParser(description='Update configuration for real trade execution')
    parser.add_argument('--config', type=str, default='config/bot_config.json', help='Path to configuration file')
    parser.add_argument('--test-mode', action='store_true', help='Enable test mode (default: false)')
    parser.add_argument('--trade-amount', type=float, default=1, help='Amount to trade (default: 1)')
    
    args = parser.parse_args()
    
    print("\nUpdate Configuration for Real Trade Execution")
    print("--------------------------------------------")
    print(f"Configuration file: {args.config}")
    print(f"Test mode: {'Enabled' if args.test_mode else 'Disabled'}")
    print(f"Trade amount: ${args.trade_amount}")
    print("")
    
    # Confirm with user
    confirm = input("Do you want to proceed with these settings? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Operation cancelled.")
        return
    
    # Update configuration
    if update_config(args.config, args.test_mode, args.trade_amount):
        print("\nConfiguration updated successfully.")
        print("You can now run the bot with the updated configuration:")
        print(f"  python self_bot.py --config {args.config}")
    else:
        print("\nFailed to update configuration.")

if __name__ == "__main__":
    main()
