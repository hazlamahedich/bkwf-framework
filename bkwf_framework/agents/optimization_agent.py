import optuna
import pandas as pd
import numpy as np
from typing import Dict, Any, Callable
import logging
import joblib
import signal
import sys

from .risk_management_agent import RiskManagementAgent
from .execution_agent import ExecutionAgent
from .backtesting_agent import BacktestingAgent
from .feature_engineering_agent import FeatureEngineeringAgent
from .modeling_agent import ModelingAgent
from pathlib import Path

class OptimizationAgent:
    """
    Agent for hyperparameter tuning of any given strategy using Optuna.
    """

    def __init__(self, config: Dict[str, Any], strategy_class: Callable):
        """
        Initializes the OptimizationAgent.
        Args:
            config (Dict[str, Any]): The main configuration dictionary.
            strategy_class (Callable): The strategy class to be optimized.
        """
        self.config = config
        self.strategy_class = strategy_class
        self.opt_config = self.config.get('optimization', {})
        self.n_trials = self.opt_config.get('n_trials', 50)

        # Convert strategy class name to snake_case to match config keys
        strategy_name_snake = ''.join(['_' + i.lower() if i.isupper() else i for i in strategy_class.__name__]).lstrip('_').replace('_strategy', '')

        # Get the correct parameter space for the given strategy
        params_by_strategy = self.opt_config.get('params_by_strategy', {})
        self.param_space = params_by_strategy.get(strategy_name_snake, {})

        if not self.param_space:
            logging.warning(f"No optimization parameters found for strategy: {strategy_name_snake}")

    def _create_objective(self, data: pd.DataFrame) -> Callable:
        """Creates the objective function for Optuna to optimize."""
        
        def objective(trial: optuna.Trial) -> float:
            strategy_params = {}
            risk_params = {}

            for name, space in self.param_space.items():
                value = None
                if space['type'] == 'int':
                    value = trial.suggest_int(name, space['low'], space['high'])
                elif space['type'] == 'float':
                    value = trial.suggest_float(name, space['low'], space['high'], log=space.get('log', False))

                if name in ['sl_atr_multiplier', 'tp_atr_multiplier', 'trailing_stop_atr_multiplier']:
                    risk_params[name] = value
                else:
                    strategy_params[name] = value
            
            # Suggest ML hyperparameters
            ml_params = {}
            ml_param_space = self.opt_config.get('ml_params', {})
            for name, space in ml_param_space.items():
                if space['type'] == 'int':
                    ml_params[name] = trial.suggest_int(name, space['low'], space['high'])
                elif space['type'] == 'float':
                    ml_params[name] = trial.suggest_float(name, space['low'], space['high'], log=space.get('log', False))

            # Create a unique model path for this trial to avoid race conditions
            trial_model_path = Path(self.config['modeling']['model_save_path']) / f"trial_{trial.number}"
            trial_model_path.mkdir(parents=True, exist_ok=True)

            trial_config = self.config.copy()
            trial_config['strategy']['params'] = strategy_params
            trial_config['risk_management'].update(risk_params)
            trial_config['modeling']['model_save_path'] = str(trial_model_path)
            trial_config['modeling'].update(ml_params)
            
            # 1. Feature Engineering for this trial
            feature_agent = FeatureEngineeringAgent(trial_config)
            featured_data = feature_agent.execute(data.copy())

            # 2. Train Model for this trial
            # Note: This assumes the strategy being optimized is an ML strategy.
            # A check might be needed for non-ML strategies.
            if self.strategy_class.__name__ == 'CnnLstmStrategy':
                logging.info(f"Trial {trial.number}: Training ML model with params: {ml_params}")
                model_agent = ModelingAgent(trial_config)
                # Pass ML hyperparameters to the training method
                model_agent.execute(featured_data.copy(), ml_params)

            # 3. Generate Signals
            strategy = self.strategy_class(config=trial_config)
            signals_df = strategy.generate_signals(featured_data)

            # 4. Manage Risk
            risk_agent = RiskManagementAgent(trial_config)
            risk_managed_df = risk_agent.execute(signals_df, trial_config.get('backtesting', {}).get('initial_capital', 100000))

            execution_agent = ExecutionAgent(trial_config)
            executed_df = execution_agent.execute(risk_managed_df)

            backtester = BacktestingAgent(trial_config)
            # Pass the trial to the backtester for pruning
            results = backtester.execute(executed_df, trial)
            
            # Return the specified objective metric, or a very low number if not available
            objective_metric = self.opt_config.get('objective_metric', 'sharpe_ratio')
            return results.get(objective_metric, -np.inf)

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
        
        # Create an Optuna study with a pruner
        pruner = optuna.pruners.MedianPruner()
        study = optuna.create_study(direction='maximize', pruner=pruner)
        
        # Ensure iterative mode is used for optimization to support pruning
        self.config['backtesting']['mode'] = 'iterative'
        logging.info("Set backtesting mode to 'iterative' for optimization.")

        # --- Graceful Shutdown ---
        def signal_handler(sig, frame):
            logging.warning("Shutdown signal received. Asking Optuna to stop...")
            study.stop()
            # Give some time for the running trials to finish
            logging.info("Waiting for running trials to complete...")

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        try:
            # Run the study with parallel jobs
            study.optimize(
                objective_func,
                n_trials=self.n_trials,
                n_jobs=-1  # Use all available CPU cores
            )
        except KeyboardInterrupt:
            logging.warning("Optimization stopped by user (KeyboardInterrupt).")
        finally:
            logging.info("Restoring default signal handlers.")
            signal.signal(signal.SIGINT, signal.SIG_DFL)
            signal.signal(signal.SIGTERM, signal.SIG_DFL)

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

    mock_data_config = {'data_path': 'bkwf_framework/data/EURUSD_m15_2022_2025.parquet'}
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