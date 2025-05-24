#!/usr/bin/env python3
"""
self_bot.py - Self Bot v1.0 for Pocket Option Trading

This script implements the Self Bot v1.0 that monitors the BINARY TRADING CLUB
Telegram channel for trading signals and executes trades on Pocket Option using
the websocket SSID authentication method.

The bot follows these steps:
1. Connect to Telegram using a user account (Telethon)
2. Monitor the BINARY TRADING CLUB channel for trading signals
3. Parse the signals in the two-message format
4. Connect to Pocket Option using the SSID authentication
5. Execute trades based on the signals at the specified time
6. Log all signals and trades to a SQLite database

Usage:
    python self_bot.py --config config/bot_config.json --telegram-config config/telegram_config.json --pocket-option-config config/pocket_option_config.json --verbose
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("self_bot.log")
    ]
)
logger = logging.getLogger(__name__)

# Signal parsing regex patterns
FIRST_MESSAGE_PATTERN = r"Trading Pair: (\w+/\w+)(?:\s*\(OTC\))?"
SECOND_MESSAGE_TIMER_PATTERN = r"SET THE TIMER TO (\d{2}:\d{2}:\d{2})"
SECOND_MESSAGE_PAIR_PATTERN = r"Currency pair (\w+/\w+)"
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
        """
        Initialize the Self Bot.
        
        Args:
            config_file: Path to bot configuration file
            telegram_config_file: Path to Telegram configuration file
            pocket_option_config_file: Path to Pocket Option configuration file
            db_file: Path to SQLite database file
            verbose: Enable verbose output
        """
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
    
    def _save_config(self, config: Dict[str, Any], config_file: str) -> None:
        """Save configuration to file."""
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=4)
        logger.info(f"Configuration saved to {config_file}")
    
    async def initialize_telegram(self) -> bool:
        """
        Initialize the Telegram client.
        
        Returns:
            True if initialized successfully, False otherwise
        """
        try:
            # Get Telegram API credentials
            api_id = self.telegram_config.get("api_id") or os.environ.get("TELEGRAM_API_ID")
            api_hash = self.telegram_config.get("api_hash") or os.environ.get("TELEGRAM_API_HASH")
            session_name = self.telegram_config.get("session_name", "pocket_option_userbot")
            
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
                await self.telegram_client.send_code_request(input("Enter your phone number: "))
                await self.telegram_client.sign_in(input("Enter your phone number again: "), input("Enter the code: "))
                logger.info("Successfully authenticated")
            else:
                logger.info("Already authenticated using existing session")
                me = await self.telegram_client.get_me()
                logger.info(f"Logged in as: {me.first_name} {getattr(me, 'last_name', '')} (@{me.username})")
            
            return True
        except Exception as e:
            logger.error(f"Error initializing Telegram client: {str(e)}")
            return False
    
    def initialize_pocket_option(self) -> bool:
        """
        Initialize the Pocket Option API client using PocketOptionAPI-v2.
        
        Returns:
            True if initialized successfully, False otherwise
        """
        try:
            # Get SSID from config
            ssid = self.pocket_option_config.get("ssid")
            if not ssid:
                logger.error("No SSID provided in configuration")
                return False
            
            # Get demo mode setting
            is_demo = self.pocket_option_config.get("is_demo", True)
            
            # Initialize the PocketOption client
            logger.info(f"Initializing Pocket Option client (Demo mode: {is_demo})")
            self.pocket_option_client = PocketOption(ssid, is_demo)
            
            # Connect to the API
            connection_result = self.pocket_option_client.connect()
            if connection_result:
                logger.info("Successfully connected to Pocket Option API")
                
                # Get account balance
                balance = self.pocket_option_client.get_balance()
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
    
    def initialize_database(self) -> bool:
        """
        Initialize the SQLite database.
        
        Returns:
            True if initialized successfully, False otherwise
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.db_file), exist_ok=True)
            
            # Connect to database
            self.db_conn = sqlite3.connect(self.db_file)
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
    
    async def access_channel(self) -> Optional[Channel]:
        """
        Access a Telegram channel that the user is already a member of.
        
        Returns:
            Channel object if found, None otherwise
        """
        if not self.telegram_client:
            logger.error("Telegram client not initialized")
            return None
        
        channel_name = self.telegram_config.get("channel_name", "BINARY TRADING CLUB")
        channel_username = self.telegram_config.get("channel_username")
        channel_id = self.telegram_config.get("channel_id")
        
        logger.info(f"Accessing channel: {channel_name}")
        
        try:
            # Try to use channel ID if available
            if channel_id:
                try:
                    entity = await self.telegram_client.get_entity(int(channel_id))
                    logger.info(f"Accessed channel by ID: {entity.title}")
                    return entity
                except Exception as e:
                    logger.debug(f"Error accessing channel by ID: {str(e)}")
            
            # Try to use channel username if available
            if channel_username:
                try:
                    entity = await self.telegram_client.get_entity(channel_username)
                    logger.info(f"Accessed channel by username: {entity.title}")
                    return entity
                except Exception as e:
                    logger.debug(f"Error accessing channel by username: {str(e)}")
            
            # Try to find by name in dialog list
            async for dialog in self.telegram_client.iter_dialogs():
                if dialog.name == channel_name or (hasattr(dialog.entity, 'username') and dialog.entity.username == channel_username):
                    logger.info(f"Found channel in dialog list: {dialog.name}")
                    return dialog.entity
            
            logger.warning(f"Channel not found: {channel_name}")
            logger.warning("Please ensure your Telegram account is already a member of this channel.")
            return None
            
        except Exception as e:
            logger.error(f"Error accessing channel: {str(e)}")
            return None
    
    def parse_first_message(self, message_text: str) -> Optional[str]:
        """
        Parse the first message of the signal format.
        
        Args:
            message_text: Message text to parse
            
        Returns:
            Trading pair if found, None otherwise
        """
        pattern = self.telegram_config.get("first_message_regex", FIRST_MESSAGE_PATTERN)
        match = re.search(pattern, message_text)
        
        if match:
            trading_pair = match.group(1)
            logger.info(f"Parsed first message: Trading pair = {trading_pair}")
            return trading_pair
        
        return None
    
    def parse_second_message(self, message_text: str) -> Optional[Dict]:
        """
        Parse the second message of the signal format.
        
        Args:
            message_text: Message text to parse
            
        Returns:
            Dictionary with signal details if parsed successfully, None otherwise
        """
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
    
    async def process_message(self, message: Message) -> None:
        """
        Process a message from the channel.
        
        Args:
            message: Message to process
        """
        if not message.text:
            return
            
        # Log all messages if enabled
        if self.telegram_config.get("log_all_messages", False):
            sender = await message.get_sender()
            sender_name = getattr(sender, 'first_name', 'Unknown')
            logger.info(f"Message from {sender_name}: {message.text}")
        
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
                        
                        logger.info(f"Complete signal detected: {complete_signal}")
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
                            
                            # Schedule trade execution
                            asyncio.create_task(self.schedule_trade_execution(complete_signal))
                        else:
                            logger.warning(f"Invalid signal: {validation_message}")
                            
                            # Save invalid signal to database
                            self.save_signal_to_db(complete_signal)
                        
                        # Reset tracking
                        self.last_first_message = None
                        self.last_first_message_time = None
                    else:
                        logger.warning(f"Pair mismatch: {self.last_first_message} vs {signal['pair']}")
    
    def validate_signal(self, signal: Dict) -> Tuple[bool, str]:
        """
        Validate a trading signal.
        
        Args:
            signal: Signal to validate
            
        Returns:
            Tuple of (is_valid, validation_message)
        """
        # Check if we have sufficient balance
        try:
            balance = self.pocket_option_client.get_balance()
            trade_amount = self.config.get("trade_amount", 1)
            
            if balance < trade_amount:
                return False, f"Insufficient balance: {balance} < {trade_amount}"
        except Exception as e:
            logger.error(f"Error checking balance: {str(e)}")
            return False, f"Error checking balance: {str(e)}"
        
        # Check if we've reached the maximum daily trades
        max_daily_trades = self.config.get("max_daily_trades", 0)
        if max_daily_trades > 0 and self.stats["executed_trades"] >= max_daily_trades:
            return False, f"Maximum daily trades reached: {max_daily_trades}"
        
        # Check if we've reached the maximum daily loss
        max_daily_loss = self.config.get("max_daily_loss", 0)
        if max_daily_loss > 0 and self.stats["total_profit"] < -max_daily_loss:
            return False, f"Maximum daily loss reached: {max_daily_loss}"
        
        # Check if the timer is in the future
        try:
            timer_parts = signal["timer"].split(":")
            timer_hour = int(timer_parts[0])
            timer_minute = int(timer_parts[1])
            timer_second = int(timer_parts[2])
            
            now = datetime.now(self.timezone)
            timer_time = now.replace(hour=timer_hour, minute=timer_minute, second=timer_second, microsecond=0)
            
            # If the timer is in the past, assume it's for the next day
            if timer_time < now:
                timer_time = timer_time + timedelta(days=1)
            
            # Check if the timer is too far in the future (more than 24 hours)
            if (timer_time - now).total_seconds() > 86400:
                return False, f"Timer is too far in the future: {signal['timer']}"
            
            # Check if the timer is too close (less than 5 seconds)
            min_seconds_before_timer = self.config.get("min_seconds_before_timer", 5)
            if (timer_time - now).total_seconds() < min_seconds_before_timer:
                return False, f"Timer is too close: {signal['timer']} (less than {min_seconds_before_timer} seconds)"
        except Exception as e:
            logger.error(f"Error validating timer: {str(e)}")
            return False, f"Error validating timer: {str(e)}"
        
        return True, "Signal is valid"
    
    def save_signal_to_db(self, signal: Dict) -> Optional[int]:
        """
        Save a signal to the database.
        
        Args:
            signal: Signal to save
            
        Returns:
            Signal ID if saved successfully, None otherwise
        """
        if not self.db_conn:
            logger.error("Database not initialized")
            return None
        
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
        except Exception as e:
            logger.error(f"Error saving signal to database: {str(e)}")
            return None
    
    def save_trade_to_db(self, trade: Dict) -> Optional[int]:
        """
        Save a trade to the database.
        
        Args:
            trade: Trade to save
            
        Returns:
            Trade ID if saved successfully, None otherwise
        """
        if not self.db_conn:
            logger.error("Database not initialized")
            return None
        
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
        except Exception as e:
            logger.error(f"Error saving trade to database: {str(e)}")
            return None
    
    async def schedule_trade_execution(self, signal: Dict) -> None:
        """
        Schedule a trade for execution at the specified timer, or execute immediately if configured.
        
        Args:
            signal: Signal to execute
        """
        try:
            # Immediate execution logic
            if self.config.get("immediate_execution", False):
                logger.info("Immediate execution enabled. Executing trade as soon as signal is validated.")
                self.execute_trade(signal)
                return

            # Parse timer
            timer_parts = signal["timer"].split(":")
            timer_hour = int(timer_parts[0])
            timer_minute = int(timer_parts[1])
            timer_second = int(timer_parts[2])
            
            now = datetime.now(self.timezone)
            
            # Check if the timer is in the format "00:01:00" which means "1 minute from now"
            # rather than a specific time of day
            if timer_hour == 0 and timer_minute <= 5:  # Assuming signals are for short timeframes (≤ 5 minutes)
                # Calculate execution time as X minutes from now
                timer_time = now + timedelta(minutes=timer_minute, seconds=timer_second)
                logger.info(f"Interpreting timer as relative time: {timer_minute} minutes and {timer_second} seconds from now")
            else:
                # Use the original absolute time calculation
                timer_time = now.replace(hour=timer_hour, minute=timer_minute, second=timer_second, microsecond=0)
                
                # If the timer is in the past, assume it's for the next day
                if timer_time < now:
                    timer_time = timer_time + timedelta(days=1)
            
            # Calculate seconds until timer
            seconds_until_timer = (timer_time - now).total_seconds()
            
            logger.info(f"Scheduling trade execution for {signal['pair']} {signal['direction']} at {timer_time.strftime('%H:%M:%S')} ({seconds_until_timer:.2f} seconds from now)")
            
            # Wait until timer
            await asyncio.sleep(seconds_until_timer)
            
            # Execute trade
            self.execute_trade(signal)
            
        except Exception as e:
            logger.error(f"Error scheduling trade execution: {str(e)}")
    
    def execute_trade(self, signal: Dict) -> None:
        """
        Execute a trade based on a signal.
        
        Args:
            signal: Signal to execute
        """
        try:
            # Get trade parameters
            asset = signal["pair"].replace("/", "")  # Remove slash for Pocket Option format
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
            logger.info(f"Executing trade: {asset} {direction.upper()} {amount} (expiry: {expiry}s)")
            
            # Check if we're in test mode
            if self.config.get("test_mode", True):
                logger.info("Test mode enabled. Simulating trade execution.")
                
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
                
                # Schedule trade result
                asyncio.create_task(self.simulate_trade_result(trade_id, expiry))
            else:
                # Execute real trade using PocketOptionAPI-v2
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
                    
                    # Update trade in database
                    self.save_trade_to_db(trade)
                    
                    # Add to active trades
                    self.active_trades[trade_id] = trade
                    
                    # Increment executed trades counter
                    self.stats["executed_trades"] += 1
                    
                    # Schedule trade result check
                    asyncio.create_task(self.check_trade_result(trade_id, expiry))
                else:
                    logger.error(f"Failed to execute trade: {result}")
                    
                    trade["status"] = "failed"
                    trade["error_message"] = f"Failed to execute trade: {result}"
                    
                    # Update trade in database
                    self.save_trade_to_db(trade)
                    
                    # Increment error trades counter
                    self.stats["error_trades"] += 1
            
        except Exception as e:
            logger.error(f"Error executing trade: {str(e)}")
            
            # Update trade record
            if "trade" in locals():
                trade["status"] = "error"
                trade["error_message"] = str(e)
                
                # Update trade in database
                self.save_trade_to_db(trade)
                
                # Increment error trades counter
                self.stats["error_trades"] += 1
    
    async def check_trade_result(self, trade_id: str, expiry: int) -> None:
        """
        Check the result of a trade.
        
        Args:
            trade_id: Trade ID to check
            expiry: Expiry time in seconds
        """
        try:
            # Wait for trade to complete
            logger.info(f"Waiting {expiry} seconds for trade {trade_id} to complete...")
            await asyncio.sleep(expiry + 2)  # Add 2 seconds buffer
            
            # Get trade result using PocketOptionAPI-v2
            result = self.pocket_option_client.check_win(trade_id)
            
            if result:
                # Extract result and profit
                win = result.get("win", False)
                profit = result.get("profit", 0.0)
                
                # Update trade record
                self.active_trades[trade_id]["status"] = "completed"
                self.active_trades[trade_id]["result"] = "win" if win else "lose"
                self.active_trades[trade_id]["profit"] = profit
                
                # Update trade in database
                self.save_trade_to_db(self.active_trades[trade_id])
                
                # Update stats
                if win:
                    self.stats["winning_trades"] += 1
                else:
                    self.stats["losing_trades"] += 1
                    
                self.stats["total_profit"] += profit
                
                logger.info(f"Trade {trade_id} completed: {'WIN' if win else 'LOSE'} (Profit: {profit})")
            else:
                logger.error(f"Failed to get result for trade {trade_id}")
                
                # Update trade record
                self.active_trades[trade_id]["status"] = "error"
                self.active_trades[trade_id]["error_message"] = "Failed to get trade result"
                
                # Update trade in database
                self.save_trade_to_db(self.active_trades[trade_id])
                
                # Increment error trades counter
                self.stats["error_trades"] += 1
            
                # Remove from active trades
                del self.active_trades[trade_id]
        except Exception as e:
            logger.error(f"Error checking trade result: {str(e)}")
    
    async def setup_message_handler(self) -> None:
        """
        Set up the message handler for the Telegram client.
        """
        if not self.telegram_client:
            logger.error("Telegram client not initialized")
            return
        
        # Get channel ID
        channel_id = self.telegram_config.get("channel_id")
        if not channel_id:
            logger.error("Channel ID not provided in configuration")
            return
        
        # Register event handler for new messages
        @self.telegram_client.on(events.NewMessage(chats=int(channel_id)))
        async def handler(event):
            await self.process_message(event.message)
        
        logger.info(f"Message handler set up for channel ID: {channel_id}")
    
    async def print_stats(self) -> None:
        """
        Print the current trading statistics.
        """
        runtime = datetime.now(self.timezone) - self.stats["start_time"]
        runtime_str = str(runtime).split('.')[0]  # Remove microseconds
        
        # Get current balance
        try:
            balance = self.pocket_option_client.get_balance()
        except Exception as e:
            logger.error(f"Error getting balance: {str(e)}")
            balance = "Unknown"
        
        # Calculate win rate
        total_completed = self.stats["winning_trades"] + self.stats["losing_trades"]
        win_rate = (self.stats["winning_trades"] / total_completed * 100) if total_completed > 0 else 0
        
        stats_str = f"""
=== Self Bot v1.0 Statistics ===
Runtime: {runtime_str}
Current Balance: {balance}

Signals:
  Total Signals: {self.stats["total_signals"]}
  Valid Signals: {self.stats["valid_signals"]}

Trades:
  Executed Trades: {self.stats["executed_trades"]}
  Winning Trades: {self.stats["winning_trades"]}
  Losing Trades: {self.stats["losing_trades"]}
  Error Trades: {self.stats["error_trades"]}
  
Performance:
  Win Rate: {win_rate:.2f}%
  Total Profit: {self.stats["total_profit"]:.2f}
==============================
"""
        logger.info(stats_str)
    
    async def run(self) -> None:
        """
        Run the Self Bot.
        """
        try:
            # Initialize database
            if not self.initialize_database():
                logger.error("Failed to initialize database")
                return
            
            # Initialize Telegram client
            if not await self.initialize_telegram():
                logger.error("Failed to initialize Telegram client")
                return
            
            # Access channel
            channel = await self.access_channel()
            if not channel:
                logger.error("Failed to access channel")
                return
            
            # Initialize Pocket Option client
            if not self.initialize_pocket_option():
                logger.error("Failed to initialize Pocket Option client")
                return
            
            # Set up message handler
            await self.setup_message_handler()
            
            # Print initial stats
            await self.print_stats()
            
            # Keep the bot running
            logger.info("Self Bot is running. Press Ctrl+C to stop.")
            
            # Print stats periodically
            stats_interval = self.config.get("stats_interval", 3600)  # Default: 1 hour
            while True:
                await asyncio.sleep(stats_interval)
                await self.print_stats()
                
        except KeyboardInterrupt:
            logger.info("Bot interrupted by user")
        except Exception as e:
            logger.error(f"Error running bot: {str(e)}")
        finally:
            # Close connections
            if self.telegram_client:
                await self.telegram_client.disconnect()
                
            if self.db_conn:
                self.db_conn.close()
            
            logger.info("Bot stopped")
    
    async def simulate_trade_result(self, trade_id: str, expiry: int) -> None:
        """
        Simulate the result of a trade (for test mode).
        
        Args:
            trade_id: Trade ID to check
            expiry: Expiry time in seconds
        """
        try:
            # Wait for trade to complete
            logger.info(f"Waiting {expiry} seconds for simulated trade {trade_id} to complete...")
            await asyncio.sleep(expiry + 2)  # Add 2 seconds buffer
            
            # Simulate trade result
            import random
            win_rate = self.config.get("test_mode_win_rate", 0.5)
            result = "win" if random.random() < win_rate else "lose"
            profit = self.active_trades[trade_id]["amount"] * 0.8 if result == "win" else -self.active_trades[trade_id]["amount"]
            
            # Update trade record
            self.active_trades[trade_id]["status"] = "completed"
            self.active_trades[trade_id]["result"] = result
            self.active_trades[trade_id]["profit"] = profit
            
            # Update trade in database
            self.save_trade_to_db(self.active_trades[trade_id])
            
            # Update stats
            if result == "win":
                self.stats["winning_trades"] += 1
            else:
                self.stats["losing_trades"] += 1
                
            self.stats["total_profit"] += profit
            
            logger.info(f"Simulated trade {trade_id} completed: {result.upper()} (Profit: {profit})")
            
            # Remove from active trades
            del self.active_trades[trade_id]
        except Exception as e:
            logger.error(f"Error simulating trade result: {str(e)}")
            
            # Update trade record if it exists
            if trade_id in self.active_trades:
                self.active_trades[trade_id]["status"] = "error"
                self.active_trades[trade_id]["error_message"] = str(e)
                
                # Update trade in database
                self.save_trade_to_db(self.active_trades[trade_id])
                
                # Increment error trades counter
                self.stats["error_trades"] += 1
                
                # Remove from active trades
                del self.active_trades[trade_id]


    def add_pairs_to_favorites(self):
        """
        Add all favorite pairs from config to Pocket Option favorites (if supported by API).
        """
        try:
            favorite_pairs = self.config.get("favorite_pairs", [])
            if not favorite_pairs:
                logger.info("No favorite pairs specified in config.")
                return
            # If PocketOptionAPI-v2 supports favorites management, call the method here.
            # Example: self.pocket_option_client.add_favorites(favorite_pairs)
            logger.info(f"Ensuring favorite pairs are set: {favorite_pairs}")
            # If not supported, just log for now.
        except Exception as e:
            logger.error(f"Error adding pairs to favorites: {str(e)}")

