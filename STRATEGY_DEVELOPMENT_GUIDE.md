# Strategy Development Guide

Complete guide for adding new trading strategies to the BKWF Trading Framework.

## 🎯 Overview

This guide covers the complete process of developing, integrating, and deploying new trading strategies in the BKWF framework. The framework supports both rule-based and machine learning strategies with automatic optimization and multi-platform export.

## 📋 Prerequisites

- Understanding of the BKWF framework architecture
- Python programming knowledge
- Trading strategy conceptual knowledge
- Git workflow familiarity (see `GIT_WORKFLOW.md`)

## 🏗️ Strategy Architecture

### Framework Components
```
ml_backtester/
├── strategies/                    # Strategy implementations
│   ├── base_strategy.py          # Abstract base class
│   ├── your_new_strategy.py      # Your strategy implementation
│   └── __init__.py               # Strategy registration
├── agents/
│   ├── strategy_agent.py         # Strategy orchestration
│   ├── export_agent.py           # MT5/Pine Script export
│   └── optimization_agent.py     # Parameter optimization
└── configs/
    └── config.yaml               # Strategy configuration
```

### Strategy Types Supported

| Type | Description | Examples | Export Support |
|------|-------------|----------|----------------|
| **Rule-Based** | Technical indicator combinations | Triple Threat, Bounce Back | ✅ MT5 + Pine |
| **Machine Learning** | Neural networks, ML models | CNN-LSTM | ⚠️ Limited export |
| **Hybrid** | ML + rules combination | Custom implementations | ✅ MT5 + Pine |

## 🚀 Step-by-Step Strategy Development

### Step 1: Create Strategy File

#### 1.1 Start from Git Workflow
```bash
# Create feature branch for new strategy
git checkout develop
git pull origin develop
git checkout -b feature/new-strategy-momentum-reversal

# Navigate to strategies directory
cd ml_backtester/strategies/
```

#### 1.2 Create Strategy File
Create `momentum_reversal.py`:

