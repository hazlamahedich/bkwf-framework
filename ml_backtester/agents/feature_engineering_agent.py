import pandas as pd
import pandas_ta as ta
from sklearn.preprocessing import StandardScaler
import logging
from typing import List, Dict, Any

# Use a relative import for testing within the same package
from .data_agent import DataAgent

class FeatureEngineeringAgent:
    """
    Agent for computing technical indicators and scaling features.

    This agent takes raw OHLCV data and enriches it with technical indicators
    specified in the configuration. It can also scale the data for use in
    machine learning models.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initializes the FeatureEngineeringAgent.

        Args:
            config (Dict[str, Any]): Configuration dictionary. Expected keys:
                'feature_engineering': {
                    'indicators': [
                        {'name': 'ema', 'params': {'length': 200}},
                        {'name': 'macd', 'params': {}},
                        ...
                    ],
                    'scaling': 'standard' or None
                }
        """
        self.config = config.get('feature_engineering', {})
        self.indicators = self.config.get('indicators', [])
        self.scaling_method = self.config.get('scaling', None)

    def execute(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Applies feature engineering to the input data.

        Args:
            data (pd.DataFrame): The input OHLCV data.

        Returns:
            pd.DataFrame: The data enriched with new features.
        """
        logging.info("FeatureEngineeringAgent: Starting feature generation...")
        
        if not isinstance(data, pd.DataFrame):
            raise TypeError("Input data must be a pandas DataFrame.")

        # Manually calculate indicators to avoid TA-Lib issues and match trained model features
        for indicator in self.indicators:
            name = indicator.get('name')
            params = indicator.get('params', {})
            if name == 'ema':
                length = params.get('length', 200)
                data[f"EMA_{length}"] = data['close'].ewm(span=length, adjust=False).mean()
            elif name == 'macd':
                fast = params.get('fast', 12)
                slow = params.get('slow', 26)
                signal_len = params.get('signal', 9)
                exp1 = data['close'].ewm(span=fast, adjust=False).mean()
                exp2 = data['close'].ewm(span=slow, adjust=False).mean()
                macd = exp1 - exp2
                signal = macd.ewm(span=signal_len, adjust=False).mean()
                histogram = macd - signal
                data[f'MACD_{fast}_{slow}_{signal_len}'] = macd
                data[f'MACDh_{fast}_{slow}_{signal_len}'] = histogram
                data[f'MACDs_{fast}_{slow}_{signal_len}'] = signal
            elif name == 'rsi':
                length = params.get('length', 14)
                delta = data['close'].diff()
                gain = delta.where(delta > 0, 0)
                loss = -delta.where(delta < 0, 0)
                avg_gain = gain.ewm(com=length - 1, min_periods=length).mean()
                avg_loss = loss.ewm(com=length - 1, min_periods=length).mean()
                rs = avg_gain / avg_loss
                data[f"RSI_{length}"] = 100 - (100 / (1 + rs))
            elif name == 'stoch':
                k = params.get('k', 14)
                d = params.get('d', 3)
                smooth_k = params.get('smooth_k', 3)
                low_min = data['low'].rolling(window=k).min()
                high_max = data['high'].rolling(window=k).max()
                stoch_k_line = 100 * ((data['close'] - low_min) / (high_max - low_min))
                data[f"STOCHk_{k}_{d}_{smooth_k}"] = stoch_k_line.rolling(window=smooth_k).mean()
                data[f"STOCHd_{k}_{d}_{smooth_k}"] = data[f"STOCHk_{k}_{d}_{smooth_k}"].rolling(window=d).mean()
            elif name == 'atr':
                length = params.get('length', 14)
                high_low = data['high'] - data['low']
                high_close = (data['high'] - data['close'].shift()).abs()
                low_close = (data['low'] - data['close'].shift()).abs()
                tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
                atr = tr.ewm(span=length, adjust=False).mean()
                data[f"ATRr_{length}"] = (atr / data['close']) * 100 # ATR Percent to match original

        # Drop rows with NaNs created by indicators
        data.dropna(inplace=True)

        if self.scaling_method == 'standard':
            logging.info("Applying StandardScaler to features.")
            scaler = StandardScaler()
            # Scale all columns except the original OHLCV for clarity
            feature_cols = [col for col in data.columns if col not in ['open', 'high', 'low', 'close', 'volume']]
            data[feature_cols] = scaler.fit_transform(data[feature_cols])

        logging.info(f"FeatureEngineeringAgent: Successfully added {len(self.indicators)} indicator(s).")
        return data


if __name__ == '__main__':
    # Example usage for testing the FeatureEngineeringAgent
    
    # 1. Define a mock configuration
    mock_data_config = {
        'data_path': 'ml_backtester/data/EURUSD_m15_2022_2025.parquet'
    }
    
    mock_feature_config = {
        'feature_engineering': {
            'indicators': [
                {'name': 'ema', 'params': {'length': 200}},
                {'name': 'macd'}, # No params needed for default
                {'name': 'rsi'},
                {'name': 'stoch'}
            ],
            'scaling': None # No scaling for this test
        }
    }

    # 2. Get sample data using the DataAgent
    try:
        data_agent = DataAgent(config=mock_data_config)
        df = data_agent.execute()

        # 3. Initialize and execute the FeatureEngineeringAgent
        feature_agent = FeatureEngineeringAgent(config=mock_feature_config)
        featured_df = feature_agent.execute(df)

        print("FeatureEngineeringAgent executed successfully.")
        print("DataFrame info after adding features:")
        featured_df.info()
        print("\nLast 5 rows with new features:")
        # Print tail with all columns visible
        with pd.option_context('display.max_columns', None):
            print(featured_df.tail())

    except Exception as e:
        print(f"An error occurred during testing: {e}")