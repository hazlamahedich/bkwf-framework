import yaml
import json
from typing import Dict, Any, Optional
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

    def __init__(self, config_path: str, params_file: Optional[str] = None):
        """
        Initializes the CoordinatorAgent.

        Args:
            config_path (str): The path to the main YAML configuration file.
            params_file (Optional[str]): Path to a JSON file with optimal parameters.
        """
        self.config = self._load_config(config_path)
        if params_file:
            self._override_config_with_params(params_file)
        self._setup_logging()

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Loads the YAML configuration file."""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    def _override_config_with_params(self, params_file: str):
        """Overrides config with parameters from a JSON file."""
        logging.info(f"Loading optimal parameters from {params_file}...")
        try:
            with open(params_file, 'r') as f:
                params = json.load(f)
            
            best_params = params.get('best_params', {})
            
            # Separate strategy and risk params
            strategy_params = {k: v for k, v in best_params.items() if k not in ['sl_atr_multiplier', 'tp_atr_multiplier', 'trailing_stop_atr_multiplier']}
            risk_params = {k: v for k, v in best_params.items() if k in ['sl_atr_multiplier', 'tp_atr_multiplier', 'trailing_stop_atr_multiplier']}

            if 'params' not in self.config['strategy']:
                self.config['strategy']['params'] = {}
            self.config['strategy']['params'].update(strategy_params)
            self.config['risk_management'].update(risk_params)
            
            logging.info(f"Config overridden with parameters: {best_params}")

        except FileNotFoundError:
            logging.error(f"Parameters file not found: {params_file}. Using default config.")
        except Exception as e:
            logging.error(f"Error loading parameters file: {e}. Using default config.")

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
        market_data, symbol, timeframe = data_agent.execute()
        
        # Update the main config with the loaded symbol and timeframe
        self.config['symbol'] = symbol
        self.config['timeframe'] = timeframe

        if run_mode == 'train':
            feature_agent = FeatureEngineeringAgent(self.config)
            featured_data = feature_agent.execute(market_data)
            modeling_agent = ModelingAgent(self.config)
            modeling_agent.execute(featured_data)
        
        elif run_mode == 'optimize':
            strategy_agent_for_opt = StrategyAgent(self.config)
            strategy_class = strategy_agent_for_opt._load_strategy_class()
            optimizer = OptimizationAgent(self.config, strategy_class)
            optimization_results = optimizer.execute(market_data)
            analytics_agent = AnalyticsAgent(self.config)
            analytics_agent.execute(optimization_results, self.config['strategy']['name'], is_optimization=True)

        elif run_mode == 'backtest':
            feature_agent = FeatureEngineeringAgent(self.config)
            featured_data = feature_agent.execute(market_data)
            strategy_names = self.config['strategy']['name']
            if not isinstance(strategy_names, list):
                strategy_names = [strategy_names]
            all_results = {}
            for strategy_name in strategy_names:
                logging.info(f"--- Running backtest for strategy: {strategy_name} ---")
                strategy_config = self.config.copy()
                strategy_config['strategy']['name'] = strategy_name
                strategy_agent = StrategyAgent(strategy_config)
                signals_df = strategy_agent.execute(featured_data.copy())
                risk_agent = RiskManagementAgent(strategy_config)
                risk_managed_df = risk_agent.execute(signals_df, self.config['backtesting']['initial_capital'])
                backtester = BacktestingAgent(strategy_config)
                backtest_results = backtester.execute(risk_managed_df)
                all_results[strategy_name] = backtest_results
            analytics_agent = AnalyticsAgent(self.config)
            analytics_agent.execute(all_results, "comparison")
        
        elif run_mode == 'optimize_and_backtest':
            strategy_names = self.config['strategy']['name']
            if not isinstance(strategy_names, list):
                strategy_names = [strategy_names]
            all_results = {}
            for strategy_name in strategy_names:
                logging.info(f"--- Processing strategy: {strategy_name} ---")
                
                strategy_config = self.config.copy()
                strategy_config['strategy']['name'] = strategy_name

                # Skip optimization for the ML-based strategy as it requires a fixed, pre-trained model
                if strategy_name == 'cnn_lstm_strategy':
                    logging.info(f"Skipping optimization for '{strategy_name}'. Resetting to default parameters.")
                    best_params = {}
                    # IMPORTANT: Reset strategy params to default for the ML model
                    if 'params' in strategy_config['strategy']:
                        strategy_config['strategy']['params'] = {}
                else:
                    # Optimize the strategy
                    strategy_agent_for_opt = StrategyAgent(strategy_config)
                    strategy_class = strategy_agent_for_opt._load_strategy_class()
                    
                    optimizer = OptimizationAgent(strategy_config, strategy_class)
                    optimization_results = optimizer.execute(market_data.copy())
                    best_params = optimization_results.get('best_params', {})
                    
                    # Update config with best params
                    strategy_params = {k: v for k, v in best_params.items() if k not in ['sl_atr_multiplier', 'tp_atr_multiplier', 'trailing_stop_atr_multiplier']}
                    risk_params = {k: v for k, v in best_params.items() if k in ['sl_atr_multiplier', 'tp_atr_multiplier', 'trailing_stop_atr_multiplier']}
                    
                    if 'params' not in strategy_config['strategy']:
                        strategy_config['strategy']['params'] = {}
                    strategy_config['strategy']['params'].update(strategy_params)
                    strategy_config['risk_management'].update(risk_params)

                logging.info(f"Running final backtest for '{strategy_name}' with params: {best_params}")

                # Run feature engineering with the correct (optimized or default) parameters
                final_feature_agent = FeatureEngineeringAgent(strategy_config)
                final_featured_data = final_feature_agent.execute(market_data.copy())

                # Run the final backtest
                strategy_agent = StrategyAgent(strategy_config)
                signals_df = strategy_agent.execute(final_featured_data)
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
            best_strategy_name = analytics_agent.execute(
                all_results, "optimized_comparison"
            )

            if best_strategy_name and self.config.get('export', {}).get('enabled', False):
                logging.info(f"--- Exporting best strategy: {best_strategy_name} ---")
                best_strategy_data = all_results[best_strategy_name]
                export_agent = ExportAgent(best_strategy_data['strategy_config'])
                export_agent.execute(
                    best_strategy_name,
                    best_strategy_data['best_params'],
                    best_strategy_data['backtest_results']
                )
            
        elif run_mode == 'train_optimize_and_backtest':
            # 1. Train the model first
            logging.info("--- Starting Training Phase ---")
            feature_agent = FeatureEngineeringAgent(self.config)
            featured_data = feature_agent.execute(market_data.copy())
            modeling_agent = ModelingAgent(self.config)
            modeling_agent.execute(featured_data)
            logging.info("--- Finished Training Phase ---")

            # 2. Proceed with optimization and backtesting
            logging.info("--- Starting Optimization and Backtest Phase ---")
            strategy_names = self.config['strategy']['name']
            if not isinstance(strategy_names, list):
                strategy_names = [strategy_names]
            all_results = {}
            for strategy_name in strategy_names:
                logging.info(f"--- Processing strategy: {strategy_name} ---")
                
                strategy_config = self.config.copy()
                strategy_config['strategy']['name'] = strategy_name

                # Unlike the 'optimize_and_backtest' mode, we don't skip optimization here
                # because the user might want to optimize risk parameters even for the ML model.
                strategy_agent_for_opt = StrategyAgent(strategy_config)
                strategy_class = strategy_agent_for_opt._load_strategy_class()
                
                optimizer = OptimizationAgent(strategy_config, strategy_class)
                optimization_results = optimizer.execute(market_data.copy())
                best_params = optimization_results.get('best_params', {})
                
                # Update config with best params
                strategy_params = {k: v for k, v in best_params.items() if k not in ['sl_atr_multiplier', 'tp_atr_multiplier', 'trailing_stop_atr_multiplier']}
                risk_params = {k: v for k, v in best_params.items() if k in ['sl_atr_multiplier', 'tp_atr_multiplier', 'trailing_stop_atr_multiplier']}
                
                if 'params' not in strategy_config['strategy']:
                    strategy_config['strategy']['params'] = {}
                strategy_config['strategy']['params'].update(strategy_params)
                strategy_config['risk_management'].update(risk_params)

                logging.info(f"Running final backtest for '{strategy_name}' with params: {best_params}")

                # Run feature engineering with the correct (optimized or default) parameters
                final_feature_agent = FeatureEngineeringAgent(strategy_config)
                final_featured_data = final_feature_agent.execute(market_data.copy())

                # Run the final backtest
                strategy_agent = StrategyAgent(strategy_config)
                signals_df = strategy_agent.execute(final_featured_data)
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
            best_strategy_name = analytics_agent.execute(
                all_results, "optimized_comparison"
            )

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
            raise ValueError(f"Invalid run_mode: '{run_mode}'. Must be 'backtest', 'optimize', 'train', 'optimize_and_backtest', or 'train_optimize_and_backtest'.")

        logging.info(f"--- Pipeline finished '{run_mode}' mode ---")