```python
import pandas as pd
import numpy as np
from typing import Dict, Any

from .base_strategy import BaseStrategy

class MomentumReversalStrategy(BaseStrategy):
    """
    Momentum Reversal Strategy
    
    Identifies overbought/oversold conditions using RSI and MACD,
    then looks for momentum reversal signals with volume confirmation.
    
    Signal Logic:
    - Long: RSI oversold + MACD bullish crossover + volume spike
    - Short: RSI overbought + MACD bearish crossover + volume spike
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Momentum Reversal Strategy.
        
        Args:
            config (Dict[str, Any]): Strategy configuration containing parameters
        """
        super().__init__(config)
        
        # Extract strategy parameters with defaults
        self.rsi_period = self.config.get('rsi_period', 14)
        self.rsi_oversold = self.config.get('rsi_oversold', 30)
        self.rsi_overbought = self.config.get('rsi_overbought', 70)
        self.macd_fast = self.config.get('macd_fast', 12)
        self.macd_slow = self.config.get('macd_slow', 26)
        self.macd_signal = self.config.get('macd_signal', 9)
        self.volume_threshold = self.config.get('volume_threshold', 1.5)  # Volume spike multiplier
        
    def _detect_volume_spike(self, data: pd.DataFrame) -> pd.Series:
        """
        Detect volume spikes above average volume.
        
        Args:
            data (pd.DataFrame): Market data with volume column
            
        Returns:
            pd.Series: Boolean series indicating volume spikes
        """
        volume_ma = data['volume'].rolling(window=20).mean()
        volume_spike = data['volume'] > (volume_ma * self.volume_threshold)
        return volume_spike
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Generate trading signals based on momentum reversal logic.
        
        Args:
            data (pd.DataFrame): DataFrame with OHLCV data and technical indicators
            
        Returns:
            pd.DataFrame: Input DataFrame with added 'signal' column
            
        Required indicators:
            - RSI_{self.rsi_period}
            - MACD_{self.macd_fast}_{self.macd_slow}_{self.macd_signal}
            - MACDs_{self.macd_fast}_{self.macd_slow}_{self.macd_signal}
        """
        # Verify required indicators are present
        required_indicators = [
            f'RSI_{self.rsi_period}',
            f'MACD_{self.macd_fast}_{self.macd_slow}_{self.macd_signal}',
            f'MACDs_{self.macd_fast}_{self.macd_slow}_{self.macd_signal}'
        ]
        
        missing_indicators = [ind for ind in required_indicators if ind not in data.columns]
        if missing_indicators:
            raise ValueError(f"Missing required indicators: {missing_indicators}")
        
        # Initialize signals array
        signals = np.zeros(len(data))
        
        # Get indicator columns
        rsi = data[f'RSI_{self.rsi_period}']
        macd_line = data[f'MACD_{self.macd_fast}_{self.macd_slow}_{self.macd_signal}']
        macd_signal = data[f'MACDs_{self.macd_fast}_{self.macd_slow}_{self.macd_signal}']
        
        # Detect volume spikes
        volume_spike = self._detect_volume_spike(data)
        
        # Define signal conditions
        
        # Long conditions
        rsi_oversold_condition = rsi < self.rsi_oversold
        macd_bullish_cross = (macd_line > macd_signal) & (macd_line.shift(1) <= macd_signal.shift(1))
        long_conditions = rsi_oversold_condition & macd_bullish_cross & volume_spike
        
        # Short conditions  
        rsi_overbought_condition = rsi > self.rsi_overbought
        macd_bearish_cross = (macd_line < macd_signal) & (macd_line.shift(1) >= macd_signal.shift(1))
        short_conditions = rsi_overbought_condition & macd_bearish_cross & volume_spike
        
        # Apply signals
        signals[long_conditions] = 1   # Buy signal
        signals[short_conditions] = -1  # Sell signal
        
        # Add signal column to dataframe
        data['signal'] = signals
        
        return data

# Test function for development
if __name__ == '__main__':
    """
    Test the strategy implementation with sample data.
    This section helps verify the strategy works correctly during development.
    """
    try:
        # Import required agents
        from ..agents.data_agent import DataAgent
        from ..agents.feature_engineering_agent import FeatureEngineeringAgent
        
        # Define test configuration
        data_config = {
            'data_path': 'ml_backtester/data/EURUSD_m15_2022_2025.parquet'
        }
        
        feature_config = {
            'feature_engineering': {
                'indicators': [
                    {'name': 'rsi', 'params': {'length': 14}},
                    {'name': 'macd', 'params': {'fast': 12, 'slow': 26, 'signal': 9}}
                ]
            }
        }
        
        strategy_config = {
            'rsi_period': 14,
            'rsi_oversold': 30,
            'rsi_overbought': 70,
            'volume_threshold': 1.5
        }
        
        # Load and prepare data
        print("Loading market data...")
        data_agent = DataAgent(config=data_config)
        df = data_agent.execute()
        
        print("Engineering features...")
        feature_agent = FeatureEngineeringAgent(config=feature_config)
        featured_df = feature_agent.execute(df)
        
        # Initialize and test strategy
        print("Testing Momentum Reversal Strategy...")
        strategy = MomentumReversalStrategy(config=strategy_config)
        signals_df = strategy.generate_signals(featured_df)
        
        # Display results
        signal_count = (signals_df['signal'] != 0).sum()
        buy_signals = (signals_df['signal'] == 1).sum()
        sell_signals = (signals_df['signal'] == -1).sum()
        
        print(f"Strategy test completed successfully!")
        print(f"Total signals generated: {signal_count}")
        print(f"Buy signals: {buy_signals}")
        print(f"Sell signals: {sell_signals}")
        
        if signal_count > 0:
            print("\nLast 5 signals:")
            recent_signals = signals_df[signals_df['signal'] != 0].tail(5)
            for idx, row in recent_signals.iterrows():
                signal_type = "BUY" if row['signal'] == 1 else "SELL"
                print(f"{row['datetime']}: {signal_type} at {row['close']:.5f}")
        
    except Exception as e:
        print(f"Strategy test failed: {e}")
        import traceback
        traceback.print_exc()
```

### Step 2: Register Strategy in Framework

#### 2.1 Update Strategy Registry
Edit `ml_backtester/strategies/__init__.py`:

