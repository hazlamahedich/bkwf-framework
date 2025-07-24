import pandas as pd
from typing import Dict, Any
import logging
import importlib

from ..strategies.base_strategy import BaseStrategy

class StrategyAgent:
    """
    Agent responsible for loading and executing a specific trading strategy.
    
    This agent dynamically imports a strategy class based on the configuration,
    instantiates it, and uses it to generate trading signals.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initializes the StrategyAgent.

        Args:
            config (Dict[str, Any]): Configuration dictionary. Expected keys:
                'strategy': {
                    'name': 'name_of_strategy_file',
                    ... other strategy-specific params ...
                }
        """
        self.config = config.get('strategy', {})
        self.strategy_name = self.config.get('name')
        if not self.strategy_name:
            raise ValueError("Strategy 'name' must be specified in the config.")

    def _load_strategy_class(self) -> BaseStrategy:
        """Dynamically imports and returns the strategy class."""
        try:
            module_path = f"ml_backtester.strategies.{self.strategy_name}"
            strategy_module = importlib.import_module(module_path)
            
            # Convention: Class name is CamelCase version of snake_case file name
            class_name = "".join(word.capitalize() for word in self.strategy_name.split('_')) + "Strategy"
            
            strategy_class = getattr(strategy_module, class_name)
            return strategy_class
        except (ImportError, AttributeError) as e:
            logging.error(f"Could not load strategy '{self.strategy_name}'. Error: {e}")
            raise ImportError(f"Failed to load strategy class '{class_name}' from '{module_path}'.")

    def execute(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Loads the strategy and generates signals.

        Args:
            data (pd.DataFrame): The feature-engineered market data.

        Returns:
            pd.DataFrame: The data with a 'signal' column appended.
        """
        logging.info(f"StrategyAgent: Loading and executing strategy '{self.strategy_name}'...")
        
        strategy_class = self._load_strategy_class()
        strategy_instance = strategy_class(config=self.config)
        
        signals_df = strategy_instance.generate_signals(data)
        
        logging.info(f"Strategy '{self.strategy_name}' executed successfully.")
        return signals_df

if __name__ == '__main__':
    # Example usage for testing the StrategyAgent
    from ..agents.data_agent import DataAgent
    from ..agents.feature_engineering_agent import FeatureEngineeringAgent

    mock_data_config = {'data_path': 'ml_backtester/data/EURUSD_m15_2022_2025.parquet'}
    mock_feature_config = {
        'feature_engineering': {
            'indicators': [
                {'name': 'ema', 'params': {'length': 200}},
                {'name': 'macd'},
                {'name': 'stoch'}
            ]
        }
    }
    # --- Test with TripleThreatStrategy ---
    mock_strategy_config_1 = {
        'strategy': {'name': 'triple_threat'}
    }

    try:
        print("--- Testing StrategyAgent with 'triple_threat' ---")
        df = DataAgent(config=mock_data_config).execute()
        featured_df = FeatureEngineeringAgent(config=mock_feature_config).execute(df)
        
        strategy_agent = StrategyAgent(config=mock_strategy_config_1)
        signals_df = strategy_agent.execute(featured_df)

        print("StrategyAgent executed successfully.")
        signal_points = signals_df[signals_df['signal'] != 0]
        print(f"Found {len(signal_points)} signals.\n")

    except Exception as e:
        print(f"An error occurred during testing: {e}")
