# trading_bot/indicators.py
import numpy as np
import pandas as pd
from typing import List, Tuple

class TechnicalIndicators:
    @staticmethod
    def calculate_ema(data: List[float], period: int) -> List[float]:
        """Calculate Exponential Moving Average."""
        prices = pd.Series(data)
        ema = prices.ewm(span=period, adjust=False).mean()
        return ema.tolist()

    @staticmethod
    def calculate_bollinger_bands(data: List[float], period: int = 10, deviation: int = 2) -> Tuple[List[float], List[float], List[float]]:
        """Calculate Bollinger Bands."""
        df = pd.Series(data)
        sma = df.rolling(window=period).mean()
        std = df.rolling(window=period).std()
        upper_band = sma + (std * deviation)
        lower_band = sma - (std * deviation)
        return upper_band.tolist(), sma.tolist(), lower_band.tolist()

    @staticmethod
    def calculate_supertrend(high: List[float], low: List[float], close: List[float], 
                         atr_period: int = 7, multiplier: float = 2) -> List[float]:
        """Calculate SuperTrend indicator."""
        df = pd.DataFrame({
            'high': high,
            'low': low,
            'close': close
        })
        
        # Calculate ATR
        tr1 = pd.Series(df['high'] - df['low'])
        tr2 = pd.Series(abs(df['high'] - df['close'].shift(1)))
        tr3 = pd.Series(abs(df['low'] - df['close'].shift(1)))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.ewm(span=atr_period, adjust=False).mean()

        # Calculate SuperTrend
        hl2 = (df['high'] + df['low']) / 2
        upperband = hl2 + (multiplier * atr)
        lowerband = hl2 - (multiplier * atr)
        
        supertrend = [upperband.iloc[0]]
        for i in range(1, len(df)):
            if df['close'].iloc[i] > supertrend[-1]:
                supertrend.append(lowerband.iloc[i])
            else:
                supertrend.append(upperband.iloc[i])
                
        return supertrend

    @staticmethod
    def calculate_donchian_channel(high: List[float], low: List[float], period: int = 10) -> Tuple[List[float], List[float]]:
        """Calculate Donchian Channel."""
        df_high = pd.Series(high)
        df_low = pd.Series(low)
        
        upper_channel = df_high.rolling(window=period).max()
        lower_channel = df_low.rolling(window=period).min()
        
        return upper_channel.tolist(), lower_channel.tolist()

    @staticmethod
    def calculate_cci(high: List[float], low: List[float], close: List[float], period: int = 20) -> List[float]:
        """Calculate Commodity Channel Index."""
        tp = pd.Series((pd.Series(high) + pd.Series(low) + pd.Series(close)) / 3)
        sma_tp = tp.rolling(window=period).mean()
        mad = tp.rolling(window=period).apply(lambda x: pd.Series(x).mad())
        cci = (tp - sma_tp) / (0.015 * mad)
        return cci.tolist()

    @staticmethod
    def calculate_rsi(data: List[float], period: int = 14) -> List[float]:
        """Calculate Relative Strength Index."""
        prices = pd.Series(data)
        deltas = prices.diff()
        seed = deltas[:period+1]
        up = seed[seed >= 0].sum()/period
        down = -seed[seed < 0].sum()/period
        rs = up/down
        rsi = np.zeros_like(prices)
        rsi[:period] = 100. - 100./(1.+rs)

        for i in range(period, len(prices)):
            delta = deltas[i-1]
            if delta > 0:
                upval = delta
                downval = 0.
            else:
                upval = 0.
                downval = -delta

            up = (up*(period-1) + upval)/period
            down = (down*(period-1) + downval)/period
            rs = up/down
            rsi[i] = 100. - 100./(1.+rs)

        return rsi.tolist()