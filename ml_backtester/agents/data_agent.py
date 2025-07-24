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

    def execute(self) -> pd.DataFrame:
        """
        Executes the data loading process.

        Returns:
            pd.DataFrame: A pandas DataFrame containing the loaded OHLCV data,
                          with a datetime index.
        
        Raises:
            FileNotFoundError: If the data file specified in the config does not exist.
        """
        logging.info(f"DataAgent: Loading data from '{self.data_path}'...")

        if not self.data_path.exists():
            logging.error(f"Data file not found at: {self.data_path}")
            raise FileNotFoundError(f"Data file not found at: {self.data_path}")

        try:
            data = pd.read_parquet(self.data_path)
            logging.info(f"DataAgent: Successfully loaded {len(data)} data points.")
            # Basic validation: ensure essential columns are present
            required_columns = {'open', 'high', 'low', 'close'}
            if not required_columns.issubset(data.columns):
                raise ValueError(f"Data loaded from {self.data_path} is missing one of the required columns: {required_columns}")
            
            return data
        except Exception as e:
            logging.error(f"DataAgent: Failed to load or validate data from {self.data_path}. Error: {e}")
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
