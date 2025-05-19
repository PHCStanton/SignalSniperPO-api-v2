#!/usr/bin/env python3
"""
risk_manager.py - Advanced risk management for the Pocket Option trading bot.

This script provides advanced risk management strategies for the Pocket Option trading bot,
including Martingale, anti-Martingale, and custom recovery strategies. It also includes
tools for analyzing trading patterns, calculating optimal position sizes, and managing
risk across multiple trades.
"""

import os
import sys
import json
import math
import random
import logging
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
import sqlite3

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("risk_manager.log")
    ]
)
logger = logging.getLogger(__name__)

# Risk management strategy types
STRATEGY_FIXED = "fixed"
STRATEGY_MARTINGALE = "martingale"
STRATEGY_ANTI_MARTINGALE = "anti_martingale"
STRATEGY_FIBONACCI = "fibonacci"
STRATEGY_KELLY = "kelly"
STRATEGY_CUSTOM = "custom"

# Default risk parameters
DEFAULT_RISK_PERCENTAGE = 2.0  # 2% of account balance per trade
DEFAULT_MAX_RISK_PERCENTAGE = 10.0  # 10% of account balance at risk at any time
DEFAULT_MAX_CONSECUTIVE_LOSSES = 3
DEFAULT_MARTINGALE_FACTOR = 2.0
DEFAULT_ANTI_MARTINGALE_FACTOR = 1.5
DEFAULT_FIBONACCI_SEQUENCE = [1, 1, 2, 3, 5, 8, 13, 21]
DEFAULT_WIN_RATE = 0.55  # 55% win rate for Kelly criterion

