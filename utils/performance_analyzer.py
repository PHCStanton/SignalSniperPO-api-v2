#!/usr/bin/env python3
"""
performance_analyzer.py - Analyzes trading performance for the Pocket Option trading bot.

This script analyzes trading performance data from the Pocket Option trading bot,
generates performance metrics, visualizes trading results, and provides insights
for improving trading strategies. It can be used to evaluate the effectiveness of
different trading strategies and risk management approaches.
"""

import os
import sys
import json
import math
import sqlite3
import logging
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from tabulate import tabulate

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("performance_analyzer.log")
    ]
)
logger = logging.getLogger(__name__)

class PerformanceAnalyzer:
    def __init__(
        self,
        db_file: str = "../data/trades.db",
        config_file: str = "../config/bot_config.json",
        output_dir: str = "../reports",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        verbose: bool = False
    ):
        """
        Initialize the performance analyzer.
        
        Args:
            db_file: Path to SQLite database file
            config_file: Path to bot configuration file
            output_dir: Directory to save reports and visualizations
            start_date: Start date for analysis (ISO format, e.g., '2023-01-01')
            end_date: End date for analysis (ISO format, e.g., '2023-12-31')
            verbose: Enable verbose output
        """
        self.db_file = db_file
        self.config_file = config_file
        self.output_dir = output_dir
        self.start_date = start_date
        self.end_date = end_date
        self.verbose = verbose
        
        # Set logging level
        if verbose:
            logger.setLevel(logging.DEBUG)
        
        # Initialize database connection
        self.db_conn = None
        
        # Load configuration
        self.config = self._load_config()
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
    
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
            "trade_amount": 1,
            "max_daily_trades": 20,
            "max_daily_loss": 50,
            "min_seconds_before_timer": 5,
            "test_mode": True,
            "test_mode_win_rate": 0.6,
            "stats_interval": 3600,
            "timezone": "Africa/Johannesburg",
            "log_level": "INFO"
        }
    
    def _connect_to_database(self) -> bool:
        """
        Connect to the SQLite database.
        
        Returns:
            True if connected successfully, False otherwise
        """
        try:
            self.db_conn = sqlite3.connect(self.db_file)
            self.db_conn.row_factory = sqlite3.Row  # Enable row factory for named columns
            logger.debug("Connected to database successfully")
            return True
        except Exception as e:
            logger.error(f"Error connecting to database: {str(e)}")
            return False
    
    def _close_database(self) -> None:
        """Close the database connection."""
        if self.db_conn:
            self.db_conn.close()
            logger.debug("Database connection closed")
    
    def _get_trades(self) -> List[Dict]:
        """
        Get trades from the database.
        
        Returns:
            List of trades as dictionaries
        """
        if not self.db_conn and not self._connect_to_database():
            return []
            
        try:
            cursor = self.db_conn.cursor()
            
            # Build query
            query = """
                SELECT 
                    t.id, t.signal_id, t.timestamp, t.asset, t.direction, 
                    t.expiry, t.amount, t.trade_id, t.status, t.result, 
                    t.profit, t.error_message,
                    s.timer, s.is_valid, s.validation_message
                FROM 
                    trades t
                LEFT JOIN 
                    signals s ON t.signal_id = s.id
                WHERE 
                    1=1
            """
            
            params = []
            
            # Add date filters if provided
            if self.start_date:
                query += " AND t.timestamp >= ?"
                params.append(self.start_date)
                
            if self.end_date:
                query += " AND t.timestamp <= ?"
                params.append(self.end_date)
                
            # Order by timestamp
            query += " ORDER BY t.timestamp"
            
            # Execute query
            cursor.execute(query, params)
            
            # Convert rows to dictionaries
            trades = []
            for row in cursor.fetchall():
                trade = {key: row[key] for key in row.keys()}
                trades.append(trade)
                
            logger.info(f"Retrieved {len(trades)} trades from database")
            return trades
            
        except Exception as e:
            logger.error(f"Error retrieving trades: {str(e)}")
            return []
    
    def _get_risk_adjustments(self) -> List[Dict]:
        """
        Get risk adjustments from the database.
        
        Returns:
            List of risk adjustments as dictionaries
        """
        if not self.db_conn and not self._connect_to_database():
            return []
            
        try:
            cursor = self.db_conn.cursor()
            
            # Build query
            query = """
                SELECT 
                    id, timestamp, strategy, trade_id, original_amount, 
                    adjusted_amount, consecutive_wins, consecutive_losses, 
                    current_balance, risk_percentage, notes
                FROM 
                    risk_management
                WHERE 
                    1=1
            """
            
            params = []
            
            # Add date filters if provided
            if self.start_date:
                query += " AND timestamp >= ?"
                params.append(self.start_date)
                
            if self.end_date:
                query += " AND timestamp <= ?"
                params.append(self.end_date)
                
            # Order by timestamp
            query += " ORDER BY timestamp"
            
            # Execute query
            cursor.execute(query, params)
            
            # Convert rows to dictionaries
            adjustments = []
            for row in cursor.fetchall():
                adjustment = {key: row[key] for key in row.keys()}
                adjustments.append(adjustment)
                
            logger.info(f"Retrieved {len(adjustments)} risk adjustments from database")
            return adjustments
            
        except Exception as e:
            logger.error(f"Error retrieving risk adjustments: {str(e)}")
            return []
    
    def calculate_performance_metrics(self, trades: List[Dict]) -> Dict:
        """
        Calculate performance metrics from trades.
        
        Args:
            trades: List of trades
            
        Returns:
            Dictionary with performance metrics
        """
        if not trades:
            return {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0,
                "total_profit": 0,
                "average_profit": 0,
                "profit_factor": 0,
                "max_drawdown": 0,
                "max_drawdown_percentage": 0,
                "sharpe_ratio": 0,
                "expectancy": 0,
                "average_win": 0,
                "average_loss": 0,
                "largest_win": 0,
                "largest_loss": 0,
                "consecutive_wins": 0,
                "consecutive_losses": 0,
                "profit_by_asset": {},
                "profit_by_direction": {},
                "profit_by_expiry": {},
                "profit_by_day": {},
                "profit_by_hour": {}
            }
        
        # Basic metrics
        total_trades = len(trades)
        winning_trades = sum(1 for trade in trades if trade["result"] == "win")
        losing_trades = sum(1 for trade in trades if trade["result"] == "lose")
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        # Profit metrics
        total_profit = sum(trade["profit"] for trade in trades if trade["profit"] is not None)
        average_profit = total_profit / total_trades if total_trades > 0 else 0
        
        # Calculate gross profit and loss
        gross_profit = sum(trade["profit"] for trade in trades if trade["profit"] is not None and trade["profit"] > 0)
        gross_loss = abs(sum(trade["profit"] for trade in trades if trade["profit"] is not None and trade["profit"] < 0))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # Calculate average win and loss
        winning_amounts = [trade["profit"] for trade in trades if trade["profit"] is not None and trade["profit"] > 0]
        losing_amounts = [abs(trade["profit"]) for trade in trades if trade["profit"] is not None and trade["profit"] < 0]
        
        average_win = sum(winning_amounts) / len(winning_amounts) if winning_amounts else 0
        average_loss = sum(losing_amounts) / len(losing_amounts) if losing_amounts else 0
        
        # Calculate largest win and loss
        largest_win = max(winning_amounts) if winning_amounts else 0
        largest_loss = max(losing_amounts) if losing_amounts else 0
        
        # Calculate expectancy
        expectancy = (win_rate * average_win) - ((1 - win_rate) * average_loss)
        
        # Calculate drawdown
        balance = 0
        peak_balance = 0
        drawdowns = []
        current_drawdown = 0
        
        for trade in trades:
            if trade["profit"] is not None:
                balance += trade["profit"]
                
                if balance > peak_balance:
                    peak_balance = balance
                    current_drawdown = 0
                else:
                    current_drawdown = peak_balance - balance
                    drawdowns.append((current_drawdown, current_drawdown / peak_balance if peak_balance > 0 else 0))
        
        max_drawdown = max([dd[0] for dd in drawdowns]) if drawdowns else 0
        max_drawdown_percentage = max([dd[1] for dd in drawdowns]) if drawdowns else 0
        
        # Calculate Sharpe ratio (simplified)
        returns = []
        for i in range(1, len(trades)):
            if trades[i]["profit"] is not None and trades[i-1]["profit"] is not None:
                returns.append(trades[i]["profit"] / trades[i-1]["amount"] if trades[i-1]["amount"] > 0 else 0)
        
        avg_return = np.mean(returns) if returns else 0
        std_return = np.std(returns) if returns else 0
        sharpe_ratio = avg_return / std_return if std_return > 0 else 0
        
        # Calculate consecutive wins and losses
        max_consecutive_wins = 0
        max_consecutive_losses = 0
        current_consecutive_wins = 0
        current_consecutive_losses = 0
        
        for trade in trades:
            if trade["result"] == "win":
                current_consecutive_wins += 1
                current_consecutive_losses = 0
                max_consecutive_wins = max(max_consecutive_wins, current_consecutive_wins)
            elif trade["result"] == "lose":
                current_consecutive_losses += 1
                current_consecutive_wins = 0
                max_consecutive_losses = max(max_consecutive_losses, current_consecutive_losses)
        
        # Calculate profit by asset
        profit_by_asset = {}
        for trade in trades:
            asset = trade["asset"]
            if asset not in profit_by_asset:
                profit_by_asset[asset] = 0
            
            if trade["profit"] is not None:
                profit_by_asset[asset] += trade["profit"]
        
        # Calculate profit by direction
        profit_by_direction = {"call": 0, "put": 0}
        for trade in trades:
            direction = trade["direction"]
            if direction not in profit_by_direction:
                profit_by_direction[direction] = 0
            
            if trade["profit"] is not None:
                profit_by_direction[direction] += trade["profit"]
        
        # Calculate profit by expiry
        profit_by_expiry = {}
        for trade in trades:
            expiry = trade["expiry"]
            if expiry not in profit_by_expiry:
                profit_by_expiry[expiry] = 0
            
            if trade["profit"] is not None:
                profit_by_expiry[expiry] += trade["profit"]
        
        # Calculate profit by day of week
        profit_by_day = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0}  # 0 = Monday, 6 = Sunday
        for trade in trades:
            try:
                timestamp = datetime.fromisoformat(trade["timestamp"])
                day = timestamp.weekday()
                
                if trade["profit"] is not None:
                    profit_by_day[day] += trade["profit"]
            except (ValueError, TypeError):
                pass
        
        # Calculate profit by hour of day
        profit_by_hour = {hour: 0 for hour in range(24)}
        for trade in trades:
            try:
                timestamp = datetime.fromisoformat(trade["timestamp"])
                hour = timestamp.hour
                
                if trade["profit"] is not None:
                    profit_by_hour[hour] += trade["profit"]
            except (ValueError, TypeError):
                pass
        
        return {
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "win_rate": win_rate,
            "total_profit": total_profit,
            "average_profit": average_profit,
            "profit_factor": profit_factor,
            "max_drawdown": max_drawdown,
            "max_drawdown_percentage": max_drawdown_percentage,
            "sharpe_ratio": sharpe_ratio,
            "expectancy": expectancy,
            "average_win": average_win,
            "average_loss": average_loss,
            "largest_win": largest_win,
            "largest_loss": largest_loss,
            "consecutive_wins": max_consecutive_wins,
            "consecutive_losses": max_consecutive_losses,
            "profit_by_asset": profit_by_asset,
            "profit_by_direction": profit_by_direction,
            "profit_by_expiry": profit_by_expiry,
            "profit_by_day": profit_by_day,
            "profit_by_hour": profit_by_hour
        }
    
    def generate_performance_report(self, metrics: Dict) -> str:
        """
        Generate a performance report from metrics.
        
        Args:
            metrics: Dictionary with performance metrics
            
        Returns:
            Performance report as a string
        """
        report = []
        
        # Add header
        report.append("=" * 80)
        report.append("POCKET OPTION TRADING BOT - PERFORMANCE REPORT")
        report.append("=" * 80)
        report.append("")
        
        # Add date range
        if self.start_date or self.end_date:
            date_range = f"Date Range: {self.start_date or 'Beginning'} to {self.end_date or 'Present'}"
            report.append(date_range)
            report.append("")
        
        # Add summary
        report.append("SUMMARY")
        report.append("-" * 80)
        report.append(f"Total Trades: {metrics['total_trades']}")
        report.append(f"Winning Trades: {metrics['winning_trades']} ({metrics['win_rate']*100:.2f}%)")
        report.append(f"Losing Trades: {metrics['losing_trades']} ({(1-metrics['win_rate'])*100:.2f}%)")
        report.append(f"Total Profit: {metrics['total_profit']:.2f}")
        report.append(f"Average Profit per Trade: {metrics['average_profit']:.2f}")
        report.append(f"Profit Factor: {metrics['profit_factor']:.2f}")
        report.append(f"Expectancy: {metrics['expectancy']:.2f}")
        report.append("")
        
        # Add risk metrics
        report.append("RISK METRICS")
        report.append("-" * 80)
        report.append(f"Maximum Drawdown: {metrics['max_drawdown']:.2f} ({metrics['max_drawdown_percentage']*100:.2f}%)")
        report.append(f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
        report.append(f"Average Win: {metrics['average_win']:.2f}")
        report.append(f"Average Loss: {metrics['average_loss']:.2f}")
        report.append(f"Largest Win: {metrics['largest_win']:.2f}")
        report.append(f"Largest Loss: {metrics['largest_loss']:.2f}")
        report.append(f"Maximum Consecutive Wins: {metrics['consecutive_wins']}")
        report.append(f"Maximum Consecutive Losses: {metrics['consecutive_losses']}")
        report.append("")
        
        # Add profit by asset
        report.append("PROFIT BY ASSET")
        report.append("-" * 80)
        asset_table = []
        for asset, profit in sorted(metrics['profit_by_asset'].items(), key=lambda x: x[1], reverse=True):
            asset_table.append([asset, f"{profit:.2f}"])
        
        report.append(tabulate(asset_table, headers=["Asset", "Profit"], tablefmt="simple"))
        report.append("")
        
        # Add profit by direction
        report.append("PROFIT BY DIRECTION")
        report.append("-" * 80)
        direction_table = []
        for direction, profit in sorted(metrics['profit_by_direction'].items(), key=lambda x: x[1], reverse=True):
            direction_display = "HIGHER (Call)" if direction == "call" else "LOWER (Put)"
            direction_table.append([direction_display, f"{profit:.2f}"])
        
        report.append(tabulate(direction_table, headers=["Direction", "Profit"], tablefmt="simple"))
        report.append("")
        
        # Add profit by expiry
        report.append("PROFIT BY EXPIRY")
        report.append("-" * 80)
        expiry_table = []
        for expiry, profit in sorted(metrics['profit_by_expiry'].items(), key=lambda x: int(x[0]) if x[0] is not None else 0):
            expiry_display = f"{int(expiry) // 60} minutes" if expiry is not None else "Unknown"
            expiry_table.append([expiry_display, f"{profit:.2f}"])
        
        report.append(tabulate(expiry_table, headers=["Expiry", "Profit"], tablefmt="simple"))
        report.append("")
        
        # Add profit by day of week
        report.append("PROFIT BY DAY OF WEEK")
        report.append("-" * 80)
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        day_table = []
        for day, profit in metrics['profit_by_day'].items():
            day_table.append([day_names[day], f"{profit:.2f}"])
        
        report.append(tabulate(day_table, headers=["Day", "Profit"], tablefmt="simple"))
        report.append("")
        
        # Add profit by hour of day
        report.append("PROFIT BY HOUR OF DAY")
        report.append("-" * 80)
        hour_table = []
        for hour, profit in metrics['profit_by_hour'].items():
            hour_display = f"{hour:02d}:00 - {hour:02d}:59"
            hour_table.append([hour_display, f"{profit:.2f}"])
        
        report.append(tabulate(hour_table, headers=["Hour", "Profit"], tablefmt="simple"))
        report.append("")
        
        # Add recommendations
        report.append("RECOMMENDATIONS")
        report.append("-" * 80)
        
        # Best performing assets
        best_assets = sorted(metrics['profit_by_asset'].items(), key=lambda x: x[1], reverse=True)[:3]
        worst_assets = sorted(metrics['profit_by_asset'].items(), key=lambda x: x[1])[:3]
        
        report.append("Best Performing Assets:")
        for asset, profit in best_assets:
            report.append(f"  - {asset}: {profit:.2f}")
        
        report.append("\nWorst Performing Assets:")
        for asset, profit in worst_assets:
            report.append(f"  - {asset}: {profit:.2f}")
        
        # Best performing times
        best_hours = sorted(metrics['profit_by_hour'].items(), key=lambda x: x[1], reverse=True)[:3]
        best_days = sorted(metrics['profit_by_day'].items(), key=lambda x: x[1], reverse=True)[:3]
        
        report.append("\nBest Trading Hours:")
        for hour, profit in best_hours:
            hour_display = f"{hour:02d}:00 - {hour:02d}:59"
            report.append(f"  - {hour_display}: {profit:.2f}")
        
        report.append("\nBest Trading Days:")
        for day, profit in best_days:
            report.append(f"  - {day_names[day]}: {profit:.2f}")
        
        # Strategy recommendations
        report.append("\nStrategy Recommendations:")
        
        if metrics['win_rate'] >= 0.6:
            report.append("  - High win rate detected. Consider using Anti-Martingale strategy to capitalize on winning streaks.")
        elif metrics['win_rate'] >= 0.5:
            report.append("  - Moderate win rate detected. Consider using Kelly criterion for optimal bet sizing.")
        elif metrics['consecutive_losses'] <= 3:
            report.append("  - Low win rate but limited losing streaks detected. Consider using Fibonacci strategy for controlled recovery.")
        else:
            report.append("  - Low win rate with longer losing streaks detected. Consider using a custom conservative strategy.")
        
        if metrics['max_drawdown_percentage'] > 0.2:
            report.append("  - High drawdown detected. Consider reducing trade size or implementing stricter risk management.")
        
        if metrics['profit_factor'] < 1.5:
            report.append("  - Low profit factor detected. Consider focusing on trades with higher probability of success.")
        
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def create_visualizations(self, trades: List[Dict], metrics: Dict) -> None:
        """
        Create visualizations from trades and metrics.
        
        Args:
            trades: List of trades
            metrics: Dictionary with performance metrics
        """
        if not trades:
            logger.warning("No trades to visualize")
            return
        
        # Convert trades to DataFrame for easier manipulation
        df = pd.DataFrame(trades)
        
        # Convert timestamp to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Set timestamp as index
        df.set_index('timestamp', inplace=True)
        
        # Sort by timestamp
        df.sort_index(inplace=True)
        
        # Create cumulative profit chart
        self._create_cumulative_profit_chart(df)
        
        # Create win/loss distribution chart
        self._create_win_loss_distribution(df)
        
        # Create profit by asset chart
        self._create_profit_by_asset_chart(metrics)
        
        # Create profit by hour chart
        self._create_profit_by_hour_chart(metrics)
        
        # Create profit by day chart
        self._create_profit_by_day_chart(metrics)
        
        # Create drawdown chart
        self._create_drawdown_chart(df)
    
    def _create_cumulative_profit_chart(self, df: pd.DataFrame) -> None:
        """
        Create cumulative profit chart.
        
        Args:
            df: DataFrame with trades
        """
        plt.figure(figsize=(12, 6))
        
        # Calculate cumulative profit
        cumulative_profit = df['profit'].cumsum()
        
        # Plot cumulative profit
        plt.plot(cumulative_profit.index, cumulative_profit.values)
        
        # Add title and labels
        plt.title('Cumulative Profit Over Time')
        plt.xlabel('Date')
        plt.ylabel('Profit')
        
        # Add grid
        plt.grid(True, alpha=0.3)
        
        # Rotate x-axis labels
        plt.xticks(rotation=45)
        
        # Tight layout
        plt.tight_layout()
        
        # Save figure
        plt.savefig(os.path.join(self.output_dir, 'cumulative_profit.png'))
        plt.close()
        
        logger.info(f"Cumulative profit chart saved to {os.path.join(self.output_dir, 'cumulative_profit.png')}")
    
    def _create_win_loss_distribution(self, df: pd.DataFrame) -> None:
        """
        Create win/loss distribution chart.
        
        Args:
            df: DataFrame with trades
        """
        plt.figure(figsize=(12, 6))
        
        # Create histogram of profits
        plt.hist(df['profit'].dropna(), bins=20, alpha=0.7)
        
        # Add title and labels
        plt.title('Profit Distribution')
        plt.xlabel('Profit')
        plt.ylabel('Frequency')
        
        # Add grid
        plt.grid(True, alpha=0.3)
        
        # Tight layout
        plt.tight_layout()
        
        # Save figure
        plt.savefig(os.path.join(self.output_dir, 'profit_distribution.png'))
        plt.close()
        
        logger.info(f"Profit distribution chart saved to {os.path.join(self.output_dir, 'profit_distribution.png')}")
    
    def _create_profit_by_asset_chart(self, metrics: Dict) -> None:
        """
        Create profit by asset chart.
        
        Args:
            metrics: Dictionary with performance metrics
        """
        plt.figure(figsize=(12, 6))
        
        # Sort assets by profit
        assets = sorted(metrics['profit_by_asset'].items(), key=lambda x: x[1], reverse=True)
        
        # Extract assets and profits
        asset_names = [asset[0] for asset in assets]
        profits = [asset[1] for asset in assets]
        
        # Create bar chart
        bars = plt.bar(asset_names, profits)
        
        # Color bars based on profit (green for positive, red for negative)
        for i, profit in enumerate(profits):
            bars[i].set_color('green' if profit >= 0 else 'red')
        
        # Add title and labels
        plt.title('Profit by Asset')
        plt.xlabel('Asset')
        plt.ylabel('Profit')
        
        # Add grid
        plt.grid(True, alpha=0.3, axis='y')
        
        # Rotate x-axis labels
        plt.xticks(rotation=45)
        
        # Tight layout
        plt.tight_layout()
        
        # Save figure
        plt.savefig(os.path.join(self.output_dir, 'profit_by_asset.png'))
        plt.close()
        
        logger.info(f"Profit by asset chart saved to {os.path.join(self.output_dir, 'profit_by_asset.png')}")
    
    def _create_profit_by_hour_chart(self, metrics: Dict) -> None:
        """
        Create profit by hour chart.
        
        Args:
            metrics: Dictionary with performance metrics
        """
        plt.figure(figsize=(12, 6))
        
        # Extract hours and profits
        hours = list(metrics['profit_by_hour'].keys())
        profits = list(metrics['profit_by_hour'].values())
        
        # Create bar chart
        bars = plt.bar(hours, profits)
        
        # Color bars based on profit (green for positive, red for negative)
        for i, profit in enumerate(profits):
            bars[i].set_color('green' if profit >= 0 else 'red')
        
        # Add title and labels
        plt.title('Profit by Hour of Day')
        plt.xlabel('Hour')
        plt.ylabel('Profit')
        
        # Set x-axis ticks
        plt.xticks(range(0, 24, 2))
        
        # Add grid
        plt.grid(True, alpha=0.3, axis='y')
        
        # Tight layout
        plt.tight_layout()
        
        # Save figure
        plt.savefig(os.path.join(self.output_dir, 'profit_by_hour.png'))
        plt.close()
        
        logger.info(f"Profit by hour chart saved to {os.path.join(self.output_dir, 'profit_by_hour.png')}")
    
    def _create_profit_by_day_chart(self, metrics: Dict) -> None:
        """
        Create profit by day chart.
        
        Args:
            metrics: Dictionary with performance metrics
        """
        plt.figure(figsize=(12, 6))
        
        # Day names
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        
        # Extract days and profits
        days = list(metrics['profit_by_day'].keys())
        profits = list(metrics['profit_by_day'].values())
        
        # Create bar chart
        bars = plt.bar(days, profits)
        
        # Color bars based on profit (green for positive, red for negative)
        for i, profit in enumerate(profits):
            bars[i].set_color('green' if profit >= 0 else 'red')
        
        # Add title and labels
        plt.title('Profit by Day of Week')
        plt.xlabel('Day')
        plt.ylabel('Profit')
        
        # Set x-axis ticks
        plt.xticks(range(7), day_names)
        
        # Add grid
        plt.grid(True, alpha=0.3, axis='y')
        
        # Tight layout
        plt.tight_layout()
        
        # Save figure
        plt.savefig(os.path.join(self.output_dir, 'profit_by_day.png'))
        plt.close()
        
        logger.info(f"Profit by day chart saved to {os.path.join(self.output_dir, 'profit_by_day.png')}")
    
    def _create_drawdown_chart(self, df: pd.DataFrame) -> None:
        """
        Create drawdown chart.
        
        Args:
            df: DataFrame with trades
        """
        plt.figure(figsize=(12, 6))
        
        # Calculate cumulative profit
        cumulative_profit = df['profit'].cumsum()
        
        # Calculate drawdown
        running_max = cumulative_profit.cummax()
        drawdown = (cumulative_profit - running_max) / running_max * 100
        
        # Plot drawdown
        plt.fill_between(drawdown.index, drawdown.values, 0, alpha=0.3, color='red')
        plt.plot(drawdown.index, drawdown.values, color='red')
        
        # Add title and labels
        plt.title('Drawdown Over Time')
        plt.xlabel('Date')
        plt.ylabel('Drawdown (%)')
        
        # Add grid
        plt.grid(True, alpha=0.3)
        
        # Rotate x-axis labels
        plt.xticks(rotation=45)
        
        # Tight layout
        plt.tight_layout()
        
        # Save figure
        plt.savefig(os.path.join(self.output_dir, 'drawdown.png'))
        plt.close()
        
        logger.info(f"Drawdown chart saved to {os.path.join(self.output_dir, 'drawdown.png')}")
    
    def analyze(self) -> Dict:
        """
        Analyze trading performance.
        
        Returns:
            Dictionary with analysis results
        """
        # Connect to database
        if not self._connect_to_database():
            logger.error("Failed to connect to database")
            return {"error": "Failed to connect to database"}
        
        try:
            # Get trades
            trades = self._get_trades()
            
            if not trades:
                logger.warning("No trades found")
                return {"error": "No trades found"}
            
            # Get risk adjustments
            risk_adjustments = self._get_risk_adjustments()
            
            # Calculate performance metrics
            metrics = self.calculate_performance_metrics(trades)
            
            # Generate performance report
            report = self.generate_performance_report(metrics)
            
            # Save report to file
            report_file = os.path.join(self.output_dir, "performance_report.txt")
            with open(report_file, "w") as f:
                f.write(report)
            
            logger.info(f"Performance report saved to {report_file}")
            
            # Create visualizations
            self.create_visualizations(trades, metrics)
            
            return {
                "metrics": metrics,
                "report_file": report_file,
                "trades_count": len(trades),
                "risk_adjustments_count": len(risk_adjustments)
            }
        except Exception as e:
            logger.error(f"Error analyzing performance: {str(e)}")
            return {"error": f"Error analyzing performance: {str(e)}"}
        finally:
            # Close database connection
            self._close_database()

def main():
    parser = argparse.ArgumentParser(description='Analyze trading performance for Pocket Option trading bot')
    parser.add_argument('-d', '--db', type=str, default='../data/trades.db', help='Path to SQLite database file')
    parser.add_argument('-c', '--config', type=str, default='../config/bot_config.json', help='Path to bot configuration file')
    parser.add_argument('-o', '--output', type=str, default='../reports', help='Directory to save reports and visualizations')
    parser.add_argument('-s', '--start', type=str, help='Start date for analysis (ISO format, e.g., 2023-01-01)')
    parser.add_argument('-e', '--end', type=str, help='End date for analysis (ISO format, e.g., 2023-12-31)')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
    
    args = parser.parse_args()
    
    # Create analyzer
    analyzer = PerformanceAnalyzer(
        db_file=args.db,
        config_file=args.config,
        output_dir=args.output,
        start_date=args.start,
        end_date=args.end,
        verbose=args.verbose
    )
    
    # Run analysis
    result = analyzer.analyze()
    
    if "error" in result:
        print(f"Error: {result['error']}")
        return 1
    
    print(f"Analysis completed successfully!")
    print(f"Analyzed {result['trades_count']} trades")
    print(f"Performance report saved to {result['report_file']}")
    print(f"Visualizations saved to {args.output}")
    
    return 0

if __name__ == "__main__":
    print("Pocket Option Trading Bot - Performance Analyzer")
    print("----------------------------------------------")
    print("")
    
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nAnalysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError during analysis: {str(e)}")
        sys.exit(1)
