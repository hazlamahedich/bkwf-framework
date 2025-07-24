# Platform Deployment Guide

Complete guide for deploying BKWF framework strategies to MetaTrader 5 and TradingView platforms.

## 🚀 Overview

The BKWF framework generates optimized trading strategies in two formats:

- **MetaTrader 5 Expert Advisors (.mq5)**: Automated trading robots for MT5 platform
- **TradingView Pine Scripts (.pine)**: Custom indicators and strategies for TradingView

## 📊 MetaTrader 5 Expert Advisor Deployment

### Prerequisites

1. **MetaTrader 5 Terminal**: Download from your broker or [MetaQuotes](https://www.metatrader5.com/)
2. **Active Trading Account**: Demo or live account with MT5 access
3. **Generated EA File**: Located in `ml_backtester/exports/`

### Step 1: Locate Your Generated EA

After running the framework with export enabled, find your EA file:
```
ml_backtester/exports/
├── triple_threat_optimized.mq5
├── bounce_back_optimized.mq5
└── cnn_lstm_strategy_optimized.mq5  # (if supported)
```

### Step 2: Install the Expert Advisor

#### Method A: Direct Copy (Recommended)
1. **Open MT5 Data Folder**:
   - In MT5: File → Open Data Folder
   - Or press `Ctrl+Shift+D`

2. **Navigate to Experts Folder**:
   ```
   MQL5/
   └── Experts/
   ```

3. **Copy EA File**:
   - Copy your `.mq5` file to the `Experts` folder
   - Example: Copy `triple_threat_optimized.mq5` to `MQL5/Experts/`

4. **Compile the EA**:
   - In MT5: Tools → MetaQuotes Language Editor (or press `F4`)
   - Open your EA file
   - Press `F7` or click Compile button
   - Ensure no compilation errors

#### Method B: MetaEditor Installation
1. **Open MetaEditor** (`F4` from MT5)
2. **Create New EA**:
   - File → New → Expert Advisor (template)
   - Name: `triple_threat_optimized`
   - Click Finish

3. **Replace Code**:
   - Delete template code
   - Copy-paste your generated EA code
   - Save file (`Ctrl+S`)
   - Compile (`F7`)

### Step 3: EA Configuration

#### Understanding EA Parameters
```mql5
// Generated EA Input Parameters
input double InpRiskPerTrade = 0.01;           // Risk per trade (1% of account)
input double InpSLMultiplier = 2.417992;       // Stop Loss ATR Multiplier (optimized)
input double InpTPMultiplier = 4.796378;       // Take Profit ATR Multiplier (optimized)  
input int    InpMAPeriod     = 200;            // EMA Period for Trend
input int    InpMACDFast     = 12;             // MACD Fast EMA
input int    InpMACDSlow     = 26;             // MACD Slow EMA
input int    InpMACDSignal   = 9;              // MACD Signal Line
input int    InpStochK       = 14;             // Stochastic %K
input int    InpStochD       = 3;              // Stochastic %D
input int    InpStochSlowing = 3;              // Stochastic Slowing
input int    InpATRPeriod    = 14;             // ATR Period for SL/TP
```

#### Key Parameter Explanations

| Parameter | Description | Recommended Range | Impact |
|-----------|-------------|-------------------|---------|
| `InpRiskPerTrade` | Risk percentage per trade | 0.005-0.02 | Higher = more risk, more profit potential |
| `InpSLMultiplier` | Stop-loss distance (ATR) | 1.0-5.0 | Higher = wider stops, fewer false exits |
| `InpTPMultiplier` | Take-profit distance (ATR) | 1.0-8.0 | Higher = larger targets, lower hit rate |
| `InpMAPeriod` | Trend filter period | 50-300 | Higher = slower trend detection |

### Step 4: Deploy EA to Chart

1. **Open Chart**:
   - Right-click in Market Watch
   - Select your trading pair (e.g., EURUSD)
   - Choose timeframe (M15 recommended for most strategies)

2. **Attach EA**:
   - In Navigator panel, expand "Expert Advisors"
   - Drag your EA onto the chart
   - Or double-click EA name

3. **Configure Settings**:
   ```
   Common Tab:
   ✓ Allow DLL imports
   ✓ Allow WebRequest
   ✓ Allow external experts imports
   
   Inputs Tab:
   - Adjust parameters if needed
   - Keep optimized values for best performance
   
   Trading Tab:
   - Maximum spread: 3-5 points (for EUR/USD)
   - Expert Advisors: Enable
   ```

4. **Enable Auto-Trading**:
   - Click "Auto Trading" button in toolbar
   - Button should turn green
   - Check "Expert Advisors" tab for status

### Step 5: Monitor EA Performance

#### EA Status Indicators
- **😊 Green smiley**: EA running normally
- **😐 Neutral face**: EA attached but conditions not met  
- **❌ Red X**: EA error or auto-trading disabled

#### Journal Messages
```
2025.01.24 10:15:32.123 triple_threat_optimized EURUSD,M15: Expert initialized successfully
2025.01.24 10:15:45.456 triple_threat_optimized EURUSD,M15: Long signal detected - conditions met
2025.01.24 10:15:45.567 triple_threat_optimized EURUSD,M15: Buy order placed at 1.0845
```

### Step 6: Risk Management Setup

#### Account Protection Settings
```mql5
// Add these inputs to your EA for additional safety
input double MaxLossPercent = 5.0;      // Maximum account loss %
input int    MaxDailyTrades = 10;       // Maximum trades per day
input double MaxDrawdown = 10.0;        // Maximum drawdown %
input string TradingHours = "00:00-23:59"; // Trading time window
```

#### Position Sizing Verification
The EA calculates lot size based on:
```
Lot Size = (Account Balance × Risk Per Trade) / (Stop Loss Distance × Pip Value)
```

Example for 1% risk on $10,000 account:
- Risk Amount: $100
- SL Distance: 50 pips  
- Pip Value: $1 (for EUR/USD mini lot)
- Lot Size: $100 / (50 × $1) = 2 mini lots (0.02 standard lots)

## 📈 TradingView Pine Script Deployment

### Prerequisites

1. **TradingView Account**: Free or paid subscription
2. **Generated Pine Script**: Located in `ml_backtester/exports/`
3. **Chart Access**: TradingView charting platform

### Step 1: Locate Your Generated Pine Script

```
ml_backtester/exports/
├── triple_threat_optimized.pine
├── bounce_back_optimized.pine
└── cnn_lstm_strategy_optimized.pine
```

### Step 2: Import to TradingView

#### Method A: Pine Editor
1. **Open TradingView**: Go to [tradingview.com](https://www.tradingview.com)
2. **Access Pine Editor**:
   - Bottom panel → Pine Editor tab
   - Or press `Alt+E`

3. **Create New Script**:
   - Click "Create new script"
   - Delete template code
   - Paste your generated Pine Script
   - Save with descriptive name

#### Method B: Direct Chart Import
1. **Open Chart**: Select your trading pair and timeframe
2. **Add Indicator**:
   - Click "Indicators" at top of chart
   - Search for "Pine Editor"
   - Click "Open Pine Editor"

3. **Load Script**:
   - Paste your generated code
   - Click "Add to Chart"

### Step 3: Understanding Pine Script Structure

#### Generated Pine Script Components
```pinescript
//@version=5
strategy("triple_threat Optimized", overlay=true, 
         initial_capital=100000, 
         default_qty_type=strategy.percent_of_equity, 
         default_qty_value=1)

// --- Optimized Parameters (from framework) ---
sl_atr_multiplier = input.float(2.417992, title="SL ATR Multiplier")
tp_atr_multiplier = input.float(4.796378, title="TP ATR Multiplier")

// --- Indicators ---
ema200 = ta.ema(close, 200)
[macd_line, signal_line, _] = ta.macd(close, 12, 26, 9)
stoch_k_line = ta.sma(ta.stoch(close, high, low, 14), 3)
atr = ta.atr(14)

// --- Strategy Logic ---
long_trend = close > ema200
long_momentum = macd_line > signal_line  
long_entry = ta.crossover(stoch_k_line, 20)

// --- Entry/Exit Logic ---
if (long_trend and long_momentum and long_entry)
    sl = close - (atr * sl_atr_multiplier)
    tp = close + (atr * tp_atr_multiplier)
    strategy.entry("Long", strategy.long)
    strategy.exit("Long Exit", from_entry="Long", stop=sl, limit=tp)
```

### Step 4: Configure Pine Script Settings

#### Strategy Settings Panel
```
Properties Tab:
- Initial Capital: $100,000
- Base Currency: USD  
- Order Size: 1% of equity
- Pyramiding: 1 (max positions)
- Commission: 0.05% (adjust for your broker)

Style Tab:
- Show trades on chart: ✓
- Show position size: ✓
- Show trade labels: ✓

Inputs Tab:
- SL ATR Multiplier: 2.418 (optimized value)
- TP ATR Multiplier: 4.796 (optimized value)
- Adjust other parameters as needed
```

#### Visual Customization
```pinescript
// Add to your Pine Script for better visualization
plot(ema200, title="EMA 200", color=color.orange, linewidth=2)
plotchar(long_entry, title="Long Entry", char="▲", location=location.belowbar, 
         color=color.green, size=size.small)
plotchar(short_entry, title="Short Entry", char="▼", location=location.abovebar, 
         color=color.red, size=size.small)

// Background color for trend
bgcolor(long_trend ? color.new(color.green, 95) : 
        short_trend ? color.new(color.red, 95) : na)
```

### Step 5: Backtesting on TradingView

#### Strategy Tester
1. **Open Strategy Tester**: Bottom panel → Strategy Tester tab
2. **Performance Summary**:
   - Net Profit: Total strategy profit/loss
   - Profit Factor: Gross profit / Gross loss  
   - Max Drawdown: Largest peak-to-trough decline
   - Sharpe Ratio: Risk-adjusted returns

3. **Trade List**: Review individual trades and performance

#### Comparison with Framework Results
```
Framework Results vs TradingView:
- Minor differences expected due to:
  • Different execution models
  • Spread/commission handling  
  • Bar close vs real-time execution
  • Data source variations
```

### Step 6: Live Trading Setup (TradingView)

#### Paper Trading
1. **Enable Paper Trading**:
   - Chart → Trading Panel
   - Select "Paper Trading"
   - Configure starting balance

2. **Auto-Trading** (Premium feature):
   - Connect broker account
   - Enable strategy auto-trading
   - Set position size limits

#### Alerts Setup
```pinescript
// Add alert functionality to your Pine Script
if (long_trend and long_momentum and long_entry)
    alert("Triple Threat: BUY signal on " + syminfo.ticker, alert.freq_once_per_bar)
    
if (short_trend and short_momentum and short_entry)  
    alert("Triple Threat: SELL signal on " + syminfo.ticker, alert.freq_once_per_bar)
```

## 🔧 Advanced Deployment Features

### Multi-Timeframe Setup

#### MT5 Multi-Chart Setup
1. **Create Chart Group**:
   - File → Open Chart → Select symbols
   - Arrange charts in preferred layout
   - File → Save Template

2. **Deploy EA to Multiple Charts**:
   - Use same EA on different timeframes
   - Adjust parameters for each timeframe
   - Monitor correlation between timeframes

#### TradingView Multi-Timeframe
```pinescript
// Add higher timeframe analysis
htf_trend = request.security(syminfo.tickerid, "240", ta.ema(close, 50))
current_above_htf = close > htf_trend

// Combine with existing conditions
long_trend = (close > ema200) and current_above_htf
```

### Performance Monitoring

#### MT5 Performance Tracking
```mql5
// Add performance tracking to EA
input bool ShowStats = true;
double initial_balance = AccountInfoDouble(ACCOUNT_BALANCE);
int total_trades = 0;
double max_profit = 0;
double max_loss = 0;

void UpdateStats()
{
    if (!ShowStats) return;
    
    double current_balance = AccountInfoDouble(ACCOUNT_BALANCE);
    double total_profit = current_balance - initial_balance;
    double profit_percent = (total_profit / initial_balance) * 100;
    
    Comment(StringFormat("EA Stats: %.2f%% | Trades: %d | Profit: $%.2f", 
            profit_percent, total_trades, total_profit));
}
```

#### TradingView Performance Dashboard
```pinescript
// Performance metrics table
if barstate.islast
    var table perf_table = table.new(position.top_right, 2, 5, 
                                   bgcolor=color.white, border_width=1)
    
    table.cell(perf_table, 0, 0, "Metric", text_color=color.black)
    table.cell(perf_table, 1, 0, "Value", text_color=color.black)
    
    table.cell(perf_table, 0, 1, "Net Profit", text_color=color.black)
    table.cell(perf_table, 1, 1, str.tostring(strategy.netprofit, "$#.##"), text_color=color.black)
    
    table.cell(perf_table, 0, 2, "Win Rate", text_color=color.black)
    win_rate = strategy.wintrades / strategy.closedtrades * 100
    table.cell(perf_table, 1, 2, str.tostring(win_rate, "#.#") + "%", text_color=color.black)
```

## 🚨 Troubleshooting Guide

### Common MT5 Issues

#### EA Not Trading
**Problem**: EA attached but no trades
**Solutions**:
- Check auto-trading is enabled (green button)
- Verify market is open
- Check spread limits in EA settings
- Review journal for error messages
- Ensure sufficient account balance

#### Compilation Errors
**Problem**: EA won't compile
**Solutions**:
```mql5
// Common fixes:
#property strict              // Add at top of file
#include <Trade\Trade.mqh>    // Include required libraries

// Fix common syntax errors:
input double Risk = 0.01;     // Use 'input' not 'extern'
```

#### Position Sizing Issues
**Problem**: Wrong lot sizes
**Solutions**:
- Check account currency vs symbol currency
- Verify broker lot size requirements (micro/mini/standard)
- Review risk calculation formula
- Test with demo account first

### Common TradingView Issues

#### Script Errors
**Problem**: Pine Script won't compile
**Solutions**:
```pinescript
// Version compatibility
//@version=5              // Always specify version

// Fix deprecated functions:
ta.sma(close, 14)         // Not: sma(close, 14)
ta.crossover(a, b)        // Not: crossover(a, b)
```

#### Performance Discrepancies
**Problem**: Results differ from framework
**Solutions**:
- Check timeframe alignment
- Verify indicator parameters match
- Account for different execution models
- Compare bar close vs real-time processing

#### Alert Issues
**Problem**: Alerts not firing
**Solutions**:
- Check alert syntax in Pine Script
- Verify alert frequency settings
- Ensure strategy conditions are met
- Check TradingView notification settings

## 📊 Performance Comparison

### Expected Performance Variations

| Platform | Execution Model | Typical Difference | Pros | Cons |
|----------|-----------------|-------------------|------|------|
| **Framework** | Vectorized backtesting | Baseline | Fast, accurate historical | No real-time execution |
| **MT5 EA** | Bar-by-bar execution | ±2-5% returns | Real-time trading | Slippage, spreads |
| **TradingView** | Bar close execution | ±1-3% returns | Visual backtesting | Limited live trading |

### Validation Checklist

#### Pre-Deployment
- [ ] Strategy parameters match optimized values
- [ ] Risk management settings configured
- [ ] Backtesting results reviewed and acceptable
- [ ] Demo testing completed successfully

#### Post-Deployment  
- [ ] EA/Script running without errors
- [ ] Position sizing working correctly
- [ ] Trade execution matching expected behavior
- [ ] Performance monitoring active

#### Ongoing Maintenance
- [ ] Regular performance review (weekly)
- [ ] Parameter adjustment if needed
- [ ] Risk management compliance
- [ ] Platform updates and compatibility

This comprehensive guide ensures successful deployment of your BKWF-generated strategies to both MetaTrader 5 and TradingView platforms, with proper risk management and performance monitoring.