```python
"""
Strategy registry for the backtesting framework.
"""

from .triple_threat import TripleThreatStrategy
from .bounce_back import BounceBackStrategy
from .cnn_lstm_strategy import CNNLSTMStrategy
from .momentum_reversal import MomentumReversalStrategy  # Add your strategy

# Strategy registry mapping
STRATEGY_REGISTRY = {
    'triple_threat': TripleThreatStrategy,
    'bounce_back': BounceBackStrategy,
    'cnn_lstm_strategy': CNNLSTMStrategy,
    'momentum_reversal': MomentumReversalStrategy,  # Register your strategy
}

def get_strategy_class(strategy_name: str):
    """
    Get strategy class by name.
    
    Args:
        strategy_name (str): Name of the strategy
        
    Returns:
        Strategy class or None if not found
    """
    return STRATEGY_REGISTRY.get(strategy_name)

def list_available_strategies():
    """
    List all available strategy names.
    
    Returns:
        List[str]: List of available strategy names
    """
    return list(STRATEGY_REGISTRY.keys())
```

#### 2.2 Update Configuration Template
Edit `ml_backtester/configs/config.yaml`:

```yaml
# Add your strategy to the available strategies
strategy:
  name: 
    - 'triple_threat'
    - 'bounce_back'  
    - 'cnn_lstm_strategy'
    - 'momentum_reversal'  # Add your new strategy

# Add strategy-specific parameters (optional)
strategy_params:
  momentum_reversal:
    rsi_period: 14
    rsi_oversold: 30
    rsi_overbought: 70
    macd_fast: 12
    macd_slow: 26
    macd_signal: 9
    volume_threshold: 1.5
```

### Step 3: Configure Required Indicators

#### 3.1 Update Feature Engineering Config
Your strategy needs specific indicators. Update the config:

```yaml
feature_engineering:
  indicators:
    - {name: 'rsi', params: {length: 14}}              # For RSI analysis
    - {name: 'macd', params: {fast: 12, slow: 26, signal: 9}}  # For MACD analysis
    # Add other indicators your strategy needs
```

### Step 4: Add Optimization Parameters

#### 4.1 Define Parameter Search Space
Update optimization config for your strategy:

```yaml
optimization:
  enabled: true
  n_trials: 100
  params:
    # Risk management (common to all strategies)
    sl_atr_multiplier:
      type: 'float'
      low: 1.0
      high: 5.0
    tp_atr_multiplier:
      type: 'float'
      low: 1.0
      high: 8.0
    
    # Strategy-specific parameters
    rsi_period:
      type: 'int'
      low: 10
      high: 20
    rsi_oversold:
      type: 'int'
      low: 20
      high: 35
    rsi_overbought:
      type: 'int'
      low: 65
      high: 80
    volume_threshold:
      type: 'float'
      low: 1.2
      high: 3.0
```

### Step 5: Test Strategy Implementation

#### 5.1 Run Strategy Test
```bash
# Test your strategy implementation
cd ml_backtester/strategies/
python momentum_reversal.py
```

Expected output:
```
Loading market data...
Engineering features...
Testing Momentum Reversal Strategy...
Strategy test completed successfully!
Total signals generated: 245
Buy signals: 123
Sell signals: 122

Last 5 signals:
2025-01-20 14:30:00: BUY at 1.08945
2025-01-21 09:15:00: SELL at 1.09123
...
```

#### 5.2 Run Framework Backtest
```bash
# Create test config for your strategy
cp ml_backtester/configs/config.yaml ml_backtester/configs/momentum_reversal_test.yaml

# Edit the test config to use only your strategy
# strategy:
#   name: ['momentum_reversal']

# Run backtest
python run_backtest.py --config ml_backtester/configs/momentum_reversal_test.yaml
```

### Step 6: Add Export Support

#### 6.1 Add MT5 Export Template
Update `ml_backtester/agents/export_agent.py` to support your strategy:

