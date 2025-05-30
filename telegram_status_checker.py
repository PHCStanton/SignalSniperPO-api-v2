#!/usr/bin/env python3
"""
Telegram Status Checker for Self Bot v3.0
==========================================

Checks Telegram connection status and integrates with session management.

Usage:
    python telegram_status_checker.py --check
    python telegram_status_checker.py --check --session-name "morning_session"
    python telegram_status_checker.py --quick-check
"""

import json
import os
import sys
import asyncio
import logging
import argparse
from typing import Dict, Any, Optional, Tuple
import pytz
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TelegramStatusChecker:
    """Telegram connection status checker integrated with session management"""
    
    def __init__(self):
        self.config_dir = "config"
        self.sessions_dir = "sessions"
        self.telegram_config_file = os.path.join(self.config_dir, "telegram_config.json")
        self.active_session_file = os.path.join(self.sessions_dir, "active_session.json")
        self.tz = pytz.timezone('Africa/Johannesburg')
        
        # Ensure directories exist
        os.makedirs(self.config_dir, exist_ok=True)
        os.makedirs(self.sessions_dir, exist_ok=True)
    
    def load_json_file(self, filepath: str, default: Any = None) -> Any:
        """Safely load JSON file"""
        if default is None:
            default = {}
        
        try:
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        return json.loads(content)
            return default
        except Exception as e:
            logger.warning(f"Error loading {filepath}: {e}")
            return default
    
    def save_json_file(self, filepath: str, data: Any) -> bool:
        """Safely save JSON file"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Error saving {filepath}: {e}")
            return False
    
    def get_current_time(self) -> str:
        """Get current time in SAST timezone"""
        return datetime.now(self.tz).isoformat()
    
    def get_active_session(self) -> Optional[Dict[str, Any]]:
        """Get current active session"""
        return self.load_json_file(self.active_session_file)
    
    def update_session_telegram_status(self, status: Dict[str, Any]) -> bool:
        """Update active session with Telegram status"""
        active_session = self.get_active_session()
        if not active_session:
            logger.warning("No active session found")
            return False
        
        # Update session with Telegram status
        active_session["telegram_status"] = status
        active_session["last_telegram_check"] = self.get_current_time()
        active_session["last_update"] = self.get_current_time()
        
        return self.save_json_file(self.active_session_file, active_session)
    
    async def check_telegram_session(self, api_id: int, api_hash: str, session_name: str) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """Check if Telegram session is valid"""
        try:
            # Import here to avoid dependency issues if telethon not installed
            from telethon import TelegramClient
            from telethon.tl.types import Channel
        except ImportError:
            error_msg = "telethon package is not installed. Please install it using: pip install telethon"
            logger.error(error_msg)
            return False, None, {"error": error_msg, "status": "dependency_missing"}
        
        logger.info(f"Checking Telegram session: {session_name}")
        
        # Check if session file exists
        session_file = f"{session_name}.session"
        if not os.path.exists(session_file):
            error_msg = f"Session file {session_file} does not exist"
            logger.warning(error_msg)
            return False, None, {"error": error_msg, "status": "session_file_missing"}
        
        try:
            # Create client
            client = TelegramClient(session_name, api_id, api_hash)
            
            # Connect
            await client.connect()
            
            # Check if authorized
            if await client.is_user_authorized():
                # Get user info
                me = await client.get_me()
                user_info = f"{me.first_name} {getattr(me, 'last_name', '')} (@{me.username})"
                logger.info(f"Telegram session valid. Logged in as: {user_info}")
                
                # Disconnect
                await client.disconnect()
                
                return True, user_info, {
                    "status": "connected",
                    "user_info": user_info,
                    "session_file": session_file,
                    "check_time": self.get_current_time()
                }
            else:
                error_msg = f"Session {session_name} is not authorized"
                logger.warning(error_msg)
                await client.disconnect()
                return False, None, {"error": error_msg, "status": "not_authorized"}
                
        except Exception as e:
            error_msg = f"Error checking Telegram session: {str(e)}"
            logger.error(error_msg)
            return False, None, {"error": error_msg, "status": "connection_error"}
    
    async def check_channel_access(self, api_id: int, api_hash: str, session_name: str, 
                                 channel_id: Optional[int] = None, channel_name: Optional[str] = None) -> Tuple[bool, Dict[str, Any]]:
        """Check if we can access the specified channel"""
        try:
            from telethon import TelegramClient
            from telethon.tl.types import Channel
        except ImportError:
            error_msg = "telethon package is not installed"
            return False, {"error": error_msg, "status": "dependency_missing"}
        
        if not channel_id and not channel_name:
            error_msg = "Either channel_id or channel_name must be specified"
            logger.error(error_msg)
            return False, {"error": error_msg, "status": "invalid_parameters"}
        
        logger.info(f"Checking access to channel: {channel_name or channel_id}")
        
        try:
            # Create client
            client = TelegramClient(session_name, api_id, api_hash)
            
            # Connect
            await client.connect()
            
            # Check if authorized
            if not await client.is_user_authorized():
                error_msg = f"Session {session_name} is not authorized"
                logger.error(error_msg)
                await client.disconnect()
                return False, {"error": error_msg, "status": "not_authorized"}
            
            # Try to access channel
            try:
                if channel_id:
                    entity = await client.get_entity(int(channel_id))
                    if isinstance(entity, Channel):
                        logger.info(f"Successfully accessed channel by ID: {entity.title}")
                        await client.disconnect()
                        return True, {
                            "status": "accessible",
                            "channel_title": entity.title,
                            "channel_id": channel_id,
                            "access_method": "by_id"
                        }
                
                if channel_name:
                    # Try to find by name in dialog list
                    async for dialog in client.iter_dialogs():
                        if dialog.name == channel_name:
                            logger.info(f"Successfully accessed channel by name: {dialog.name}")
                            await client.disconnect()
                            return True, {
                                "status": "accessible",
                                "channel_title": dialog.name,
                                "channel_id": dialog.id,
                                "access_method": "by_name"
                            }
                
                error_msg = f"Channel not found: {channel_name or channel_id}"
                logger.warning(error_msg)
                await client.disconnect()
                return False, {"error": error_msg, "status": "channel_not_found"}
                
            except Exception as e:
                error_msg = f"Error accessing channel: {str(e)}"
                logger.error(error_msg)
                await client.disconnect()
                return False, {"error": error_msg, "status": "channel_access_error"}
                
        except Exception as e:
            error_msg = f"Error checking channel access: {str(e)}"
            logger.error(error_msg)
            return False, {"error": error_msg, "status": "connection_error"}
    
    async def full_telegram_check(self, update_session: bool = True) -> Dict[str, Any]:
        """Perform full Telegram connection and channel access check"""
        # Load Telegram configuration
        telegram_config = self.load_json_file(self.telegram_config_file)
        
        if not telegram_config:
            return {
                "status": "error",
                "error": "Telegram configuration not found",
                "config_file": self.telegram_config_file
            }
        
        # Extract configuration
        api_id = telegram_config.get('api_id')
        api_hash = telegram_config.get('api_hash')
        session_name = telegram_config.get('session_name', 'pocket_option_userbot')
        channel_id = telegram_config.get('channel_id')
        channel_name = telegram_config.get('channel_name', 'BINARY TRADING CLUB')
        
        if not api_id or not api_hash:
            return {
                "status": "error",
                "error": "API credentials not found in configuration",
                "config_file": self.telegram_config_file
            }
        
        # Check session
        session_valid, user_info, session_status = await self.check_telegram_session(api_id, api_hash, session_name)
        
        result = {
            "check_time": self.get_current_time(),
            "session_status": session_status,
            "session_valid": session_valid,
            "user_info": user_info,
            "config": {
                "api_id": api_id,
                "session_name": session_name,
                "channel_name": channel_name,
                "channel_id": channel_id
            }
        }
        
        if session_valid:
            # Check channel access
            channel_accessible, channel_status = await self.check_channel_access(
                api_id, api_hash, session_name, channel_id, channel_name
            )
            
            result["channel_status"] = channel_status
            result["channel_accessible"] = channel_accessible
            
            if channel_accessible:
                result["status"] = "fully_operational"
                result["message"] = "Telegram session and channel access verified"
            else:
                result["status"] = "session_ok_channel_issue"
                result["message"] = "Telegram session valid but channel access failed"
        else:
            result["status"] = "session_invalid"
            result["message"] = "Telegram session is not valid"
        
        # Update active session if requested
        if update_session:
            self.update_session_telegram_status(result)
        
        return result
    
    async def quick_check(self) -> Dict[str, Any]:
        """Quick check - just verify session file exists and basic config"""
        telegram_config = self.load_json_file(self.telegram_config_file)
        
        if not telegram_config:
            return {
                "status": "error",
                "error": "Telegram configuration not found",
                "quick_check": True
            }
        
        session_name = telegram_config.get('session_name', 'pocket_option_userbot')
        session_file = f"{session_name}.session"
        
        result = {
            "quick_check": True,
            "check_time": self.get_current_time(),
            "config_exists": True,
            "session_file_exists": os.path.exists(session_file),
            "session_file": session_file,
            "config": {
                "api_id": bool(telegram_config.get('api_id')),
                "api_hash": bool(telegram_config.get('api_hash')),
                "session_name": session_name,
                "channel_name": telegram_config.get('channel_name'),
                "channel_id": telegram_config.get('channel_id')
            }
        }
        
        if result["session_file_exists"] and telegram_config.get('api_id') and telegram_config.get('api_hash'):
            result["status"] = "likely_ok"
            result["message"] = "Configuration and session file exist (full check recommended)"
        else:
            result["status"] = "issues_detected"
            result["message"] = "Missing configuration or session file"
        
        return result
    
    def print_status(self, result: Dict[str, Any]):
        """Print formatted status report"""
        print("\n" + "="*60)
        print("📱 TELEGRAM CONNECTION STATUS")
        print("="*60)
        
        if result.get("quick_check"):
            print("🔍 QUICK CHECK RESULTS:")
            print(f"   Config File: {'✅' if result.get('config_exists') else '❌'}")
            print(f"   Session File: {'✅' if result.get('session_file_exists') else '❌'} ({result.get('session_file', 'unknown')})")
            print(f"   API Credentials: {'✅' if result['config'].get('api_id') and result['config'].get('api_hash') else '❌'}")
            print(f"   Status: {result.get('status', 'unknown').upper()}")
            print(f"   Message: {result.get('message', 'No message')}")
        else:
            print("🔍 FULL CHECK RESULTS:")
            print(f"   Session Valid: {'✅' if result.get('session_valid') else '❌'}")
            if result.get('user_info'):
                print(f"   Logged in as: {result['user_info']}")
            
            if result.get('channel_accessible') is not None:
                print(f"   Channel Access: {'✅' if result.get('channel_accessible') else '❌'}")
                if result.get('channel_status', {}).get('channel_title'):
                    print(f"   Channel: {result['channel_status']['channel_title']}")
            
            print(f"   Overall Status: {result.get('status', 'unknown').upper()}")
            print(f"   Message: {result.get('message', 'No message')}")
        
        # Show active session info
        active_session = self.get_active_session()
        if active_session:
            print(f"\n📍 ACTIVE SESSION: {active_session.get('session_id', 'unknown')}")
            if result.get('status') == 'fully_operational':
                print("   Telegram Status: ✅ READY FOR TRADING")
            else:
                print("   Telegram Status: ⚠️ NEEDS ATTENTION")
        else:
            print("\n📍 ACTIVE SESSION: None")
            print("   Use: python session_control.py --start --name 'session_name'")
        
        print("\n" + "="*60)

async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Telegram Status Checker for Self Bot v3.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python telegram_status_checker.py --check
  python telegram_status_checker.py --quick-check
  python telegram_status_checker.py --check --session-name "morning_session"
        """
    )
    
    parser.add_argument('--check', action='store_true', help='Perform full Telegram connection check')
    parser.add_argument('--quick-check', action='store_true', help='Perform quick configuration check')
    parser.add_argument('--session-name', type=str, help='Specific session name to check')
    parser.add_argument('--no-update', action='store_true', help='Do not update active session with results')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # Create checker
    checker = TelegramStatusChecker()
    
    # Handle no arguments - show help
    if not args.check and not args.quick_check:
        parser.print_help()
        return
    
    try:
        if args.quick_check:
            result = await checker.quick_check()
        else:
            result = await checker.full_telegram_check(update_session=not args.no_update)
        
        checker.print_status(result)
        
        # Exit with appropriate code
        if result.get('status') in ['fully_operational', 'likely_ok']:
            sys.exit(0)
        else:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Check cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"\n❌ Error during check: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
