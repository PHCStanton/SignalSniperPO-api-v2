#!/usr/bin/env python
"""
SSID Refresh Utility for SelfBot v1.0

This script helps refresh the SSID in the Pocket Option configuration file.
It prompts the user for a new SSID and updates the configuration file.
"""

import json
import os
import logging
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

CONFIG_FILE = 'config/pocket_option_config.json'

def main():
    """Main function to refresh the SSID."""
    print("\nSSID Refresh Utility for SelfBot v1.0")
    print("-------------------------------------")
    
    # Check if config file exists
    if not os.path.exists(CONFIG_FILE):
        logger.error(f"Configuration file not found: {CONFIG_FILE}")
        return
    
    # Load current configuration
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
        
        # Display current SSID (truncated for security)
        current_ssid = config.get('ssid', '')
        if current_ssid:
            truncated_ssid = current_ssid[:20] + "..." + current_ssid[-20:] if len(current_ssid) > 40 else current_ssid
            print(f"\nCurrent SSID (truncated): {truncated_ssid}")
        else:
            print("\nNo current SSID found.")
        
        # Prompt for new SSID
        print("\nPlease enter the new SSID:")
        print("(Note: This should be the full SSID string from the Pocket Option website)")
        new_ssid = input("SSID: ").strip()
        
        if not new_ssid:
            logger.error("No SSID provided. Aborting.")
            return
        
        # Confirm update
        print(f"\nYou are about to update the SSID in {CONFIG_FILE}.")
        confirm = input("Proceed? (y/n): ").strip().lower()
        
        if confirm != 'y':
            logger.info("Operation cancelled by user.")
            return
        
        # Update configuration
        config['ssid'] = new_ssid
        
        # Save updated configuration
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.info(f"SSID updated successfully in {CONFIG_FILE}")
        logger.info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Suggest next steps
        print("\nNext Steps:")
        print("1. Verify the SSID is valid: python test_ssid_direct.py")
        print("2. Start the bot: python self_bot.py --verbose")
        
    except Exception as e:
        logger.error(f"Error updating SSID: {str(e)}")

if __name__ == "__main__":
    main()
