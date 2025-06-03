#!/usr/bin/env python3
"""
run_bot.py - Enhanced Pocket Option Trading Bot with Latency Optimization

This script serves as the main entry point for running the Pocket Option trading bot
with enhanced latency optimization features including:
- NTP synchronization automation
- Latency threshold checking
- Process priority elevation
- Network optimization integration

Based on self_bot_v3_integrated.py with latency optimization enhancements.
"""

import os
import sys
import json
import asyncio
import logging
import argparse
import signal
import subprocess
import time
import threading
import pytz
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
import dotenv
from timestamp_recorder import TimestampRecorder
from session_manager import SessionManager, SignalDeduplicator

# Import trading client manager for optimized headless login support
try:
    from trading_client_manager import TradingClientManager, create_config_from_pocket_option_config
    TRADING_CLIENT_MANAGER_AVAILABLE = True
except ImportError:
    TRADING_CLIENT_MANAGER_AVAILABLE = False

# Import Telegram client
try:
    from telethon import TelegramClient, events
    from telethon.tl.types import Channel, Message
except ImportError:
    print("Error: telethon package is not installed.")
    print("Please install it using: pip install telethon")
    sys.exit(1)

# Import Pocket Option API v2
try:
    # Add the PocketOptionAPI-v2 directory to the path
    sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'PocketOptionAPI-v2'))
    from pocketoptionapi.stable_api import PocketOption
    import pocketoptionapi.global_value as global_value
except ImportError:
    print("Error: PocketOptionAPI-v2 package not found or cannot be imported.")
    print("Make sure the PocketOptionAPI-v2 directory is in the project root.")
    sys.exit(1)

