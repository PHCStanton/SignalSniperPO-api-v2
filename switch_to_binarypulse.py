#!/usr/bin/env python3
"""
Quick script to switch to BinaryPulse bot for testing
"""

import json
import os
from datetime import datetime

def switch_to_binarypulse():
    """Switch telegram config to BinaryPulse bot for testing"""
    
    config_file = "config/telegram_config.json"
    
    # Create backup
    backup_file = f"{config_file}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    try:
        # Load current config
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Create backup
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        print(f"✅ Backup created: {backup_file}")
        
        # Update config for BinaryPulse bot
        config.update({
            "channel_name": "BinaryPulse Bot",
            "channel_id": "@BinaryPulse_bot",  # Bot username for testing
            "log_all_messages": True,
            "pair_match_window": 60
        })
        
        # Save updated config
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        print("✅ Successfully switched to BinaryPulse Bot configuration")
        print(f"   Channel: {config['channel_name']}")
        print(f"   Channel ID: {config['channel_id']}")
        print("\n🚀 Ready to test BinaryPulse integration with SignalSniper_mod.py")
        
        return True
        
    except Exception as e:
        print(f"❌ Error switching configuration: {e}")
        return False

if __name__ == "__main__":
    switch_to_binarypulse()
