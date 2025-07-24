# BKWF Trading Framework

A comprehensive machine learning-powered backtesting and strategy optimization framework for quantitative trading.

## 🚀 Overview

The BKWF (Backtesting & Knowledge-driven Workflow Framework) is an advanced algorithmic trading platform that combines:

- **Multi-Agent Architecture**: Specialized agents for data processing, feature engineering, strategy execution, and optimization
- **Machine Learning Integration**: CNN-LSTM models for predictive trading signals
- **Strategy Optimization**: Automated parameter tuning using Optuna
- **Multi-Platform Export**: Generate MT5 Expert Advisors and Pine Script indicators
- **Advanced Risk Management**: ATR-based position sizing and trailing stops
- **Comprehensive Analytics**: Detailed performance reports and visualizations

## 📁 Project Structure

```
bkwf framework/
├── ml_backtester/                 # Core framework
│   ├── agents/                    # Specialized processing agents
│   │   ├── analytics_agent.py     # Performance analytics
│   │   ├── backtesting_agent.py   # Strategy backtesting
│   │   ├── coordinator_agent.py   # Main orchestrator
│   │   ├── data_agent.py          # Data loading & preprocessing
│   │   ├── execution_agent.py     # Trade execution simulation
│   │   ├── export_agent.py        # MT5/Pine Script export
│   │   ├── feature_engineering_agent.py  # Technical indicators
│   │   ├── modeling_agent.py      # ML model training
│   │   ├── optimization_agent.py  # Parameter optimization
│   │   ├── risk_management_agent.py  # Risk controls
│   │   └── strategy_agent.py      # Strategy orchestration
│   ├── configs/
│   │   └── config.yaml            # Main configuration file
│   ├── data/                      # Market data storage
│   ├── exports/                   # Generated EA/Pine files
│   ├── models/                    # Trained ML models
│   ├── reports/                   # Performance reports
│   ├── strategies/                # Trading strategy implementations
│   │   ├── base_strategy.py       # Strategy base class
│   │   ├── bounce_back.py         # Mean reversion strategy
│   │   ├── cnn_lstm_strategy.py   # ML-based strategy
│   │   └── triple_threat.py       # Multi-indicator strategy
│   └── utils/                     # Helper utilities
├── run_backtest.py               # Main execution script
└── requirements.txt              # Python dependencies
```

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.8+
- 8GB+ RAM recommended
- MetaTrader 5 (optional, for live trading)
- TradingView account (optional, for Pine Script deployment)

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd "bkwf framework"
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Prepare data directory**
   ```bash
   mkdir -p ml_backtester/data
   mkdir -p ml_backtester/logs
   mkdir -p ml_backtester/reports
   mkdir -p ml_backtester/exports
   ```

## 🎯 Quick Start

### Basic Backtesting

1. **Configure your settings** in `ml_backtester/configs/config.yaml`:
   ```yaml
   run_mode: 'backtest'
   data_path: 'ml_backtester/data/EURUSD_m15_2022_2025.parquet'
   strategy:
     name: 
       - 'triple_threat'
   ```

2. **Run backtest**:
   ```bash
   python run_backtest.py --config ml_backtester/configs/config.yaml
   ```

3. **View results** in `ml_backtester/reports/`

### Strategy Optimization

1. **Enable optimization** in config:
   ```yaml
   run_mode: 'optimize_and_backtest'
   optimization:
     enabled: true
     n_trials: 100
   ```

2. **Run optimization**:
   ```bash
   python run_backtest.py
   ```

### Export to Trading Platforms

1. **Enable export** in config:
   ```yaml
   export:
     enabled: true
     formats: ['mt5', 'pinescript']
   ```

2. **Generated files** will be in `ml_backtester/exports/`

## 📊 Available Strategies

### Triple Threat Strategy
- **Concept**: Multi-timeframe trend-following system
- **Components**: EMA trend filter + MACD momentum + Stochastic entries
- **Best for**: Trending markets with clear directional bias
- **Risk Level**: Medium

### Bounce Back Strategy  
- **Concept**: Mean reversion with dynamic support/resistance
- **Components**: Oversold/overbought conditions + price action
- **Best for**: Range-bound or sideways markets
- **Risk Level**: Medium-High

### CNN-LSTM Strategy
- **Concept**: Deep learning predictive model
- **Components**: Convolutional Neural Network + Long Short-Term Memory
- **Best for**: Complex pattern recognition across multiple timeframes
- **Risk Level**: High (requires extensive training data)

## ⚙️ Configuration System

The framework uses a centralized YAML configuration system. Key sections:

- **Data Configuration**: Source files and preprocessing
- **Feature Engineering**: Technical indicators and transformations
- **Strategy Parameters**: Strategy-specific settings
- **Risk Management**: Position sizing and stop-loss rules
- **Optimization**: Parameter search spaces
- **Export Settings**: Output format preferences

See `PARAMETER_REFERENCE.md` for detailed configuration options.

## 📈 Performance Metrics

The framework provides comprehensive analytics:

- **Return Metrics**: Total return, annualized return, Sharpe ratio
- **Risk Metrics**: Maximum drawdown, volatility, VaR
- **Trade Statistics**: Win rate, profit factor, average trade duration
- **Visual Reports**: Equity curves, drawdown charts, trade distribution

## 🔧 Advanced Features

### Walk-Forward Analysis
- Out-of-sample testing with rolling optimization windows
- Prevents overfitting and provides realistic performance estimates

### Multi-Asset Support
- Simultaneous backtesting across multiple instruments
- Portfolio-level risk management and allocation

### Custom Indicators
- Easy integration of proprietary technical indicators
- Pandas-TA integration for 100+ built-in indicators

### API Server
- RESTful API for integration with external systems
- Real-time strategy monitoring and control

## 🎛️ API Usage

Start the API server:
```bash
python ml_backtester/api_server.py
```

Example endpoints:
- `GET /health` - System status
- `POST /backtest` - Run backtest with JSON config
- `GET /strategies` - List available strategies
- `POST /optimize` - Run parameter optimization

## 🐛 Troubleshooting

### Common Issues

1. **Memory errors**: Reduce dataset size or increase system RAM
2. **Missing indicators**: Check pandas-ta installation
3. **Export failures**: Verify output directory permissions
4. **Model training issues**: Ensure sufficient training data (>1000 samples)

### Debug Mode
Enable detailed logging:
```yaml
logging:
  level: 'DEBUG'
```

### Performance Tips
- Use Parquet format for large datasets
- Enable parallel processing for optimization
- Consider GPU acceleration for deep learning models

## 📚 Documentation

- `PARAMETER_REFERENCE.md` - Complete configuration guide
- `DATA_IMPORT_GUIDE.md` - Import data from MT5/TradingView
- `PLATFORM_DEPLOYMENT.md` - MT5 EA and Pine Script setup

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is proprietary software. All rights reserved.

## 📞 Support

For technical support or feature requests:
- Create an issue in the repository
- Contact the development team
- Check the documentation wiki

---

**Disclaimer**: This framework is for educational and research purposes. Past performance does not guarantee future results. Always conduct thorough testing before live trading.