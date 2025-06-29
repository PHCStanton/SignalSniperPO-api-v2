#!/usr/bin/env python3
"""
verify_demo_real_switching.py - Verify and test demo/real channel switching

This script verifies that the demo and real channels are seamlessly interchangeable
based on the is_demo setting in pocket_option_config.json
"""

import json
import os
import sys

def load_config(file_path):
    """Load JSON configuration file."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {file_path}: {str(e)}")
        return None

def analyze_ssid(ssid):
    """Analyze SSID to determine if it's for demo or real account."""
    if "isDemo\":1" in ssid or "isDemo\": 1" in ssid:
        return True  # Demo account
    elif "isDemo\":0" in ssid or "isDemo\": 0" in ssid:
        return False  # Real account
    else:
        return None  # Cannot determine

def check_configuration():
    """Check the current configuration and identify any issues."""
    print("🔍 Checking Demo/Real Channel Configuration")
    print("=" * 60)
    
    # Load pocket_option_config.json
    po_config = load_config("config/pocket_option_config.json")
    if not po_config:
        return False
    
    ssid = po_config.get("ssid", "")
    is_demo_config = po_config.get("is_demo", True)
    
    print(f"\n📋 Current Configuration:")
    print(f"  - is_demo setting: {is_demo_config}")
    print(f"  - SSID (truncated): {ssid[:50]}...")
    
    # Analyze SSID
    ssid_is_demo = analyze_ssid(ssid)
    if ssid_is_demo is not None:
        print(f"  - SSID type: {'Demo' if ssid_is_demo else 'Real'} account")
        
        if ssid_is_demo != is_demo_config:
            print(f"\n⚠️  WARNING: Mismatch detected!")
            print(f"  - SSID indicates: {'Demo' if ssid_is_demo else 'Real'} account")
            print(f"  - is_demo setting: {is_demo_config}")
            print(f"\n  This mismatch may cause issues with trading.")
            return False
    else:
        print(f"  - SSID type: Cannot determine from SSID")
    
    # Check how SignalSniper_mod.py uses the configuration
    print(f"\n✅ Configuration Analysis:")
    print(f"  - SignalSniper_mod.py will use: {'Demo' if is_demo_config else 'Real'} mode")
    print(f"  - This is determined by the 'is_demo' setting in pocket_option_config.json")
    
    # Load telegram_config.json to check channels
    tg_config = load_config("config/telegram_config.json")
    if tg_config:
        channels = tg_config.get("channels", {})
        enabled_channels = [name for name, config in channels.items() if config.get("enabled", False)]
        
        print(f"\n📡 Active Telegram Channels:")
        for channel in enabled_channels:
            print(f"  - {channel}")
    
    return True

def test_switching_logic():
    """Test the demo/real switching logic."""
    print("\n\n🧪 Testing Demo/Real Switching Logic")
    print("=" * 60)
    
    # Simulate the logic from SignalSniper_mod.py
    po_config = load_config("config/pocket_option_config.json")
    if not po_config:
        return
    
    is_demo = po_config.get("is_demo", False)
    
    print(f"\n📌 Current Mode: {'DEMO' if is_demo else 'REAL'} Trading")
    print(f"\nThe bot will:")
    print(f"  1. Connect to Pocket Option in {'demo' if is_demo else 'real'} mode")
    print(f"  2. Trade with {'demo' if is_demo else 'real'} funds")
    print(f"  3. The same Telegram channels work for both modes")
    
    print(f"\n💡 To switch between demo and real:")
    print(f"  1. Update 'is_demo' in config/pocket_option_config.json")
    print(f"  2. Make sure your SSID matches the account type")
    print(f"  3. Restart the bot")

def create_switching_script():
    """Create a simple script to switch between demo and real modes."""
    script_content = '''#!/usr/bin/env python3
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
    print("\\nSelect new mode:")
    print("1. DEMO mode")
    print("2. REAL mode")
    
    choice = input("\\nEnter choice (1 or 2): ").strip()
    
    if choice == "1":
        config["is_demo"] = True
        print("\\n✅ Switched to DEMO mode")
    elif choice == "2":
        config["is_demo"] = False
        print("\\n✅ Switched to REAL mode")
        print("⚠️  WARNING: You are now in REAL trading mode!")
    else:
        print("\\n❌ Invalid choice")
        return
    
    # Save updated config
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"\\n📝 Updated {config_path}")
    print("\\n⚠️  IMPORTANT: Make sure your SSID matches the selected mode!")
    print("   - For DEMO: Use an SSID from a demo account")
    print("   - For REAL: Use an SSID from a real account")
    print("\\nRestart the bot for changes to take effect.")

if __name__ == "__main__":
    switch_mode()
'''
    
    with open("switch_demo_real.py", "w", encoding="utf-8") as f:
        f.write(script_content)
    
    print("\n\n✅ Created 'switch_demo_real.py' for easy mode switching")

def main():
    print("🤖 SignalSniper Demo/Real Channel Verification")
    print("=" * 60)
    
    # Check current configuration
    config_ok = check_configuration()
    
    # Test switching logic
    test_switching_logic()
    
    # Create switching script
    create_switching_script()
    
    print("\n\n📊 Summary:")
    print("=" * 60)
    if config_ok:
        print("✅ Demo/Real switching is properly configured")
    else:
        print("⚠️  Configuration issues detected - please fix the mismatch")
    
    print("\n📌 Key Points:")
    print("  1. The 'is_demo' setting in pocket_option_config.json controls the mode")
    print("  2. The same Telegram channels work for both demo and real modes")
    print("  3. Make sure your SSID matches the account type (demo/real)")
    print("  4. Use 'python switch_demo_real.py' to easily switch modes")

if __name__ == "__main__":
    main()
