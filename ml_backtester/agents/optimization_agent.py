import optuna
import pandas as pd
import numpy as np
from typing import Dict, Any, Callable
import logging
import joblib

from .risk_management_agent import RiskManagementAgent
from .execution_agent import ExecutionAgent
from .backtesting_agent import BacktestingAgent

class OptimizationAgent:
    """
    Agent for hyperparameter tuning of any given strategy using Optuna.
    """

    def __init__(self, config: Dict[str, Any], strategy_class: Callable):
        """
        Initializes the OptimizationAgent.

        Args:
            config (Dict[str, Any]): Configuration dictionary. Expected keys:
                'optimization': {
                    'n_trials': 100,
                    'metric': 'sharpe_ratio',
                    'params': {
                        'ema_period': {'type': 'int', 'low': 50, 'high': 250},
                        ...
                    }
                }
            strategy_class (Callable): The strategy class to be optimized.
        """
        self.config = config.get('optimization', {})
        self.strategy_class = strategy_class
        self.param_space = self.config.get('params', {})
        self.n_trials = self.config.get('n_trials', 50)

    def _create_objective(self, data: pd.DataFrame) -> Callable:
        """Creates the objective function for Optuna to optimize."""
        
        def objective(trial: optuna.Trial) -> float:
            trial_params = {}
            for name, space in self.param_space.items():
                if space['type'] == 'int':
                    trial_params[name] = trial.suggest_int(name, space['low'], space['high'])
                elif space['type'] == 'float':
                    trial_params[name] = trial.suggest_float(name, space['low'], space['high'])

            # Create a temporary config for this trial
            trial_config = self.config.copy()
            trial_config['risk_management'] = trial_params

            # Run the core backtesting pipeline for this trial
            strategy = self.strategy_class(config=trial_config)
            signals_df = strategy.generate_signals(data.copy())
            
            risk_agent = RiskManagementAgent(trial_config)
            risk_managed_df = risk_agent.execute(signals_df, self.config.get('backtesting', {}).get('initial_capital', 100000))

            execution_agent = ExecutionAgent(trial_config)
            executed_df = execution_agent.execute(risk_managed_df)

            backtester = BacktestingAgent(trial_config)
            results = backtester.execute(executed_df)
            
            # Return the Sharpe ratio, or a very low number if it's not available
            return results.get('sharpe_ratio', -np.inf)

        return objective

    def execute(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Runs the optimization process.

        Args:
            data (pd.DataFrame): The feature-engineered market data.

        Returns:
            Dict[str, Any]: A dictionary containing the best parameters found.
        """
        logging.info(f"OptimizationAgent: Starting optimization for {self.strategy_class.__name__}...")
        
        objective_func = self._create_objective(data)
        
        # Create an Optuna study
        study = optuna.create_study(direction='maximize')
        
        # Run the study with parallel jobs
        study.optimize(
            objective_func,
            n_trials=self.n_trials,
            n_jobs=-1  # Use all available CPU cores
        )

        logging.info(f"Optimization complete. Best trial score: {study.best_value:.4f}")
        logging.info(f"Best parameters found: {study.best_params}")
        
        return {'best_params': study.best_params, 'best_value': study.best_value}

if __name__ == '__main__':
    # Example usage for testing the OptimizationAgent
    from ..agents.data_agent import DataAgent
    from ..agents.feature_engineering_agent import FeatureEngineeringAgent
    from ..strategies.triple_threat import TripleThreatStrategy

    # This is a placeholder as the strategy itself doesn't use config yet.
    # We will adapt this when we refactor the strategies.
    class OptimizableTripleThreat(TripleThreatStrategy):
        def __init__(self, config: Dict[str, Any]):
            super().__init__(config)
            # In a real scenario, these would be read from config
            # For now, we just need to show Optuna can pass them.
            self.ema_period = config.get('strategy', {}).get('ema_period', 200)

    mock_data_config = {'data_path': 'ml_backtester/data/EURUSD_m15_2022_2025.parquet'}
    mock_feature_config = {'feature_engineering': {'indicators': [{'name': 'ema', 'params': {'length': 200}}, {'name': 'macd'}, {'name': 'stoch'}]}}
    
    mock_opt_config = {
        'optimization': {
            'n_trials': 20, # Small number for a quick test
            'params': {
                'ema_period': {'type': 'int', 'low': 150, 'high': 250}
            }
        }
    }

    try:
        df = DataAgent(config=mock_data_config).execute()
        featured_df = FeatureEngineeringAgent(config=mock_feature_config).execute(df)
        
        optimizer = OptimizationAgent(config=mock_opt_config, strategy_class=OptimizableTripleThreat)
        best_params = optimizer.execute(featured_df)

        print("\nOptimizationAgent executed successfully.")
        print(f"Optimal parameters found: {best_params}")

    except Exception as e:
        print(f"An error occurred during testing: {e}")