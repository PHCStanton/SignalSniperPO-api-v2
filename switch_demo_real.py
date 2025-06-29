#!/usr/bin/env python3
"""
switch_demo_real.py - Switch between demo and real trading modes
"""

import json
import os

def switch_mode():
    config_path = "config/pocket_option_config.json"
    
    # Load current config
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    current_mode = config.get("is_demo", True)
    
    print(f"Current mode: {'DEMO' if current_mode else 'REAL'}")
    print("\nSelect new mode:")
    print("1. DEMO mode")
    print("2. REAL mode")
    
    choice = input("\nEnter choice (1 or 2): ").strip()
    
    if choice == "1":
        config["is_demo"] = True
        print("\n✅ Switched to DEMO mode")
    elif choice == "2":
        config["is_demo"] = False
        print("\n✅ Switched to REAL mode")
        print("⚠️  WARNING: You are now in REAL trading mode!")
    else:
        print("\n❌ Invalid choice")
        return
    
    # Save updated config
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"\n📝 Updated {config_path}")
    print("\n⚠️  IMPORTANT: Make sure your SSID matches the selected mode!")
    print("   - For DEMO: Use an SSID from a demo account")
    print("   - For REAL: Use an SSID from a real account")
    print("\nRestart the bot for changes to take effect.")

if __name__ == "__main__":
    switch_mode()
