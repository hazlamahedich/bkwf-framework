from abc import ABC, abstractmethod
import pandas as pd
from typing import Dict, Any

class BaseStrategy(ABC):
    """
    Abstract base class for all trading strategies.

    This class defines the essential interface that every strategy, whether it's
    rule-based or machine learning-based, must implement. This ensures that
    the backtesting framework can interact with any strategy in a consistent way.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initializes the strategy with its configuration.

        Args:
            config (Dict[str, Any]): A dictionary containing strategy-specific
                                     parameters and settings.
        """
        self.config = config

    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Generates trading signals for the given data.

        This method must be implemented by all subclasses. It should take a
        DataFrame with OHLCV data and features, and return a DataFrame with
        an added 'signal' column.

        The 'signal' column should contain values like:
        -  1: Buy signal
        - -1: Sell signal
        -  0: Hold or no signal

        Args:
            data (pd.DataFrame): A DataFrame containing the market data and any
                                 necessary technical indicators.

        Returns:
            pd.DataFrame: The input DataFrame with a 'signal' column appended.
        """
        pass

if __name__ == '__main__':
    # This is an abstract class and cannot be instantiated directly.
    # The following code demonstrates how a concrete strategy would inherit from it.

    class MyExampleStrategy(BaseStrategy):
        def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
            # Example logic: Buy if close > previous close, otherwise sell.
            data['signal'] = 0
            data.loc[data['close'] > data['close'].shift(1), 'signal'] = 1
            data.loc[data['close'] < data['close'].shift(1), 'signal'] = -1
            return data

    # You would then use it like this:
    # my_strategy = MyExampleStrategy(config={})
    # signals_df = my_strategy.generate_signals(some_dataframe)
    
    print("BaseStrategy abstract class defined successfully.")
    print("An example concrete strategy 'MyExampleStrategy' has been defined for demonstration.")
