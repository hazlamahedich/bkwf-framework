# Parameter Reference Guide

Complete configuration reference for the BKWF Trading Framework.

## 📋 Quick Reference Table

| Category | Parameter | Type | Default | Range | Description |
|----------|-----------|------|---------|-------|-------------|
| **Data** | `data_path` | string | - | - | Path to market data file |
| **Risk** | `risk_per_trade` | float | 0.01 | 0.001-0.1 | Risk as % of account per trade |
| **Risk** | `sl_atr_multiplier` | float | 2.0 | 0.5-10.0 | Stop-loss ATR multiplier |
| **Risk** | `tp_atr_multiplier` | float | 3.0 | 0.5-15.0 | Take-profit ATR multiplier |
| **Execution** | `slippage_percent` | float | 0.0005 | 0.0-0.01 | Execution slippage (0.05% default) |
| **Backtest** | `initial_capital` | int | 100000 | 1000+ | Starting account balance |
| **Optimization** | `n_trials` | int | 50 | 10-1000 | Number of optimization trials |
| **ML** | `look_back` | int | 60 | 10-200 | Sequence length for ML models |
| **ML** | `epochs` | int | 5 | 1-100 | Training epochs for neural networks |

## 🔧 Configuration Structure

### 1. Run Mode Configuration
```yaml
run_mode: 'optimize_and_backtest'  # Options: 'train', 'optimize', 'backtest', 'optimize_and_backtest'
```

**Options:**
- `'train'`: Train ML models only
- `'optimize'`: Run parameter optimization only  
- `'backtest'`: Run backtest with current parameters
- `'optimize_and_backtest'`: Full pipeline with optimization

### 2. Data Agent Configuration
```yaml
data_path: 'ml_backtester/data/EURUSD_m15_2022_2025.parquet'
```

**Supported Formats:**
- `.parquet` (recommended for performance)
- `.csv` (standard format)

**Data Requirements:**
- Columns: `datetime`, `open`, `high`, `low`, `close`, `volume`
- Minimum: 1000+ rows for meaningful backtesting
- Recommended: 10,000+ rows for ML strategies

### 3. Feature Engineering Configuration
```yaml
feature_engineering:
  indicators:
    - {name: 'ema', params: {length: 200}}      # Exponential Moving Average
    - {name: 'macd'}                            # MACD with default params
    - {name: 'rsi', params: {length: 14}}       # RSI with custom period
    - {name: 'stoch', params: {k: 14, d: 3}}    # Stochastic oscillator
    - {name: 'atr', params: {length: 14}}       # Average True Range
    - {name: 'bb', params: {length: 20, std: 2}} # Bollinger Bands
  scaling: 'standard'  # Options: 'standard', 'minmax', null
```

**Available Indicators:**
| Indicator | Parameters | Description |
|-----------|------------|-------------|
| `ema` | `length` (int, default: 14) | Exponential Moving Average |
| `sma` | `length` (int, default: 14) | Simple Moving Average |
| `macd` | `fast` (12), `slow` (26), `signal` (9) | MACD Oscillator |
| `rsi` | `length` (int, default: 14) | Relative Strength Index |
| `stoch` | `k` (14), `d` (3), `smooth_k` (3) | Stochastic Oscillator |
| `atr` | `length` (int, default: 14) | Average True Range |
| `bb` | `length` (20), `std` (2) | Bollinger Bands |
| `adx` | `length` (int, default: 14) | Average Directional Index |
| `cci` | `length` (int, default: 20) | Commodity Channel Index |
| `williams` | `length` (int, default: 14) | Williams %R |

**Scaling Options:**
- `'standard'`: Z-score normalization (mean=0, std=1)
- `'minmax'`: Min-max normalization (0-1 range)
- `null`: No scaling applied

### 4. Strategy Configuration
```yaml
strategy:
  name: 
    - 'triple_threat'    # Multi-indicator trend following
    - 'bounce_back'      # Mean reversion strategy
    - 'cnn_lstm_strategy' # Deep learning strategy
```

**Strategy-Specific Parameters:**

#### Triple Threat Strategy
```yaml
# No additional parameters - uses standard indicator settings
```

#### Bounce Back Strategy
```yaml
strategy:
  params:
    lookback_period: 20        # Lookback for support/resistance
    bounce_threshold: 0.5      # Bounce sensitivity (0.1-2.0)
```

#### CNN-LSTM Strategy
```yaml
modeling:
  look_back: 60              # Sequence length for LSTM
  hidden_size: 50            # LSTM hidden units
  num_layers: 2              # LSTM layers
  dropout: 0.2               # Dropout rate
```

### 5. Modeling Configuration
```yaml
modeling:
  model_save_path: 'ml_backtester/models/trained_model_pytorch'
  look_back: 60              # Sequence length (10-200)
  epochs: 50                 # Training epochs (5-200)
  batch_size: 32             # Batch size (16-128)
  learning_rate: 0.001       # Learning rate (0.0001-0.01)
  validation_split: 0.2      # Validation data ratio (0.1-0.3)
```

