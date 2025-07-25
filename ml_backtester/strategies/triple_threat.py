import pandas as pd
import numpy as np
from typing import Dict, Any

from .base_strategy import BaseStrategy

class TripleThreatStrategy(BaseStrategy):
    """
    Implements the "Triple Threat" trend-following strategy.

    This strategy combines a long-term trend filter (EMA), a medium-term
    momentum indicator (MACD), and a short-term entry signal (Stochastic)
    to generate trading signals.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initializes the TripleThreatStrategy.
        Args:
            config (Dict[str, Any]): Configuration dictionary.
        """
        super().__init__(config)
        strategy_params = config.get('strategy', {}).get('params', {})
        self.ema_period = strategy_params.get('ema_period', 200)
        self.macd_fast = strategy_params.get('macd_fast', 12)
        self.macd_slow = strategy_params.get('macd_slow', 26)
        self.macd_signal = strategy_params.get('macd_signal', 9)
        self.stoch_k = strategy_params.get('stoch_k', 14)
        self.stoch_d = strategy_params.get('stoch_d', 3)
        self.stoch_smooth_k = strategy_params.get('stoch_smooth_k', 3)
        self.stoch_oversold = strategy_params.get('stoch_oversold', 20)
        self.stoch_overbought = strategy_params.get('stoch_overbought', 80)

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Generates buy/sell signals based on the Triple Threat logic.
        Args:
            data (pd.DataFrame): DataFrame with OHLCV and indicator data.
        Returns:
            pd.DataFrame: The input DataFrame with a 'signal' column.
        """
        # Define dynamic column names based on parameters
        ema_col = f'EMA_{self.ema_period}'
        macd_col = f'MACD_{self.macd_fast}_{self.macd_slow}_{self.macd_signal}'
        macds_col = f'MACDs_{self.macd_fast}_{self.macd_slow}_{self.macd_signal}'
        stoch_col = f'STOCHk_{self.stoch_k}_{self.stoch_d}_{self.stoch_smooth_k}'

        required_cols = [ema_col, macd_col, macds_col, stoch_col]
        if not all(col in data.columns for col in required_cols):
            raise ValueError(f"Input data is missing one of the required indicator columns: {required_cols}")

        signals = np.zeros(len(data))

        # --- Define Conditions using Vectorized Operations ---
        long_trend = data['close'] > data[ema_col]
        long_momentum = data[macd_col] > data[macds_col]
        long_entry = (data[stoch_col] > data[stoch_col].shift(1)) & (data[stoch_col].shift(1) < self.stoch_oversold)

        short_trend = data['close'] < data[ema_col]
        short_momentum = data[macd_col] < data[macds_col]
        short_entry = (data[stoch_col] < data[stoch_col].shift(1)) & (data[stoch_col].shift(1) > self.stoch_overbought)

        # --- Apply Conditions to Generate Signals ---
        
        # Set buy signals (1) where all long conditions are met
        signals[long_trend & long_momentum & long_entry] = 1
        
        # Set sell signals (-1) where all short conditions are met
        signals[short_trend & short_momentum & short_entry] = -1

        data['signal'] = signals
        return data

if __name__ == '__main__':
    # Example usage for testing the TripleThreatStrategy
    
    # 1. Import necessary agents
    from ..agents.data_agent import DataAgent
    from ..agents.feature_engineering_agent import FeatureEngineeringAgent

    # 2. Define mock configurations
    mock_data_config = {
        'data_path': 'ml_backtester/data/EURUSD_m15_2022_2025.parquet'
    }
    
    mock_feature_config = {
        'feature_engineering': {
            'indicators': [
                {'name': 'ema', 'params': {'length': 200}},
                {'name': 'macd'},
                {'name': 'stoch'}
            ]
        }
    }

    # 3. Load and prepare data
    try:
        data_agent = DataAgent(config=mock_data_config)
        df = data_agent.execute()

        feature_agent = FeatureEngineeringAgent(config=mock_feature_config)
        featured_df = feature_agent.execute(df)

        # 4. Initialize and execute the strategy
        strategy = TripleThreatStrategy(config={})
        signals_df = strategy.generate_signals(featured_df)

        print("TripleThreatStrategy executed successfully.")
        
        # 5. Display signals
        signal_points = signals_df[signals_df['signal'] != 0]
        print(f"\nFound {len(signal_points)} trading signals.")
        if not signal_points.empty:
            print("Last 10 signals:")
            with pd.option_context('display.max_columns', None):
                print(signal_points.tail(10))

    except Exception as e:
        print(f"An error occurred during testing: {e}")