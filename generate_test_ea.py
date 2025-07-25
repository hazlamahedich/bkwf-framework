import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent
sys.path.append(str(project_root))

from ml_backtester.agents.export_agent import ExportAgent

def generate_test_ea():
    """
    Generates a test EA file for the cnn_lstm strategy without running a full backtest.
    """
    # 1. Mock configuration
    mock_config = {
        'export': {
            'path': 'ml_backtester/exports',
            'formats': ['mt5']
        },
        'risk_management': {
            'risk_per_trade': 0.01
        },
        'modeling': {
            'look_back': 96
        },
        'api_server': {
            'port': 5001
        },
        'symbol': 'EURUSD',
        'timeframe': 'H1'
    }

    # 2. Mock best parameters
    mock_best_params = {
        'sl_atr_multiplier': 2.5,
        'tp_atr_multiplier': 3.5,
    }

    # 3. Initialize the ExportAgent
    export_agent = ExportAgent(config=mock_config)

    # 4. Generate the MQL5 code
    strategy_name = 'cnn_lstm_strategy'
    mt5_code = export_agent._generate_mt5_for_cnn_lstm(strategy_name, mock_best_params)

    # 5. Save the code to a test file
    export_path = Path(mock_config['export']['path'])
    export_path.mkdir(exist_ok=True)
    file_path = export_path / 'test_cnn_lstm_ea.mq5'
    
    with open(file_path, 'w') as f:
        f.write(mt5_code)
        
    print(f"Successfully generated test EA file at: {file_path}")

if __name__ == '__main__':
    generate_test_ea()