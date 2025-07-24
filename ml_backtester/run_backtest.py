import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

import argparse
from ml_backtester.agents.coordinator_agent import CoordinatorAgent

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
    args = parser.parse_args()

    # Initialize and run the coordinator
    coordinator = CoordinatorAgent(config_path=args.config)
    coordinator.run()

if __name__ == '__main__':
    main()