```python
def _export_to_mt5(self, strategy_name: str, best_params: Dict[str, Any], backtest_results: Dict[str, Any]):
    """Export strategy to MetaTrader 5 Expert Advisor."""
    
    if strategy_name == 'momentum_reversal':
        mt5_template = self._generate_momentum_reversal_mt5(best_params)
    elif strategy_name == 'triple_threat':
        mt5_template = self._generate_triple_threat_mt5(best_params)
    # ... other strategies
    else:
        logging.warning(f"MT5 export not supported for strategy: {strategy_name}")
        return
    
    # Save MT5 file
    mt5_filename = f"{strategy_name}_optimized.mq5"
    mt5_path = self.export_path / mt5_filename
    
    with open(mt5_path, 'w', encoding='utf-8') as f:
        f.write(mt5_template)
    
    logging.info(f"MT5 EA exported: {mt5_path}")

def _generate_momentum_reversal_mt5(self, params: Dict[str, Any]) -> str:
    """Generate MT5 code for Momentum Reversal strategy."""
    
    template = f'''
//+------------------------------------------------------------------+
//|                      momentum_reversal_Optimized.mq5             |
//|      Generated by ML Backtester Framework - Copyright 2025       |
//+------------------------------------------------------------------+
#property copyright "Copyright 2025, ML Backtester Framework"
#property version   "1.00"
#property strict

#include <Trade\\Trade.mqh>
#include <Trade\\SymbolInfo.mqh>

//--- Optimized Input Parameters
input double InpRiskPerTrade = 0.01;
input double InpSLMultiplier = {params.get('sl_atr_multiplier', 2.0)};
input double InpTPMultiplier = {params.get('tp_atr_multiplier', 3.0)};
input int    InpRSIPeriod    = {params.get('rsi_period', 14)};
input int    InpRSIOversold  = {params.get('rsi_oversold', 30)};
input int    InpRSIOverbought = {params.get('rsi_overbought', 70)};
input int    InpMACDFast     = {params.get('macd_fast', 12)};
input int    InpMACDSlow     = {params.get('macd_slow', 26)};
input int    InpMACDSignal   = {params.get('macd_signal', 9)};
input double InpVolumeThreshold = {params.get('volume_threshold', 1.5)};
input int    InpATRPeriod    = 14;

//--- Global Variables
CTrade      trade;
CSymbolInfo symbol;
datetime    lastBarTime = 0;

//--- Indicator Handles
int rsi_handle;
int macd_handle;
int atr_handle;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{{
    symbol.Name(_Symbol);
    trade.SetExpertMagicNumber(54321);
    trade.SetMarginMode();
    
    // Initialize indicators
    rsi_handle = iRSI(_Symbol, _Period, InpRSIPeriod, PRICE_CLOSE);
    macd_handle = iMACD(_Symbol, _Period, InpMACDFast, InpMACDSlow, InpMACDSignal, PRICE_CLOSE);
    atr_handle = iATR(_Symbol, _Period, InpATRPeriod);
    
    if(rsi_handle == INVALID_HANDLE || macd_handle == INVALID_HANDLE || atr_handle == INVALID_HANDLE)
    {{
        Print("Error initializing indicators");
        return INIT_FAILED;
    }}
    
    Print("Momentum Reversal EA initialized successfully");
    return INIT_SUCCEEDED;
}}

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
{{
    // Check for new bar
    if(Time[0] == lastBarTime)
        return;
    lastBarTime = Time[0];
    
    // Get indicator values
    double rsi[], macd_main[], macd_signal[], atr_values[];
    
    if(CopyBuffer(rsi_handle, 0, 0, 3, rsi) < 3 ||
       CopyBuffer(macd_handle, 0, 0, 3, macd_main) < 3 ||
       CopyBuffer(macd_handle, 1, 0, 3, macd_signal) < 3 ||
       CopyBuffer(atr_handle, 0, 0, 3, atr_values) < 3)
        return;
    
    // Volume spike detection (simplified)
    double volume_ma = 0;
    for(int i = 1; i <= 20; i++)
        volume_ma += Volume[i];
    volume_ma /= 20;
    bool volume_spike = Volume[0] > (volume_ma * InpVolumeThreshold);
    
    // Signal conditions
    bool rsi_oversold = rsi[0] < InpRSIOversold;
    bool rsi_overbought = rsi[0] > InpRSIOverbought;
    bool macd_bullish_cross = (macd_main[0] > macd_signal[0]) && (macd_main[1] <= macd_signal[1]);
    bool macd_bearish_cross = (macd_main[0] < macd_signal[0]) && (macd_main[1] >= macd_signal[1]);
    
    // Entry logic
    if(rsi_oversold && macd_bullish_cross && volume_spike && PositionsTotal() == 0)
    {{
        double sl = symbol.Bid() - (atr_values[0] * InpSLMultiplier);
        double tp = symbol.Ask() + (atr_values[0] * InpTPMultiplier);
        
        trade.Buy(CalculateLotSize(sl), _Symbol, 0, sl, tp, "Momentum Reversal Long");
    }}
    
    if(rsi_overbought && macd_bearish_cross && volume_spike && PositionsTotal() == 0)
    {{
        double sl = symbol.Ask() + (atr_values[0] * InpSLMultiplier);
        double tp = symbol.Bid() - (atr_values[0] * InpTPMultiplier);
        
        trade.Sell(CalculateLotSize(sl), _Symbol, 0, sl, tp, "Momentum Reversal Short");
    }}
}}

//+------------------------------------------------------------------+
//| Calculate lot size based on risk                                |
//+------------------------------------------------------------------+
double CalculateLotSize(double sl_price)
{{
    double risk_amount = AccountInfoDouble(ACCOUNT_BALANCE) * InpRiskPerTrade;
    double sl_distance = MathAbs(symbol.Bid() - sl_price);
    double pip_value = symbol.TickValue();
    
    if(sl_distance == 0 || pip_value == 0)
        return 0.01;
    
    double lot_size = risk_amount / (sl_distance / symbol.Point() * pip_value);
    
    // Normalize lot size
    double min_lot = symbol.LotsMin();
    double max_lot = symbol.LotsMax();
    double lot_step = symbol.LotsStep();
    
    lot_size = MathMax(min_lot, MathMin(max_lot, MathRound(lot_size / lot_step) * lot_step));
    
    return lot_size;
}}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{{
    // Release indicator handles
    if(rsi_handle != INVALID_HANDLE) IndicatorRelease(rsi_handle);
    if(macd_handle != INVALID_HANDLE) IndicatorRelease(macd_handle);
    if(atr_handle != INVALID_HANDLE) IndicatorRelease(atr_handle);
}}
'''
    
    return template.strip()
```

