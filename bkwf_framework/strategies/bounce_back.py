import pandas as pd
import numpy as np
from typing import Dict, Any

from .base_strategy import BaseStrategy

class BounceBackStrategy(BaseStrategy):
    """
    Implements the "Bounce Back" support and resistance strategy.

    This strategy identifies potential reversals at key Fibonacci levels,
    confirmed by candlestick patterns (engulfing) and RSI divergence.
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        strategy_params = config.get('strategy', {}).get('params', {})
        self.fib_window = strategy_params.get('fib_window', 252)
        self.rsi_period = strategy_params.get('rsi_period', 14)

    def _detect_engulfing(self, data: pd.DataFrame) -> pd.Series:
        """Detects bullish and bearish engulfing patterns."""
        body = abs(data['close'] - data['open'])
        prev_body = abs(data['close'].shift(1) - data['open'].shift(1))

        bullish_engulfing = (data['open'] < data['close'].shift(1)) & \
                            (data['close'] > data['open'].shift(1)) & \
                            (body > prev_body) & \
                            (data['close'].shift(1) > data['open'].shift(1)) # Previous candle is bullish

        bearish_engulfing = (data['open'] > data['close'].shift(1)) & \
                            (data['close'] < data['open'].shift(1)) & \
                            (body > prev_body) & \
                            (data['close'].shift(1) < data['open'].shift(1)) # Previous candle is bearish
        
        engulfing = pd.Series(np.zeros(len(data)), index=data.index)
        engulfing[bullish_engulfing] = 1
        engulfing[bearish_engulfing] = -1
        return engulfing

    def _detect_rsi_divergence(self, data: pd.DataFrame) -> pd.Series:
        """Detects simple bullish and bearish RSI divergence."""
        # A simple implementation: look for lower low in price but higher low in RSI
        lows = data['low']
        rsi = data[f'RSI_{self.rsi_period}']

        bullish_divergence = (lows < lows.shift(1)) & (rsi > rsi.shift(1))
        bearish_divergence = (data['high'] > data['high'].shift(1)) & (rsi < rsi.shift(1))

        divergence = pd.Series(np.zeros(len(data)), index=data.index)
        divergence[bullish_divergence] = 1
        divergence[bearish_divergence] = -1
        return divergence

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Generates signals based on the Bounce Back logic.
        """
        # --- Feature Calculation ---
        # 1. Fibonacci Levels
        rolling_high = data['high'].rolling(window=self.fib_window).max()
        rolling_low = data['low'].rolling(window=self.fib_window).min()
        fib_range = rolling_high - rolling_low
        
        data['fib_50'] = rolling_low + 0.5 * fib_range
        data['fib_618'] = rolling_low + 0.618 * fib_range

        # 2. Engulfing Patterns
        data['engulfing'] = self._detect_engulfing(data)

        # 3. RSI Divergence
        data['rsi_divergence'] = self._detect_rsi_divergence(data)

        # --- Signal Generation ---
        signals = np.zeros(len(data))

        # Long conditions
        at_support = (data['low'] <= data['fib_50']) | (data['low'] <= data['fib_618'])
        long_signal = at_support & (data['engulfing'] == 1) & (data['rsi_divergence'] == 1)

        # Short conditions
        at_resistance = (data['high'] >= data['fib_50']) | (data['high'] >= data['fib_618'])
        short_signal = at_resistance & (data['engulfing'] == -1) & (data['rsi_divergence'] == -1)

        signals[long_signal] = 1
        signals[short_signal] = -1

        data['signal'] = signals
        return data

if __name__ == '__main__':
    from ..agents.data_agent import DataAgent
    from ..agents.feature_engineering_agent import FeatureEngineeringAgent

    mock_data_config = {'data_path': 'bkwf_framework/data/EURUSD_m15_2022_2025.parquet'}
    mock_feature_config = {'feature_engineering': {'indicators': [{'name': 'rsi'}]}}

    try:
        df = DataAgent(config=mock_data_config).execute()
        featured_df = FeatureEngineeringAgent(config=mock_feature_config).execute(df)
        
        strategy = BounceBackStrategy(config={})
        signals_df = strategy.generate_signals(featured_df)

        print("BounceBackStrategy executed successfully.")
        signal_points = signals_df[signals_df['signal'] != 0]
        print(f"\nFound {len(signal_points)} trading signals.")
        if not signal_points.empty:
            print("Last 10 signals:")
            with pd.option_context('display.max_columns', None):
                print(signal_points.tail(10))

    except Exception as e:
        print(f"An error occurred during testing: {e}")