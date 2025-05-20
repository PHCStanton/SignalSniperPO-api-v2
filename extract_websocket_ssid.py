#!/usr/bin/env python3
"""
extract_websocket_ssid.py - Extract SSID from WebSocket messages

This script helps extract the correct SSID format from WebSocket messages
in the browser's developer tools. It provides instructions and formatting
for the SSID to be used with the PocketOptionAPI-v2 library.
"""

import os
import sys
import json
import re
import argparse

def extract_ssid_from_auth_message(auth_message):
    """
    Extract the SSID from an auth message.
    
    Args:
        auth_message: The auth message from the WebSocket connection
        
    Returns:
        The extracted SSID or None if not found
    """
    # Check if the message is already in the correct format
    if auth_message.startswith('42["auth",') and '"session"' in auth_message:
        return auth_message
    
    # Try to parse as JSON
    try:
        # If the message is just the data part without the socket.io prefix
        if auth_message.startswith('["auth",'):
            auth_message = '42' + auth_message
            return auth_message
        
        # If the message is a JSON object
        data = json.loads(auth_message)
        
        # Check if it's an array with "auth" as the first element
        if isinstance(data, list) and len(data) >= 2 and data[0] == "auth":
            return f'42{json.dumps(data)}'
        
        # Check if it's an object with session information
        if isinstance(data, dict) and "session" in data:
            return f'42["auth",{json.dumps(data)}]'
        
    except json.JSONDecodeError:
        pass
    
    # Try to extract using regex
    session_match = re.search(r'"session"\s*:\s*"([^"]+)"', auth_message)
    if session_match:
        session = session_match.group(1)
        is_demo = 1 if '"isDemo"\s*:\s*1' in auth_message or '"isDemo"\s*:\s*true' in auth_message else 0
        uid_match = re.search(r'"uid"\s*:\s*(\d+)', auth_message)
        uid = uid_match.group(1) if uid_match else "12345678"
        
        return f'42["auth",{{"session":"{session}","isDemo":{is_demo},"uid":{uid},"platform":2}}]'
    
    return None

def main():
    parser = argparse.ArgumentParser(description='Extract SSID from WebSocket auth message')
    parser.add_argument('--message', type=str, help='The auth message from WebSocket')
    parser.add_argument('--file', type=str, help='File containing the auth message')
    
    args = parser.parse_args()
    
    print("\nPocket Option WebSocket SSID Extractor")
    print("--------------------------------------")
    
    auth_message = None
    
    # Get auth message from arguments or prompt
    if args.message:
        auth_message = args.message
    elif args.file:
        try:
            with open(args.file, 'r') as f:
                auth_message = f.read().strip()
        except Exception as e:
            print(f"Error reading file: {str(e)}")
            return
    else:
        print("\nInstructions:")
        print("1. Log in to Pocket Option in your browser")
        print("2. Open Developer Tools (F12 or right-click > Inspect)")
        print("3. Go to the Network tab")
        print("4. Filter for 'WS' to show WebSocket connections")
        print("5. Look for a connection to 'socket.io' or similar")
        print("6. In the messages, find one that starts with '42[\"auth\",' or contains 'session'")
        print("7. Copy the entire message and paste it below")
        print("\nPaste the WebSocket auth message:")
        auth_message = input().strip()
    
    if not auth_message:
        print("No auth message provided. Exiting.")
        return
    
    # Extract SSID
    ssid = extract_ssid_from_auth_message(auth_message)
    
    if ssid:
        print("\n" + "="*60)
        print("EXTRACTED SSID")
        print("="*60)
        print(f"\n{ssid}\n")
        print("="*60)
        
        # Save to file
        save_to_file = input("\nWould you like to save this SSID to a file? (y/n): ").strip().lower()
        if save_to_file == 'y':
            filename = input("Enter filename (default: ssid.txt): ").strip()
            if not filename:
                filename = "ssid.txt"
            
            try:
                with open(filename, 'w') as f:
                    f.write(ssid)
                print(f"\n✅ SSID saved to {filename}")
            except Exception as e:
                print(f"\n❌ Error saving to file: {str(e)}")
        
        # Update config
        update_config = input("\nWould you like to update pocket_option_config.json with this SSID? (y/n): ").strip().lower()
        if update_config == 'y':
            config_path = "config/pocket_option_config.json"
            
            try:
                # Read the current configuration
                with open(config_path, 'r') as f:
                    config = json.load(f)
                
                # Update the SSID
                config['ssid'] = ssid
                
                # Write the updated configuration
                with open(config_path, 'w') as f:
                    json.dump(config, f, indent=2)
                
                print(f"\n✅ Successfully updated {config_path} with the extracted SSID")
            except Exception as e:
                print(f"\n❌ Error updating configuration file: {str(e)}")
                print("Please manually update the SSID in your configuration file.")
        
        # Test the SSID
        test_ssid = input("\nWould you like to test this SSID now? (y/n): ").strip().lower()
        if test_ssid == 'y':
            try:
                os.system(f"python test_ssid_direct.py")
            except Exception as e:
                print(f"\n❌ Error running test: {str(e)}")
    else:
        print("\n❌ Could not extract SSID from the provided message.")
        print("Please make sure you're copying the correct WebSocket message.")
        print("The message should contain 'auth' and 'session' fields.")

if __name__ == "__main__":
    main()