#### 6.2 Add Pine Script Export Template
Similarly, add Pine Script support:

```python
def _generate_momentum_reversal_pinescript(self, params: Dict[str, Any]) -> str:
    """Generate Pine Script for Momentum Reversal strategy."""
    
    template = f'''
//@version=5
strategy("Momentum Reversal Optimized", overlay=true, 
         initial_capital=100000, 
         default_qty_type=strategy.percent_of_equity, 
         default_qty_value=1)

// --- Optimized Parameters ---
sl_atr_multiplier = input.float({params.get('sl_atr_multiplier', 2.0)}, title="SL ATR Multiplier")
tp_atr_multiplier = input.float({params.get('tp_atr_multiplier', 3.0)}, title="TP ATR Multiplier")
rsi_period = input.int({params.get('rsi_period', 14)}, title="RSI Period")
rsi_oversold = input.int({params.get('rsi_oversold', 30)}, title="RSI Oversold Level")
rsi_overbought = input.int({params.get('rsi_overbought', 70)}, title="RSI Overbought Level")
macd_fast = input.int({params.get('macd_fast', 12)}, title="MACD Fast Length")
macd_slow = input.int({params.get('macd_slow', 26)}, title="MACD Slow Length")
macd_signal = input.int({params.get('macd_signal', 9)}, title="MACD Signal Length")
volume_threshold = input.float({params.get('volume_threshold', 1.5)}, title="Volume Spike Threshold")
atr_length = input.int(14, title="ATR Length")

// --- Indicators ---
rsi = ta.rsi(close, rsi_period)
[macd_line, signal_line, _] = ta.macd(close, macd_fast, macd_slow, macd_signal)
atr = ta.atr(atr_length)

// Volume spike detection
volume_ma = ta.sma(volume, 20)
volume_spike = volume > (volume_ma * volume_threshold)

// --- Strategy Conditions ---
rsi_oversold_condition = rsi < rsi_oversold
rsi_overbought_condition = rsi > rsi_overbought
macd_bullish_cross = ta.crossover(macd_line, signal_line)
macd_bearish_cross = ta.crossunder(macd_line, signal_line)

// Entry conditions
long_condition = rsi_oversold_condition and macd_bullish_cross and volume_spike
short_condition = rsi_overbought_condition and macd_bearish_cross and volume_spike

// --- Execution Logic ---
if (long_condition)
    sl = close - (atr * sl_atr_multiplier)
    tp = close + (atr * tp_atr_multiplier)
    strategy.entry("Long", strategy.long)
    strategy.exit("Long Exit", from_entry="Long", stop=sl, limit=tp)

if (short_condition)
    sl = close + (atr * sl_atr_multiplier) 
    tp = close - (atr * tp_atr_multiplier)
    strategy.entry("Short", strategy.short)
    strategy.exit("Short Exit", from_entry="Short", stop=sl, limit=tp)

// --- Plotting ---
plot(ta.sma(close, 20), title="SMA 20", color=color.blue)
hline(rsi_oversold, "RSI Oversold", color=color.green, linestyle=hline.style_dashed)
hline(rsi_overbought, "RSI Overbought", color=color.red, linestyle=hline.style_dashed)

// Background color for RSI levels
bgcolor(rsi_oversold_condition ? color.new(color.green, 90) : 
        rsi_overbought_condition ? color.new(color.red, 90) : na)
'''
    
    return template.strip()
```

