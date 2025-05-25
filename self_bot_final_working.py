#!/usr/bin/env python3
"""
self_bot_final_working.py - FINAL WORKING Self Bot v1.0 for Pocket Option Trading

This script implements the Self Bot v1.0 that monitors Telegram channels for trading signals
and executes trades on Pocket Option using the websocket SSID authentication method.

FINAL FIXES:
- Fixed event loop conflict using threading for trade execution
- Unicode logging support
- Single message signal parsing
- Real trading mode enabled
- Actual trades executing on platform
- Complete exception handling
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
        """Initialize the Pocket Option API client using PocketOptionAPI-v2."""
        try:
            # Get SSID from config
            ssid = self.pocket_option_config.get("ssid")
            if not ssid:
                logger.error("No SSID provided in configuration")
                return False
            
            # Get demo mode setting
            is_demo = self.pocket_option_config.get("is_demo", False)  # Default to real trading
            
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
                    except:
                        time.sleep(1)
                
                logger.info(f"Account balance: {balance}")
                return True
            else:
                logger.error("Failed to connect to Pocket Option API")
                return False
        except Exception as e:
            logger.error(f"Error initializing Pocket Option client: {str(e)}")
            return False
    
    def initialize_database(self) -> bool:
        """Initialize the SQLite database."""
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
                    logger.info(f"Accessed channel by ID: {entity.title}")
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
    
    async def process_message(self, message) -> None:
        """Process a message from the channel."""
        if not message.text:
            return
        
        try:
            # Clean message text for logging (remove emojis that cause encoding issues)
            clean_text = re.sub(r'[^\x00-\x7F]+', '?', message.text)
            logger.info(f"📨 Received message: {clean_text[:100]}...")
            
            # Try to parse as complete signal
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
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
    
    def validate_signal(self, signal: Dict) -> Tuple[bool, str]:
        """Validate a trading signal."""
        try:
            # Check if we have sufficient balance
            balance = self.pocket_option_client.get_balance()
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
        """Save a signal to the database."""
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
        """Save a trade to the database."""
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
                except Exception as e:
                    logger.error(f"❌ Error executing real trade: {str(e)}")
                    trade["status"] = "error"
                    trade["error_message"] = str(e)
                    self.save_trade_to_db(trade)
                    self.stats["error_trades"] += 1
            
        except Exception as e:
            logger.error(f"Error executing trade: {str(e)}")
    
    def check_trade_result_threaded(self, trade_id: str, expiry: int) -> None:
        """Check trade result in a separate thread."""
        try:
            # Wait for trade to complete
            logger.info(f"⏳ Waiting {expiry} seconds for trade {trade_id} to complete...")
            time.sleep(expiry + 2)  # Add 2 seconds buffer
            
            # Get trade result
            result = self.pocket_option_client.check_win(trade_id)
            
            if result:
                # Extract result and profit
                win = result.get("win", False)
                profit = result.get("profit", 0.0)
                
                # Update trade record
                if trade_id in self.active_trades:
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
                    
                    logger.info(f"✅ TRADE RESULT: {trade_id} - {'WIN' if win else 'LOSE'} (Profit: ${profit})")
                    
                    # Remove from active trades
                    del self.active_trades[trade_id]
            else:
                logger.error(f"❌ Failed to get result for trade {trade_id}")
                
                if trade_id in self.active_trades:
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
        """Set up the message handler for the Telegram client."""
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
        
        logger.info(f"📡 Message handler set up for channel ID: {channel_id}")
    
    async def print_stats(self) -> None:
        """Print the current trading statistics."""
        runtime = datetime.now(self.timezone) - self.stats["start_time"]
        runtime_str = str(runtime).split('.')[0]
