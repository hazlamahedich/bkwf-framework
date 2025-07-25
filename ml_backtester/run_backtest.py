import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

import argparse
import warnings
from ml_backtester.agents.coordinator_agent import CoordinatorAgent

# Suppress the specific UserWarning from pandas_ta
warnings.filterwarnings(
    "ignore",
    category=UserWarning,
    message="pkg_resources is deprecated as an API.*"
)

def main():
    """
    Main entry point for running the backtesting framework.
    """
    parser = argparse.ArgumentParser(description="Run a backtest from a configuration file.")
    parser.add_argument(
        '--config',
        type=str,
        default='ml_backtester/configs/config.yaml',
        help='Path to the configuration YAML file.'
    )
    parser.add_argument(
        '--params_file',
        type=str,
        default=None,
        help='Optional path to a JSON file with optimal parameters to override the config.'
    )
    args = parser.parse_args()

    # Initialize and run the coordinator
    coordinator = CoordinatorAgent(config_path=args.config, params_file=args.params_file)
    coordinator.run()

if __name__ == '__main__':
    main()