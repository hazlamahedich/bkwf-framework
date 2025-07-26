import pandas as pd
import numpy as np
from typing import Dict, Any
import logging

class ExecutionAgent:
    """
    Agent for simulating trade execution, including spread and slippage.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initializes the ExecutionAgent.

        Args:
            config (Dict[str, Any]): Configuration dictionary. Expected keys:
                'execution': {
                    'slippage_percent': 0.0005 // e.g., 0.05%
                }
        """
        self.config = config.get('execution', {})
        self.slippage_percent = self.config.get('slippage_percent', 0.0005)

    def execute(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Simulates trade execution and calculates trade prices.

        Args:
            data (pd.DataFrame): DataFrame with signals, position sizes,
                                 and spread information.

        Returns:
            pd.DataFrame: DataFrame with an added 'entry_price' column.
        """
        logging.info("ExecutionAgent: Simulating trade execution...")

        # --- Calculate Entry Price with Spread and Slippage ---
        
        # Spread is applied to all trades (buy at ask, sell at bid)
        # We'll use the 'spread' column from the data, assuming it's in points.
        # For simplicity, we'll assume 1 point = 0.0001 for forex.
        spread_cost = (data['spread'] * 0.0001) / 2
        
        # Slippage is a random factor applied to the execution price
        slippage = np.random.uniform(0, self.slippage_percent, len(data)) * data['close']

        # Calculate entry price
        buy_price = data['close'] + spread_cost + slippage
        sell_price = data['close'] - spread_cost - slippage
        
        data['entry_price'] = np.where(data['signal'] == 1, buy_price,
                                       np.where(data['signal'] == -1, sell_price, np.nan))

        # Forward-fill the entry price for the duration of the trade
        data['entry_price'] = data['entry_price'].ffill()

        logging.info("Trade execution simulated successfully.")
        return data

if __name__ == '__main__':
    from ..agents.data_agent import DataAgent
    from ..agents.feature_engineering_agent import FeatureEngineeringAgent
    from ..agents.strategy_agent import StrategyAgent
    from ..agents.risk_management_agent import RiskManagementAgent

    mock_data_config = {'data_path': 'bkwf_framework/data/EURUSD_m15_2022_2025.parquet'}
    mock_feature_config = {'feature_engineering': {'indicators': [{'name': 'ema', 'params': {'length': 200}}, {'name': 'macd'}, {'name': 'stoch'}, {'name': 'atr'}]}}
    mock_strategy_config = {'strategy': {'name': 'triple_threat'}}
    mock_risk_config = {'risk_management': {'risk_per_trade': 0.01}}
    mock_exec_config = {'execution': {'slippage_percent': 0.0005}}
    INITIAL_CAPITAL = 100000

    try:
        df = DataAgent(config=mock_data_config).execute()
        featured_df = FeatureEngineeringAgent(config=mock_feature_config).execute(df)
        signals_df = StrategyAgent(config=mock_strategy_config).execute(featured_df)
        risk_df = RiskManagementAgent(config=mock_risk_config).execute(signals_df, INITIAL_CAPITAL)
        
        execution_agent = ExecutionAgent(config=mock_exec_config)
        executed_df = execution_agent.execute(risk_df)

        print("\nExecutionAgent executed successfully.")
        trade_signals = executed_df[executed_df['signal'] != 0]
        
        print("Last 5 trade signals with execution details:")
        with pd.option_context('display.max_columns', None):
            print(trade_signals[['close', 'signal', 'entry_price', 'position_size']].tail())

    except Exception as e:
        print(f"An error occurred during testing: {e}")