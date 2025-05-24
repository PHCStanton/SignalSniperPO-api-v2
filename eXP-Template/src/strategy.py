# src/strategy.py
from typing import Dict, List, Optional
from datetime import datetime
import logging
from .indicators import TechnicalIndicators

class TradingStrategy:
    def __init__(self, config: Dict):
        self.config = config
        self.indicators = TechnicalIndicators()
        self.logger = logging.getLogger(__name__)
        self.price_history = {
            'high': [],
            'low': [],
            'close': []
        }
        self.last_trade_time = None
        self.daily_loss = 0
        self.consecutive_losses = 0

    def update_price_history(self, price_data: Dict):
        """Update price history with new data."""
        self.price_history['high'].append(price_data['high'])
        self.price_history['low'].append(price_data['low'])
        self.price_history['close'].append(price_data['close'])
        
        # Keep only necessary history
        max_period = 20  # Maximum period needed for indicators
        if len(self.price_history['close']) > max_period:
            for key in self.price_history:
                self.price_history[key] = self.price_history[key][-max_period:]

    def check_trading_hours(self) -> bool:
        """Check if current time is within trading hours."""
        current_time = datetime.now()
        start_time = datetime.strptime(self.config['trading_hours']['start'], "%H:%M").time()
        end_time = datetime.strptime(self.config['trading_hours']['end'], "%H:%M").time()
        return start_time <= current_time.time() <= end_time

    def check_risk_parameters(self, account_balance: float) -> bool:
        """Check if risk parameters allow trading."""
        if self.daily_loss >= account_balance * 0.05:  # 5% daily loss limit
            self.logger.warning("Daily loss limit reached")
            return False
        
        if self.consecutive_losses >= self.config['risk_management']['consecutive_losses_limit']:
            self.logger.warning("Consecutive losses limit reached")
            return False
            
        return True

    def analyze_entry_signal(self) -> Optional[str]:
        """Analyze price data and return trading signal."""
        if len(self.price_history['close']) < 20:  # Minimum required history
            return None

        # Calculate indicators
        supertrend = self.indicators.calculate_supertrend(
            self.price_history['high'],
            self.price_history['low'],
            self.price_history['close'],
            self.config['indicators']['SuperTrend']['atr_period'],
            self.config['indicators']['SuperTrend']['multiplier']
        )

        ema_fast = self.indicators.calculate_ema(
            self.price_history['close'],
            self.config['indicators']['EMA']['fast']['period']
        )

        ema_slow = self.indicators.calculate_ema(
            self.price_history['close'],
            self.config['indicators']['EMA']['slow']['period']
        )

        bb_upper, _, bb_lower = self.indicators.calculate_bollinger_bands(
            self.price_history['close'],
            self.config['indicators']['BollingerBands']['period'],
            self.config['indicators']['BollingerBands']['deviation']
        )

        donchian_upper, donchian_lower = self.indicators.calculate_donchian_channel(
            self.price_history['high'],
            self.price_history['low'],
            self.config['indicators']['DonchianChannel']['period']
        )

        cci = self.indicators.calculate_cci(
            self.price_history['high'],
            self.price_history['low'],
            self.price_history['close']
        )

        rsi = self.indicators.calculate_rsi(self.price_history['close'])

        # Check conditions for CALL option
        current_price = self.price_history['close'][-1]
        if (current_price > supertrend[-1] and  # SuperTrend below price
            ema_fast[-1] > ema_slow[-1] and  # EMA crossover
            current_price > donchian_upper[-1] and  # Donchian breakout
            current_price >= bb_upper[-1] and  # BB touch/break
            cci[-1] > self.config['indicators']['CCI']['overbought'] and  # CCI momentum
            rsi[-1] < self.config['indicators']['RSI']['overbought']):  # RSI not overbought
            return "call"

        # Check conditions for PUT option
        if (current_price < supertrend[-1] and  # SuperTrend above price
            ema_fast[-1] < ema_slow[-1] and  # EMA crossover
            current_price < donchian_lower[-1] and  # Donchian breakout
            current_price <= bb_lower[-1] and  # BB touch/break
            cci[-1] < self.config['indicators']['CCI']['oversold'] and  # CCI momentum
            rsi[-1] > self.config['indicators']['RSI']['oversold']):  # RSI not oversold
            return "put"

        return None

    def can_place_trade(self) -> bool:
        """Check if enough time has passed since last trade."""
        if not self.last_trade_time:
            return True
        
        time_diff = (datetime.now() - self.last_trade_time).seconds
        return time_diff >= self.config['trade_parameters']['minimum_time_between_trades']

    def update_trade_result(self, win: bool, trade_amount: float):
        """Update trading statistics after a trade."""
        if win:
            self.consecutive_losses = 0
        else:
            self.consecutive_losses += 1
            self.daily_loss += trade_amount

    def reset_daily_stats(self):
        """Reset daily statistics."""
        self.daily_loss = 0
        self.consecutive_losses = 0