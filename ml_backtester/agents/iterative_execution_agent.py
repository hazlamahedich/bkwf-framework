import pandas as pd
import numpy as np
from typing import Dict, Any
import logging

class IterativeExecutionAgent:
    """
    Agent for simulating trade execution on a bar-by-bar basis,
    allowing for dynamic features like trailing stops.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initializes the IterativeExecutionAgent.
        """
        self.execution_config = config.get('execution', {})
        self.risk_config = config.get('risk_management', {})
        self.slippage_percent = self.execution_config.get('slippage_percent', 0.0005)
        
        # Trailing stop settings
        self.tsl_config = self.risk_config.get('trailing_stop', {})
        self.tsl_enabled = self.tsl_config.get('enabled', False)
        self.tsl_atr_multiplier = self.tsl_config.get('atr_multiplier', 1.5)

    def execute(self, data: pd.DataFrame, initial_capital: float) -> pd.DataFrame:
        """
        Simulates trade execution iteratively.
        """
        logging.info("IterativeExecutionAgent: Simulating trade execution...")

        # --- Calculate Entry Price (similar to ExecutionAgent) ---
        spread_cost = (data.get('spread', 0) * 0.0001) / 2
        slippage = np.random.uniform(0, self.slippage_percent, len(data)) * data['close']
        
        buy_price = data['close'] + spread_cost + slippage
        sell_price = data['close'] - spread_cost - slippage
        
        data['entry_price'] = np.where(data['signal'] == 1, buy_price,
                                       np.where(data['signal'] == -1, sell_price, np.nan))
        data['entry_price'] = data['entry_price'].ffill()


        atr_col = next((col for col in data.columns if 'ATR' in col), 'atr')
        
        # --- State Variables ---
        in_trade = False
        capital = initial_capital
        position = 0
        entry_price = 0
        stop_loss = 0
        take_profit = 0
        peak_price = 0 # For trailing stop
        trades = []

        # --- Main Loop ---
        for i, row in data.iterrows():
            # --- Check for Exits ---
            if in_trade:
                # Check SL/TP
                exit_reason = None
                if (position > 0 and row['low'] <= stop_loss) or \
                   (position < 0 and row['high'] >= stop_loss):
                    exit_price = stop_loss
                    exit_reason = 'SL'
                elif (position > 0 and row['high'] >= take_profit) or \
                     (position < 0 and row['low'] <= take_profit):
                    exit_price = take_profit
                    exit_reason = 'TP'
                
                if exit_reason:
                    # Record trade
                    pnl = (exit_price - entry_price) * position
                    capital += pnl
                    trades.append({
                        'entry_time': entry_time, 'exit_time': row.name,
                        'entry_price': entry_price, 'exit_price': exit_price,
                        'position_size': position, 'pnl': pnl, 'exit_reason': exit_reason
                    })
                    in_trade = False
                    position = 0
                
                # --- Trailing Stop Logic ---
                elif self.tsl_enabled:
                    if position > 0: # Long trade
                        peak_price = max(peak_price, row['high'])
                        new_sl = peak_price - self.tsl_atr_multiplier * row[atr_col]
                        stop_loss = max(stop_loss, new_sl) # Only move SL up
                    elif position < 0: # Short trade
                        peak_price = min(peak_price, row['low'])
                        new_sl = peak_price + self.tsl_atr_multiplier * row[atr_col]
                        stop_loss = min(stop_loss, new_sl) # Only move SL down

            # --- Check for Entries ---
            if not in_trade and row['signal'] != 0:
                in_trade = True
                entry_time = row.name
                position = row['position_size'] if row['signal'] == 1 else -row['position_size']
                entry_price = row['entry_price']
                stop_loss = row['stop_loss']
                take_profit = row['take_profit']
                
                if position > 0:
                    peak_price = entry_price
                else:
                    peak_price = entry_price

        logging.info(f"Iterative execution finished. Total trades: {len(trades)}")
        return pd.DataFrame(trades)