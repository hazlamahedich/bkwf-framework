You're a senior quant developer and software engineer.

Create a modular Python framework for backtesting and walk-forward analysis of trading strategies that are powered by machine learning and deep learning (e.g., CNN-LSTM, Random Forest). The system must follow an **agentic architecture**, where each module (agent) is responsible for one part of the pipeline.

The framework should be designed to:
- Load historical OHLCV data
- Engineer features and technical indicators
- Train and optimize ML/DL models
- Run backtests and walk-forward validations
- Generate trade signals based on model outputs
- Manage risk (position sizing, SL/TP, exposure)
- Simulate or perform executions
- Log and visualize results
- Handle multiple symbols and timeframes
- Be OS-agnostic and modular

Each agent must be a class or module, interacting via a central `CoordinatorAgent`. Use simple, reusable data exchange formats (like Python dicts or dataclasses). Implement at least one full working example end-to-end using a CNN-LSTM model.

Agent Overview:

1. 🧮 **DataAgent**
   - Loads OHLCV data from CSV, MT5, or API.
   - Fills NaNs, handles missing values, resamples if needed.

2. 📊 **FeatureEngineeringAgent**
   - Computes technical indicators: RSI, MACD, Bollinger Bands, EMA, etc.
   - Optionally performs rolling stats (mean, std, momentum).
   - Normalizes or scales data for modeling (MinMax or StandardScaler).
   - Returns features `X` and targets `y`.

3. 🧠 **ModelingAgent**
   - Trains models like CNN-LSTM, LSTM, or RandomForest.
   - Uses Optuna to optimize hyperparameters.
   - Implements time-series cross-validation.
   - Saves trained models and their performance metrics.

4. 🎯 **StrategyAgent**
   - Loads the trained model and uses it to generate buy/sell/hold signals on unseen data.
   - Translates predictions (e.g., [0.9, 0.1, 0.0]) into trade actions.

5. 🧪 **BacktestingAgent**
   - Simulates trades based on signals and historical data.
   - Calculates metrics like Sharpe ratio, win rate, max drawdown, and equity curve.
   - Supports multi-symbol strategies and multiple timeframes.

6. 🚶‍♂️ **WalkForwardAgent**
   - Implements walk-forward validation:
     - Rolling train-test splits.
     - Retrains model on each rolling window.
     - Collects and logs performance metrics per fold.

7. ⚖️ **RiskManagementAgent**
   - Applies risk rules:
     - Position sizing based on risk % or volatility.
     - Stop-loss and take-profit calculation.
     - Max drawdown or exposure limits.
     - Handles capital allocation for portfolio trading.

8. 💹 **ExecutionAgent**
   - Simulates trade execution in backtest mode.
   - Models slippage, spreads, latency.
   - Can be extended to place real orders in MetaTrader 5.

9. 📈 **AnalyticsAgent**
   - Aggregates and visualizes metrics (matplotlib, Plotly, seaborn).
   - Saves logs, model reports, and trade history.
   - Optionally recommends improvements (e.g., indicators with most predictive power).

10. 🤝 **CoordinatorAgent**
    - Manages pipeline execution:
      - Load → Feature → Train → Predict → Backtest → Walkforward → Report
    - Coordinates interaction between agents
    - Loads external configs (JSON or YAML)

Also include:
- Modular folder structure:

/ml_backtester/
│
├── agents/
│   ├── data_agent.py
│   ├── feature_engineering_agent.py
│   ├── modeling_agent.py
│   ├── strategy_agent.py
│   ├── backtesting_agent.py
│   ├── walk_forward_agent.py
│   ├── risk_management_agent.py
│   ├── execution_agent.py
│   ├── analytics_agent.py
│   └── coordinator_agent.py
│
├── models/
│   └── cnn_lstm_model.py
│
├── configs/
│   └── config.yaml
│
├── run_backtest.py
└── utils/
└── helpers.py

Final goal:
Build an agentic, deep-learning-first backtesting and walk-forward framework with CNN-LSTM integration. Provide clear documentation and examples. First deliver a basic working version using synthetic data or any common dataset (like EURUSD 15m or BTC/USDT 1h).

Optional (if time allows): implement model explainability tools (e.g., SHAP or LIME) for predictions.