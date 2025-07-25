import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, Callable
from sklearn.model_selection import TimeSeriesSplit

from .optimization_agent import OptimizationAgent
from .backtesting_agent import BacktestingAgent
from .feature_engineering_agent import FeatureEngineeringAgent
from .risk_management_agent import RiskManagementAgent
from .execution_agent import ExecutionAgent

class WalkForwardAgent:
    """
    Agent for performing walk-forward optimization and validation.
    """

    def __init__(self, config: Dict[str, Any], strategy_class: Callable):
        """
        Initializes the WalkForwardAgent.

        Args:
            config (Dict[str, Any]): The main configuration dictionary.
            strategy_class (Callable): The strategy class to be optimized and validated.
        """
        self.config = config
        self.strategy_class = strategy_class
        self.wf_config = self.config.get('walk_forward', {})
        self.n_splits = self.wf_config.get('n_splits', 5)
        
        if self.n_splits <= 1:
            raise ValueError("n_splits for walk-forward validation must be greater than 1.")

    def execute(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Executes the walk-forward validation process.

        The data is split into n_splits folds. For each fold, we train on all
        past data and test on the current fold. This simulates a realistic
        trading scenario where the model is periodically retrained.

        Args:
            data (pd.DataFrame): The entire dataset.

        Returns:
            Dict[str, Any]: A dictionary containing aggregated performance metrics
                           and results from each walk-forward cycle.
        """
        logging.info(f"Starting walk-forward validation with {self.n_splits} splits.")
        
        tscv = TimeSeriesSplit(n_splits=self.n_splits)
        
        all_results = []
        all_trades = []
        
        for i, (train_index, test_index) in enumerate(tscv.split(data)):
            logging.info(f"--- Walk-Forward Fold {i+1}/{self.n_splits} ---")
            
            train_data = data.iloc[train_index]
            test_data = data.iloc[test_index]
            
            logging.info(f"Training Period: {train_data.index.min()} to {train_data.index.max()}")
            logging.info(f"Testing Period:  {test_data.index.min()} to {test_data.index.max()}")

            # 1. Optimize the strategy on the training data
            optimization_agent = OptimizationAgent(self.config, self.strategy_class)
            opt_results = optimization_agent.execute(train_data.copy())
            best_params = opt_results['best_params']
            
            logging.info(f"Best parameters found for this fold: {best_params}")

            # 2. Backtest the strategy with the best parameters on the out-of-sample test data
            trial_config = self.config.copy()
            
            # Separate risk and strategy params from the optimized set
            strategy_params = {}
            risk_params = {}
            for name, value in best_params.items():
                if name in ['sl_atr_multiplier', 'tp_atr_multiplier', 'trailing_stop_atr_multiplier']:
                    risk_params[name] = value
                else:
                    strategy_params[name] = value
            
            trial_config['strategy']['params'] = strategy_params
            trial_config['risk_management'].update(risk_params)

            # Run the full backtesting pipeline on the test data
            feature_agent = FeatureEngineeringAgent(trial_config)
            featured_data = feature_agent.execute(test_data.copy())

            strategy = self.strategy_class(config=trial_config)
            signals_df = strategy.generate_signals(featured_data)

            risk_agent = RiskManagementAgent(trial_config)
            risk_managed_df = risk_agent.execute(signals_df, self.config['backtesting']['initial_capital'])

            execution_agent = ExecutionAgent(trial_config)
            executed_df = execution_agent.execute(risk_managed_df)

            backtester = BacktestingAgent(trial_config)
            fold_results = backtester.execute(executed_df)
            
            all_results.append(fold_results)
            if 'trades' in fold_results and not fold_results['trades'].empty:
                all_trades.append(fold_results['trades'])

            logging.info(f"Fold {i+1} Results: Sharpe Ratio = {fold_results.get('sharpe_ratio', 'N/A'):.2f}, "
                         f"Profit = {fold_results.get('total_profit', 'N/A'):.2f}")

        # 3. Aggregate results from all folds
        if not all_trades:
            logging.warning("No trades were executed during the entire walk-forward analysis.")
            return {"summary": "No trades executed.", "folds": all_results}

        combined_trades = pd.concat(all_trades)
        
        # Recalculate overall portfolio metrics based on combined trades
        final_backtester = BacktestingAgent(self.config)
        final_metrics = final_backtester.calculate_metrics(combined_trades, self.config['backtesting']['initial_capital'])

        logging.info("--- Walk-Forward Validation Complete ---")
        logging.info(f"Aggregated Sharpe Ratio: {final_metrics.get('sharpe_ratio', 'N/A'):.2f}")
        logging.info(f"Aggregated Total Profit: {final_metrics.get('total_profit', 'N/A'):.2f}")
        logging.info(f"Total Trades: {final_metrics.get('total_trades', 'N/A')}")

        return {
            "summary": final_metrics,
            "folds": all_results,
            "trades": combined_trades
        }