**Performance Guidelines:**
- `look_back`: Higher = more context, slower training
- `epochs`: More = better fit, risk of overfitting
- `batch_size`: Higher = faster training, more memory
- `learning_rate`: Lower = stable training, slower convergence

### 6. Optimization Configuration
```yaml
optimization:
  enabled: true              # Enable/disable optimization
  n_trials: 100              # Number of optimization trials
  timeout: 3600              # Max optimization time (seconds)
  params:
    # Parameter search spaces
    sl_atr_multiplier: 
      type: 'float'
      low: 1.0
      high: 5.0
    tp_atr_multiplier:
      type: 'float'  
      low: 1.0
      high: 5.0
    risk_per_trade:
      type: 'float'
      low: 0.005
      high: 0.02
```

**Parameter Types:**
- `'float'`: Continuous values with `low` and `high` bounds
- `'int'`: Integer values with `low` and `high` bounds  
- `'categorical'`: Choice from list of `choices`

**Example Categorical Parameter:**
```yaml
indicator_period:
  type: 'categorical'
  choices: [10, 14, 20, 25, 30]
```

### 7. Risk Management Configuration
```yaml
risk_management:
  risk_per_trade: 0.01       # Risk per trade (0.001-0.1)
  sl_atr_multiplier: 2.0     # Stop-loss ATR multiplier (0.5-10.0)
  tp_atr_multiplier: 3.0     # Take-profit ATR multiplier (0.5-15.0)
  max_positions: 1           # Maximum concurrent positions
  trailing_stop:
    enabled: true            # Enable trailing stops
    atr_multiplier: 1.5      # Trailing stop ATR multiplier
    activation_ratio: 0.5    # Activate when profit > 50% of TP
```

**Risk Guidelines:**
- Conservative: `risk_per_trade: 0.005`, `sl_atr_multiplier: 3.0`
- Moderate: `risk_per_trade: 0.01`, `sl_atr_multiplier: 2.0`  
- Aggressive: `risk_per_trade: 0.02`, `sl_atr_multiplier: 1.5`

### 8. Execution Configuration
```yaml
execution:
  slippage_percent: 0.0005   # Execution slippage (0.0-0.01)
  commission_per_lot: 7.0    # Commission per standard lot
  spread_points: 1.5         # Average spread in points
```

**Market Impact Settings:**
- **Forex**: `slippage_percent: 0.0005`, `spread_points: 1-3`
- **Stocks**: `slippage_percent: 0.001`, `commission_per_share: 0.005`
- **Crypto**: `slippage_percent: 0.002`, higher spreads

### 9. Backtesting Configuration
```yaml
backtesting:
  mode: 'iterative'          # Options: 'vectorized', 'iterative'
  initial_capital: 100000    # Starting balance (1000+)
  leverage: 1.0              # Account leverage (1.0-500.0)
  margin_call_level: 0.2     # Margin call at 20% equity
```

**Mode Options:**
- `'vectorized'`: Faster, less realistic execution
- `'iterative'`: Slower, more realistic bar-by-bar execution

### 10. Analytics Configuration
```yaml
analytics:
  report_path: 'ml_backtester/reports'
  generate_plots: true       # Generate equity curve plots
  save_trades: true          # Save individual trade details
  benchmark_symbol: 'SPY'    # Benchmark for comparison
```

### 11. Export Configuration
```yaml
export:
  enabled: true              # Enable strategy export
  path: 'ml_backtester/exports'
  formats: ['mt5', 'pinescript']  # Export formats
  include_optimization: true # Include optimized parameters
```

**Export Formats:**
- `'mt5'`: MetaTrader 5 Expert Advisor (.mq5)
- `'pinescript'`: TradingView Pine Script (.pine)
- `'json'`: JSON configuration for API integration

### 12. Logging Configuration
```yaml
logging:
  level: 'INFO'              # Options: 'DEBUG', 'INFO', 'WARNING', 'ERROR'
  file_path: 'ml_backtester/logs/backtest.log'
  max_file_size: '10MB'      # Log rotation size
  backup_count: 5            # Number of backup log files
```

## 🎯 Strategy-Specific Parameters

### Triple Threat Strategy Parameters
```yaml
strategy:
  name: ['triple_threat']
  params:
    ema_period: 200          # Trend filter EMA period (50-300)
    macd_fast: 12            # MACD fast EMA (8-15)
    macd_slow: 26            # MACD slow EMA (20-35)  
    macd_signal: 9           # MACD signal line (5-15)
    stoch_k: 14              # Stochastic %K period (10-20)
    stoch_d: 3               # Stochastic %D smoothing (1-5)
    stoch_oversold: 20       # Oversold level (15-25)
    stoch_overbought: 80     # Overbought level (75-85)
```

### Bounce Back Strategy Parameters
```yaml
strategy:
  name: ['bounce_back']
  params:
    lookback_period: 20      # Support/resistance lookback (10-50)
    bounce_threshold: 0.5    # Bounce sensitivity (0.1-2.0)
    rsi_period: 14           # RSI period for confirmation (10-20)
    rsi_oversold: 30         # RSI oversold level (20-35)
    rsi_overbought: 70       # RSI overbought level (65-80)
```

