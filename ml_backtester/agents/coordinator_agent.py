import yaml
from typing import Dict, Any
import logging

from .data_agent import DataAgent
from .feature_engineering_agent import FeatureEngineeringAgent
from .strategy_agent import StrategyAgent
from .risk_management_agent import RiskManagementAgent
from .execution_agent import ExecutionAgent
from .iterative_execution_agent import IterativeExecutionAgent
from .backtesting_agent import BacktestingAgent
from .analytics_agent import AnalyticsAgent
from .optimization_agent import OptimizationAgent
from .modeling_agent import ModelingAgent
from .export_agent import ExportAgent

class CoordinatorAgent:
    """
    The master agent that orchestrates the entire backtesting pipeline.
    """

    def __init__(self, config_path: str):
        """
        Initializes the CoordinatorAgent.

        Args:
            config_path (str): The path to the main YAML configuration file.
        """
        self.config = self._load_config(config_path)
        self._setup_logging()

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Loads the YAML configuration file."""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    def _setup_logging(self):
        """Configures the logging for the framework."""
        logging.basicConfig(
            level=self.config.get('logging', {}).get('level', 'INFO'),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    def run(self):
        """
        Executes the full pipeline based on the mode in the config.
        """
        run_mode = self.config.get('run_mode', 'backtest') # 'backtest', 'optimize', 'train', or 'optimize_and_backtest'
        
        logging.info(f"--- Starting Pipeline in '{run_mode}' mode ---")

        # --- Common Steps: Data Loading and Feature Engineering ---
        data_agent = DataAgent(self.config)
        market_data = data_agent.execute()

        feature_agent = FeatureEngineeringAgent(self.config)
        featured_data = feature_agent.execute(market_data)

        if run_mode == 'train':
            # --- Training Mode ---
            modeling_agent = ModelingAgent(self.config)
            modeling_agent.execute(featured_data)
        
        elif run_mode == 'optimize':
            # --- Optimization Mode ---
            strategy_agent_for_opt = StrategyAgent(self.config)
            strategy_class = strategy_agent_for_opt._load_strategy_class()
            
            optimizer = OptimizationAgent(self.config, strategy_class)
            optimization_results = optimizer.execute(featured_data)
            
            analytics_agent = AnalyticsAgent(self.config)
            analytics_agent.execute(optimization_results, self.config['strategy']['name'], is_optimization=True)

        elif run_mode == 'backtest':
            # --- Backtesting Mode ---
            strategy_names = self.config['strategy']['name']
            if not isinstance(strategy_names, list):
                strategy_names = [strategy_names]

            all_results = {}
            for strategy_name in strategy_names:
                logging.info(f"--- Running backtest for strategy: {strategy_name} ---")
                
                # Create a temporary config for this strategy
                strategy_config = self.config.copy()
                strategy_config['strategy']['name'] = strategy_name

                strategy_agent = StrategyAgent(strategy_config)
                signals_df = strategy_agent.execute(featured_data.copy())

                risk_agent = RiskManagementAgent(strategy_config)
                risk_managed_df = risk_agent.execute(signals_df, self.config['backtesting']['initial_capital'])

                backtester = BacktestingAgent(strategy_config)
                
                # The backtester now handles which execution model to use.
                # For iterative mode, it uses the IterativeExecutionAgent internally.
                # For vectorized, it uses its own internal logic.
                # We just need to pass the risk-managed data to it.
                backtest_results = backtester.execute(risk_managed_df)
                
                all_results[strategy_name] = backtest_results

            analytics_agent = AnalyticsAgent(self.config)
            analytics_agent.execute(all_results, "comparison")
        
        elif run_mode == 'optimize_and_backtest':
            # --- Optimize and Backtest Mode ---
            strategy_names = self.config['strategy']['name']
            if not isinstance(strategy_names, list):
                strategy_names = [strategy_names]

            all_results = {}
            for strategy_name in strategy_names:
                logging.info(f"--- Optimizing and backtesting strategy: {strategy_name} ---")
                
                # Create a temporary config for this strategy
                strategy_config = self.config.copy()
                strategy_config['strategy']['name'] = strategy_name

                # Optimize the strategy
                strategy_agent_for_opt = StrategyAgent(strategy_config)
                strategy_class = strategy_agent_for_opt._load_strategy_class()
                
                optimizer = OptimizationAgent(strategy_config, strategy_class)
                optimization_results = optimizer.execute(featured_data.copy())
                
                # Update the config with the best parameters
                best_params = optimization_results.get('best_params', {})
                strategy_config['risk_management'].update(best_params)
                logging.info(f"Running final backtest with optimal params: {best_params}")

                # Run the final backtest
                strategy_agent = StrategyAgent(strategy_config)
                signals_df = strategy_agent.execute(featured_data.copy())

                risk_agent = RiskManagementAgent(strategy_config)
                risk_managed_df = risk_agent.execute(signals_df, self.config['backtesting']['initial_capital'])

                backtester = BacktestingAgent(strategy_config)
                backtest_results = backtester.execute(risk_managed_df)
                
                all_results[strategy_name] = {
                    "backtest_results": backtest_results,
                    "best_params": best_params,
                    "strategy_config": strategy_config
                }

            analytics_agent = AnalyticsAgent(self.config)
            # The execute method now returns the best strategy name
            best_strategy_name = analytics_agent.execute(
                {k: v['backtest_results'] for k, v in all_results.items()},
                "optimized_comparison"
            )

            # --- Exporting Step for the Best Strategy ---
            if best_strategy_name and self.config.get('export', {}).get('enabled', False):
                logging.info(f"--- Exporting best strategy: {best_strategy_name} ---")
                best_strategy_data = all_results[best_strategy_name]
                export_agent = ExportAgent(best_strategy_data['strategy_config'])
                export_agent.execute(
                    best_strategy_name,
                    best_strategy_data['best_params'],
                    best_strategy_data['backtest_results']
                )
            
        else:
            raise ValueError(f"Invalid run_mode: '{run_mode}'. Must be 'backtest', 'optimize', 'train', or 'optimize_and_backtest'.")

        logging.info(f"--- Pipeline finished '{run_mode}' mode ---")