#!/usr/bin/env python3
"""
Test script to diagnose and run SignalSniper_mod.py
"""
import os
import sys
import json
import subprocess

def check_channel_config():
    """Check if channel configuration exists and is properly set up."""
    print("=== Checking Channel Configuration ===")
    
    # Check main telegram config
    telegram_config_path = "config/telegram_config.json"
    if os.path.exists(telegram_config_path):
        with open(telegram_config_path, 'r') as f:
            config = json.load(f)
        channel_name = config.get('channel_name', '')
        print(f"✓ Main config channel: {channel_name}")
        
        # Check if channel config file exists
        safe_name = channel_name.lower().replace(' ', '_').replace('-', '_')
        safe_name = ''.join(c for c in safe_name if c.isalnum() or c == '_')
        channel_config_path = f"
