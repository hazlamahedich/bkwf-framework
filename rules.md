
# Claude.md: Coding Standards & Rules for Backtesting Framework

---

## 🧼 1. General Coding Principles
- ✅ Follow **PEP 8** for Python code formatting.
- ✅ Write **clear, consistent, and self-explanatory code**. Avoid clever hacks.
- ✅ Use **type hints** in all function definitions and class methods.
- ✅ Prefer **pure functions** and **stateless agents** unless state is necessary (like model cache).
- ✅ Group related logic into **modular agents** (e.g., data_agent.py, modeling_agent.py).
- ✅ Minimize global variables. Use config files or passed parameters.
- ✅ All modules must be **cross-platform compatible** (works on macOS, Linux, Windows).

---

## 🏗️ 2. Project Structure & Naming
- ✅ Use the following folder layout:

```
/ml_backtester/
├── agents/                    # Each agent in its own module
├── models/                    # Deep learning model definitions
├── configs/                   # YAML or JSON config files
├── utils/                     # Helper functions/utilities
├── logs/                      # Auto-generated logs
├── reports/                   # Backtest result exports
└── run_backtest.py            # Pipeline runner
```

- ✅ Use **snake_case** for files, variables, functions.
- ✅ Use **PascalCase** for class names (e.g., `DataAgent`, `WalkForwardAgent`).

---

## 📦 3. Modularity & Agent Architecture
- ✅ Each agent must:
  - Inherit from a base `Agent` class (optional but useful for structure).
  - Have a `run()` or `execute()` method as the main entry point.
  - Accept and return data as Python `dict`, `dataclass`, or Pandas DataFrame.
- ✅ Agents must not have hard-coded dependencies on each other.
- ✅ Use the `CoordinatorAgent` to orchestrate all interactions.

---

## 📋 4. Documentation
- ✅ Every function and class must have a **docstring** using the **Google style** or **NumPy style**.
- ✅ All public-facing modules must have a header with:
  - Purpose of the module
  - Author and date
  - Example usage if applicable

Example:
```python
def generate_signals(prices: pd.DataFrame) -> pd.DataFrame:
    """
    Generate buy/sell signals using model predictions.

    Args:
        prices (pd.DataFrame): OHLCV data with features.

    Returns:
        pd.DataFrame: DataFrame with signal column added.
    """
```

---

## 🔍 5. Logging & Debugging
- ✅ Use the `loguru` or built-in `logging` module for all logs.
- ✅ Never use print statements in production modules.
- ✅ Log important events like:
  - Model training start/finish
  - Backtest start/end
  - Strategy signal generation
  - Risk trigger violations

---

## 🧪 6. Testing & Validation
- ✅ Use `pytest` or `unittest` to test key modules (especially feature engineering, risk agent, backtesting logic).
- ✅ Ensure:
  - Agent input/output shape consistency
  - No NaNs/unexpected values passed between agents
  - Model predictions are within expected ranges
- ✅ Every agent must be independently testable with a mock config.

---

## 🧠 7. Deep Learning Practices
- ✅ Use Apple-optimized packages: `tensorflow-macos` or `torch` with MPS.
- ✅ Save models with versioning (e.g., `model_v1_fold3.h5`).
- ✅ Separate training vs inference logic (e.g., `train_model()`, `predict_signals()`).
- ✅ All models must be trained and tested using **walk-forward** or **time-series splits** — never random splits.
- ✅ Use Optuna trials only in `ModelingAgent`.

---

## 🧾 8. Configuration & Parameters
- ✅ All hyperparameters and settings must be placed in a `config.yaml` file.
- ✅ Do not hardcode symbols, timeframes, or model types.
- ✅ Use environment variables (e.g., `.env`) for API keys and MT5 credentials.

---

## 📈 9. Reporting & Outputs
- ✅ Save all metrics in CSV and JSON format for reproducibility.
- ✅ Visualize:
  - Equity curve
  - Signal overlay on price chart
  - Confusion matrix for ML models
- ✅ Reports must include timestamps, version numbers, and symbol info.

---

## 💣 10. Safety & Risk Control
- ✅ Backtests must fail if:
  - NaNs exist in critical data
  - Position sizing exceeds configured leverage/risk
  - Missing model file or corrupted data
- ✅ Validate all input data for completeness before processing.

---

## 🧹 Bonus: Code Hygiene Checklist
- [ ] No `print()` statements
- [ ] All functions documented
- [ ] Config-driven, no magic numbers
- [ ] Logs generated
- [ ] Test run with mock data before pushing