### Step 7: Documentation & Testing

#### 7.1 Update Strategy Documentation
Add your strategy to `README.md`:

```markdown
### Momentum Reversal Strategy
- **Concept**: Identifies overbought/oversold reversals with momentum confirmation
- **Components**: RSI levels + MACD crossover + volume spike confirmation  
- **Best for**: Volatile markets with clear reversal patterns
- **Risk Level**: Medium-High

**Parameters:**
- `rsi_period`: RSI calculation period (10-20)
- `rsi_oversold`: Oversold threshold (20-35)  
- `rsi_overbought`: Overbought threshold (65-80)
- `volume_threshold`: Volume spike multiplier (1.2-3.0)
```

#### 7.2 Add to Parameter Reference
Update `PARAMETER_REFERENCE.md`:

```markdown
### Momentum Reversal Strategy Parameters
```yaml
strategy:
  name: ['momentum_reversal']
  params:
    rsi_period: 14               # RSI calculation period (10-20)
    rsi_oversold: 30             # RSI oversold level (20-35)
    rsi_overbought: 70           # RSI overbought level (65-80)
    macd_fast: 12                # MACD fast EMA (8-15)
    macd_slow: 26                # MACD slow EMA (20-35)
    macd_signal: 9               # MACD signal line (5-15)
    volume_threshold: 1.5        # Volume spike threshold (1.2-3.0)
```
```

### Step 8: Integration Testing

#### 8.1 Full Framework Test
```bash
# Test complete pipeline with your strategy
python run_backtest.py --config ml_backtester/configs/momentum_reversal_test.yaml
```

#### 8.2 Optimization Test
```bash
# Test with optimization enabled
# Edit config.yaml:
# optimization:
#   enabled: true
#   n_trials: 20  # Small number for testing

python run_backtest.py --config ml_backtester/configs/momentum_reversal_test.yaml
```

#### 8.3 Export Test
```bash
# Test export functionality
# Edit config.yaml:
# export:
#   enabled: true
#   formats: ['mt5', 'pinescript']

python run_backtest.py --config ml_backtester/configs/momentum_reversal_test.yaml

# Check exports folder
ls ml_backtester/exports/momentum_reversal*
```

### Step 9: Git Integration & Deployment

#### 9.1 Commit Your Changes
```bash
# Add all your changes
git add .

# Commit with descriptive message
git commit -m "Add: Momentum Reversal Strategy implementation

- Implement RSI + MACD + Volume reversal strategy
- Add parameter optimization support
- Include MT5 and Pine Script export templates
- Add comprehensive testing and documentation
- Update strategy registry and configuration"

# Push feature branch
git push -u origin feature/new-strategy-momentum-reversal
```