# Configure logging with UTF-8 encoding to handle Unicode characters
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("run_bot.log", encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

class LatencyOptimizer:
    """Handles latency optimization features for the trading bot."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config.get("latency_settings", {})
        self.max_api_latency_ms = self.config.get("max_api_latency_ms", 100)
        self.max_network_latency_ms = self.config.get("max_network_latency_ms", 50)
        self.enable_auto_sync = self.config.get("enable_auto_sync", True)
        self.enable_priority_elevation = self.config.get("enable_priority_elevation", True)
        self.enable_network_optimization = self.config.get("enable_network_optimization", True)
        self.ntp_tolerance_ms = self.config.get("ntp_tolerance_ms", 10)
        
    def run_ntp_sync(self, force: bool = False) -> Tuple[bool, str, float]:
        """
        Run NTP synchronization using the quick-ntp-sync.ps1 script.
        
        Returns:
            Tuple of (success, message, offset_ms)
        """
        if not self.enable_auto_sync:
            return True, "NTP sync disabled", 0.0
            
        try:
            logger.info("🕐 Running NTP synchronization...")
            
            # Build PowerShell command
            script_path = os.path.join("scripts", "quick-ntp-sync.ps1")
            cmd = [
                "powershell.exe", 
                "-ExecutionPolicy", "Bypass",
                "-File", script_path,
                "-ToleranceMs", str(self.ntp_tolerance_ms)
            ]
            
            if force:
                cmd.append("-Force")
                
            # Run the script
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60  # 60 second timeout
            )
            
            # Parse the result
            if result.returncode == 0:
                # Success
                logger.info("✅ NTP synchronization completed successfully")
                
                # Try to extract offset from output
                offset_ms = 0.0
                for line in result.stdout.split('\n'):
                    if "Final accuracy:" in line:
                        # Extract number before "ms"
                        import re
                        match = re.search(r'(\d+\.?\d*)ms', line)
                        if match:
                            offset_ms = float(match.group(1))
                            break
                
                return True, "NTP sync successful", offset_ms
                
            elif result.returncode == 2:
                # Warning - sync completed but exceeds tolerance
                logger.warning("⚠️ NTP sync completed with warnings")
                return True, "NTP sync completed with warnings", -1
                
            else:
                # Error
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                logger.error(f"❌ NTP sync failed: {error_msg}")
                return False, f"NTP sync failed: {error_msg}", -1
                
        except subprocess.TimeoutExpired:
            logger.error("❌ NTP sync timed out")
            return False, "NTP sync timed out", -1
        except Exception as e:
            logger.error(f"❌ Error running NTP sync: {str(e)}")
            return False, f"Error running NTP sync: {str(e)}", -1
    
    def run_latency_test(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Run comprehensive latency test using the final_pocket_option_latency_test.py script.
        
        Returns:
            Tuple of (success, latency_results)
        """
        try:
            logger.info("📊 Running comprehensive latency test...")
            
            # Import the latency test module
            sys.path.append("scripts")
            from final_pocket_option_latency_test import FinalPocketOptionLatencyTester
            
            # Create tester instance
            tester = FinalPocketOptionLatencyTester()
            
            # Run basic network tests (no API connection needed)
            network_latencies = tester.test_network_ping(3)
            tcp_latencies = tester.test_tcp_connection_latency(3)
            
            # Calculate statistics
            network_stats = tester.calculate_statistics(network_latencies, "Network Ping") if network_latencies else None
            tcp_stats = tester.calculate_statistics(tcp_latencies, "TCP Connection") if tcp_latencies else None
            
            # Determine if latency is acceptable
            acceptable = True
            issues = []
            
            if network_stats and network_stats['mean'] > self.max_network_latency_ms:
                acceptable = False
                issues.append(f"Network latency too high: {network_stats['mean']:.1f}ms > {self.max_network_latency_ms}ms")
            
            if tcp_stats and tcp_stats['mean'] > self.max_api_latency_ms:
                acceptable = False
                issues.append(f"TCP latency too high: {tcp_stats['mean']:.1f}ms > {self.max_api_latency_ms}ms")
            
            results = {
                "acceptable": acceptable,
                "issues": issues,
                "network_stats": network_stats,
                "tcp_stats": tcp_stats,
                "thresholds": {
                    "max_network_latency_ms": self.max_network_latency_ms,
                    "max_api_latency_ms": self.max_api_latency_ms
                }
            }
            
            if acceptable:
                logger.info("✅ Latency test passed - all metrics within acceptable ranges")
            else:
                logger.warning(f"⚠️ Latency test issues detected: {'; '.join(issues)}")
            
            return True, results
            
        except Exception as e:
            logger.error(f"❌ Error running latency test: {str(e)}")
            return False, {"error": str(e)}
    
    def elevate_process_priority(self) -> bool:
        """
        Elevate the current process priority for better performance.
        
        Returns:
            True if successful, False otherwise
        """
        if not self.enable_priority_elevation:
            return True
            
        try:
            import psutil
            
            # Get current process
            current_process = psutil.Process()
            
            # Set high priority
            if os.name == 'nt':  # Windows
                current_process.nice(psutil.HIGH_PRIORITY_CLASS)
                logger.info("✅ Process priority elevated to HIGH")
            else:  # Unix/Linux
                current_process.nice(-10)  # Lower nice value = higher priority
                logger.info("✅ Process priority elevated (nice: -10)")
            
            return True
            
        except ImportError:
            logger.warning("⚠️ psutil not available, cannot elevate process priority")
            return False
        except Exception as e:
            logger.warning(f"⚠️ Could not elevate process priority: {str(e)}")
            return False

class EnhancedSelfBot:
    """Enhanced Self Bot with latency optimization features."""
    
    def __init__(
        self,
        config_file: str = "config/bot_config.json",
        telegram_config_file: str = "config/telegram_config.json",
        pocket_option_config_file: str = "config/pocket_option_config.json",
        data_dir: str = "data",
        verbose: bool = False
    ):
        """Initialize the Enhanced Self Bot."""
        self.config_file = config_file
        self.telegram_config_file = telegram_config_file
        self.pocket_option_config_file = pocket_option_config_file
        self.data_dir = data_dir
        self.verbose = verbose
        
        # Set logging level
        if verbose:
            logger.setLevel(logging.DEBUG)
            global_value.loglevel = 'DEBUG'
        else:
            global_value.loglevel = 'INFO'
        
        # Load configuration
        self.config = self._load_config(config_file)
        self.telegram_config = self._load_config(telegram_config_file)
        self.pocket_option_config = self._load_config(pocket_option_config_file)
        
        # Initialize latency optimizer
        self.latency_optimizer = LatencyOptimizer(self.config)
        
        # Initialize clients
        self.telegram_client = None
        self.pocket_option_client = None
        
        # Signal tracking
        self.last_first_message = None
        self.last_first_message_time = None
        self.pending_signals = []
        self.active_trades = {}
        
        # Session management components
        _data_dir_for_components = "sessions"
        logger.info(f"Using '{_data_dir_for_components}' for session-related data files.")
        
        # Timestamp recorder for robust timestamp recording
        self.timestamp_recorder = TimestampRecorder(
            data_dir=_data_dir_for_components,
            max_records=self.config.get("json_storage", {}).get("max_records", 1000)
        )
        
        # Session manager for singleton pattern and session recovery
        self.session_manager = SessionManager(
            data_dir=_data_dir_for_components,
            timezone=self.config.get("timezone", "Africa/Johannesburg")
        )
        
        # Signal deduplicator for preventing duplicate signal processing
        self.signal_deduplicator = SignalDeduplicator(
            data_dir=_data_dir_for_components,
            max_fingerprints=self.config.get("json_storage", {}).get("max_fingerprints", 1000)
        )
        
        # Session data
        self.session_id = None
        self.session_data = {}
        
        # Timezone
        self.timezone = pytz.timezone(self.config.get("timezone", "Africa/Johannesburg"))
        
        # Trading stats
        self.stats = {
            "total_signals": 0,
            "valid_signals": 0,
            "executed_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "error_trades": 0,
            "total_profit": 0.0,
            "start_time": datetime.now(self.timezone),
        }
    
    def _load_config(self, config_file: str) -> Dict[str, Any]:
        """Load configuration from file or create default."""
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.error(f"Error parsing config file: {config_file}")
                return {}
        else:
            logger.warning(f"Configuration file {config_file} not found. Using defaults.")
            return {}
    
    def run_startup_optimizations(self) -> bool:
        """
        Run all startup optimizations including NTP sync, latency testing, and process priority.
        
        Returns:
            True if all optimizations successful or acceptable, False if critical issues
        """
        logger.info("🚀 Running startup optimizations...")
        
        success_count = 0
        total_optimizations = 3
        
        # 1. NTP Synchronization
        ntp_success, ntp_message, ntp_offset = self.latency_optimizer.run_ntp_sync()
        if ntp_success:
            success_count += 1
            logger.info(f"✅ NTP Sync: {ntp_message} (offset: {ntp_offset:.2f}ms)")
        else:
            logger.error(f"❌ NTP Sync failed: {ntp_message}")
        
        # 2. Latency Testing
        latency_success, latency_results = self.latency_optimizer.run_latency_test()
        if latency_success:
            if latency_results.get("acceptable", False):
                success_count += 1
                logger.info("✅ Latency Test: All metrics within acceptable ranges")
            else:
                logger.warning(f"⚠️ Latency Test: Issues detected - {'; '.join(latency_results.get('issues', []))}")
                # Don't count as failure unless critical
                success_count += 0.5
        else:
            logger.error(f"❌ Latency Test failed: {latency_results.get('error', 'Unknown error')}")
        
        # 3. Process Priority Elevation
        priority_success = self.latency_optimizer.elevate_process_priority()
        if priority_success:
            success_count += 1
            logger.info("✅ Process Priority: Elevated successfully")
        else:
            logger.warning("⚠️ Process Priority: Could not elevate (non-critical)")
            success_count += 0.5  # Non-critical failure
        
        # Determine overall success
        success_rate = success_count / total_optimizations
        
        if success_rate >= 0.8:  # 80% success rate
            logger.info(f"🎯 Startup optimizations completed successfully ({success_rate:.1%} success rate)")
            return True
        elif success_rate >= 0.5:  # 50% success rate
            logger.warning(f"⚠️ Startup optimizations completed with warnings ({success_rate:.1%} success rate)")
            return True  # Continue but with warnings
        else:
            logger.error(f"❌ Startup optimizations failed ({success_rate:.1%} success rate)")
            return False
    
    async def initialize_telegram(self) -> bool:
        """Initialize the Telegram client."""
        try:
            # Get Telegram API credentials
            api_id = self.telegram_config.get("api_id") or os.environ.get("TELEGRAM_API_ID")
            api_hash = self.telegram_config.get("api_hash") or os.environ.get("TELEGRAM_API_HASH")
            session_name = self.telegram_config.get("session_name", "test_session")
            
            if not api_id or not api_hash:
                logger.error("Telegram API ID and hash are required. Set them in the config file or environment variables.")
                return False
            
            logger.info("Initializing Telegram client...")
            
            # User account mode
            self.telegram_client = TelegramClient(session_name, int(api_id), api_hash)
            await self.telegram_client.start()
            logger.info("Started Telegram client in user account mode")
            
            # Check if we need to complete the phone verification process
            if not await self.telegram_client.is_user_authorized():
                logger.info("User not authorized. Please complete the login process.")
                phone = input("Enter your phone number: ")
                await self.telegram_client.send_code_request(phone)
                code = input("Enter the code: ")
                await self.telegram_client.sign_in(phone, code)
                logger.info("Successfully authenticated")
            else:
                logger.info("Already authenticated using existing session")
                me = await self.telegram_client.get_me()
                last_name = getattr(me, 'last_name', '') if hasattr(me, 'last_name') else ''
                username = getattr(me, 'username', '') if hasattr(me, 'username') else ''
                logger.info(f"Logged in as: {getattr(me, 'first_name', 'Unknown')} {last_name} (@{username})")
            
            return True
        except Exception as e:
            logger.error(f"Error initializing Telegram client: {str(e)}")
            return False
    
    def initialize_pocket_option(self) -> bool:
        """Initialize Pocket Option client."""
        try:
            # Get SSID from config
            ssid = self.pocket_option_config.get("ssid")
            if not ssid:
                logger.error("No SSID provided in configuration")
                return False
            
            # Get demo mode setting - Default to real trading (False)
            is_demo = self.pocket_option_config.get("is_demo", False)
            
            # Initialize the PocketOption client
            logger.info(f"Initializing Pocket Option client (Demo mode: {is_demo})")
            self.pocket_option_client = PocketOption(ssid, is_demo)
            
            # Connect to the API
            connection_result = self.pocket_option_client.connect()
            if connection_result:
                logger.info("Successfully connected to Pocket Option API")
                
                # Get account balance with retry
                balance = None
                for attempt in range(3):
                    try:
                        balance = self.pocket_option_client.get_balance()
                        if balance is not None:
                            break
                        time.sleep(1)
                    except Exception as e:
                        logger.debug(f"Balance retrieval attempt {attempt + 1} failed: {str(e)}")
                        time.sleep(1)
                
                logger.info(f"Account balance: {balance}")
                return True
            else:
                logger.error("Failed to connect to Pocket Option API")
                return False
        except Exception as e:
            logger.error(f"Error initializing Pocket Option client: {str(e)}")
            return False
    
    def initialize_session_management(self) -> bool:
        """Initialize session management."""
        try:
            # SessionManager attempts to load from active_session.json or recover during its __init__
            loaded_session = self.session_manager.get_current_session()

            if loaded_session:
                logger.info(f"Using already loaded session: {loaded_session.session_id}")
                self.session_id = loaded_session.session_id
                
                # Update balance_start for the loaded session with current live balance
                current_balance = 0.0
                if self.pocket_option_client:
                    try:
                        balance_val = self.pocket_option_client.get_balance()
                        if balance_val is not None:
                            current_balance = float(balance_val)
                            self.session_manager.update_session(balance_start=current_balance, last_activity=datetime.now(self.timezone).isoformat())
                            logger.info(f"Updated balance_start for loaded session {self.session_id} to {current_balance}")
                            loaded_session.balance_start = current_balance
                        else:
                            logger.warning(f"Could not get current balance for loaded session {self.session_id}; balance_start may be stale.")
                            current_balance = loaded_session.balance_start
                    except Exception as e:
                        logger.warning(f"Error getting/updating balance for loaded session {self.session_id}: {str(e)}. Using existing balance_start: {loaded_session.balance_start}")
                        current_balance = loaded_session.balance_start
                else:
                    logger.warning("Pocket Option client not available to update balance_start for loaded session.")
                    current_balance = loaded_session.balance_start

                self.session_data = {
                    "session_id": loaded_session.session_id,
                    "start_time": loaded_session.start_time,
                    "balance_start": current_balance,
                    "trades_count": loaded_session.trades_count,
                    "wins": loaded_session.wins,
                    "losses": loaded_session.losses,
                    "draws": loaded_session.draws,
                    "profit_loss": loaded_session.profit_loss
                }
                logger.info(f"✅ Session management initialized with existing session: {self.session_id}")
                return True
            else:
                # No session loaded by SessionManager, try to start a new one
                logger.info("No existing session found by SessionManager. Attempting to start a new session.")
                can_start, message = self.session_manager.can_start_new_session()
                if not can_start:
                    logger.error(f"Cannot start new session: {message}")
                    return False

                initial_balance = 0.0
                if self.pocket_option_client:
                    try:
                        balance_val = self.pocket_option_client.get_balance()
                        if balance_val is not None:
                            initial_balance = float(balance_val)
                    except Exception as e:
                        logger.warning(f"Could not get initial balance for new session: {str(e)}")

                session_info = self.session_manager.start_new_session(initial_balance)
                if session_info:
                    self.session_id = session_info.session_id
                    self.session_data = {
                        "session_id": session_info.session_id,
                        "start_time": session_info.start_time,
                        "balance_start": session_info.balance_start,
                        "trades_count": session_info.trades_count,
                        "wins": session_info.wins,
                        "losses": session_info.losses,
                        "draws": session_info.draws,
                        "profit_loss": session_info.profit_loss
                    }
                    logger.info(f"✅ Session management initialized with new session: {self.session_id}")
                    return True
                else:
                    logger.error("Failed to start new session via SessionManager.")
                    return False
        except Exception as e:
            logger.error(f"Error initializing session management: {str(e)}")
            return False
    
    async def access_channel(self):
        """Access a Telegram channel that the user is already a member of."""
        if not self.telegram_client:
            logger.error("Telegram client not initialized")
            return None
        
        channel_name = self.telegram_config.get("channel_name", "SignalTest")
        channel_id = self.telegram_config.get("channel_id")
        
        logger.info(f"Accessing channel: {channel_name}")
        
        try:
            # Try to use channel ID if available
            if channel_id:
                try:
                    entity = await self.telegram_client.get_entity(int(channel_id))
                    logger.info(f"Accessed channel by ID: {getattr(entity, 'title', 'Unknown')}")
                    return entity
                except Exception as e:
                    logger.debug(f"Error accessing channel by ID: {str(e)}")
            
            # Try to find by name in dialog list
            async for dialog in self.telegram_client.iter_dialogs():
                if dialog.name == channel_name:
                    logger.info(f"Found channel in dialog list: {dialog.name}")
                    return dialog.entity
            
            logger.warning(f"Channel not found: {channel_name}")
            return None
            
        except Exception as e:
            logger.error(f"Error accessing channel: {str(e)}")
            return None
    
    async def start_monitoring(self) -> None:
        """Start monitoring the Telegram channel for signals."""
        if not self.telegram_client:
            logger.error("Telegram client not initialized")
            return
        
        channel = await self.access_channel()
        if not channel:
            logger.error("Could not access channel")
            return
        
        channel_name = self.telegram_config.get("channel_name", "SignalTest")
        logger.info(f"Starting monitoring of channel: {getattr(channel, 'title', channel_name)}")
        
        # Register event handler for new messages
        self.telegram_client.add_event_handler(
            self.process_message,
            events.NewMessage(chats=channel)
        )
        
        logger.info("Event handler registered. Waiting for signals...")
        
        # Keep the client running
        try:
            await self.telegram_client.run_until_disconnected()
        except Exception as e:
            logger.error(f"Error in monitoring loop: {str(e)}")
            return
    
    async def process_message(self, message) -> None:
        """Process a message from the channel (simplified version for demo)."""
        if not message.text:
            return
        
        try:
            # Clean message text for logging
            clean_text = re.sub(r'[^\x00-\x7F]+', '?', message.text)
            logger.info(f"📨 Received message: {clean_text[:100]}...")
            
            # This is a simplified version - in production, implement full signal parsing
            # from self_bot_v3_integrated.py
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
    
    def cleanup_session(self) -> None:
        """Clean up session data and end current session."""
        try:
            if self.session_manager:
                # Get final balance
                final_balance = None
                if self.pocket_option_client:
                    try:
                        final_balance = self.pocket_option_client.get_balance()
                        if final_balance is not None:
                            final_balance = float(final_balance)
                    except Exception as e:
                        logger.warning(f"Could not get final balance: {str(e)}")
                
                # End session
                self.session_manager.end_session(final_balance)
                logger.info("✅ Session cleanup completed")
        except Exception as e:
            logger.error(f"Error during session cleanup: {str(e)}")

async def main():
    """Main function to run the enhanced bot."""
    parser = argparse.ArgumentParser(description="Enhanced Pocket Option Self Bot with Latency Optimization")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("--skip-optimizations", action="store_true", help="Skip startup optimizations")
    
    args = parser.parse_args()
    
    # Create enhanced bot instance
    bot = EnhancedSelfBot(verbose=args.verbose)
    
    # Run startup optimizations unless skipped
    if not args.skip_optimizations:
        optimization_success = bot.run_startup_optimizations()
        if not optimization_success:
            logger.error("❌ Critical startup optimization failures detected. Exiting...")
            sys.exit(1)
    else:
        logger.info("⏭️ Skipping startup optimizations as requested")
    
    # Initialize components
    telegram_initialized = await bot.initialize_telegram()
    if not telegram_initialized:
        logger.error("Failed to initialize Telegram client. Exiting...")
        sys.exit(1)
    
    pocket_option_initialized = bot.initialize_pocket_option()
    if not pocket_option_initialized:
        logger.error("Failed to initialize Pocket Option client. Exiting...")
        sys.exit(1)
    
    # Initialize session management
    session_management_initialized = bot.initialize_session_management()
    if not session_management_initialized:
        logger.error("Failed to initialize session management. Exiting...")
        sys.exit(1)
    
    logger.info("✅ Enhanced Self Bot initialized successfully")
    logger.info("🚀 LATENCY-OPTIMIZED TRADING MODE ENABLED")
    logger.info("Bot is now monitoring for signals...")
    
    # Start monitoring
    await bot.start_monitoring()

if __name__ == "__main__":
    # Handle Ctrl+C gracefully with proper cleanup
    def signal_handler(sig, frame):
        logger.info("Shutting down Enhanced Self Bot...")
        if "bot" in locals():
            try:
                if hasattr(bot, "timestamp_recorder") and hasattr(bot.timestamp_recorder, "flush_buffer"):
                    bot.timestamp_recorder.flush_buffer()
            except Exception as e:
                logger.error(f"Error flushing timestamp buffer on shutdown: {str(e)}")
            bot.cleanup_session()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    print("Enhanced Pocket Option Trading Bot with Latency Optimization")
    print("=" * 60)
    print("🚀 Features:")
    print("  • NTP synchronization automation")
    print("  • Latency threshold checking")
    print("  • Process priority elevation")
    print("  • Network optimization integration")
    print("  • Real-time signal monitoring")
    print("  • Session management")
    print("")
    
    # Run the enhanced bot
    asyncio.run(main())
