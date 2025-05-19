#!/usr/bin/env python3
"""
login_manager.py - Manages authentication and login for the Pocket Option trading bot.

This script provides a secure way to handle SSID-based authentication with Pocket Option,
including session management, secure storage of credentials, and automatic session renewal.
"""

import os
import sys
import json
import time
import base64
import asyncio
import logging
import argparse
import getpass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
import pytz
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Add the parent directory to the path so we can import from pocketoptionapi
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from pocketoptionapi.api import PocketOption
except ImportError:
    print("Error: pocketoptionapi package not found or cannot be imported.")
    print("Make sure you're running this script from the correct directory.")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("login_manager.log")
    ]
)
logger = logging.getLogger(__name__)

class LoginManager:
    def __init__(
        self,
        config_file: str = "../config/pocket_option_config.json",
        credentials_file: str = "../config/credentials.enc",
        session_file: str = "../config/session.json",
        verbose: bool = False
    ):
        """
        Initialize the login manager.
        
        Args:
            config_file: Path to Pocket Option configuration file
            credentials_file: Path to encrypted credentials file
            session_file: Path to session file
            verbose: Enable verbose output
        """
        self.config_file = config_file
        self.credentials_file = credentials_file
        self.session_file = session_file
        self.verbose = verbose
        
        # Set logging level
        if verbose:
            logger.setLevel(logging.DEBUG)
        
        # Load configuration
        self.config = self._load_config()
        
        # Initialize client
        self.client = None
        self.is_authenticated = False
        self.session_data = None
        self.session_expiry = None
        
        # Load session if available
        self._load_session()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.error(f"Error parsing config file: {self.config_file}")
                return {}
        else:
            logger.warning(f"Configuration file {self.config_file} not found. Using defaults.")
            return {}
    
    def _save_config(self) -> None:
        """Save configuration to file."""
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
        logger.info(f"Configuration saved to {self.config_file}")
    
    def _derive_key(self, password: str, salt: Optional[bytes] = None) -> Tuple[bytes, bytes]:
        """
        Derive an encryption key from a password.
        
        Args:
            password: Password to derive key from
            salt: Salt for key derivation (generated if None)
            
        Returns:
            Tuple of (key, salt)
        """
        if salt is None:
            salt = os.urandom(16)
            
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key, salt
    
    def _encrypt_credentials(self, ssid: str, password: str) -> bool:
        """
        Encrypt and save credentials.
        
        Args:
            ssid: SSID to encrypt
            password: Password to derive encryption key from
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.credentials_file), exist_ok=True)
            
            # Generate salt and derive key
            key, salt = self._derive_key(password)
            
            # Create Fernet cipher
            cipher = Fernet(key)
            
            # Encrypt SSID
            encrypted_ssid = cipher.encrypt(ssid.encode())
            
            # Save encrypted SSID and salt
            with open(self.credentials_file, 'wb') as f:
                f.write(salt)
                f.write(encrypted_ssid)
                
            logger.info(f"Credentials encrypted and saved to {self.credentials_file}")
            return True
        except Exception as e:
            logger.error(f"Error encrypting credentials: {str(e)}")
            return False
    
    def _decrypt_credentials(self, password: str) -> Optional[str]:
        """
        Decrypt and retrieve credentials.
        
        Args:
            password: Password to derive encryption key from
            
        Returns:
            Decrypted SSID if successful, None otherwise
        """
        if not os.path.exists(self.credentials_file):
            logger.error(f"Credentials file {self.credentials_file} not found")
            return None
            
        try:
            # Read encrypted SSID and salt
            with open(self.credentials_file, 'rb') as f:
                salt = f.read(16)
                encrypted_ssid = f.read()
                
            # Derive key
            key, _ = self._derive_key(password, salt)
            
            # Create Fernet cipher
            cipher = Fernet(key)
            
            # Decrypt SSID
            decrypted_ssid = cipher.decrypt(encrypted_ssid).decode()
            
            logger.info("Credentials decrypted successfully")
            return decrypted_ssid
        except Exception as e:
            logger.error(f"Error decrypting credentials: {str(e)}")
            return None
    
    def _save_session(self, ssid: str, expiry_days: int = 7) -> None:
        """
        Save session data.
        
        Args:
            ssid: SSID to save
            expiry_days: Number of days until session expires
        """
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(self.session_file), exist_ok=True)
        
        # Calculate expiry time
        expiry_time = datetime.now() + timedelta(days=expiry_days)
        
        # Create session data
        session_data = {
            "ssid": ssid,
            "expiry": expiry_time.isoformat()
        }
        
        # Save session data
        with open(self.session_file, 'w') as f:
            json.dump(session_data, f, indent=2)
            
        # Update instance variables
        self.session_data = session_data
        self.session_expiry = expiry_time
        
        logger.info(f"Session saved to {self.session_file} (expires: {expiry_time.isoformat()})")
    
    def _load_session(self) -> bool:
        """
        Load session data.
        
        Returns:
            True if session is valid, False otherwise
        """
        if not os.path.exists(self.session_file):
            logger.debug(f"Session file {self.session_file} not found")
            return False
            
        try:
            # Read session data
            with open(self.session_file, 'r') as f:
                session_data = json.load(f)
                
            # Parse expiry time
            expiry_time = datetime.fromisoformat(session_data["expiry"])
            
            # Check if session is expired
            if expiry_time <= datetime.now():
                logger.info("Session is expired")
                return False
                
            # Update instance variables
            self.session_data = session_data
            self.session_expiry = expiry_time
            
            logger.info(f"Session loaded from {self.session_file} (expires: {expiry_time.isoformat()})")
            return True
        except Exception as e:
            logger.error(f"Error loading session: {str(e)}")
            return False
    
    def _clear_session(self) -> None:
        """Clear session data."""
        if os.path.exists(self.session_file):
            try:
                os.remove(self.session_file)
                logger.info(f"Session file {self.session_file} removed")
            except Exception as e:
                logger.error(f"Error removing session file: {str(e)}")
                
        self.session_data = None
        self.session_expiry = None
    
    def has_saved_credentials(self) -> bool:
        """
        Check if saved credentials exist.
        
        Returns:
            True if saved credentials exist, False otherwise
        """
        return os.path.exists(self.credentials_file)
    
    def has_valid_session(self) -> bool:
        """
        Check if a valid session exists.
        
        Returns:
            True if a valid session exists, False otherwise
        """
        return self.session_data is not None and self.session_expiry > datetime.now()
    
    def save_credentials(self, ssid: str, password: str) -> bool:
        """
        Save credentials.
        
        Args:
            ssid: SSID to save
            password: Password to encrypt credentials
            
        Returns:
            True if successful, False otherwise
        """
        return self._encrypt_credentials(ssid, password)
    
    def get_ssid(self, password: Optional[str] = None) -> Optional[str]:
        """
        Get SSID from saved credentials or session.
        
        Args:
            password: Password to decrypt credentials (if needed)
            
        Returns:
            SSID if available, None otherwise
        """
        # Check if we have a valid session
        if self.has_valid_session():
            return self.session_data["ssid"]
            
        # Check if we have saved credentials
        if self.has_saved_credentials():
            if password is None:
                logger.error("Password is required to decrypt credentials")
                return None
                
            return self._decrypt_credentials(password)
            
        return None
    
    async def initialize_client(self, ssid: str) -> bool:
        """
        Initialize the Pocket Option client with SSID.
        
        Args:
            ssid: SSID for authentication
            
        Returns:
            True if initialized successfully, False otherwise
        """
        try:
            logger.info("Initializing Pocket Option client...")
            
            # Create client instance
            self.client = PocketOption(ssid)
            
            # Connect to API
            check_connect, message = await self.client.connect()
            
            if check_connect:
                logger.info("Successfully connected to Pocket Option API")
                
                # Set balance type based on config
                use_practice = self.config.get("use_practice_account", True)
                balance_type = "PRACTICE" if use_practice else "REAL"
                
                # Change balance type
                self.client.change_balance(balance_type)
                logger.info(f"Using {balance_type} account")
                
                # Get balance to verify authentication
                balance = await self.client.get_balance()
                
                if balance is not None:
                    logger.info(f"Authentication successful. Balance: {balance}")
                    self.is_authenticated = True
                    
                    # Save session
                    self._save_session(ssid)
                    
                    return True
                else:
                    logger.error("Failed to get balance. Authentication may have failed.")
                    return False
            else:
                logger.error(f"Failed to connect to Pocket Option API: {message}")
                return False
                
        except Exception as e:
            logger.error(f"Error initializing Pocket Option client: {str(e)}")
            return False
    
    async def login(self, ssid: Optional[str] = None, password: Optional[str] = None, save_credentials: bool = False) -> bool:
        """
        Login to Pocket Option.
        
        Args:
            ssid: SSID for authentication (if not using saved credentials)
            password: Password to decrypt saved credentials (if using saved credentials)
            save_credentials: Whether to save credentials for future use
            
        Returns:
            True if logged in successfully, False otherwise
        """
        # Check if we already have a valid session
        if self.has_valid_session():
            logger.info("Using existing session")
            return await self.initialize_client(self.session_data["ssid"])
            
        # Get SSID from saved credentials or parameter
        if ssid is None:
            ssid = self.get_ssid(password)
            
            if ssid is None:
                logger.error("No SSID provided and no saved credentials found")
                return False
        
        # Initialize client with SSID
        success = await self.initialize_client(ssid)
        
        # Save credentials if requested
        if success and save_credentials and password is not None:
            self.save_credentials(ssid, password)
            
        return success
    
    async def logout(self) -> None:
        """Logout from Pocket Option."""
        if self.client:
            await self.client.close()
            logger.info("Logged out from Pocket Option")
            
        self._clear_session()
        self.is_authenticated = False
        self.client = None
    
    async def check_session_validity(self) -> bool:
        """
        Check if the current session is valid.
        
        Returns:
            True if session is valid, False otherwise
        """
        if not self.client or not self.is_authenticated:
            logger.error("Not authenticated")
            return False
            
        try:
            # Try to get balance to check if session is valid
            balance = await self.client.get_balance()
            
            if balance is not None:
                logger.info(f"Session is valid. Balance: {balance}")
                return True
            else:
                logger.warning("Session appears to be invalid")
                return False
                
        except Exception as e:
            logger.error(f"Error checking session validity: {str(e)}")
            return False
    
    async def renew_session_if_needed(self, password: Optional[str] = None) -> bool:
        """
        Renew session if it's close to expiry.
        
        Args:
            password: Password to decrypt saved credentials (if needed)
            
        Returns:
            True if session is valid (renewed or not), False otherwise
        """
        # Check if we have a session
        if not self.has_valid_session():
            logger.warning("No valid session to renew")
            return False
            
        # Check if session is close to expiry (less than 1 day)
        time_until_expiry = self.session_expiry - datetime.now()
        
        if time_until_expiry < timedelta(days=1):
            logger.info("Session is close to expiry. Attempting to renew...")
            
            # Logout
            await self.logout()
            
            # Login again
            return await self.login(password=password)
        else:
            # Session is still valid
            logger.info(f"Session is still valid. Expires in {time_until_expiry}")
            return True
    
    def get_client(self) -> Optional[PocketOption]:
        """
        Get the authenticated Pocket Option client.
        
        Returns:
            Authenticated PocketOption client if available, None otherwise
        """
        if not self.is_authenticated or not self.client:
            logger.error("Not authenticated. Call login() first.")
            return None
            
        return self.client

async def interactive_login(login_manager: LoginManager) -> bool:
    """
    Interactive login process.
    
    Args:
        login_manager: LoginManager instance
        
    Returns:
        True if logged in successfully, False otherwise
    """
    print("\nPocket Option Login")
    print("-------------------")
    
    # Check if we have saved credentials
    if login_manager.has_saved_credentials():
        print("\nSaved credentials found.")
        use_saved = input("Use saved credentials? (y/n): ").lower() == 'y'
        
        if use_saved:
            password = getpass.getpass("Enter password to decrypt credentials: ")
            return await login_manager.login(password=password)
    
    # No saved credentials or user chose not to use them
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
            return False
            
        return await login_manager.login(ssid=ssid, password=password, save_credentials=True)
    else:
        return await login_manager.login(ssid=ssid)

async def main():
    parser = argparse.ArgumentParser(description='Pocket Option Login Manager')
    parser.add_argument('--config', type=str, default='../config/pocket_option_config.json', help='Path to configuration file')
    parser.add_argument('--credentials', type=str, default='../config/credentials.enc', help='Path to encrypted credentials file')
    parser.add_argument('--session', type=str, default='../config/session.json', help='Path to session file')
    parser.add_argument('--ssid', type=str, help='SSID for authentication')
    parser.add_argument('--password', type=str, help='Password to decrypt saved credentials')
    parser.add_argument('--save', action='store_true', help='Save credentials for future use')
    parser.add_argument('--check', action='store_true', help='Check if current session is valid')
    parser.add_argument('--logout', action='store_true', help='Logout and clear session')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose output')
    
    args = parser.parse_args()
    
    # Create login manager
    login_manager = LoginManager(
        config_file=args.config,
        credentials_file=args.credentials,
        session_file=args.session,
        verbose=args.verbose
    )
    
    try:
        if args.logout:
            # Logout
            await login_manager.logout()
            print("Logged out successfully")
            return
            
        if args.check:
            # Check session validity
            if login_manager.has_valid_session():
                # Initialize client with session
                if await login_manager.login():
                    valid = await login_manager.check_session_validity()
                    if valid:
                        print("Session is valid")
                    else:
                        print("Session is invalid")
                else:
                    print("Failed to initialize client with session")
            else:
                print("No valid session found")
            return
            
        # Login
        if args.ssid:
            # Login with provided SSID
            success = await login_manager.login(ssid=args.ssid, password=args.password, save_credentials=args.save)
        elif login_manager.has_saved_credentials() or login_manager.has_valid_session():
            # Login with saved credentials or session
            success = await login_manager.login(password=args.password)
        else:
            # Interactive login
            success = await interactive_login(login_manager)
            
        if success:
            print("\n✅ Login successful!")
            
            # Get client and check balance
            client = login_manager.get_client()
            if client:
                balance = await client.get_balance()
                print(f"Account balance: {balance}")
                
                # Get account type
                account_type = "Practice" if client.account_type == "PRACTICE" else "Real"
                print(f"Account type: {account_type}")
                
                # Close client
                await login_manager.logout()
        else:
            print("\n❌ Login failed. Please check your credentials and try again.")
            
    except KeyboardInterrupt:
        print("\nLogin process interrupted by user")
    except Exception as e:
        print(f"\nError during login: {str(e)}")
    finally:
        # Ensure client is closed
        if login_manager.client:
            await login_manager.logout()

if __name__ == "__main__":
    print("Pocket Option Login Manager")
    print("---------------------------")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nLogin manager interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError in login manager: {str(e)}")
        sys.exit(1)
