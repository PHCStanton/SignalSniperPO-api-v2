# src/indicators.py
import numpy as np
from typing import List, Tuple, Dict
import pandas as pd

class TechnicalIndicators:
    @staticmethod
    def calculate_ema(data: List[float], period: int) -> List[float]:
        """Calculate Exponential Moving Average."""
        ema = []
        multiplier = 2 / (period + 1)
        
        for i in range(len(data)):
            if i == 0:
                ema.append(data[0])
            else:
                ema.append((data[i] * multiplier) + (ema[i-1] * (1 - multiplier)))
        return ema

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
        atr = []
        supertrend = []
        
        for i in range(len(close)):
            if i == 0:
                atr.append(high[0] - low[0])
            else:
                tr = max(high[i] - low[i], 
                        abs(high[i] - close[i-1]),
                        abs(low[i] - close[i-1]))
                atr.append((atr[-1] * (atr_period - 1) + tr) / atr_period)
            
            basic_upperband = (high[i] + low[i]) / 2 + multiplier * atr[-1]
            basic_lowerband = (high[i] + low[i]) / 2 - multiplier * atr[-1]
            
            if i == 0:
                supertrend.append(basic_upperband if close[i] <= basic_upperband else basic_lowerband)
            else:
                supertrend.append(
                    basic_upperband if (supertrend[-1] == basic_lowerband and close[i] > basic_upperband) 
                    else basic_lowerband if (supertrend[-1] == basic_upperband and close[i] < basic_lowerband)
                    else supertrend[-1]
                )
        
        return supertrend

    @staticmethod
    def calculate_donchian_channel(high: List[float], low: List[float], period: int = 10) -> Tuple[List[float], List[float]]:
        """Calculate Donchian Channel."""
        upper_channel = []
        lower_channel = []
        
        for i in range(len(high)):
            if i < period:
                upper_channel.append(max(high[:i+1]))
                lower_channel.append(min(low[:i+1]))
            else:
                upper_channel.append(max(high[i-period+1:i+1]))
                lower_channel.append(min(low[i-period+1:i+1]))
        
        return upper_channel, lower_channel

    @staticmethod
    def calculate_cci(high: List[float], low: List[float], close: List[float], period: int = 20) -> List[float]:
        """Calculate Commodity Channel Index."""
        tp = [(h + l + c) / 3 for h, l, c in zip(high, low, close)]
        sma_tp = pd.Series(tp).rolling(window=period).mean()
        mad = pd.Series(tp).rolling(window=period).apply(lambda x: pd.Series(x).mad())
        cci = pd.Series(tp - sma_tp) / (0.015 * mad)
        return cci.tolist()

    @staticmethod
    def calculate_rsi(data: List[float], period: int = 14) -> List[float]:
        """Calculate Relative Strength Index."""
        delta = pd.Series(data).diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.tolist()