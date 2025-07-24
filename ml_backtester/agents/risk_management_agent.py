import pandas as pd
import numpy as np
from typing import Dict, Any
import logging

class RiskManagementAgent:
    """
    Agent for applying risk management rules to trading signals.
    This includes position sizing, stop-loss, and take-profit.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initializes the RiskManagementAgent.

        Args:
            config (Dict[str, Any]): Configuration dictionary. Expected keys:
                'risk_management': {
                    'risk_per_trade': 0.01, // e.g., 1% of capital
                    'sl_atr_multiplier': 2.0,
                    'tp_atr_multiplier': 3.0,
                    'trailing_stop': {
                       'enabled': True,
                       'atr_multiplier': 1.5
                    }
                }
        """
        self.config = config.get('risk_management', {})
        self.risk_per_trade = self.config.get('risk_per_trade', 0.01)
        self.sl_atr_multiplier = self.config.get('sl_atr_multiplier', 2.0)
        self.tp_atr_multiplier = self.config.get('tp_atr_multiplier', 3.0)
        
        # Trailing stop configuration
        self.trailing_stop_config = self.config.get('trailing_stop', {})
        self.trailing_stop_enabled = self.trailing_stop_config.get('enabled', False)
        self.tsl_atr_multiplier = self.trailing_stop_config.get('atr_multiplier', 1.5)

    def execute(self, data: pd.DataFrame, capital: float) -> pd.DataFrame:
        """
        Applies risk management rules to the data.

        Args:
            data (pd.DataFrame): DataFrame with signals and ATR.
            capital (float): The current account capital.

        Returns:
            pd.DataFrame: DataFrame with added 'position_size', 'stop_loss',
                          and 'take_profit' columns.
        """
        logging.info("RiskManagementAgent: Applying risk rules...")
        
        if self.trailing_stop_enabled:
           data['trailing_stop_activated'] = True
           logging.info(f"Trailing stop enabled with ATR multiplier: {self.tsl_atr_multiplier}")

        atr_col = next((col for col in data.columns if 'ATR' in col), None)
        if not atr_col:
            raise ValueError("ATR indicator not found in data. It is required for risk management.")

        # Calculate SL and TP levels
        data['stop_loss'] = np.where(data['signal'] == 1, data['close'] - self.sl_atr_multiplier * data[atr_col], 
                                     np.where(data['signal'] == -1, data['close'] + self.sl_atr_multiplier * data[atr_col], np.nan))
        
        data['take_profit'] = np.where(data['signal'] == 1, data['close'] + self.tp_atr_multiplier * data[atr_col],
                                       np.where(data['signal'] == -1, data['close'] - self.tp_atr_multiplier * data[atr_col], np.nan))

        # Calculate position size
        risk_per_share = self.sl_atr_multiplier * data[atr_col]
        capital_at_risk = capital * self.risk_per_trade
        
        # Avoid division by zero
        position_size = np.where(risk_per_share > 0, capital_at_risk / risk_per_share, 0)
        data['position_size'] = np.floor(position_size)

        # Forward-fill SL/TP and position size for the duration of the trade
        data[['stop_loss', 'take_profit', 'position_size']] = data[['stop_loss', 'take_profit', 'position_size']].ffill()

        logging.info("Risk management rules applied successfully.")
        return data

if __name__ == '__main__':
    from ..agents.data_agent import DataAgent
    from ..agents.feature_engineering_agent import FeatureEngineeringAgent
    from ..agents.strategy_agent import StrategyAgent

    mock_data_config = {'data_path': 'ml_backtester/data/EURUSD_m15_2022_2025.parquet'}
    mock_feature_config = {
        'feature_engineering': {
            'indicators': [
                {'name': 'ema', 'params': {'length': 200}},
                {'name': 'macd'},
                {'name': 'stoch'},
                {'name': 'atr'} # Add ATR for risk management
            ]
        }
    }
    mock_strategy_config = {'strategy': {'name': 'triple_threat'}}
    mock_risk_config = {'risk_management': {'risk_per_trade': 0.01, 'sl_atr_multiplier': 2, 'tp_atr_multiplier': 3}}
    INITIAL_CAPITAL = 100000

    try:
        df = DataAgent(config=mock_data_config).execute()
        featured_df = FeatureEngineeringAgent(config=mock_feature_config).execute(df)
        signals_df = StrategyAgent(config=mock_strategy_config).execute(featured_df)
        
        risk_agent = RiskManagementAgent(config=mock_risk_config)
        risk_managed_df = risk_agent.execute(signals_df, INITIAL_CAPITAL)

        print("\nRiskManagementAgent executed successfully.")
        trade_signals = risk_managed_df[risk_managed_df['signal'] != 0]
        
        print("Last 5 trade signals with risk management applied:")
        with pd.option_context('display.max_columns', None):
            print(trade_signals[['close', 'signal', 'stop_loss', 'take_profit', 'position_size']].tail())

    except Exception as e:
        print(f"An error occurred during testing: {e}")