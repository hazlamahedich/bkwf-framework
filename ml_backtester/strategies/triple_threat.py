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
            config (Dict[str, Any]): Configuration dictionary. The strategy
                                     logic itself is parameter-less in this
                                     implementation, but it adheres to the
                                     BaseStrategy interface.
        """
        super().__init__(config)

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Generates buy/sell signals based on the Triple Threat logic.

        Args:
            data (pd.DataFrame): A DataFrame containing OHLCV data and the
                                 necessary indicators (EMA_200, MACD, STOCH).

        Returns:
            pd.DataFrame: The input DataFrame with a 'signal' column appended.
        """
        # Ensure required columns are present
        required_cols = ['EMA_200', 'MACD_12_26_9', 'MACDs_12_26_9', 'STOCHk_14_3_3']
        if not all(col in data.columns for col in required_cols):
            raise ValueError(f"Input data is missing one of the required indicator columns: {required_cols}")

        # Initialize signal column
        signals = np.zeros(len(data))

        # --- Define Conditions using Vectorized Operations ---
        
        # Long conditions
        long_trend = data['close'] > data['EMA_200']
        long_momentum = data['MACD_12_26_9'] > data['MACDs_12_26_9']
        long_entry = (data['STOCHk_14_3_3'] > data['STOCHk_14_3_3'].shift(1)) & (data['STOCHk_14_3_3'].shift(1) < 20)

        # Short conditions
        short_trend = data['close'] < data['EMA_200']
        short_momentum = data['MACD_12_26_9'] < data['MACDs_12_26_9']
        short_entry = (data['STOCHk_14_3_3'] < data['STOCHk_14_3_3'].shift(1)) & (data['STOCHk_14_3_3'].shift(1) > 80)

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