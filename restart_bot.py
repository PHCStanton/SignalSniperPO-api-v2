#!/usr/bin/env python
"""
Bot Restart Utility for SelfBot v1.0

This script helps stop and restart the SelfBot v1.0.
It provides options to update configuration before restarting.
"""

import os
import sys
import json
import logging
import subprocess
import time
import signal
import psutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

BOT_CONFIG_FILE = 'config/bot_config.json'
PO_CONFIG_FILE = 'config/pocket_option_config.json'

def find_bot_process():
    """Find the self_bot.py process if it's running."""
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info['cmdline']
            if cmdline and len(cmdline) > 1 and 'python' in cmdline[0].lower() and 'self_bot.py' in cmdline[1]:
                return proc
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return None

def stop_bot():
    """Stop the bot if it's running."""
    proc = find_bot_process()
    if proc:
        logger.info(f"Found bot process (PID: {proc.pid}). Stopping...")
        try:
            proc.terminate()
            proc.wait(timeout=10)
            logger.info("Bot stopped successfully.")
            return True
        except Exception as e:
            logger.error(f"Error stopping bot: {str(e)}")
            return False
    else:
        logger.info("Bot is not currently running.")
        return True

def update_bot_config():
    """Update the bot configuration."""
    if not os.path.exists(BOT_CONFIG_FILE):
        logger.error(f"Bot configuration file not found: {BOT_CONFIG_FILE}")
        return False
    
    try:
        with open(BOT_CONFIG_FILE, 'r') as f:
            config = json.load(f)
        
        print("\nCurrent Bot Configuration:")
        print(f"- Test Mode: {'Enabled' if config.get('test_mode', True) else 'Disabled'}")
        print(f"- Trade Amount: ${config.get('trade_amount', 10)}")
        print(f"- Max Daily Trades: {config.get('max_daily_trades', 20)}")
        print(f"- Max Daily Loss: ${config.get('max_daily_loss', 100)}")
        
        update = input("\nDo you want to update the bot configuration? (y/n): ").strip().lower()
        if update != 'y':
            return True
        
        # Update test mode
        test_mode_input = input("\nEnable test mode? (y/n, default: n): ").strip().lower()
        config['test_mode'] = test_mode_input == 'y'
        
        # Update trade amount
        try:
            trade_amount = float(input("\nEnter trade amount (default: $1): $").strip() or "1")
            config['trade_amount'] = trade_amount
        except ValueError:
            logger.warning("Invalid trade amount. Using default: $1")
            config['trade_amount'] = 1
        
        # Save updated configuration
        with open(BOT_CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
        
        logger.info(f"Bot configuration updated successfully.")
        return True
        
    except Exception as e:
        logger.error(f"Error updating bot configuration: {str(e)}")
        return False

def start_bot():
    """Start the bot."""
    try:
        logger.info("Starting bot...")
        subprocess.Popen([sys.executable, 'self_bot.py', '--verbose'])
        logger.info("Bot started successfully.")
        return True
    except Exception as e:
        logger.error(f"Error starting bot: {str(e)}")
        return False

def main():
    """Main function to restart the bot."""
    print("\nBot Restart Utility for SelfBot v1.0")
    print("-----------------------------------")
    
    # Check if bot is running
    bot_running = find_bot_process() is not None
    if bot_running:
        print("\nThe bot is currently running.")
        stop = input("Do you want to stop it? (y/n): ").strip().lower()
        if stop != 'y':
            print("Operation cancelled.")
            return
        
        # Stop the bot
        if not stop_bot():
            logger.error("Failed to stop the bot. Please stop it manually.")
            return
    else:
        print("\nThe bot is not currently running.")
    
    # Update configuration
    print("\nWould you like to update the configuration before restarting?")
    update_config = input("(y/n): ").strip().lower()
    if update_config == 'y':
        if not update_bot_config():
            logger.error("Failed to update bot configuration.")
            return
    
    # Ask about SSID refresh
    print("\nDo you need to refresh the SSID?")
    refresh_ssid = input("(y/n): ").strip().lower()
    if refresh_ssid == 'y':
        print("\nPlease run 'python refresh_ssid.py' to update the SSID.")
        print("After updating the SSID, run this script again to start the bot.")
        return
    
    # Start the bot
    start = input("\nDo you want to start the bot now? (y/n): ").strip().lower()
    if start == 'y':
        if start_bot():
            print("\nBot started successfully. You can monitor it in the terminal.")
        else:
            logger.error("Failed to start the bot.")
    else:
        print("\nBot not started. You can start it manually with 'python self_bot.py --verbose'")

if __name__ == "__main__":
    main()
