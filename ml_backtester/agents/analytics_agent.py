import pandas as pd
import plotly.graph_objects as go
from typing import Dict, Any
import logging
from pathlib import Path

class AnalyticsAgent:
    """
    Agent for visualizing backtest results and generating reports.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initializes the AnalyticsAgent.

        Args:
            config (Dict[str, Any]): The main configuration dictionary.
        """
        self.config = config
        self.analytics_config = self.config.get('analytics', {})
        self.report_path = Path(self.analytics_config.get('report_path', 'ml_backtester/reports'))
        self.report_path.mkdir(exist_ok=True)
        self.symbol = self.config.get('symbol')
        self.timeframe = self.config.get('timeframe')

    def execute(self, results: Dict[str, Any], report_name: str, is_optimization: bool = False) -> str:
        """
        Generates and saves analytics reports and visualizations.
        Args:
            results (Dict[str, Any]): A dictionary of results.
            report_name (str): The base name for the report file(s).
            is_optimization (bool): Flag to indicate if the results are from an optimization run.
        Returns:
            str: The name of the best performing strategy, or None.
        """
        logging.info("AnalyticsAgent: Generating reports...")
        best_strategy = None

        # In a comparison run, results dict contains strategy names as keys
        if not is_optimization and isinstance(results, dict) and any(isinstance(v, dict) for v in results.values()):
            # This handles both regular comparison and post-optimization comparison
            for strategy_name, strategy_results in results.items():
                if "equity_curve" in strategy_results:
                    self._plot_equity_curve(strategy_results['equity_curve'], strategy_name)
                if "best_params" in strategy_results:
                    self._save_optimization_results(strategy_results, strategy_name)
            
            best_strategy = self._generate_comparison_report(results, report_name)

        elif is_optimization: # Direct optimization run
            self._save_optimization_results(results, report_name)
        
        elif "equity_curve" in results: # Single backtest run
            self._plot_equity_curve(results['equity_curve'], report_name)

        logging.info(f"Reports saved to '{self.report_path}'.")
        return best_strategy

    def _plot_equity_curve(self, equity_curve: pd.Series, strategy_name: str):
        """
        Creates and saves an interactive plot of the equity curve.
        """
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=equity_curve.index, y=equity_curve.values, mode='lines', name='Equity'))
        
        fig.update_layout(
            title=f'Equity Curve for Strategy: {strategy_name}',
            xaxis_title='Date',
            yaxis_title='Equity',
            template='plotly_dark'
        )
        
        filename_base = self._get_filename_base(strategy_name)
        report_file = self.report_path / f"{filename_base}_equity_curve.html"
        fig.write_html(report_file)
        logging.info(f"Equity curve plot saved to '{report_file}'.")

    def _save_optimization_results(self, results: Dict[str, Any], strategy_name: str):
        """
        Saves the best parameters from an optimization run to a JSON file.
        """
        import json
        
        best_params = results.get('best_params')
        if best_params:
            filename_base = self._get_filename_base(strategy_name)
            report_file = self.report_path / f"{filename_base}_best_params.json"
            with open(report_file, 'w') as f:
                json.dump(best_params, f, indent=4)
            logging.info(f"Best optimization parameters saved to '{report_file}'.")

    def _generate_comparison_report(self, all_results: Dict[str, Any], report_name: str) -> str:
        """
        Generates a comparison report and identifies the best strategy.

        Returns:
            str: The name of the best strategy based on Sharpe Ratio.
        """
        comparison_data = []
        for strategy_name, results in all_results.items():
            metrics = results.get('formatted_metrics', {})
            metrics['Strategy'] = strategy_name
            # Ensure Sharpe Ratio is a float for comparison
            try:
                metrics['Sharpe Ratio'] = float(metrics.get('Sharpe Ratio', '0'))
            except (ValueError, TypeError):
                metrics['Sharpe Ratio'] = 0.0
            comparison_data.append(metrics)
        
        if not comparison_data:
            return None

        df = pd.DataFrame(comparison_data)
        df = df.set_index('Strategy')
        
        filename_base = self._get_filename_base(report_name)
        report_file = self.report_path / f"{filename_base}_report.csv"
        df.to_csv(report_file)
        logging.info(f"Comparison report saved to '{report_file}'.")

        # Determine the best strategy
        best_strategy = df['Sharpe Ratio'].idxmax()
        logging.info(f"Best performing strategy: '{best_strategy}' with Sharpe Ratio: {df.loc[best_strategy]['Sharpe Ratio']:.2f}")
        
        return best_strategy

    def _get_filename_base(self, name: str) -> str:
        """Constructs a filename base from symbol, timeframe, and a given name."""
        parts = []
        if self.symbol:
            parts.append(self.symbol)
        if self.timeframe:
            parts.append(self.timeframe)
        parts.append(name)

        # If the strategy is the ML one, add the model type to the filename
        if 'cnn_lstm_strategy' in name:
            model_type = self.config.get('modeling', {}).get('model_type')
            if model_type:
                parts.append(model_type)
                
        return "_".join(parts)

if __name__ == '__main__':
    # Example usage for testing the AnalyticsAgent
    from ..agents.data_agent import DataAgent
    from ..agents.feature_engineering_agent import FeatureEngineeringAgent
    from ..agents.strategy_agent import StrategyAgent
    from ..agents.backtesting_agent import BacktestingAgent

    mock_data_config = {'data_path': 'ml_backtester/data/EURUSD_m15_2022_2025.parquet'}
    mock_feature_config = {'feature_engineering': {'indicators': [{'name': 'ema', 'params': {'length': 200}}, {'name': 'macd'}, {'name': 'stoch'}]}}
    mock_strategy_config = {'strategy': {'name': 'triple_threat'}}
    mock_backtest_config = {'backtesting': {'mode': 'vectorized'}}
    mock_analytics_config = {'analytics': {'report_path': 'ml_backtester/reports'}}

    try:
        df = DataAgent(config=mock_data_config).execute()
        featured_df = FeatureEngineeringAgent(config=mock_feature_config).execute(df)
        signals_df = StrategyAgent(config=mock_strategy_config).execute(featured_df)
        results = BacktestingAgent(config=mock_backtest_config).execute(signals_df)
        
        analytics_agent = AnalyticsAgent(config=mock_analytics_config)
        analytics_agent.execute(results, mock_strategy_config['strategy']['name'])

        print("\nAnalyticsAgent executed successfully.")
        print(f"Report saved in '{mock_analytics_config['analytics']['report_path']}'")

    except Exception as e:
        print(f"An error occurred during testing: {e}")