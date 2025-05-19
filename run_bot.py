#!/usr/bin/env python3
"""
run_bot.py - Controller script for the Pocket Option trading bot.

This script serves as the main entry point for running the Pocket Option trading bot
with enhanced features. It integrates the regional optimization, risk management,
and performance analysis modules to create a more profitable and efficient trading bot.
"""

import os
import sys
import json
import asyncio
import logging
import argparse
import signal
from datetime import datetime
import pytz
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("run_bot.log")
    ]
)
logger = logging.getLogger(__name__)

# Import bot and utility modules
try:
    from bot import PocketOptionBot
    from utils.regional_optimizer import RegionalOptimizer
    from utils.risk_manager import RiskManager
    from utils.performance_analyzer import PerformanceAnalyzer
except ImportError as e:
    logger.error(f"Error importing modules: {str(e)}")
    logger.error("Make sure you're running this script from the correct directory.")
    sys.exit(1)

class BotController:
    def __init__(
        self,
        bot_config_file: str = "config/bot_config.json",
        telegram_config_file: str = "config/telegram_config.json",
        pocket_option_config_file: str = "config/pocket_option_config.json",
        db_file: str = "data/trades.db",
        optimize_region: bool = True,
        use_risk_management: bool = True,
        analyze_performance: bool = True,
        verbose: bool = False
    ):
        """
        Initialize the bot controller.
        
        Args:
            bot_config_file: Path to bot configuration file
            telegram_config_file: Path to Telegram configuration file
            pocket_option_config_file: Path to Pocket Option configuration file
            db_file: Path to SQLite database file
            optimize_region: Whether to optimize for regional latency
            use_risk_management: Whether to use advanced risk management
            analyze_performance: Whether to analyze performance
            verbose: Enable verbose output
        """
        self.bot_config_file = bot_config_file
        self.telegram_config_file = telegram_config_file
        self.pocket_option_config_file = pocket_option_config_file
        self.db_file = db_file
        self.optimize_region = optimize_region
        self.use_risk_management = use_risk_management
        self.analyze_performance = analyze_performance
        self.verbose = verbose
        
        # Set logging level
        if verbose:
            logger.setLevel(logging.DEBUG)
        
        # Load configurations
        self.bot_config = self._load_config(bot_config_file)
        self.telegram_config = self._load_config(telegram_config_file)
        self.pocket_option_config = self._load_config(pocket_option_config_file)
        
        # Initialize components
        self.bot = None
        self.regional_optimizer = None
        self.risk_manager = None
        self.performance_analyzer = None
        
        # Create data directory if it doesn't exist
        os.makedirs(os.path.dirname(db_file), exist_ok=True)
    
    def _load_config(self, config_file: str) -> Dict[str, Any]:
        """Load configuration from file."""
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Error loading configuration from {config_file}: {str(e)}")
            return {}
    
    def _save_config(self, config: Dict[str, Any], config_file: str) -> None:
        """Save configuration to file."""
        try:
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            logger.info(f"Configuration saved to {config_file}")
        except Exception as e:
            logger.error(f"Error saving configuration to {config_file}: {str(e)}")
    
    async def optimize_region(self) -> None:
        """Optimize for regional latency."""
        if not self.optimize_region:
            logger.info("Regional optimization disabled")
            return
        
        logger.info("Optimizing for regional latency...")
        
        # Create regional optimizer
        self.regional_optimizer = RegionalOptimizer(
            region="South Africa",
            timezone=self.bot_config.get("timezone", "Africa/Johannesburg"),
            config_file=self.pocket_option_config_file,
            verbose=self.verbose
        )
        
        # Run optimization
        optimization_result = await self.regional_optimizer.optimize()
        
        logger.info(f"Regional optimization completed. Best server: {optimization_result['best_server']} ({optimization_result['best_avg_latency']:.2f}ms)")
    
    def initialize_risk_manager(self) -> None:
        """Initialize risk manager."""
        if not self.use_risk_management:
            logger.info("Advanced risk management disabled")
            return
        
        logger.info("Initializing risk manager...")
        
        # Get risk management configuration
        risk_config = self.bot_config.get("risk_management", {})
        
        # Create risk manager
        self.risk_manager = RiskManager(
            config_file=self.bot_config_file,
            db_file=self.db_file,
            strategy=risk_config.get("strategy", "fixed"),
            initial_balance=100.0,  # This will be updated when the bot connects
            trade_amount=self.bot_config.get("trade_amount", 1.0),
            risk_percentage=risk_config.get("risk_percentage", 2.0),
            max_risk_percentage=risk_config.get("max_risk_percentage", 10.0),
            max_consecutive_losses=risk_config.get("max_consecutive_losses", 3),
            verbose=self.verbose
        )
        
        logger.info("Risk manager initialized")
    
    def analyze_performance_data(self) -> None:
        """Analyze performance data."""
        if not self.analyze_performance:
            logger.info("Performance analysis disabled")
            return
        
        logger.info("Analyzing performance data...")
        
        # Create performance analyzer
        self.performance_analyzer = PerformanceAnalyzer(
            db_file=self.db_file,
            config_file=self.bot_config_file,
            output_dir="reports",
            verbose=self.verbose
        )
        
        # Run analysis
        analysis_result = self.performance_analyzer.analyze()
        
        if "error" in analysis_result:
            logger.warning(f"Performance analysis error: {analysis_result['error']}")
        else:
            logger.info(f"Performance analysis completed. Analyzed {analysis_result['trades_count']} trades.")
            logger.info(f"Performance report saved to {analysis_result['report_file']}")
    
    async def initialize_bot(self) -> bool:
        """
        Initialize the trading bot.
        
        Returns:
            True if initialized successfully, False otherwise
        """
        logger.info("Initializing Pocket Option trading bot...")
        
        # Check if we need to handle login first
        if self.pocket_option_config.get("use_login_ui", False):
            # Import login manager
            from utils.login_manager import LoginManager, interactive_login
            
            # Create login manager
            login_manager = LoginManager(
                config_file=self.pocket_option_config_file,
                credentials_file=os.path.join(os.path.dirname(self.pocket_option_config_file), "credentials.enc"),
                session_file=os.path.join(os.path.dirname(self.pocket_option_config_file), "session.json"),
                verbose=self.verbose
            )
            
            # Check if we have a valid session
            if not login_manager.has_valid_session() and not login_manager.has_saved_credentials():
                logger.info("No valid session or saved credentials found. Starting interactive login...")
                success = await interactive_login(login_manager)
                
                if not success:
                    logger.error("Interactive login failed")
                    return False
                    
                # Get SSID from login manager
                client = login_manager.get_client()
                if client:
                    # Update config with SSID
                    self.pocket_option_config["ssid"] = client._ssid
                    
                    # Save config
                    with open(self.pocket_option_config_file, 'w') as f:
                        json.dump(self.pocket_option_config, f, indent=2)
                    
                    # Close client
                    await login_manager.logout()
        
        # Create bot instance
        self.bot = PocketOptionBot(
            config_file=self.bot_config_file,
            telegram_config_file=self.telegram_config_file,
            pocket_option_config_file=self.pocket_option_config_file,
            db_file=self.db_file,
            verbose=self.verbose
        )
        
        # Initialize database
        if not self.bot.initialize_database():
            logger.error("Failed to initialize database")
            return False
        
        # Initialize Telegram client
        if not await self.bot.initialize_telegram():
            logger.error("Failed to initialize Telegram client")
            return False
        
        # Access channel
        channel = await self.bot.access_channel()
        if not channel:
            logger.error("Failed to access channel")
            logger.error("Please ensure your Telegram account is already a member of the channel.")
            return False
        
        # Initialize Pocket Option client
        if not await self.bot.initialize_pocket_option():
            logger.error("Failed to initialize Pocket Option client")
            return False
        
        # Set up message handler
        await self.bot.setup_message_handler()
        
        # If risk management is enabled, update the initial balance
        if self.use_risk_management and self.risk_manager:
            balance = await self.bot.pocket_option_client.get_balance()
            self.risk_manager.update_balance(balance)
            logger.info(f"Updated risk manager with current balance: {balance}")
        
        logger.info("Bot initialized successfully")
        return True
    
    async def run(self) -> None:
        """Run the trading bot with enhanced features."""
        try:
            # Optimize for regional latency
            await self.optimize_region()
            
            # Initialize risk manager
            self.initialize_risk_manager()
            
            # Initialize bot
            if not await self.initialize_bot():
                logger.error("Failed to initialize bot")
                return
            
            # Analyze performance data
            self.analyze_performance_data()
            
            # Print initial stats
            await self.bot.print_stats()
            
            # Keep the bot running
            logger.info("Bot is running. Press Ctrl+C to stop.")
            
            # Print stats periodically
            stats_interval = self.bot_config.get("stats_interval", 3600)  # Default: 1 hour
            while True:
                await asyncio.sleep(stats_interval)
                await self.bot.print_stats()
                
                # Optimize risk strategy if enabled
                if self.use_risk_management and self.risk_manager:
                    optimization = self.risk_manager.optimize_strategy()
                    if optimization["optimized"]:
                        logger.info(f"Risk strategy optimized: {optimization['previous_strategy']} -> {optimization['new_strategy']}")
                
        except KeyboardInterrupt:
            logger.info("Bot interrupted by user")
        except Exception as e:
            logger.error(f"Error running bot: {str(e)}")
        finally:
            # Close connections
            if self.bot:
                if self.bot.telegram_client:
                    await self.bot.telegram_client.disconnect()
                    
                if self.bot.pocket_option_client:
                    await self.bot.pocket_option_client.close()
                    
                if self.bot.db_conn:
                    self.bot.db_conn.close()
            
            # Close risk manager
            if self.risk_manager:
                self.risk_manager.close()
                
            logger.info("Bot stopped")