class RiskManager:
    def __init__(
        self,
        config_file: str = "../config/bot_config.json",
        db_file: str = "../data/trades.db",
        strategy: str = STRATEGY_FIXED,
        initial_balance: float = 100.0,
        trade_amount: float = 1.0,
        risk_percentage: float = DEFAULT_RISK_PERCENTAGE,
        max_risk_percentage: float = DEFAULT_MAX_RISK_PERCENTAGE,
        max_consecutive_losses: int = DEFAULT_MAX_CONSECUTIVE_LOSSES,
        martingale_factor: float = DEFAULT_MARTINGALE_FACTOR,
        anti_martingale_factor: float = DEFAULT_ANTI_MARTINGALE_FACTOR,
        fibonacci_sequence: List[int] = None,
        win_rate: float = DEFAULT_WIN_RATE,
        verbose: bool = False
    ):
        """
        Initialize the risk manager.
        
        Args:
            config_file: Path to bot configuration file
            db_file: Path to SQLite database file
            strategy: Risk management strategy
            initial_balance: Initial account balance
            trade_amount: Base trade amount
            risk_percentage: Percentage of account balance to risk per trade
            max_risk_percentage: Maximum percentage of account balance at risk at any time
            max_consecutive_losses: Maximum number of consecutive losses before reducing risk
            martingale_factor: Factor to multiply trade amount after a loss (Martingale)
            anti_martingale_factor: Factor to multiply trade amount after a win (Anti-Martingale)
            fibonacci_sequence: Fibonacci sequence for Fibonacci strategy
            win_rate: Expected win rate for Kelly criterion
            verbose: Enable verbose output
        """
        self.config_file = config_file
        self.db_file = db_file
        self.strategy = strategy
        self.initial_balance = initial_balance
        self.trade_amount = trade_amount
        self.risk_percentage = risk_percentage
        self.max_risk_percentage = max_risk_percentage
        self.max_consecutive_losses = max_consecutive_losses
        self.martingale_factor = martingale_factor
        self.anti_martingale_factor = anti_martingale_factor
        self.fibonacci_sequence = fibonacci_sequence or DEFAULT_FIBONACCI_SEQUENCE
        self.win_rate = win_rate
        self.verbose = verbose
        
        # Set logging level
        if verbose:
            logger.setLevel(logging.DEBUG)
        
        # Trade tracking
        self.current_balance = initial_balance
        self.current_trade_amount = trade_amount
        self.consecutive_wins = 0
        self.consecutive_losses = 0
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_profit = 0.0
        self.fibonacci_index = 0
        self.trade_history = []
        
        # Load configuration
        self.config = self._load_config()
        
        # Initialize database connection
        self.db_conn = None
        self._init_database()
    
    def _load_config(self) -> Dict:
        """Load configuration from file or create default."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.error(f"Error parsing config file: {self.config_file}")
                
        # Default configuration
        return {
            "trade_amount": self.trade_amount,
            "max_daily_trades": 20,
            "max_daily_loss": 50,
            "min_seconds_before_timer": 5,
            "test_mode": True,
            "test_mode_win_rate": 0.6,
            "stats_interval": 3600,
            "timezone": "Africa/Johannesburg",
            "log_level": "INFO",
            
            "risk_management": {
                "enabled": True,
                "strategy": self.strategy,
                "risk_percentage": self.risk_percentage,
                "max_risk_percentage": self.max_risk_percentage,
                "max_consecutive_losses": self.max_consecutive_losses,
                "martingale_factor": self.martingale_factor,
                "anti_martingale_factor": self.anti_martingale_factor,
                "fibonacci_sequence": self.fibonacci_sequence,
                "win_rate": self.win_rate,
                "max_trades_per_asset": 5,
                "max_trades_per_hour": 10,
                "recovery_mode": {
                    "enabled": False,
                    "increase_amount_after_loss": False,
                    "increase_factor": 2.0,
                    "max_recovery_attempts": 3
                }
            }
        }
    
    def _save_config(self) -> None:
        """Save configuration to file."""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            logger.info(f"Configuration saved to {self.config_file}")
        except Exception as e:
            logger.error(f"Error saving configuration: {str(e)}")
    
    def _init_database(self) -> None:
        """Initialize the database connection."""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.db_file), exist_ok=True)
            
            # Connect to database
            self.db_conn = sqlite3.connect(self.db_file)
            cursor = self.db_conn.cursor()
            
            # Create tables if they don't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS risk_management (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    strategy TEXT NOT NULL,
                    trade_id INTEGER,
                    original_amount REAL NOT NULL,
                    adjusted_amount REAL NOT NULL,
                    consecutive_wins INTEGER NOT NULL,
                    consecutive_losses INTEGER NOT NULL,
                    current_balance REAL NOT NULL,
                    risk_percentage REAL NOT NULL,
                    notes TEXT
                )
            ''')
            
            self.db_conn.commit()
            logger.debug("Database initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing database: {str(e)}")
    
    def _log_risk_adjustment(self, trade_id: Optional[int], original_amount: float, adjusted_amount: float, notes: str) -> None:
        """
        Log a risk adjustment to the database.
        
        Args:
            trade_id: Trade ID (optional)
            original_amount: Original trade amount
            adjusted_amount: Adjusted trade amount
            notes: Notes about the adjustment
        """
        if not self.db_conn:
            logger.error("Database not initialized")
            return
            
        try:
            cursor = self.db_conn.cursor()
            
            cursor.execute('''
                INSERT INTO risk_management (
                    timestamp, strategy, trade_id, original_amount, adjusted_amount,
                    consecutive_wins, consecutive_losses, current_balance, risk_percentage, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                self.strategy,
                trade_id,
                original_amount,
                adjusted_amount,
                self.consecutive_wins,
                self.consecutive_losses,
                self.current_balance,
                self.risk_percentage,
                notes
            ))
            
            self.db_conn.commit()
            logger.debug(f"Risk adjustment logged: {original_amount} -> {adjusted_amount} ({notes})")
        except Exception as e:
            logger.error(f"Error logging risk adjustment: {str(e)}")
    
    def update_balance(self, new_balance: float) -> None:
        """
        Update the current account balance.
        
        Args:
            new_balance: New account balance
        """
        old_balance = self.current_balance
        self.current_balance = new_balance
        logger.info(f"Balance updated: {old_balance} -> {new_balance}")
    
    def record_trade_result(self, trade_id: Optional[int], result: str, profit: float) -> None:
        """
        Record the result of a trade.
        
        Args:
            trade_id: Trade ID (optional)
            result: Trade result ('win' or 'lose')
            profit: Profit/loss amount
        """
        self.total_trades += 1
        self.total_profit += profit
        
        # Update current balance
        self.current_balance += profit
        
        # Update trade history
        self.trade_history.append({
            "trade_id": trade_id,
            "timestamp": datetime.now().isoformat(),
            "amount": self.current_trade_amount,
            "result": result,
            "profit": profit
        })
        
        # Update consecutive wins/losses
        if result == 'win':
            self.winning_trades += 1
            self.consecutive_wins += 1
            self.consecutive_losses = 0
            logger.info(f"Trade {trade_id} won: +{profit} (Consecutive wins: {self.consecutive_wins})")
        else:
            self.losing_trades += 1
            self.consecutive_losses += 1
            self.consecutive_wins = 0
            logger.info(f"Trade {trade_id} lost: {profit} (Consecutive losses: {self.consecutive_losses})")
    
    def calculate_trade_amount(self, asset: str = None) -> float:
        """
        Calculate the trade amount based on the selected risk management strategy.
        
        Args:
            asset: Asset to trade (optional)
            
        Returns:
            Calculated trade amount
        """
        original_amount = self.trade_amount
        
        # Check if risk management is enabled
        if not self.config["risk_management"]["enabled"]:
            return original_amount
        
        # Get strategy from config (may have been updated)
        strategy = self.config["risk_management"]["strategy"]
        
        # Calculate trade amount based on strategy
        if strategy == STRATEGY_FIXED:
            # Fixed amount strategy - always use the same amount
            adjusted_amount = original_amount
            notes = "Fixed amount strategy"
            
        elif strategy == STRATEGY_MARTINGALE:
            # Martingale strategy - increase amount after a loss
            if self.consecutive_losses > 0:
                factor = self.config["risk_management"]["martingale_factor"] ** self.consecutive_losses
                adjusted_amount = original_amount * factor
                notes = f"Martingale strategy (factor: {factor})"
            else:
                adjusted_amount = original_amount
                notes = "Martingale strategy (base amount)"
                
        elif strategy == STRATEGY_ANTI_MARTINGALE:
            # Anti-Martingale strategy - increase amount after a win
            if self.consecutive_wins > 0:
                factor = self.config["risk_management"]["anti_martingale_factor"] ** self.consecutive_wins
                adjusted_amount = original_amount * factor
                notes = f"Anti-Martingale strategy (factor: {factor})"
            else:
                adjusted_amount = original_amount
                notes = "Anti-Martingale strategy (base amount)"
                
        elif strategy == STRATEGY_FIBONACCI:
            # Fibonacci strategy - use Fibonacci sequence for consecutive losses
            if self.consecutive_losses > 0:
                # Get Fibonacci sequence from config
                fibonacci_sequence = self.config["risk_management"]["fibonacci_sequence"]
                
                # Use the appropriate Fibonacci number based on consecutive losses
                index = min(self.consecutive_losses - 1, len(fibonacci_sequence) - 1)
                factor = fibonacci_sequence[index]
                adjusted_amount = original_amount * factor
                notes = f"Fibonacci strategy (factor: {factor}, index: {index})"
            else:
                adjusted_amount = original_amount
                notes = "Fibonacci strategy (base amount)"
                
        elif strategy == STRATEGY_KELLY:
            # Kelly criterion - optimal bet size based on win rate and odds
            win_rate = self.config["risk_management"]["win_rate"]
            
            # Calculate win/loss ratio from trade history
            if self.total_trades > 0:
                actual_win_rate = self.winning_trades / self.total_trades
            else:
                actual_win_rate = win_rate
            
            # Use actual win rate if we have enough trades, otherwise use expected win rate
            if self.total_trades >= 20:
                win_rate = actual_win_rate
            
            # Calculate Kelly fraction (f* = p - q/b where p = win probability, q = loss probability, b = odds)
            # For binary options, odds are typically 0.8 (80% payout)
            odds = 0.8
            loss_rate = 1 - win_rate
            kelly_fraction = win_rate - (loss_rate / odds)
            
            # Limit Kelly fraction to avoid excessive risk
            kelly_fraction = max(0, min(kelly_fraction, 0.25))
            
            # Calculate trade amount as a percentage of balance
            adjusted_amount = self.current_balance * kelly_fraction * (self.risk_percentage / 100)
            notes = f"Kelly criterion (win rate: {win_rate:.2f}, fraction: {kelly_fraction:.2f})"
            
        elif strategy == STRATEGY_CUSTOM:
            # Custom strategy - implement your own logic here
            # This is a simple example that combines elements of Martingale and Anti-Martingale
            if self.consecutive_losses > 0:
                # Increase amount after a loss, but with a smaller factor than Martingale
                factor = 1.5 ** min(self.consecutive_losses, 3)
                adjusted_amount = original_amount * factor
                notes = f"Custom strategy - loss recovery (factor: {factor})"
            elif self.consecutive_wins > 0:
                # Increase amount after a win, but with a smaller factor than Anti-Martingale
                factor = 1.2 ** min(self.consecutive_wins, 5)
                adjusted_amount = original_amount * factor
                notes = f"Custom strategy - win progression (factor: {factor})"
            else:
                adjusted_amount = original_amount
                notes = "Custom strategy (base amount)"
        else:
            # Unknown strategy - use fixed amount
            adjusted_amount = original_amount
            notes = f"Unknown strategy '{strategy}', using fixed amount"
        
        # Apply risk limits
        adjusted_amount = self._apply_risk_limits(adjusted_amount, notes)
        
        # Log the adjustment
        self._log_risk_adjustment(None, original_amount, adjusted_amount, notes)
        
        # Update current trade amount
        self.current_trade_amount = adjusted_amount
        
        return adjusted_amount
    
    def _apply_risk_limits(self, amount: float, notes: str) -> float:
        """
        Apply risk limits to the calculated trade amount.
        
        Args:
            amount: Calculated trade amount
            notes: Notes about the calculation
            
        Returns:
            Trade amount after applying risk limits
        """
        # Ensure amount is positive
        amount = max(0.1, amount)
        
        # Limit amount to a percentage of balance
        max_amount = self.current_balance * (self.max_risk_percentage / 100)
        if amount > max_amount:
            amount = max_amount
            logger.warning(f"Trade amount limited to {max_amount} ({self.max_risk_percentage}% of balance)")
        
        # Reduce risk after consecutive losses
        if self.consecutive_losses >= self.max_consecutive_losses:
            reduction_factor = 0.5
            amount *= reduction_factor
            logger.warning(f"Trade amount reduced by {reduction_factor} after {self.consecutive_losses} consecutive losses")
        
        # Round to 2 decimal places
        amount = round(amount, 2)
        
        return amount
    
    def analyze_trade_history(self) -> Dict:
        """
        Analyze trade history to identify patterns and optimize strategy.
        
        Returns:
            Dictionary with analysis results
        """
        if not self.trade_history:
            return {
                "total_trades": 0,
                "win_rate": 0,
                "average_profit": 0,
                "profit_factor": 0,
                "max_consecutive_wins": 0,
                "max_consecutive_losses": 0,
                "recommended_strategy": STRATEGY_FIXED
            }
        
        # Calculate basic statistics
        total_trades = len(self.trade_history)
        winning_trades = sum(1 for trade in self.trade_history if trade["result"] == "win")
        losing_trades = total_trades - winning_trades
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        total_profit = sum(trade["profit"] for trade in self.trade_history)
        average_profit = total_profit / total_trades if total_trades > 0 else 0
        
        gross_profit = sum(trade["profit"] for trade in self.trade_history if trade["profit"] > 0)
        gross_loss = abs(sum(trade["profit"] for trade in self.trade_history if trade["profit"] < 0))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # Calculate max consecutive wins/losses
        max_consecutive_wins = 0
        max_consecutive_losses = 0
        current_consecutive_wins = 0
        current_consecutive_losses = 0
        
        for trade in self.trade_history:
            if trade["result"] == "win":
                current_consecutive_wins += 1
                current_consecutive_losses = 0
                max_consecutive_wins = max(max_consecutive_wins, current_consecutive_wins)
            else:
                current_consecutive_losses += 1
                current_consecutive_wins = 0
                max_consecutive_losses = max(max_consecutive_losses, current_consecutive_losses)
        
        # Determine recommended strategy based on analysis
        recommended_strategy = STRATEGY_FIXED
        
        if total_trades >= 20:  # Only recommend if we have enough data
            if win_rate >= 0.6:
                # High win rate - use Anti-Martingale to capitalize on winning streaks
                recommended_strategy = STRATEGY_ANTI_MARTINGALE
            elif win_rate >= 0.5:
                # Moderate win rate - use Kelly criterion for optimal bet sizing
                recommended_strategy = STRATEGY_KELLY
            elif max_consecutive_losses <= 3:
                # Low win rate but limited losing streaks - use Fibonacci for controlled recovery
                recommended_strategy = STRATEGY_FIBONACCI
            else:
                # Low win rate with longer losing streaks - use custom strategy with conservative approach
                recommended_strategy = STRATEGY_CUSTOM
        
        return {
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "win_rate": win_rate,
            "total_profit": total_profit,
            "average_profit": average_profit,
            "gross_profit": gross_profit,
            "gross_loss": gross_loss,
            "profit_factor": profit_factor,
            "max_consecutive_wins": max_consecutive_wins,
            "max_consecutive_losses": max_consecutive_losses,
            "recommended_strategy": recommended_strategy
        }
    
    def optimize_strategy(self) -> Dict:
        """
        Optimize the risk management strategy based on trade history.
        
        Returns:
            Dictionary with optimization results
        """
        # Analyze trade history
        analysis = self.analyze_trade_history()
        
        if analysis["total_trades"] < 20:
            logger.info("Not enough trade history for optimization (minimum 20 trades required)")
            return {
                "optimized": False,
                "reason": "Not enough trade history",
                "current_strategy": self.strategy,
                "recommended_strategy": self.strategy
            }
        
        # Get recommended strategy from analysis
        recommended_strategy = analysis["recommended_strategy"]
        
        # Update strategy if different from current
        if recommended_strategy != self.strategy:
            old_strategy = self.strategy
            self.strategy = recommended_strategy
            
            # Update configuration
            self.config["risk_management"]["strategy"] = recommended_strategy
            self._save_config()
            
            logger.info(f"Strategy optimized: {old_strategy} -> {recommended_strategy}")
            
            return {
                "optimized": True,
                "reason": f"Better performance expected with {recommended_strategy} strategy",
                "previous_strategy": old_strategy,
                "new_strategy": recommended_strategy,
                "analysis": analysis
            }
        else:
            logger.info(f"Current strategy ({self.strategy}) is already optimal")
            
            return {
                "optimized": False,
                "reason": "Current strategy is already optimal",
                "current_strategy": self.strategy,
                "analysis": analysis
            }
    
    def print_statistics(self) -> None:
        """Print risk management statistics."""
        analysis = self.analyze_trade_history()
        
        print("\n" + "="*80)
        print("RISK MANAGEMENT STATISTICS")
        print("="*80)
        
        print(f"Strategy: {self.strategy}")
        print(f"Initial Balance: {self.initial_balance}")
        print(f"Current Balance: {self.current_balance}")
        print(f"Total Profit: {self.total_profit}")
        print(f"Total Trades: {analysis['total_trades']}")
        print(f"Win Rate: {analysis['win_rate']*100:.2f}%")
        print(f"Profit Factor: {analysis['profit_factor']:.2f}")
        print(f"Max Consecutive Wins: {analysis['max_consecutive_wins']}")
        print(f"Max Consecutive Losses: {analysis['max_consecutive_losses']}")
        
        if analysis['total_trades'] >= 20:
            print(f"\nRecommended Strategy: {analysis['recommended_strategy']}")
        
        print("="*80)
    
    def close(self) -> None:
        """Close the risk manager."""
        if self.db_conn:
            self.db_conn.close()
            logger.debug("Database connection closed")

def main():
    parser = argparse.ArgumentParser(description='Advanced risk management for Pocket Option trading bot')
    parser.add_argument('-c', '--config', type=str, default='../config/bot_config.json', help='Path to bot configuration file')
    parser.add_argument('-d', '--db', type=str, default='../data/trades.db', help='Path to SQLite database file')
    parser.add_argument('-s', '--strategy', type=str, choices=[STRATEGY_FIXED, STRATEGY_MARTINGALE, STRATEGY_ANTI_MARTINGALE, STRATEGY_FIBONACCI, STRATEGY_KELLY, STRATEGY_CUSTOM], default=STRATEGY_FIXED, help='Risk management strategy')
    parser.add_argument('-b', '--balance', type=float, default=100.0, help='Initial account balance')
    parser.add_argument('-a', '--amount', type=float, default=1.0, help='Base trade amount')
    parser.add_argument('-r', '--risk', type=float, default=DEFAULT_RISK_PERCENTAGE, help='Risk percentage per trade')
    parser.add_argument('-m', '--max-risk', type=float, default=DEFAULT_MAX_RISK_PERCENTAGE, help='Maximum risk percentage')
    parser.add_argument('-l', '--max-losses', type=int, default=DEFAULT_MAX_CONSECUTIVE_LOSSES, help='Maximum consecutive losses')
    parser.add_argument('--simulate', action='store_true', help='Run a simulation')
    parser.add_argument('--trades', type=int, default=100, help='Number of trades to simulate')
    parser.add_argument('--win-rate', type=float, default=0.55, help='Win rate for simulation')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
    
    args = parser.parse_args()
    
    # Create risk manager
    risk_manager = RiskManager(
        config_file=args.config,
        db_file=args.db,
        strategy=args.strategy,
        initial_balance=args.balance,
        trade_amount=args.amount,
        risk_percentage=args.risk,
        max_risk_percentage=args.max_risk,
        max_consecutive_losses=args.max_losses,
        win_rate=args.win_rate,
        verbose=args.verbose
    )
    
    try:
        # Run simulation if requested
        if args.simulate:
            print(f"Simulating {args.trades} trades with {args.strategy} strategy...")
            print(f"Initial balance: {args.balance}")
            print(f"Base trade amount: {args.amount}")
            print(f"Win rate: {args.win_rate}")
            print("")
            
            for i in range(args.trades):
                # Calculate trade amount
                trade_amount = risk_manager.calculate_trade_amount()
                
                # Simulate trade result
                is_win = random.random() < args.win_rate
                result = "win" if is_win else "lose"
                profit = trade_amount * 0.8 if is_win else -trade_amount
                
                # Record trade result
                risk_manager.record_trade_result(i+1, result, profit)
                
                # Print progress
                if (i+1) % 10 == 0 or i == 0:
                    print(f"Trade {i+1}/{args.trades}: {result.upper()} (Amount: {trade_amount:.2f}, Profit: {profit:.2f}, Balance: {risk_manager.current_balance:.2f})")
            
            # Print statistics
            risk_manager.print_statistics()
            
            # Optimize strategy
            optimization = risk_manager.optimize_strategy()
            if optimization["optimized"]:
                print(f"\nStrategy optimized: {optimization['previous_strategy']} -> {optimization['new_strategy']}")
                print(f"Reason: {optimization['reason']}")
        else:
            print("Risk manager initialized. Use in your trading bot or run with --simulate to test strategies.")
    finally:
        # Close risk manager
        risk_manager.close()

if __name__ == "__main__":
    print("Pocket Option Trading Bot - Risk Manager")
    print("---------------------------------------")
    print("")
    
    try:
        main()
    except KeyboardInterrupt:
        print("\nRisk manager interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError in risk manager: {str(e)}")
        sys.exit(1)
