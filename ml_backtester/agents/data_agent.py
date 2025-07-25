import pandas as pd
from pathlib import Path
import logging

class DataAgent:
    """
    Agent responsible for loading historical market data.

    This agent loads data from a specified Parquet file, which is a high-performance,
    columnar storage format ideal for large datasets.
    """

    def __init__(self, config: dict):
        """
        Initializes the DataAgent with a configuration dictionary.

        Args:
            config (dict): A dictionary containing the configuration for the agent.
                           Expected key: 'data_path'.
        """
        self.config = config
        self.data_path = Path(self.config['data_path'])

    def execute(self) -> tuple[pd.DataFrame, str, str]:
        """
        Executes the data loading process and extracts symbol and timeframe.

        Returns:
            tuple[pd.DataFrame, str, str]: A tuple containing:
                - pd.DataFrame: The loaded OHLCV data.
                - str: The symbol (e.g., 'EURUSD').
                - str: The timeframe (e.g., 'm15').
        
        Raises:
            FileNotFoundError: If the data file does not exist.
            ValueError: If the filename format is incorrect or data is invalid.
        """
        logging.info(f"DataAgent: Loading data from '{self.data_path}'...")

        if not self.data_path.exists():
            logging.error(f"Data file not found at: {self.data_path}")
            raise FileNotFoundError(f"Data file not found at: {self.data_path}")

        try:
            # Extract symbol and timeframe from filename
            # Expected format: SYMBOL_TIMEFRAME_... .parquet
            parts = self.data_path.stem.split('_')
            if len(parts) < 2:
                raise ValueError(f"Invalid filename format: '{self.data_path.name}'. Expected 'SYMBOL_TIMEFRAME_...'.")
            symbol = parts[0]
            timeframe = parts[1]
            logging.info(f"DataAgent: Extracted Symbol='{symbol}', Timeframe='{timeframe}'")

            data = pd.read_parquet(self.data_path)
            logging.info(f"DataAgent: Successfully loaded {len(data)} data points.")
            
            required_columns = {'open', 'high', 'low', 'close'}
            if not required_columns.issubset(data.columns):
                raise ValueError(f"Data loaded from {self.data_path} is missing required columns: {required_columns}")
            
            # Standardize volume column
            volume_cols = ['vol', 'volume', 'tick_volume']
            for col in volume_cols:
                if col in data.columns:
                    data.rename(columns={col: 'volume'}, inplace=True)
                    logging.info(f"DataAgent: Standardized volume column from '{col}' to 'volume'.")
                    break
            
            if 'volume' not in data.columns:
                logging.warning("DataAgent: Volume column not found. Some indicators may not be available.")

            return data, symbol, timeframe
        except Exception as e:
            logging.error(f"DataAgent: Failed to process data from {self.data_path}. Error: {e}")
            raise

if __name__ == '__main__':
    # Example usage for testing the DataAgent directly
    
    # 1. Define a mock configuration
    mock_config = {
        'data_path': 'ml_backtester/data/EURUSD_m15_2022_2025.parquet'
    }

    # 2. Initialize the agent
    data_agent = DataAgent(config=mock_config)

    # 3. Execute the agent
    try:
        df = data_agent.execute()
        print("DataAgent executed successfully.")
        print("Loaded DataFrame info:")
        df.info()
        print("\nFirst 5 rows:")
        print(df.head())
        print("\nLast 5 rows:")
        print(df.tail())
    except (FileNotFoundError, ValueError) as e:
        print(f"An error occurred: {e}")