async def main():
    parser = argparse.ArgumentParser(description='Run Pocket Option Trading Bot with enhanced features')
    parser.add_argument('--bot-config', type=str, default='config/bot_config.json', help='Path to bot configuration file')
    parser.add_argument('--telegram-config', type=str, default='config/telegram_config.json', help='Path to Telegram configuration file')
    parser.add_argument('--pocket-option-config', type=str, default='config/pocket_option_config.json', help='Path to Pocket Option configuration file')
    parser.add_argument('--db', type=str, default='data/trades.db', help='Path to SQLite database file')
    parser.add_argument('--no-optimize-region', action='store_true', help='Disable regional optimization')
    parser.add_argument('--no-risk-management', action='store_true', help='Disable advanced risk management')
    parser.add_argument('--no-performance-analysis', action='store_true', help='Disable performance analysis')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose output')
    
    args = parser.parse_args()
    
    # Create controller
    controller = BotController(
        bot_config_file=args.bot_config,
        telegram_config_file=args.telegram_config,
        pocket_option_config_file=args.pocket_option_config,
        db_file=args.db,
        optimize_region=not args.no_optimize_region,
        use_risk_management=not args.no_risk_management,
        analyze_performance=not args.no_performance_analysis,
        verbose=args.verbose
    )
    
    # Run bot
    await controller.run()

if __name__ == "__main__":
    print("Pocket Option Trading Bot Controller")
    print("-----------------------------------")
    print("This script runs the Pocket Option trading bot with enhanced features:")
    print("- Regional optimization for reduced latency")
    print("- Advanced risk management strategies")
    print("- Performance analysis and visualization")
    print("")
    
    try:
        # Set up signal handlers for graceful shutdown
        loop = asyncio.get_event_loop()
        
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, lambda: asyncio.create_task(
                logger.info("Received shutdown signal, closing connections...")
            ))
        
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError running bot: {str(e)}")
        sys.exit(1)