#### 9.2 Merge to Develop
```bash
# Switch to develop and merge
git checkout develop
git merge --no-ff feature/new-strategy-momentum-reversal
git push origin develop

# Clean up feature branch
git branch -d feature/new-strategy-momentum-reversal
git push origin --delete feature/new-strategy-momentum-reversal
```

## 🎯 Advanced Strategy Features

### Machine Learning Integration

For ML-based strategies, extend the pattern:

```python
from sklearn.ensemble import RandomForestClassifier
import joblib

class MLMomentumStrategy(BaseStrategy):
    """
    Machine Learning enhanced momentum strategy
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.model_path = config.get('model_path', 'models/momentum_rf_model.pkl')
        self.model = self._load_or_train_model()
    
    def _load_or_train_model(self):
        """Load pre-trained model or train new one"""
        try:
            return joblib.load(self.model_path)
        except FileNotFoundError:
            return self._train_model()
    
    def _train_model(self):
        """Train ML model for signal prediction"""
        # Training logic here
        model = RandomForestClassifier(n_estimators=100)
        # ... training code
        joblib.dump(model, self.model_path)
        return model
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """Generate ML-based signals"""
        # Feature engineering
        features = self._engineer_features(data)
        
        # ML prediction
        predictions = self.model.predict(features)
        
        # Convert to signals
        data['signal'] = predictions
        return data
```

### Multi-Timeframe Strategies

```python
class MultiTimeframeStrategy(BaseStrategy):
    """
    Strategy using multiple timeframes
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.timeframes = config.get('timeframes', ['M15', 'H1', 'H4'])
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """Generate signals using multiple timeframes"""
        
        # Higher timeframe trend
        htf_trend = self._get_higher_timeframe_trend(data)
        
        # Current timeframe signals
        signals = self._generate_base_signals(data)
        
        # Filter signals by higher timeframe trend
        filtered_signals = signals * htf_trend
        
        data['signal'] = filtered_signals
        return data
```

## 🚨 Common Issues & Solutions

### Strategy Not Working
**Problem**: Strategy not generating signals
**Solutions**:
- Check required indicators are in data
- Verify signal conditions are reasonable
- Test with different parameters
- Add debug prints to understand logic flow

### Export Issues
**Problem**: MT5/Pine export not working
**Solutions**:
- Verify strategy name in export templates
- Check parameter mapping in export functions
- Test generated code syntax
- Ensure all required indicators are supported

### Optimization Problems
**Problem**: Optimization not finding good parameters
**Solutions**:
- Expand parameter search ranges
- Increase number of trials
- Check if strategy is overfitting
- Validate on out-of-sample data

### Performance Issues  
**Problem**: Strategy running slowly
**Solutions**:
- Vectorize operations instead of loops
- Reduce indicator calculations
- Optimize data access patterns
- Use numba for performance-critical functions

## 📋 Strategy Development Checklist

### Pre-Development
- [ ] Strategy concept clearly defined
- [ ] Required indicators identified
- [ ] Parameter ranges estimated
- [ ] Git feature branch created

### Development Phase
- [ ] BaseStrategy inherited correctly
- [ ] generate_signals() method implemented
- [ ] Required indicators validated
- [ ] Test function works correctly
- [ ] Strategy registered in __init__.py

### Integration Phase  
- [ ] Configuration updated
- [ ] Optimization parameters defined
- [ ] Export templates added (if needed)
- [ ] Full framework test passed

### Documentation Phase
- [ ] Strategy added to README.md
- [ ] Parameters documented in PARAMETER_REFERENCE.md
- [ ] Code comments comprehensive
- [ ] Test cases documented

### Deployment Phase
- [ ] Git workflow followed
- [ ] Changes committed with clear messages
- [ ] Feature branch merged to develop
- [ ] Export functionality tested

This comprehensive guide provides everything needed to successfully develop, integrate, and deploy new trading strategies in the BKWF framework. Follow the step-by-step process for best results and maintainable code.