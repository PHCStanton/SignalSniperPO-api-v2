#!/usr/bin/env python3
"""
Fix session limit and SSID issues for SignalSniper bot
"""

import json
import os
from datetime import datetime, timezone
import pytz

def reset_daily_sessions():
    """Reset the daily session count"""
    sessions_file = "sessions/sessions.json"
    
    if os.path.exists(sessions_file):
        # Backup current sessions
        backup_file = f"sessions/sessions_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(sessions_file, 'r') as f:
            sessions = json.load(f)
        
        with open(backup_file, 'w') as f:
            json.dump(sessions, f, indent=2)
        
        print(f"✓ Backed up sessions to {backup_file}")
        
        # Clear sessions for today to reset the limit
        today = datetime.now(pytz.UTC).date().isoformat()
        filtered_sessions = [s for s in sessions if not s.get('start_time', '').startswith(today)]
        
        with open(sessions_file, 'w') as f:
            json.dump(filtered_sessions, f, indent=2)
        
        print(f"✓ Reset daily session limit (removed {len(sessions) - len(filtered_sessions)} sessions from today)")
    else:
        print("✗ No sessions file found")

def update_ssid():
    """Guide user to update SSID"""
    print("\n" + "="*60)
    print("SSID UPDATE REQUIRED")
    print("="*60)
    print("\nThe Pocket Option SSID has expired. To get a new one:")
    print("\n1. Open Chrome/Edge browser")
    print("2. Go to https://pocketoption.com")
    print("3. Log in to your account")
    print("4. Press F12 to open Developer Tools")
    print("5. Go to the 'Application' tab")
    print("6. In the left sidebar, expand 'Cookies' > 'https://pocketoption.com'")
    print("7. Find the cookie named 'ssid'")
    print("8. Copy the entire value (it's a long string)")
    print("\n" + "="*60)
    
    new_ssid = input("\nPaste the new SSID here (or press Enter to skip): ").strip()
    
    if new_ssid:
        # Update .env file
        env_file = ".env"
        if os.path.exists(env_file):
            with open(env_file, 'r') as f:
                lines = f.readlines()
            
            # Update or add SSID
            ssid_found = False
            for i, line in enumerate(lines):
                if line.startswith('SSID='):
                    lines[i] = f'SSID={new_ssid}\n'
                    ssid_found = True
                    break
            
            if not ssid_found:
                lines.append(f'\nSSID={new_ssid}\n')
            
            with open(env_file, 'w') as f:
                f.writelines(lines)
            
            print(f"\n✓ Updated SSID in {env_file}")
        else:
            # Create .env file
            with open(env_file, 'w') as f:
                f.write(f'SSID={new_ssid}\n')
            print(f"\n✓ Created {env_file} with new SSID")
    else:
        print("\n⚠ SSID update skipped. The bot will not be able to connect to Pocket Option.")

def main():
    print("SignalSniper Session & SSID Fixer")
    print("="*40)
    
    # Reset session limit
    print("\n1. Resetting daily session limit...")
    reset_daily_sessions()
    
    # Update SSID
    print("\n2. Updating Pocket Option SSID...")
    update_ssid()
    
    print("\n✓ Done! You can now run the bot again.")
    print("\nTo run the bot:")
    print("  - Double-click run_bot.bat")
    print("  - Or run: .\\run_bot_powershell.ps1")

if __name__ == "__main__":
    main()