async def main():
    """Main function to parse arguments and start the Self Bot."""
    parser = argparse.ArgumentParser(description='Self Bot v1.0 for Pocket Option Trading')
    parser.add_argument('--config', type=str, default='config/bot_config.json', help='Path to bot configuration file')
    parser.add_argument('--telegram-config', type=str, default='config/telegram_config.json', help='Path to Telegram configuration file')
    parser.add_argument('--pocket-option-config', type=str, default='config/pocket_option_config.json', help='Path to Pocket Option configuration file')
    parser.add_argument('--db', type=str, default='data/trades.db', help='Path to SQLite database file')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose output')
    parser.add_argument('--test-mode', action='store_true', help='Run in test mode (simulated trades)')
    
    args = parser.parse_args()
    
    # Load .env file if it exists
    dotenv.load_dotenv()
    
    # Create bot instance
    bot = SelfBot(
        config_file=args.config,
        telegram_config_file=args.telegram_config,
        pocket_option_config_file=args.pocket_option_config,
        db_file=args.db,
        verbose=args.verbose
    )
    
    # If test mode is specified, update config
    if args.test_mode:
        bot.config["test_mode"] = True
        logger.info("Test mode enabled via command line argument")
    
    # Run bot
    await bot.run()


if __name__ == "__main__":
    print("Self Bot v1.0 for Pocket Option Trading")
    print("---------------------------------------")
    print("This bot monitors the BINARY TRADING CLUB Telegram channel for trading signals")
    print("and executes trades on Pocket Option using the websocket SSID authentication.")
    print("")
    
    try:
        # Set up signal handlers for graceful shutdown if platform supports it
        import platform
        if platform.system() != "Windows":
            loop = asyncio.get_event_loop()
            for sig in (signal.SIGINT, signal.SIGTERM):
                loop.add_signal_handler(sig, lambda: asyncio.create_task(
                    logger.info("Received shutdown signal, closing connections...")
                ))
        
        # Run the main function
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot interrupted by user")
        sys.exit(1)
    except Exception as e:
        import traceback
        print(f"\nError running bot: {str(e)}")
        print("\nTraceback:")
        traceback.print_exc()
        sys.exit(1)
