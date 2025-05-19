#!/usr/bin/env python3
"""
login_ui.py - User interface for the Pocket Option login manager.

This script provides a simple command-line interface for the login manager,
allowing users to log in to Pocket Option, save credentials, and manage sessions.
"""

import os
import sys
import asyncio
import argparse
import getpass
from typing import Optional

# Add the parent directory to the path so we can import from utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from utils.login_manager import LoginManager, interactive_login
except ImportError:
    print("Error: login_manager.py not found or cannot be imported.")
    print("Make sure you're running this script from the correct directory.")
    sys.exit(1)

class LoginUI:
    def __init__(self):
        """Initialize the login UI."""
        self.login_manager = None
    
    async def setup(self, config_file: str, credentials_file: str, session_file: str, verbose: bool) -> None:
        """
        Set up the login UI.
        
        Args:
            config_file: Path to configuration file
            credentials_file: Path to encrypted credentials file
            session_file: Path to session file
            verbose: Enable verbose output
        """
        self.login_manager = LoginManager(
            config_file=config_file,
            credentials_file=credentials_file,
            session_file=session_file,
            verbose=verbose
        )
    
    async def login_menu(self) -> None:
        """Display the login menu and handle user input."""
        while True:
            print("\nPocket Option Login Menu")
            print("------------------------")
            print("1. Login with saved credentials")
            print("2. Login with new SSID")
            print("3. Check session validity")
            print("4. Logout")
            print("5. Exit")
            
            choice = input("\nEnter your choice (1-5): ")
            
            if choice == "1":
                await self.login_with_saved_credentials()
            elif choice == "2":
                await self.login_with_new_ssid()
            elif choice == "3":
                await self.check_session()
            elif choice == "4":
                await self.logout()
            elif choice == "5":
                print("Exiting...")
                break
            else:
                print("Invalid choice. Please try again.")
    
    async def login_with_saved_credentials(self) -> None:
        """Login with saved credentials."""
        if not self.login_manager.has_saved_credentials() and not self.login_manager.has_valid_session():
            print("No saved credentials or valid session found.")
            return
            
        if self.login_manager.has_valid_session():
            print("Using existing session...")
            success = await self.login_manager.login()
        else:
            password = getpass.getpass("Enter password to decrypt credentials: ")
            success = await self.login_manager.login(password=password)
            
        if success:
            print("\n✅ Login successful!")
            await self.show_account_info()
        else:
            print("\n❌ Login failed. Please check your credentials and try again.")
    
    async def login_with_new_ssid(self) -> None:
        """Login with a new SSID."""
        print("\nPlease enter your Pocket Option SSID.")
        print("You can find this in your browser's developer tools after logging in to Pocket Option.")
        print("Look for a WebSocket message containing 'auth' and a 'session' parameter.")
        
        ssid = input("\nSSID: ")
        
        save_creds = input("Save credentials for future use? (y/n): ").lower() == 'y'
        
        if save_creds:
            password = getpass.getpass("Enter a password to encrypt your credentials: ")
            password_confirm = getpass.getpass("Confirm password: ")
            
            if password != password_confirm:
                print("Passwords do not match.")
                return
                
            success = await self.login_manager.login(ssid=ssid, password=password, save_credentials=True)
        else:
            success = await self.login_manager.login(ssid=ssid)
            
        if success:
            print("\n✅ Login successful!")
            await self.show_account_info()
        else:
            print("\n❌ Login failed. Please check your credentials and try again.")
    
    async def check_session(self) -> None:
        """Check if the current session is valid."""
        if not self.login_manager.has_valid_session():
            print("No valid session found.")
            return
            
        print("Checking session validity...")
        
        # Initialize client with session
        if await self.login_manager.login():
            valid = await self.login_manager.check_session_validity()
            if valid:
                print("✅ Session is valid")
                await self.show_account_info()
            else:
                print("❌ Session is invalid")
        else:
            print("❌ Failed to initialize client with session")
    
    async def logout(self) -> None:
        """Logout and clear session."""
        await self.login_manager.logout()
        print("✅ Logged out successfully")
    
    async def show_account_info(self) -> None:
        """Show account information."""
        client = self.login_manager.get_client()
        if client:
            try:
                balance = await client.get_balance()
                print(f"Account balance: {balance}")
                
                # Get account type
                account_type = "Practice" if client.account_type == "PRACTICE" else "Real"
                print(f"Account type: {account_type}")
                
                # Get available assets
                assets = await client.get_all_assets()
                print(f"Available assets: {len(assets)}")
                
                # Show a few assets as example
                if assets:
                    print("Example assets:")
                    for i, asset in enumerate(assets[:5]):
                        print(f"  - {asset['name']}")
                    
                    if len(assets) > 5:
                        print(f"  - ... and {len(assets) - 5} more")
            except Exception as e:
                print(f"Error retrieving account information: {str(e)}")

async def main():
    parser = argparse.ArgumentParser(description='Pocket Option Login UI')
    parser.add_argument('--config', type=str, default='config/pocket_option_config.json', help='Path to configuration file')
    parser.add_argument('--credentials', type=str, default='config/credentials.enc', help='Path to encrypted credentials file')
    parser.add_argument('--session', type=str, default='config/session.json', help='Path to session file')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose output')
    
    args = parser.parse_args()
    
    # Create login UI
    ui = LoginUI()
    
    try:
        # Set up login UI
        await ui.setup(
            config_file=args.config,
            credentials_file=args.credentials,
            session_file=args.session,
            verbose=args.verbose
        )
        
        # Display login menu
        await ui.login_menu()
    except KeyboardInterrupt:
        print("\nLogin UI interrupted by user")
    except Exception as e:
        print(f"\nError in login UI: {str(e)}")
    finally:
        # Ensure client is closed
        if ui.login_manager and ui.login_manager.client:
            await ui.login_manager.logout()

if __name__ == "__main__":
    print("Pocket Option Login UI")
    print("---------------------")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nLogin UI interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError in login UI: {str(e)}")
        sys.exit(1)
