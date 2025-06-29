#!/usr/bin/env python3
"""
Diagnostic script to check and run SignalSniper_mod.py
"""
import os
import sys
import json
import subprocess
import shutil

def check_environment():
    """Check the environment setup."""
    print("=== Environment Check ===")
    print(f"Python version: {sys.version}")
    print(f"Current directory: {os.getcwd()}")
    print()

def check_channel_config():
    """Check if channel configuration exists and is properly set up."""
    print("=== Channel Configuration Check ===")
    
    # Check main telegram config
    telegram_config_path = "config/telegram_config.json"
    if os.path.exists(telegram_config_path):
        with open(telegram_config_path, 'r') as f:
            config = json.load(f)
        channel_name = config.get('channel_name', '')
        channel_id = config.get('channel_id', '')
        print(f"✓ Main config found")
        print(f"  - Channel name: {channel_name}")
        print(f"  - Channel ID: {channel_id}")
        
        # Check if channel-specific config exists
        # The channel manager converts the name to a safe filename
        safe_name = channel_name.lower().replace(' ', '_').replace('-', '_')
        safe_name = ''.join(c for c in safe_name if c.isalnum() or c == '_')
        channel_config_path = f"config/channels/{safe_name}.json"
        
        print(f"\n  Looking for channel config at: {channel_config_path}")
        if os.path.exists(channel_config_path):
            print(f"  ✓ Channel config exists")
        else:
            print(f"  ✗ Channel config NOT found")
            print(f"    Expected file: {channel_config_path}")
    else:
        print("✗ Main telegram config not found!")
    print()

def check_session_status():
    """Check session status."""
    print("=== Session Status Check ===")
    
    active_session_path = "sessions/active_session.json"
    if os.path.exists(active_session_path):
        with open(active_session_path, 'r') as f:
            session = json.load(f)
        print(f"✓ Active session found: {session.get('session_id', 'Unknown')}")
        print(f"  - Status: {session.get('status', 'Unknown')}")
        print(f"  - Started: {session.get('start_time', 'Unknown')}")
        print(f"  - Last activity: {session.get('last_activity', 'Unknown')}")
    else:
        print("✗ No active session found")
    print()

def check_dependencies():
    """Check if required dependencies are available."""
    print("=== Dependencies Check ===")
    
    # Check for required files
    required_files = [
        "SignalSniper_mod.py",
        "channel_manager.py",
        "session_manager.py",
        "timestamp_recorder.py",
        "src/parsers/multi_parser.py",
        "PocketOptionAPI-v2/pocketoptionapi/stable_api.py"
    ]
    
    for file in required_files:
        if os.path.exists(file):
            print(f"✓ {file}")
        else:
            print(f"✗ {file} - NOT FOUND")
    print()

def check_pocket_option_config():
    """Check Pocket Option configuration."""
    print("=== Pocket Option Configuration Check ===")
    
    po_config_path = "config/pocket_option_config.json"
    if os.path.exists(po_config_path):
        with open(po_config_path, 'r') as f:
            config = json.load(f)
        print("✓ Pocket Option config found")
        print(f"  - Demo mode: {config.get('is_demo', 'Unknown')}")
        print(f"  - SSID present: {'Yes' if config.get('ssid') else 'No'}")
        if config.get('ssid'):
            # Check if SSID looks valid
            ssid = config.get('ssid', '')
            if 'auth' in ssid and 'session' in ssid:
                print("  - SSID format: Looks valid")
            else:
                print("  - SSID format: May be invalid")
    else:
        print("✗ Pocket Option config not found!")
    print()

def run_bot():
    """Run the SignalSniper_mod.py bot."""
    print("=== Running SignalSniper_mod.py ===")
    print("Starting bot...\n")
    
    try:
        # Run the bot
        subprocess.run([sys.executable, "SignalSniper_mod.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Bot exited with error code: {e.returncode}")
    except KeyboardInterrupt:
        print("\n✓ Bot stopped by user")
    except Exception as e:
        print(f"\n✗ Error running bot: {str(e)}")

def main():
    """Main function."""
    print("SignalSniper Modular Bot Diagnostic Tool")
    print("=" * 50)
    print()
    
    # Run checks
    check_environment()
    check_channel_config()
    check_session_status()
    check_dependencies()
    check_pocket_option_config()
    
    # Ask if user wants to run the bot
    print("\n" + "=" * 50)
    response = input("\nAll checks complete. Do you want to run SignalSniper_mod.py? (y/n): ")
    
    if response.lower() == 'y':
        print()
        run_bot()
    else:
        print("\nDiagnostic complete. Bot not started.")

if __name__ == "__main__":
    main()
