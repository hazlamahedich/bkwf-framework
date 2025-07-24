import pandas as pd
import numpy as np
from typing import Dict, Any
import logging
from ..agents.iterative_execution_agent import IterativeExecutionAgent

class BacktestingAgent:
    """
    Agent for simulating strategy performance and calculating metrics.
    Supports both high-speed vectorized and flexible event-driven backtesting.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initializes the BacktestingAgent.

        Args:
            config (Dict[str, Any]): Configuration dictionary. Expected keys:
                'backtesting': {
                    'mode': 'vectorized' or 'event_driven',
                    'initial_capital': 100000
                }
        """
        self.config = config.get('backtesting', {})
        self.mode = self.config.get('mode', 'vectorized')
        self.initial_capital = self.config.get('initial_capital', 100000)
        self.full_config = config # Store full config for iterative agent

    def _vectorized_backtest(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Performs a high-speed vectorized backtest."""
        logging.info("Running in vectorized mode.")
        
        # Calculate strategy returns
        data['returns'] = data['close'].pct_change()
        data['strategy_returns'] = data['returns'] * data['signal'].shift(1)
        
        # Calculate equity curve
        data['cumulative_returns'] = (1 + data['strategy_returns']).cumprod()
        data['equity_curve'] = self.initial_capital * data['cumulative_returns']

        # Performance metrics
        total_return = data['cumulative_returns'].iloc[-1] - 1
        # Sharpe Ratio Calculation with safeguards
        if data['strategy_returns'].std() == 0:
            sharpe_ratio = 0.0
        else:
            sharpe_ratio = (data['strategy_returns'].mean() / data['strategy_returns'].std()) * np.sqrt(252 * 96) # 15m data
        
        # Drawdown
        previous_peaks = data['equity_curve'].cummax()
        drawdown = (data['equity_curve'] - previous_peaks) / previous_peaks
        max_drawdown = drawdown.min() if not drawdown.empty else 0.0

        # Trade-level analysis
        positions = data['signal'].diff().fillna(0)
        trades = positions[positions != 0]
        
        trade_returns = []
        for i in range(len(trades) - 1):
            if trades.iloc[i] != 0: # Entry
                entry_price = data['close'].loc[trades.index[i]]
                exit_price = data['close'].loc[trades.index[i+1]]
                
                if trades.iloc[i] > 0: # Long
                    trade_returns.append((exit_price - entry_price) / entry_price)
                else: # Short
                    trade_returns.append((entry_price - exit_price) / entry_price)

        trade_returns = np.array(trade_returns)
        
        wins = np.sum(trade_returns > 0)
        total_trades = len(trade_returns)
        win_rate = wins / total_trades if total_trades > 0 else 0.0

        return {
            "total_return": total_return,
            "sharpe_ratio": sharpe_ratio if np.isfinite(sharpe_ratio) else 0.0,
            "max_drawdown": max_drawdown,
            "total_trades": int(total_trades),
            "win_rate": win_rate,
            "equity_curve": data['equity_curve'],
            # Formatted versions for final reports
            "formatted_metrics": {
                "Total Return": f"{total_return:.2%}",
                "Sharpe Ratio": f"{sharpe_ratio:.2f}" if np.isfinite(sharpe_ratio) else "N/A",
                "Max Drawdown": f"{max_drawdown:.2%}",
                "Total Trades": int(total_trades),
                "Win Rate": f"{win_rate:.2%}"
            }
        }

    def _iterative_backtest(self, data: pd.DataFrame) -> Dict[str, Any]:
       """Performs a flexible, iterative backtest."""
       logging.info("Running in iterative mode.")
       
       iterative_agent = IterativeExecutionAgent(config=self.full_config)
       trades_df = iterative_agent.execute(data, self.initial_capital)

       if trades_df.empty:
           return {
               "total_return": 0, "sharpe_ratio": 0, "max_drawdown": 0,
               "total_trades": 0, "win_rate": 0, "equity_curve": pd.Series([self.initial_capital]),
               "formatted_metrics": {
                   "Total Return": "0.00%", "Sharpe Ratio": "0.00",
                   "Max Drawdown": "0.00%", "Total Trades": 0, "Win Rate": "0.00%"
               }
           }

       # Calculate equity curve from trades
       trades_df['pnl_cumulative'] = trades_df['pnl'].cumsum()
       trades_df['equity'] = self.initial_capital + trades_df['pnl_cumulative']
       
       # Create a full equity curve series aligned with the original data index
       equity_curve = pd.Series(self.initial_capital, index=data.index)
       equity_updates = pd.Series(trades_df['equity'].values, index=pd.to_datetime(trades_df['exit_time']))
       equity_curve.update(equity_updates)
       equity_curve = equity_curve.ffill()

       # Performance metrics
       total_return = (equity_curve.iloc[-1] / self.initial_capital) - 1
       
       # Drawdown
       previous_peaks = equity_curve.cummax()
       drawdown = (equity_curve - previous_peaks) / previous_peaks
       max_drawdown = drawdown.min()

       # Trade stats
       total_trades = len(trades_df)
       wins = np.sum(trades_df['pnl'] > 0)
       win_rate = wins / total_trades if total_trades > 0 else 0.0

       # Sharpe Ratio (approximated from returns)
       daily_returns = equity_curve.pct_change().dropna()
       sharpe_ratio = (daily_returns.mean() / daily_returns.std()) * np.sqrt(252) if daily_returns.std() > 0 else 0

       return {
           "total_return": total_return,
           "sharpe_ratio": sharpe_ratio,
           "max_drawdown": max_drawdown,
           "total_trades": total_trades,
           "win_rate": win_rate,
           "equity_curve": equity_curve,
           "formatted_metrics": {
               "Total Return": f"{total_return:.2%}",
               "Sharpe Ratio": f"{sharpe_ratio:.2f}",
               "Max Drawdown": f"{max_drawdown:.2%}",
               "Total Trades": total_trades,
               "Win Rate": f"{win_rate:.2%}"
           }
       }

    def execute(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Executes the backtest based on the configured mode.
        """
        logging.info(f"BacktestingAgent: Starting backtest in '{self.mode}' mode...")
        
        if 'signal' not in data.columns:
            raise ValueError("Input data must contain a 'signal' column.")

        if self.mode == 'vectorized':
            results = self._vectorized_backtest(data)
        elif self.mode == 'iterative':
            results = self._iterative_backtest(data)
        else:
            raise NotImplementedError(f"Backtesting mode '{self.mode}' is not supported.")
            
        logging.info("Backtest complete.")
        return results