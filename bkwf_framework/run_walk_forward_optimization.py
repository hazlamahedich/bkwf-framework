import yaml
import argparse
import logging
from pathlib import Path
import pandas as pd

from agents.data_agent import DataAgent
from agents.walk_forward_agent import WalkForwardAgent
from strategies.triple_threat import TripleThreatStrategy
from strategies.bounce_back import BounceBackStrategy
from strategies.cnn_lstm import CnnLstmStrategy

# --- Strategy Mapping ---
STRATEGY_MAP = {
    'triple_threat': TripleThreatStrategy,
    'bounce_back': BounceBackStrategy,
    'cnn_lstm': CnnLstmStrategy,
}

def setup_logging(config):
    """Sets up the logging for the application."""
    log_config = config.get('logging', {})
    level = getattr(logging, log_config.get('level', 'INFO').upper())
    log_file = log_config.get('log_file', 'logs/backtest.log')
    
    # Ensure the directory for the log file exists
    Path(log_file).parent.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, mode='w'),
            logging.StreamHandler()
        ]
    )
    logging.info("Logging configured.")

def main():
    """
    Main function to run the walk-forward optimization.
    """
    parser = argparse.ArgumentParser(description="Run Walk-Forward Optimization for a trading strategy.")
    parser.add_argument('--config', type=str, default='bkwf_framework/configs/config.yaml', help='Path to the configuration file.')
    args = parser.parse_args()

    # --- Load Configuration ---
    try:
        with open(args.config, 'r') as f:
            config = yaml.safe_load(f)
        print("Configuration loaded successfully.")
    except FileNotFoundError:
        print(f"Error: Configuration file not found at {args.config}")
        return
    except Exception as e:
        print(f"Error loading configuration: {e}")
        return

    # --- Setup Logging ---
    setup_logging(config)

    # --- Load Data ---
    logging.info("Loading data...")
    data_agent = DataAgent(config)
    data = data_agent.execute()
    if data.empty:
        logging.error("Data could not be loaded. Exiting.")
        return
    
    # --- Select Strategy ---
    strategy_name = config.get('strategy', {}).get('name', 'triple_threat')
    strategy_class = STRATEGY_MAP.get(strategy_name)
    if not strategy_class:
        logging.error(f"Strategy '{strategy_name}' not found. Please check your config. Exiting.")
        return
    logging.info(f"Selected strategy: {strategy_name}")

    # --- Execute Walk-Forward Optimization ---
    logging.info("Initializing Walk-Forward Agent...")
    walk_forward_agent = WalkForwardAgent(config, strategy_class)
    results = walk_forward_agent.execute(data)

    # --- Report and Save Results ---
    logging.info("--- Final Walk-Forward Optimization Results ---")
    summary = results.get('summary', {})
    if summary:
        for key, value in summary.items():
            if isinstance(value, float):
                logging.info(f"{key.replace('_', ' ').title()}: {value:.4f}")
            else:
                logging.info(f"{key.replace('_', ' ').title()}: {value}")
        
        # Save the final combined trades and summary report
        reports_path = Path(config.get('reporting', {}).get('report_path', 'bkwf_framework/reports'))
        reports_path.mkdir(exist_ok=True)
        
        trades_path = reports_path / f"{strategy_name}_walk_forward_trades.csv"
        results['trades'].to_csv(trades_path)
        logging.info(f"Walk-forward trades saved to {trades_path}")

        summary_path = reports_path / f"{strategy_name}_walk_forward_summary.json"
        pd.Series(summary).to_json(summary_path, indent=4)
        logging.info(f"Walk-forward summary saved to {summary_path}")
    else:
        logging.error("Walk-forward analysis did not produce a final summary.")

if __name__ == '__main__':
    main()