#!/usr/bin/env python3
"""
self_bot.py - FINAL WORKING Self Bot v1.0 for Pocket Option Trading

This script implements the Self Bot v1.0 that monitors Telegram channels for trading signals
and executes trades on Pocket Option using the websocket SSID authentication method.

FINAL FIXES APPLIED:
- Added threading for trade execution to avoid event loop conflicts
- Enhanced Unicode logging support
- Added single message signal parsing
- Real trading mode enabled
- Complete exception handling
- OTC pairs support
"""

import os
import sys
import json
import asyncio
import logging
import argparse
import sqlite3
import pytz
import re
import signal
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
import dotenv

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
        logging.FileHandler("self_bot.log", encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# Signal parsing regex patterns
FIRST_MESSAGE_PATTERN = r"Trading Pair: (\w+/\w+)(?:\s*\(OTC\))?"
SECOND_MESSAGE_TIMER_PATTERN = r"SET THE TIMER TO (\d{2}:\d{2}:\d{2})"
SECOND_MESSAGE_PAIR_PATTERN = r"Currency pair ([A-Z]{3}/[A-Z]{3})"
SECOND_MESSAGE_DIRECTION_PATTERN = r"(HIGHER|LOWER)"
SECOND_MESSAGE_EXPIRY_PATTERN = r"Trade time: (\d+) MIN"

class SelfBot:
    def __init__(
        self,
        config_file: str = "config/bot_config.json",
        telegram_config_file: str = "config/telegram_config.json",
        pocket_option_config_file: str = "config/pocket_option_config.json",
        db_file: str = "data/trades.db",
        verbose: bool = False
    ):
        """Initialize the Self Bot."""
        self.config_file = config_file
        self.telegram_config_file = telegram_config_file
        self.pocket_option_config_file = pocket_option_config_file
        self.db_file = db_file
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
        
        # Initialize clients
        self.telegram_client = None
        self.pocket_option_client = None
        
        # Signal tracking
        self.last_first_message = None
        self.last_first_message_time = None
        self.pending_signals = []
        self.active_trades = {}
        
        # Database connection
        self.db_conn = None
        
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
        """Initialize the Pocket Option API client using PocketOptionAPI-v2."""
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
                
                # Add favorite pairs after connection
                self.add_pairs_to_favorites()
                
                return True
            else:
                logger.error("Failed to connect to Pocket Option API")
                return False
        except Exception as e:
            logger.error(f"Error initializing Pocket Option client: {str(e)}")
            return False
    
    def add_pairs_to_favorites(self) -> None:
        """Add trading pairs to favorites. Commented out due to missing subscribe method in PocketOptionAPI-v2."""
        try:
            # Get favorite pairs from config
            favorite_pairs = self.config.get("favorite_pairs", [
                "EURUSD_otc", "GBPUSD_otc", "USDJPY_otc", "AUDUSD_otc", 
                "USDCAD_otc", "USDCHF_otc", "NZDUSD_otc", "EURJPY_otc"
            ])
            
            # Commented out subscribe calls as the method does not exist in PocketOptionAPI-v2
            """
            for pair in favorite_pairs:
                try:
                    if self.pocket_option_client:
                        self.pocket_option_client.subscribe(pair)
                        logger.debug(f"Added {pair} to favorites")
                except Exception as e:
                    logger.debug(f"Could not add {pair} to favorites: {str(e)}")
            """
            logger.info("Subscription to favorite pairs is currently disabled due to API limitations.")
                    
        except Exception as e:
            logger.error(f"Error adding pairs to favorites: {str(e)}")
    
    def initialize_database(self) -> bool:
        """Initialize the SQLite database with improved connection handling."""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.db_file), exist_ok=True)
            
            # Connect to database with timeout to prevent locking issues
            self.db_conn = sqlite3.connect(self.db_file, timeout=10)
            cursor = self.db_conn.cursor()
            
            # Create tables if they don't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    asset TEXT NOT NULL,
                    direction TEXT NOT NULL,
                    expiry INTEGER NOT NULL,
                    timer TEXT NOT NULL,
                    is_valid BOOLEAN NOT NULL,
                    validation_message TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    signal_id INTEGER NOT NULL,
                    timestamp TEXT NOT NULL,
                    asset TEXT NOT NULL,
                    direction TEXT NOT NULL,
                    expiry INTEGER NOT NULL,
                    amount REAL NOT NULL,
                    trade_id TEXT,
                    status TEXT NOT NULL,
                    result TEXT,
                    profit REAL,
                    error_message TEXT,
                    FOREIGN KEY (signal_id) REFERENCES signals (id)
                )
            ''')
            
            self.db_conn.commit()
            logger.info("Database initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Error initializing database: {str(e)}")
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
    
    def parse_signal_message(self, message_text: str) -> Optional[Dict]:
        """
        Parse a single message that contains the complete signal.
        
        Your format:
        ❗️SET THE TIMER TO 00:01:00❗️
        
        First signal: Currency pair AUD/USD 
        HIGHER ⬆️ 
        Trade time: 1 MIN
        """
        try:
            # Clean the message text
            text = message_text.strip()
            
            # Extract timer
            timer_match = re.search(r"SET THE TIMER TO (\d{2}:\d{2}:\d{2})", text)
            if not timer_match:
                return None
            timer = timer_match.group(1)
            
            # Extract currency pair
            pair_match = re.search(r"Currency pair ([A-Z]{3}/[A-Z]{3})", text)
            if not pair_match:
                return None
            pair = pair_match.group(1)
            
            # Extract direction
            direction = None
            if "HIGHER" in text or "⬆️" in text:
                direction = "HIGHER"
            elif "LOWER" in text or "⬇️" in text:
                direction = "LOWER"
            
            if not direction:
                return None
            
            # Extract expiry
            expiry_match = re.search(r"Trade time: (\d+) MIN", text)
            if not expiry_match:
                return None
            expiry = int(expiry_match.group(1))
            
            signal = {
                "timer": timer,
                "pair": pair,
                "direction": direction,
                "expiry": expiry
            }
            
            logger.info(f"✅ PARSED SIGNAL: {signal}")
            return signal
            
        except Exception as e:
            logger.error(f"Error parsing signal: {str(e)}")
            return None
    
    def parse_first_message(self, message_text: str) -> Optional[str]:
        """Parse the first message of the signal format."""
        pattern = self.telegram_config.get("first_message_regex", FIRST_MESSAGE_PATTERN)
        match = re.search(pattern, message_text)
        
        if match:
            trading_pair = match.group(1)
            logger.info(f"Parsed first message: Trading pair = {trading_pair}")
            return trading_pair
        
        return None
    
    def parse_second_message(self, message_text: str) -> Optional[Dict]:
        """Parse the second message of the signal format."""
        second_message_regex = self.telegram_config.get("second_message_regex", {})
        
        # Extract timer
        timer_pattern = second_message_regex.get("timer", SECOND_MESSAGE_TIMER_PATTERN)
        timer_match = re.search(timer_pattern, message_text)
        if not timer_match:
            return None
        timer = timer_match.group(1)
        
        # Extract pair
        pair_pattern = second_message_regex.get("pair", SECOND_MESSAGE_PAIR_PATTERN)
        pair_match = re.search(pair_pattern, message_text)
        if not pair_match:
            return None
        pair = pair_match.group(1)
        
        # Extract direction
        direction_pattern = second_message_regex.get("direction", SECOND_MESSAGE_DIRECTION_PATTERN)
        direction_match = re.search(direction_pattern, message_text)
        if not direction_match:
            return None
        direction = direction_match.group(1)
        
        # Extract expiry
        expiry_pattern = second_message_regex.get("expiry", SECOND_MESSAGE_EXPIRY_PATTERN)
        expiry_match = re.search(expiry_pattern, message_text)
        if not expiry_match:
            return None
        expiry = int(expiry_match.group(1))
        
        signal = {
            "timer": timer,
            "pair": pair,
            "direction": direction,
            "expiry": expiry
        }
        
        logger.info(f"Parsed second message: {signal}")
        return signal
    
    async def process_message(self, message) -> None:
        """Process a message from the channel."""
        if not message.text:
            return
        
        try:
            # Clean message text for logging (remove emojis that cause encoding issues)
            clean_text = re.sub(r'[^\x00-\x7F]+', '?', message.text)
            logger.info(f"📨 Received message: {clean_text[:100]}...")
            
            # Try to parse as complete signal first (single message format)
            signal = self.parse_signal_message(message.text)
            if signal:
                # Complete signal detected
                complete_signal = {
                    "pair": signal["pair"],
                    "timer": signal["timer"],
                    "direction": signal["direction"],
                    "expiry": signal["expiry"],
                    "timestamp": datetime.now(self.timezone).isoformat()
                }
                
                logger.info(f"🎯 COMPLETE SIGNAL DETECTED: {complete_signal}")
                self.stats["total_signals"] += 1
                
                # Validate signal
                valid, validation_message = self.validate_signal(complete_signal)
                complete_signal["is_valid"] = valid
                complete_signal["validation_message"] = validation_message
                
                if valid:
                    self.stats["valid_signals"] += 1
                    self.pending_signals.append(complete_signal)
                    
                    # Save signal to database
                    signal_id = self.save_signal_to_db(complete_signal)
                    if signal_id:
                        complete_signal["id"] = signal_id
                    
                    # Execute trade immediately using threading to avoid event loop conflict
                    logger.info("🚀 EXECUTING TRADE IMMEDIATELY")
                    trade_thread = threading.Thread(target=self.execute_trade_threaded, args=(complete_signal,))
                    trade_thread.daemon = True
                    trade_thread.start()
                else:
                    logger.warning(f"❌ Invalid signal: {validation_message}")
                    # Save invalid signal to database
                    self.save_signal_to_db(complete_signal)
                return
            
            # Fallback to two-message format
            # Try to parse as first message
            trading_pair = self.parse_first_message(message.text)
            if trading_pair:
                self.last_first_message = trading_pair
                self.last_first_message_time = datetime.now(self.timezone)
                return
                
            # Try to parse as second message
            if self.last_first_message and self.last_first_message_time:
                # Check if the time between messages is within the allowed window
                pair_match_window = self.telegram_config.get("pair_match_window", 60)
                time_diff = (datetime.now(self.timezone) - self.last_first_message_time).total_seconds()
                
                if time_diff <= pair_match_window:
                    signal = self.parse_second_message(message.text)
                    if signal:
                        # Verify that the pair matches
                        if signal["pair"] == self.last_first_message:
                            # Complete signal
                            complete_signal = {
                                "pair": self.last_first_message,
                                "timer": signal["timer"],
                                "direction": signal["direction"],
                                "expiry": signal["expiry"],
                                "timestamp": datetime.now(self.timezone).isoformat()
                            }
                            
                            logger.info(f"🎯 COMPLETE SIGNAL DETECTED (Two-message): {complete_signal}")
                            self.stats["total_signals"] += 1
                            
                            # Validate signal
                            valid, validation_message = self.validate_signal(complete_signal)
                            complete_signal["is_valid"] = valid
                            complete_signal["validation_message"] = validation_message
                            
                            if valid:
                                self.stats["valid_signals"] += 1
                                self.pending_signals.append(complete_signal)
                                
                                # Save signal to database
                                signal_id = self.save_signal_to_db(complete_signal)
                                if signal_id:
                                    complete_signal["id"] = signal_id
                                
                                # Execute trade immediately using threading
                                logger.info("🚀 EXECUTING TRADE IMMEDIATELY")
                                trade_thread = threading.Thread(target=self.execute_trade_threaded, args=(complete_signal,))
                                trade_thread.daemon = True
                                trade_thread.start()
                            else:
                                logger.warning(f"❌ Invalid signal: {validation_message}")
                                # Save invalid signal to database
                                self.save_signal_to_db(complete_signal)
                            
                            # Reset tracking
                            self.last_first_message = None
                            self.last_first_message_time = None
                        else:
                            logger.warning(f"Pair mismatch: {self.last_first_message} vs {signal['pair']}")
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
    
    def validate_signal(self, signal: Dict) -> Tuple[bool, str]:
        """Validate a trading signal."""
        try:
            # Check if we have sufficient balance
            if self.pocket_option_client:
                balance = self.pocket_option_client.get_balance()
            else:
                return False, "Pocket Option client not initialized"
                
            trade_amount = self.config.get("trade_amount", 1)
            
            if balance is None:
                return False, "Could not retrieve account balance"
            
            if balance < trade_amount:
                return False, f"Insufficient balance: {balance} < {trade_amount}"
            
            # Check if we've reached the maximum daily trades
            max_daily_trades = self.config.get("max_daily_trades", 0)
            if max_daily_trades > 0 and self.stats["executed_trades"] >= max_daily_trades:
                return False, f"Maximum daily trades reached: {max_daily_trades}"
            
            # Check if we've reached the maximum daily loss
            max_daily_loss = self.config.get("max_daily_loss", 0)
            if max_daily_loss > 0 and self.stats["total_profit"] < -max_daily_loss:
                return False, f"Maximum daily loss reached: {max_daily_loss}"
            
            return True, "Signal is valid"
            
        except Exception as e:
            logger.error(f"Error validating signal: {str(e)}")
            return False, f"Error validating signal: {str(e)}"
    
    def save_signal_to_db(self, signal: Dict) -> Optional[int]:
        """Save a signal to the database with retry mechanism for locked database."""
        if not self.db_conn:
            logger.error("Database not initialized")
            return None
        
        max_retries = 5
        for attempt in range(max_retries):
            try:
                cursor = self.db_conn.cursor()
                
                # Insert signal
                cursor.execute('''
                    INSERT INTO signals (
                        timestamp, asset, direction, expiry, timer, is_valid, validation_message
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    signal["timestamp"],
                    signal["pair"],
                    signal["direction"],
                    signal["expiry"],
                    signal["timer"],
                    signal.get("is_valid", True),
                    signal.get("validation_message", "")
                ))
                
                self.db_conn.commit()
                signal_id = cursor.lastrowid
                logger.debug(f"Signal saved to database with ID: {signal_id}")
                return signal_id
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e).lower() and attempt < max_retries - 1:
                    logger.warning(f"Database locked, retrying ({attempt+1}/{max_retries})...")
                    time.sleep(1)  # Wait before retrying
                    continue
                else:
                    logger.error(f"Error saving signal to database: {str(e)}")
                    return None
            except Exception as e:
                logger.error(f"Error saving signal to database: {str(e)}")
                return None
    
    def save_trade_to_db(self, trade: Dict) -> Optional[int]:
        """Save a trade to the database with retry mechanism for locked database."""
        if not self.db_conn:
            logger.error("Database not initialized")
            return None
        
        max_retries = 5
        for attempt in range(max_retries):
            try:
                cursor = self.db_conn.cursor()
                
                # Insert trade
                cursor.execute('''
                    INSERT INTO trades (
                        signal_id, timestamp, asset, direction, expiry, amount, trade_id, status, result, profit, error_message
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    trade.get("signal_id"),
                    trade["timestamp"],
                    trade["asset"],
                    trade["direction"],
                    trade["expiry"],
                    trade["amount"],
                    trade.get("trade_id", ""),
                    trade["status"],
                    trade.get("result", ""),
                    trade.get("profit", 0.0),
                    trade.get("error_message", "")
                ))
                
                self.db_conn.commit()
                trade_id = cursor.lastrowid
                logger.debug(f"Trade saved to database with ID: {trade_id}")
                return trade_id
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e).lower() and attempt < max_retries - 1:
                    logger.warning(f"Database locked, retrying ({attempt+1}/{max_retries})...")
                    time.sleep(1)  # Wait before retrying
                    continue
                else:
                    logger.error(f"Error saving trade to database: {str(e)}")
                    return None
            except Exception as e:
                logger.error(f"Error saving trade to database: {str(e)}")
                return None
    
    def execute_trade_threaded(self, signal: Dict) -> None:
        """Execute a trade in a separate thread to avoid event loop conflicts."""
        try:
            # Get trade parameters and handle OTC pairs
            raw_pair = signal["pair"].replace("/", "")  # Remove slash for Pocket Option format
            
            # Check if this should be an OTC pair based on configuration
            use_otc_by_default = self.config.get("use_otc_by_default", True)
            
            # Determine if we should use OTC version
            if use_otc_by_default:
                asset = f"{raw_pair}_otc"
                logger.info(f"🎯 Using OTC pair: {asset} for signal pair: {signal['pair']}")
            else:
                asset = raw_pair
                logger.info(f"🎯 Using regular pair: {asset} for signal pair: {signal['pair']}")
            
            direction = "call" if signal["direction"] == "HIGHER" else "put"
            expiry = signal["expiry"] * 60  # Convert to seconds
            amount = self.config.get("trade_amount", 1)
            
            # Create trade record
            trade = {
                "signal_id": signal.get("id"),
                "timestamp": datetime.now(self.timezone).isoformat(),
                "asset": asset,
                "direction": direction,
                "expiry": expiry,
                "amount": amount,
                "status": "executing"
            }
            
            # Save trade to database
            trade_db_id = self.save_trade_to_db(trade)
            
            # Execute trade
            logger.info(f"🚀 EXECUTING TRADE: {asset} {direction.upper()} ${amount} (expiry: {expiry}s)")
            
            # Check if we're in test mode
            if self.config.get("test_mode", False):
                logger.info("🧪 TEST MODE: Simulating trade execution")
                
                # Simulate trade execution
                import random
                trade_id = f"test_{int(datetime.now().timestamp())}"
                trade["trade_id"] = trade_id
                trade["status"] = "executed"
                
                # Update trade in database
                self.save_trade_to_db(trade)
                
                # Add to active trades
                self.active_trades[trade_id] = trade
                
                # Increment executed trades counter
                self.stats["executed_trades"] += 1
                
                logger.info(f"✅ TEST TRADE EXECUTED: {trade_id}")
            else:
                # Execute real trade using PocketOptionAPI-v2
                logger.info("💰 REAL TRADING MODE: Executing actual trade on Pocket Option platform")
                
                try:
                    if self.pocket_option_client:
                        # Execute the trade
                        result = self.pocket_option_client.buy(
                            amount=amount,
                            active=asset,
                            action=direction,
                            expirations=expiry
                        )
                        
                        if result and result[0]:
                            trade_id = result[1]
                            trade["trade_id"] = trade_id
                            trade["status"] = "executed"
                            
                            logger.info(f"✅ REAL TRADE EXECUTED: {asset} {direction.upper()} ${amount} - Trade ID: {trade_id}")
                            
                            # Update trade in database
                            self.save_trade_to_db(trade)
                            
                            # Add to active trades
                            self.active_trades[trade_id] = trade
                            
                            # Increment executed trades counter
                            self.stats["executed_trades"] += 1
                            
                            # Schedule result checking
                            result_thread = threading.Thread(target=self.check_trade_result_threaded, args=(trade_id, expiry))
                            result_thread.daemon = True
                            result_thread.start()
                        else:
                            logger.error(f"❌ REAL TRADE FAILED: {result}")
                            
                            trade["status"] = "failed"
                            trade["error_message"] = f"Failed to execute trade: {result}"
                            
                            # Update trade in database
                            self.save_trade_to_db(trade)
                            
                            # Increment error trades counter
                            self.stats["error_trades"] += 1
                    else:
                        logger.error("❌ Pocket Option client not initialized")
                        trade["status"] = "error"
                        trade["error_message"] = "Pocket Option client not initialized"
                        self.save_trade_to_db(trade)
                        self.stats["error_trades"] += 1
                except Exception as e:
                    logger.error(f"❌ Error executing real trade: {str(e)}")
                    trade["status"] = "error"
                    trade["error_message"] = str(e)
                    self.save_trade_to_db(trade)
                    self.stats["error_trades"] += 1
            
        except Exception as e:
            logger.error(f"Error executing trade: {str(e)}")
    
    def check_trade_result_threaded(self, trade_id: str, expiry: int) -> None:
        """Check trade result in a separate thread to avoid event loop conflicts."""
        try:
            # Wait for the trade to complete
            time.sleep(expiry + 5)  # Wait for expiry plus buffer
            
            logger.info(f"🔍 Checking trade result for trade ID: {trade_id}")
            trade = self.active_trades.get(trade_id)
            
            if trade and self.pocket_option_client:
                try:
                    # Check trade result
                    result = self.pocket_option_client.check_win(trade_id)
                    
                    if result is not None:
                        if result > 0:
                            # Winning trade
                            logger.info(f"✅ WINNING TRADE: {trade_id} - Profit: ${result}")
                            trade["result"] = "win"
                            trade["profit"] = result
                            self.stats["winning_trades"] += 1
                            self.stats["total_profit"] += result
                        elif result < 0:
                            # Losing trade
                            logger.info(f"❌ LOSING TRADE: {trade_id} - Loss: ${result}")
                            trade["result"] = "loss"
                            trade["profit"] = result
                            self.stats["losing_trades"] += 1
                            self.stats["total_profit"] += result
                        else:
                            # Draw
                            logger.info(f"⚖️ DRAW TRADE: {trade_id} - No profit/loss")
                            trade["result"] = "draw"
                            trade["profit"] = 0.0
                        
                        # Update trade in database
                        self.save_trade_to_db(trade)
                        
                        # Log current stats
                        logger.info(f"📊 TRADING STATS: Total Profit: ${self.stats['total_profit']:.2f} | Wins: {self.stats['winning_trades']} | Losses: {self.stats['losing_trades']} | Total Trades: {self.stats['executed_trades']}")
                    else:
                        logger.warning(f"⚠️ Could not retrieve trade result for {trade_id}")
                        trade["result"] = "unknown"
                        trade["error_message"] = "Could not retrieve trade result"
                        self.save_trade_to_db(trade)
                except Exception as e:
                    logger.error(f"Error checking trade result: {str(e)}")
                    trade["result"] = "error"
                    trade["error_message"] = str(e)
                    self.save_trade_to_db(trade)
            else:
                logger.error(f"Trade {trade_id} not found or client not initialized")
        except Exception as e:
            logger.error(f"Error in check_trade_result_threaded: {str(e)}")
    
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

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Pocket Option Self Bot v1.0")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    return parser.parse_args()

async def main():
    """Main function to run the bot."""
    args = parse_arguments()
    
    # Create bot instance
    bot = SelfBot(verbose=args.verbose)
    
    # Initialize components
    telegram_initialized = await bot.initialize_telegram()
    if not telegram_initialized:
        logger.error("Failed to initialize Telegram client. Exiting...")
        sys.exit(1)
    
    pocket_option_initialized = bot.initialize_pocket_option()
    if not pocket_option_initialized:
        logger.error("Failed to initialize Pocket Option client. Exiting...")
        sys.exit(1)
    
    database_initialized = bot.initialize_database()
    if not database_initialized:
        logger.error("Failed to initialize database. Exiting...")
        sys.exit(1)
    
    logger.info("✅ Self Bot v1.0 initialized successfully")
    logger.info("💰 REAL TRADING MODE ENABLED")
    logger.info("Bot is now monitoring for signals...")
    
    # Start monitoring
    await bot.start_monitoring()

if __name__ == "__main__":
    # Handle Ctrl+C gracefully with proper cleanup
    def signal_handler(sig, frame):
        logger.info("Shutting down Self Bot...")
        # Ensure database connection is closed to prevent locks
        bot_instance = globals().get('bot')
        if bot_instance and bot_instance.db_conn:
            try:
                bot_instance.db_conn.close()
                logger.info("Database connection closed successfully.")
            except Exception as e:
                logger.error(f"Error closing database connection: {str(e)}")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    # Run the bot with global bot instance for signal handler
    bot = None
    asyncio.run(main())