### CNN-LSTM Strategy Parameters
```yaml
strategy:
  name: ['cnn_lstm_strategy']
modeling:
  look_back: 60              # Input sequence length (30-120)
  # CNN parameters
  conv_filters: [32, 64, 128] # Convolutional filters
  kernel_size: 3             # Convolution kernel size (2-5)
  pool_size: 2               # Max pooling size (2-4)
  # LSTM parameters  
  lstm_units: 50             # LSTM hidden units (32-128)
  lstm_layers: 2             # Number of LSTM layers (1-3)
  dropout: 0.2               # Dropout rate (0.1-0.5)
  # Training parameters
  epochs: 50                 # Training epochs (20-100)
  batch_size: 32             # Batch size (16-64)
  learning_rate: 0.001       # Learning rate (0.0001-0.01)
```

## 🔍 Parameter Selection Guidelines

### For Trending Markets
```yaml
risk_management:
  sl_atr_multiplier: 2.5     # Wider stops for trend following
  tp_atr_multiplier: 4.0     # Higher reward-to-risk ratio
  trailing_stop:
    enabled: true            # Let profits run
    atr_multiplier: 2.0
```

### For Range-Bound Markets  
```yaml
risk_management:
  sl_atr_multiplier: 1.5     # Tighter stops for mean reversion
  tp_atr_multiplier: 2.0     # Conservative targets
  trailing_stop:
    enabled: false           # Fixed targets work better
```

### For High-Frequency Trading
```yaml
execution:
  slippage_percent: 0.001    # Account for higher slippage
  commission_per_lot: 7.0    # Include realistic commissions

backtesting:
  mode: 'iterative'          # More realistic execution
```

### For Development/Testing
```yaml
optimization:
  n_trials: 20               # Quick optimization
  timeout: 600               # 10-minute limit

logging:
  level: 'DEBUG'             # Detailed logging

analytics:
  generate_plots: true       # Visual feedback
```

### For Production Deployment
```yaml
optimization:
  n_trials: 200              # Thorough optimization
  timeout: 7200              # 2-hour limit

logging:
  level: 'INFO'              # Essential logging only

export:
  enabled: true              # Generate trading files
  include_optimization: true # Use optimized parameters
```

## ⚡ Performance Optimization Tips

### Memory Usage
- Use smaller `look_back` values for ML models
- Reduce `batch_size` if memory errors occur  
- Process data in chunks for large datasets

### Speed Optimization
- Use `'vectorized'` backtesting mode for initial testing
- Reduce `n_trials` for quick optimization rounds
- Enable parallel processing where available

### Accuracy vs Speed Trade-offs
- `'iterative'` mode: More accurate, slower
- `'vectorized'` mode: Less accurate, faster
- Higher `n_trials`: Better optimization, slower
- More indicators: Better signals, slower processing

## 🚨 Common Configuration Errors

### Invalid Parameter Ranges
```yaml
# ❌ Wrong - negative risk
risk_per_trade: -0.01

# ✅ Correct - positive risk
risk_per_trade: 0.01
```

### Missing Required Files
```yaml
# ❌ Wrong - file doesn't exist  
data_path: 'nonexistent_file.csv'

# ✅ Correct - valid path
data_path: 'ml_backtester/data/EURUSD_m15_2022_2025.parquet'
```

### Incompatible Mode Settings
```yaml
# ❌ Wrong - can't optimize without enabled flag
run_mode: 'optimize'
optimization:
  enabled: false

# ✅ Correct - matching settings
run_mode: 'optimize'  
optimization:
  enabled: true
```

### Invalid Strategy Names
```yaml
# ❌ Wrong - strategy doesn't exist
strategy:
  name: ['non_existent_strategy']

# ✅ Correct - valid strategy name  
strategy:
  name: ['triple_threat']
```

## 📊 Configuration Examples

### Conservative Long-Term Trading
```yaml
risk_management:
  risk_per_trade: 0.005      # 0.5% risk per trade
  sl_atr_multiplier: 3.0     # Wide stop losses
  tp_atr_multiplier: 6.0     # 1:2 risk-reward ratio

strategy:
  name: ['triple_threat']    # Trend-following strategy

backtesting:
  initial_capital: 100000    # $100k starting capital
```

### Aggressive Day Trading
```yaml
risk_management:
  risk_per_trade: 0.02       # 2% risk per trade
  sl_atr_multiplier: 1.0     # Tight stop losses
  tp_atr_multiplier: 1.5     # Quick profit targets

execution:
  slippage_percent: 0.001    # Account for faster execution

strategy:
  name: ['bounce_back']      # Mean reversion strategy
```

### Machine Learning Development
```yaml
run_mode: 'train'            # Training mode only

modeling:
  epochs: 100                # Extensive training
  validation_split: 0.2      # 20% validation data
  
strategy:
  name: ['cnn_lstm_strategy'] # ML-based strategy

logging:
  level: 'DEBUG'             # Detailed training logs
```

This parameter reference provides comprehensive guidance for configuring the BKWF Trading Framework. Adjust parameters based on your trading style, risk tolerance, and market conditions.