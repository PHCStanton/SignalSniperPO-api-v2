#!/usr/bin/env python3
"""
channel-switch.py - Channel Configuration Updater for HFT SignalSniper Bot

This script allows you to update the Telegram channel configuration in 
config/telegram_config.json before running the bot. It's a standalone utility
that doesn't interfere with the running bot.

Usage:
    python channel-switch.py

The script will prompt you for:
1. Channel Name
2. Channel ID

After updating the configuration, restart your bot to use the new channel.
"""

import os
import json
import sys
from datetime import datetime

def load_config(config_file):
    """Load the current Telegram configuration."""
    try:
        if not os.path.exists(config_file):
            print(f"❌ Configuration file not found: {config_file}")
            return None
        
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        print(f"✅ Loaded configuration from {config_file}")
        return config
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing JSON configuration: {str(e)}")
        return None
    except Exception as e:
        print(f"❌ Error loading configuration: {str(e)}")
        return None

def create_backup(config_file):
    """Create a backup of the current configuration."""
    try:
        backup_file = f"{config_file}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        with open(config_file, 'r', encoding='utf-8') as src:
            with open(backup_file, 'w', encoding='utf-8') as dst:
                dst.write(src.read())
        
        print(f"✅ Backup created: {backup_file}")
        return True
    except Exception as e:
        print(f"❌ Error creating backup: {str(e)}")
        return False

def display_current_config(config):
    """Display the current channel configuration."""
    print("\n" + "="*60)
    print("📡 CURRENT TELEGRAM CHANNEL CONFIGURATION")
    print("="*60)
    print(f"Channel Name: {config.get('channel_name', 'Not set')}")
    print(f"Channel ID: {config.get('channel_id', 'Not set')}")
    print(f"API ID: {config.get('api_id', 'Not set')}")
    print(f"Session Name: {config.get('session_name', 'Not set')}")
    print("="*60)

def validate_channel_id(channel_id_str):
    """Validate and convert channel ID to integer."""
    try:
        # Remove any whitespace
        channel_id_str = channel_id_str.strip()
        
        # Handle negative channel IDs (which are common for Telegram channels)
        if channel_id_str.startswith('-'):
            channel_id = int(channel_id_str)
        else:
            # If positive, assume it should be negative for channels
            channel_id = int(channel_id_str)
            if channel_id > 0:
                print(f"⚠️  Note: Channel ID {channel_id} is positive. Most Telegram channels have negative IDs.")
                confirm = input("Do you want to make it negative? (y/n): ").strip().lower()
                if confirm == 'y':
                    channel_id = -abs(channel_id)
        
        return channel_id
    except ValueError:
        print(f"❌ Invalid channel ID format: {channel_id_str}")
        return None

def get_user_input(config):
    """Get new channel information from user input."""
    print("\n" + "="*60)
    print("🔄 CHANNEL SWITCHING TOOL")
    print("="*60)
    print("Enter the new channel information:")
    print("(Press Enter to keep current value)")
    print("-"*60)
    
    # Get channel name
    current_name = config.get('channel_name', '')
    print(f"\nCurrent Channel Name: {current_name}")
    new_name = input("Enter new Channel Name: ").strip()
    
    if not new_name:
        new_name = current_name
        print(f"✅ Keeping current channel name: {new_name}")
    else:
        print(f"✅ New channel name: {new_name}")
    
    # Get channel ID
    current_id = config.get('channel_id', '')
    print(f"\nCurrent Channel ID: {current_id}")
    new_id_str = input("Enter new Channel ID: ").strip()
    
    if not new_id_str:
        new_id = current_id
        print(f"✅ Keeping current channel ID: {new_id}")
    else:
        new_id = validate_channel_id(new_id_str)
        if new_id is None:
            print("❌ Invalid channel ID. Keeping current value.")
            new_id = current_id
        else:
            print(f"✅ New channel ID: {new_id}")
    
    return {
        'channel_name': new_name,
        'channel_id': new_id
    }

def save_config(config_file, config):
    """Save the updated configuration."""
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Configuration saved to {config_file}")
        return True
    except Exception as e:
        print(f"❌ Error saving configuration: {str(e)}")
        return False

def main():
    """Main function."""
    print("🎯 HFT SignalSniper - Channel Configuration Tool")
    print("="*60)
    
    config_file = "config/telegram_config.json"
    
    # Load current configuration
    config = load_config(config_file)
    if config is None:
        sys.exit(1)
    
    # Display current configuration
    display_current_config(config)
    
    # Ask if user wants to proceed
    print("\n" + "-"*60)
    proceed = input("Do you want to update the channel configuration? (y/n): ").strip().lower()
    if proceed != 'y':
        print("❌ Operation cancelled.")
        sys.exit(0)
    
    # Create backup
    if not create_backup(config_file):
        print("⚠️  Could not create backup. Continue anyway? (y/n): ", end="")
        if input().strip().lower() != 'y':
            print("❌ Operation cancelled.")
            sys.exit(1)
    
    # Get new channel information
    new_channel_info = get_user_input(config)
    
    # Update configuration
    config['channel_name'] = new_channel_info['channel_name']
    config['channel_id'] = new_channel_info['channel_id']
    
    # Show summary of changes
    print("\n" + "="*60)
    print("📋 CONFIGURATION SUMMARY")
    print("="*60)
    print(f"Channel Name: {config['channel_name']}")
    print(f"Channel ID: {config['channel_id']}")
    print("="*60)
    
    # Confirm changes
    confirm = input("\nSave these changes? (y/n): ").strip().lower()
    if confirm != 'y':
        print("❌ Changes not saved.")
        sys.exit(0)
    
    # Save configuration
    if save_config(config_file, config):
        print("\n" + "="*60)
        print("✅ CHANNEL CONFIGURATION UPDATED SUCCESSFULLY!")
        print("="*60)
        print("📌 Next steps:")
        print("   1. The configuration has been updated")
        print("   2. Start/restart your bot to use the new channel")
        print("   3. The bot will now monitor the new channel for signals")
        print("="*60)
    else:
        print("❌ Failed to save configuration.")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        sys.exit(1)
