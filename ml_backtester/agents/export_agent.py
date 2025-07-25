import logging
import platform
import socket
from typing import Dict, Any
from pathlib import Path

class ExportAgent:
    """
    Agent for exporting optimized strategies to different platforms.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initializes the ExportAgent.

        Args:
            config (Dict[str, Any]): Configuration dictionary.
        """
        self.config = config
        self.export_path = Path(self.config.get('export', {}).get('path', 'ml_backtester/exports'))
        self.export_path.mkdir(exist_ok=True)
        logging.info(f"ExportAgent initialized. Export path: '{self.export_path}'")

    def execute(self, strategy_name: str, best_params: Dict[str, Any], backtest_results: Dict[str, Any]):
        """
        Executes the export process for the given strategy.

        Args:
            strategy_name (str): The name of the strategy to export.
            best_params (Dict[str, Any]): The best parameters found during optimization.
            backtest_results (Dict[str, Any]): The results from the final backtest run.
        """
        export_formats = self.config.get('export', {}).get('formats', [])
        if not export_formats:
            logging.warning("No export formats specified in the config. Skipping export.")
            return

        logging.info(f"Exporting strategy '{strategy_name}' with params: {best_params}")

        if 'mt5' in export_formats:
            self._export_to_mt5(strategy_name, best_params, backtest_results)

        if 'pinescript' in export_formats:
            self._export_to_pinescript(strategy_name, best_params, backtest_results)

    def _export_to_mt5(self, strategy_name: str, best_params: Dict[str, Any], backtest_results: Dict[str, Any]):
        """
        Exports the strategy to a MetaTrader 5 Expert Advisor (.mq5 file).
        """
        logging.info(f"Generating MT5 EA for '{strategy_name}'...")
        mt5_code = self._generate_mt5_code(strategy_name, best_params)
        symbol = self.config.get('symbol', 'default_symbol')
        timeframe = self.config.get('timeframe', 'H1')
        
        filename_parts = [symbol, timeframe, strategy_name]
        if 'cnn_lstm_strategy' in strategy_name:
            model_type = self.config.get('modeling', {}).get('model_type')
            if model_type:
                filename_parts.append(model_type)
        
        file_path = self.export_path / f"{'_'.join(filename_parts)}_optimized.mq5"
        with open(file_path, 'w') as f:
            f.write(mt5_code)
        logging.info(f"MT5 EA saved to '{file_path}'")

    def _export_to_pinescript(self, strategy_name: str, best_params: Dict[str, Any], backtest_results: Dict[str, Any]):
        """
        Exports the strategy to a TradingView PineScript (.pine file).
        """
        logging.info(f"Generating PineScript for '{strategy_name}'...")
        pinescript_code = self._generate_pinescript_code(strategy_name, best_params)
        symbol = self.config.get('symbol', 'default_symbol')
        timeframe = self.config.get('timeframe', 'H1')

        filename_parts = [symbol, timeframe, strategy_name]
        if 'cnn_lstm_strategy' in strategy_name:
            model_type = self.config.get('modeling', {}).get('model_type')
            if model_type:
                filename_parts.append(model_type)

        file_path = self.export_path / f"{'_'.join(filename_parts)}_optimized.pine"
        with open(file_path, 'w') as f:
            f.write(pinescript_code)
        logging.info(f"PineScript saved to '{file_path}'")

    def _get_api_endpoint(self) -> str:
        """
        Determines the local IP address to construct the API endpoint.
        """
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # Doesn't have to be reachable
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
        except Exception:
            ip = "127.0.0.1" # Fallback to localhost
        
        port = self.config.get('api_server', {}).get('port', 5001)
        return f"http://{ip}:{port}/predict"

    def _generate_mt5_code(self, strategy_name: str, best_params: Dict[str, Any]) -> str:
        """
        Generates the MQL5 code for the strategy.
        """
        if strategy_name == 'triple_threat':
            return self._generate_mt5_for_triple_threat(strategy_name, best_params)
        elif strategy_name == 'bounce_back':
            return self._generate_mt5_for_bounce_back(strategy_name, best_params)
        elif strategy_name == 'cnn_lstm_strategy':
           return self._generate_mt5_for_cnn_lstm(strategy_name, best_params)
        else:
            return f"// Strategy '{strategy_name}' is not supported for MT5 export yet."

    def _generate_mt5_for_triple_threat(self, strategy_name: str, best_params: Dict[str, Any]) -> str:
        sl_multiplier = best_params.get('sl_atr_multiplier', 2.0)
        tp_multiplier = best_params.get('tp_atr_multiplier', 3.0)
        risk_per_trade = self.config.get('risk_management', {}).get('risk_per_trade', 0.01)

        return f"""
//+------------------------------------------------------------------+
//|                  {strategy_name}_Optimized.mq5                     |
//|      Generated by ML Backtester Framework - Copyright 2025       |
//+------------------------------------------------------------------+
#property copyright "Copyright 2025, ML Backtester Framework"
#property link      "https://github.com/your_repo"
#property version   "1.00"
#property strict

#include <Trade\\Trade.mqh>
#include <Trade\\SymbolInfo.mqh>

//--- Optimized Input Parameters
input double InpRiskPerTrade = {risk_per_trade};      // Risk per trade as a percentage of account balance
input double InpSLMultiplier = {sl_multiplier};    // Stop Loss ATR Multiplier
input double InpTPMultiplier = {tp_multiplier};    // Take Profit ATR Multiplier
input int    InpMAPeriod     = 200;      // EMA Period for Trend
input int    InpMACDFast     = 12;       // MACD Fast EMA
input int    InpMACDSlow     = 26;       // MACD Slow EMA
input int    InpMACDSignal   = 9;        // MACD Signal Line
input int    InpStochK       = 14;       // Stochastic %K
input int    InpStochD       = 3;        // Stochastic %D
input int    InpStochSlowing = 3;        // Stochastic Slowing
input int    InpATRPeriod    = 14;       // ATR Period for SL/TP

//--- Global Variables
CTrade      trade;
CSymbolInfo symbol;
datetime    lastBarTime = 0;

//--- Indicator Handles
int ema_handle;
int macd_handle;
int stoch_handle;
int atr_handle;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
  {{
   symbol.Name(_Symbol);
   trade.SetExpertMagicNumber(12345);
   trade.SetMarginMode();

   ema_handle = iMA(_Symbol, _Period, InpMAPeriod, 0, MODE_EMA, PRICE_CLOSE);
   macd_handle = iMACD(_Symbol, _Period, InpMACDFast, InpMACDSlow, InpMACDSignal, PRICE_CLOSE);
   stoch_handle = iStochastic(_Symbol, _Period, InpStochK, InpStochD, InpStochSlowing, MODE_SMA, STO_LOWHIGH);
   atr_handle = iATR(_Symbol, _Period, InpATRPeriod);

   if(ema_handle < 0 || macd_handle < 0 || stoch_handle < 0 || atr_handle < 0)
     {{
      printf("Error initializing indicators");
      return(INIT_FAILED);
     }}

   return(INIT_SUCCEEDED);
  }}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
  {{
   IndicatorRelease(ema_handle);
   IndicatorRelease(macd_handle);
   IndicatorRelease(stoch_handle);
   IndicatorRelease(atr_handle);
  }}

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
  {{
   if(IsNewBar())
     {{
      CheckForSignal();
     }}
  }}

//+------------------------------------------------------------------+
//| Check for trading signals                                        |
//+------------------------------------------------------------------+
void CheckForSignal()
  {{
   // --- Get Indicator Values ---
   double ema[], macd_main[], macd_signal[], stoch_main[], stoch_signal[], atr[];
   if(CopyBuffer(ema_handle, 0, 1, 1, ema) <= 0 ||
      CopyBuffer(macd_handle, 0, 1, 2, macd_main) <= 0 ||
      CopyBuffer(macd_handle, 1, 1, 2, macd_signal) <= 0 ||
      CopyBuffer(stoch_handle, 0, 1, 2, stoch_main) <= 0 ||
      CopyBuffer(stoch_handle, 1, 1, 2, stoch_signal) <= 0 ||
      CopyBuffer(atr_handle, 0, 1, 1, atr) <= 0)
     {{
      printf("Error copying indicator buffers");
      return;
     }}

   MqlRates rates[2];
   if(CopyRates(_Symbol, _Period, 1, 2, rates) < 2) return;
   double current_close = rates[1].close;
   double prev_stoch_main = stoch_main[1];

   // --- Trading Conditions ---
   bool long_trend = current_close > ema[0];
   bool long_momentum = macd_main[0] > macd_signal[0];
   bool long_entry = stoch_main[0] > prev_stoch_main && prev_stoch_main < 20;

   bool short_trend = current_close < ema[0];
   bool short_momentum = macd_main[0] < macd_signal[0];
   bool short_entry = stoch_main[0] < prev_stoch_main && prev_stoch_main > 80;

   // --- Execution ---
   if(PositionsTotal() == 0)
     {{
      double lot_size = CalculateLotSize(atr[0]);
      double sl = 0, tp = 0;

      if(long_trend && long_momentum && long_entry)
        {{
         sl = symbol.Ask() - atr[0] * InpSLMultiplier;
         tp = symbol.Ask() + atr[0] * InpTPMultiplier;
         trade.Buy(lot_size, _Symbol, symbol.Ask(), sl, tp, "Buy Signal");
        }}
      else if(short_trend && short_momentum && short_entry)
        {{
         sl = symbol.Bid() + atr[0] * InpSLMultiplier;
         tp = symbol.Bid() - atr[0] * InpTPMultiplier;
         trade.Sell(lot_size, _Symbol, symbol.Bid(), sl, tp, "Sell Signal");
        }}
     }}
  }}

//+------------------------------------------------------------------+
//| Calculate Lot Size based on risk                                 |
//+------------------------------------------------------------------+
double CalculateLotSize(double atr_value)
  {{
   double account_balance = AccountInfoDouble(ACCOUNT_BALANCE);
   double risk_amount = account_balance * InpRiskPerTrade;
   double sl_pips = atr_value * InpSLMultiplier;
   
   if(sl_pips == 0) return 0.01;

   double tick_value = symbol.TickValue();
   double lot_size = risk_amount / (sl_pips * tick_value);

   lot_size = NormalizeDouble(lot_size, 2);
   if(lot_size < symbol.LotsMin()) lot_size = symbol.LotsMin();
   if(lot_size > symbol.LotsMax()) lot_size = symbol.LotsMax();
   
   return lot_size;
  }}

//+------------------------------------------------------------------+
//| Check for a new bar                                              |
//+------------------------------------------------------------------+
bool IsNewBar()
  {{
   datetime server_time = TimeCurrent();
   if(lastBarTime != iTime(_Symbol, _Period, 0))
     {{
      lastBarTime = iTime(_Symbol, _Period, 0);
      return(true);
     }}
   return(false);
  }}
//+------------------------------------------------------------------+
"""

    def _generate_pinescript_code(self, strategy_name: str, best_params: Dict[str, Any]) -> str:
        """
        Generates the PineScript code for the strategy.
        """
        if strategy_name == 'triple_threat':
            return self._generate_pinescript_for_triple_threat(strategy_name, best_params)
        elif strategy_name == 'bounce_back':
            return self._generate_pinescript_for_bounce_back(strategy_name, best_params)
        elif strategy_name == 'cnn_lstm_strategy':
            return self._generate_pinescript_for_cnn_lstm(strategy_name, best_params)
        else:
            return f"// Strategy '{strategy_name}' is not supported for PineScript export yet."

    def _generate_pinescript_for_triple_threat(self, strategy_name: str, best_params: Dict[str, Any]) -> str:
        sl_multiplier = best_params.get('sl_atr_multiplier', 2.0)
        tp_multiplier = best_params.get('tp_atr_multiplier', 3.0)

        return f"""
//@version=5
strategy("{strategy_name} Optimized", overlay=true, initial_capital=100000, default_qty_type=strategy.percent_of_equity, default_qty_value=1)

// --- Optimized Parameters ---
sl_atr_multiplier = input.float({sl_multiplier}, title="SL ATR Multiplier")
tp_atr_multiplier = input.float({tp_multiplier}, title="TP ATR Multiplier")
ema_len = input.int(200, title="EMA Length")
macd_fast = input.int(12, title="MACD Fast Length")
macd_slow = input.int(26, title="MACD Slow Length")
macd_signal = input.int(9, title="MACD Signal Length")
stoch_k = input.int(14, title="Stochastic %K")
stoch_d = input.int(3, title="Stochastic %D")
stoch_smooth = input.int(3, title="Stochastic Smoothing")
atr_len = input.int(14, title="ATR Length")

// --- Indicators ---
ema200 = ta.ema(close, ema_len)
[macd_line, signal_line, _] = ta.macd(close, macd_fast, macd_slow, macd_signal)
stoch_k_line = ta.sma(ta.stoch(close, high, low, stoch_k), stoch_smooth)
atr = ta.atr(atr_len)

// --- Plotting Indicators ---
plot(ema200, title="EMA 200", color=color.orange)

// --- Strategy Conditions ---
long_trend = close > ema200
long_momentum = macd_line > signal_line
long_entry = ta.crossover(stoch_k_line, 20)

short_trend = close < ema200
short_momentum = macd_line < signal_line
short_entry = ta.crossunder(stoch_k_line, 80)

// --- Execution Logic ---
if (long_trend and long_momentum and long_entry)
    sl = close - (atr * sl_atr_multiplier)
    tp = close + (atr * tp_atr_multiplier)
    strategy.entry("Long", strategy.long)
    strategy.exit("Long Exit", from_entry="Long", stop=sl, limit=tp)

if (short_trend and short_momentum and short_entry)
    sl = close + (atr * sl_atr_multiplier)
    tp = close - (atr * tp_atr_multiplier)
    strategy.entry("Short", strategy.short)
    strategy.exit("Short Exit", from_entry="Short", stop=sl, limit=tp)
"""

    def _generate_mt5_for_bounce_back(self, strategy_name: str, best_params: Dict[str, Any]) -> str:
        sl_multiplier = best_params.get('sl_atr_multiplier', 2.0)
        tp_multiplier = best_params.get('tp_atr_multiplier', 3.0)
        risk_per_trade = self.config.get('risk_management', {}).get('risk_per_trade', 0.01)
        fib_window = self.config.get('fib_window', 252)
        rsi_period = self.config.get('rsi_period', 14)

        return f"""
#property copyright "Copyright 2025, ML Backtester Framework"
#property link      "https://github.com/your_repo"
#property version   "1.00"

#include <Trade\\Trade.mqh>

//--- Input Parameters
input double InpRiskPerTrade = {risk_per_trade};
input double InpSLMultiplier = {sl_multiplier};
input double InpTPMultiplier = {tp_multiplier};
input int    InpFibWindow    = {fib_window};
input int    InpRsiPeriod    = {rsi_period};
input int    InpATRPeriod    = 14;

CTrade trade;
datetime lastBarTime = 0;

int rsi_handle;
int atr_handle;

int OnInit() {{
    rsi_handle = iRSI(_Symbol, _Period, InpRsiPeriod, PRICE_CLOSE);
    atr_handle = iATR(_Symbol, _Period, InpATRPeriod);
    return(INIT_SUCCEEDED);
}}

void OnDeinit(const int reason) {{
    IndicatorRelease(rsi_handle);
    IndicatorRelease(atr_handle);
}}

void OnTick() {{
    if(IsNewBar()) {{
        CheckForSignal();
    }}
}}

void CheckForSignal() {{
    MqlRates rates[3];
    if(CopyRates(_Symbol, _Period, 0, 3, rates) < 3) return;

    double rsi_buffer[2];
    if(CopyBuffer(rsi_handle, 0, 1, 2, rsi_buffer) <= 0) return;

    double high_fib = High[iHighest(_Symbol, _Period, MODE_HIGH, InpFibWindow, 1)];
    double low_fib = Low[iLowest(_Symbol, _Period, MODE_LOW, InpFibWindow, 1)];
    double fib_50 = low_fib + 0.5 * (high_fib - low_fib);
    double fib_618 = low_fib + 0.618 * (high_fib - low_fib);

    bool is_bullish_engulfing = rates[1].close > rates[2].open && rates[1].open < rates[2].close && (rates[1].close - rates[1].open) > (rates[2].open - rates[2].close);
    bool is_bearish_engulfing = rates[1].open > rates[2].close && rates[1].close < rates[2].open && (rates[1].open - rates[1].close) > (rates[2].close - rates[2].open);
    
    bool bullish_divergence = rates[1].low < rates[2].low && rsi_buffer[0] > rsi_buffer[1];
    bool bearish_divergence = rates[1].high > rates[2].high && rsi_buffer[0] < rsi_buffer[1];

    bool at_support = rates[1].low <= fib_50 || rates[1].low <= fib_618;
    bool at_resistance = rates[1].high >= fib_50 || rates[1].high >= fib_618;

    double atr_val[1];
    CopyBuffer(atr_handle, 0, 0, 1, atr_val);

    if (at_support && is_bullish_engulfing && bullish_divergence) {{
        double sl = rates[1].close - atr_val[0] * InpSLMultiplier;
        double tp = rates[1].close + atr_val[0] * InpTPMultiplier;
        trade.Buy(CalculateLotSize(atr_val[0]), _Symbol, SymbolInfoDouble(_Symbol, SYMBOL_ASK), sl, tp);
    }}

    if (at_resistance && is_bearish_engulfing && bearish_divergence) {{
        double sl = rates[1].close + atr_val[0] * InpSLMultiplier;
        double tp = rates[1].close - atr_val[0] * InpTPMultiplier;
        trade.Sell(CalculateLotSize(atr_val[0]), _Symbol, SymbolInfoDouble(_Symbol, SYMBOL_BID), sl, tp);
    }}
}}

bool IsNewBar() {{
    datetime server_time = TimeCurrent();
    if(lastBarTime != iTime(_Symbol, _Period, 0)) {{
        lastBarTime = iTime(_Symbol, _Period, 0);
        return(true);
    }}
    return(false);
}}

double CalculateLotSize(double atr_value) {{
   double account_balance = AccountInfoDouble(ACCOUNT_BALANCE);
   double risk_amount = account_balance * InpRiskPerTrade;
   double sl_pips = atr_value * InpSLMultiplier;
   if(sl_pips == 0) return 0.01;
   double tick_value = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
   double lot_size = risk_amount / (sl_pips * tick_value);
   lot_size = NormalizeDouble(lot_size, 2);
   if(lot_size < SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN)) lot_size = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   if(lot_size > SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX)) lot_size = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   return lot_size;
}}
"""

    def _generate_pinescript_for_bounce_back(self, best_params: Dict[str, Any]) -> str:
        sl_multiplier = best_params.get('sl_atr_multiplier', 2.0)
        tp_multiplier = best_params.get('tp_atr_multiplier', 3.0)
        fib_window = self.config.get('fib_window', 252)
        rsi_period = self.config.get('rsi_period', 14)

        return f"""
//@version=5
strategy("Bounce Back Optimized", overlay=true)

// --- Parameters ---
sl_atr_multiplier = input.float({sl_multiplier}, title="SL ATR Multiplier")
tp_atr_multiplier = input.float({tp_multiplier}, title="TP ATR Multiplier")
fib_window = input.int({fib_window}, title="Fibonacci Window")
rsi_period = input.int({rsi_period}, title="RSI Period")
atr_len = input.int(14, title="ATR Length")

// --- Indicators and Logic ---
rsi = ta.rsi(close, rsi_period)
atr = ta.atr(atr_len)

high_fib = ta.highest(high, fib_window)
low_fib = ta.lowest(low, fib_window)
fib_range = high_fib - low_fib
fib_50 = low_fib + 0.5 * fib_range
fib_618 = low_fib + 0.618 * fib_range

bullish_engulfing = close > open[1] and open < close[1] and (close - open) > (open[1] - close[1])
bearish_engulfing = open > close[1] and close < open[1] and (open - close) > (close[1] - open[1])

bullish_divergence = low < low[1] and rsi > rsi[1]
bearish_divergence = high > high[1] and rsi < rsi[1]

at_support = low <= fib_50 or low <= fib_618
at_resistance = high >= fib_50 or high >= fib_618

// --- Entry Conditions ---
long_signal = at_support and bullish_engulfing and bullish_divergence
short_signal = at_resistance and bearish_engulfing and bearish_divergence

if (long_signal)
    sl = close - (atr * sl_atr_multiplier)
    tp = close + (atr * tp_atr_multiplier)
    strategy.entry("Long", strategy.long)
    strategy.exit("Long Exit", from_entry="Long", stop=sl, limit=tp)

if (short_signal)
    sl = close + (atr * sl_atr_multiplier)
    tp = close - (atr * tp_atr_multiplier)
    strategy.entry("Short", strategy.short)
    strategy.exit("Short Exit", from_entry="Short", stop=sl, limit=tp)

// --- Plotting ---
plot(fib_50, "Fib 50.0", color=color.new(color.blue, 50))
plot(fib_618, "Fib 61.8", color=color.new(color.purple, 50))
"""

    def _generate_mt5_for_cnn_lstm(self, strategy_name: str, best_params: Dict[str, Any]) -> str:
        sl_multiplier = best_params.get('sl_atr_multiplier', 2.0)
        tp_multiplier = best_params.get('tp_atr_multiplier', 3.0)
        risk_per_trade = self.config.get('risk_management', {}).get('risk_per_trade', 0.01)
        look_back = self.config.get('modeling', {}).get('look_back', 60)
        api_endpoint = self._get_api_endpoint()

        # Feature configurations from the project
        ema_len = 200
        # macd_fast = 12
        # macd_slow = 26
        # macd_signal = 9
        rsi_len = 14
        stoch_k = 14
        stoch_d = 3
        stoch_slowing = 3
        atr_len = 14
        # macd_total_period = macd_slow + macd_signal
        max_indicator_period = max(ema_len, rsi_len, stoch_k, atr_len)


        return f"""
//+------------------------------------------------------------------+
//|         {strategy_name}_Optimized.mq5 - API Client               |
//|      Generated by ML Backtester Framework - Copyright 2025       |
//+------------------------------------------------------------------+
#property copyright "Copyright 2025, ML Backtester Framework"
#property link      "https://github.com/your_repo"
#property version   "1.00"
#property strict

#include <Trade\\Trade.mqh>
#include <Trade\\SymbolInfo.mqh>

//--- EA Inputs
input string InpApiEndpoint = "{api_endpoint}"; // API Endpoint for predictions
input double InpRiskPerTrade = {risk_per_trade};      // Risk per trade
input double InpSLMultiplier = {sl_multiplier};    // Stop Loss ATR Multiplier
input double InpTPMultiplier = {tp_multiplier};    // Take Profit ATR Multiplier
input int    InpLookBack     = {look_back};      // Model Look-back period

//--- Indicator Parameters (must match training)
input int    InpMAPeriod     = {ema_len};
// input int    InpMACDFast     = 12;
// input int    InpMACDSlow     = 26;
// input int    InpMACDSignal   = 9;
input int    InpRSIPeriod    = {rsi_len};
input int    InpStochK       = {stoch_k};
input int    InpStochD       = {stoch_d};
input int    InpStochSlowing = {stoch_slowing};
input int    InpATRPeriod    = {atr_len};

//--- Global Variables
CTrade      trade;
CSymbolInfo symbol;
datetime    lastBarTime = 0;
int         minBarsRequired;

//--- Indicator Handles
int ema_handle, rsi_handle, stoch_handle, atr_handle; // macd_handle removed

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
  {{
   symbol.Name(_Symbol);
   trade.SetExpertMagicNumber(67890);
   trade.SetMarginMode();

   //--- Calculate minimum bars required
   minBarsRequired = InpLookBack + {max_indicator_period};

   //--- Check for enough bars on chart
   if(Bars(_Symbol, _Period) < minBarsRequired)
     {{
      printf("Not enough history on the chart. Required: %d, Available: %d", minBarsRequired, Bars(_Symbol, _Period));
      return(INIT_FAILED);
     }}

   //--- Initialize all indicators needed for features
   ema_handle = iMA(_Symbol, _Period, InpMAPeriod, 0, MODE_EMA, PRICE_CLOSE);
   // macd_handle = iMACD(_Symbol, _Period, InpMACDFast, InpMACDSlow, InpMACDSignal, PRICE_CLOSE);
   rsi_handle = iRSI(_Symbol, _Period, InpRSIPeriod, PRICE_CLOSE);
   stoch_handle = iStochastic(_Symbol, _Period, InpStochK, InpStochD, InpStochSlowing, MODE_SMA, STO_LOWHIGH);
   atr_handle = iATR(_Symbol, _Period, InpATRPeriod);

   if(ema_handle < 0 || rsi_handle < 0 || stoch_handle < 0 || atr_handle < 0)
     {{
      printf("Error initializing one or more indicators.");
      return(INIT_FAILED);
     }}
     
   Comment("CNN-LSTM EA Initialized. Waiting for new bar...");
   return(INIT_SUCCEEDED);
  }}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
  {{
   IndicatorRelease(ema_handle);
   // IndicatorRelease(macd_handle);
   IndicatorRelease(rsi_handle);
   IndicatorRelease(stoch_handle);
   IndicatorRelease(atr_handle);
   Comment("");
  }}

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
  {{
   if(IsNewBar())
     {{
      CheckForSignal();
     }}
  }}

//+------------------------------------------------------------------+
//| Check for a trading signal from the API                          |
//+------------------------------------------------------------------+
void CheckForSignal()
  {{
   if(PositionsTotal() > 0) return; // Only trade if no open positions

   //--- Ensure we have enough bars for the look-back period + indicator warmup
   if(Bars(_Symbol, _Period) < minBarsRequired)
     {{
      Comment("Not enough bars for look-back and indicator warmup.");
      return;
     }}

   int signal = GetPrediction();

   if(signal == 0) return; // No signal or error

   double atr_val[];
   if(CopyBuffer(atr_handle, 0, 0, 1, atr_val) <= 0) return;
   
   double lot_size = CalculateLotSize(atr_val[0]);
   double sl=0, tp=0;

   if(signal == 1) // Buy Signal
     {{
      sl = symbol.Ask() - atr_val[0] * InpSLMultiplier;
      tp = symbol.Ask() + atr_val[0] * InpTPMultiplier;
      trade.Buy(lot_size, _Symbol, symbol.Ask(), sl, tp, "CNN-LSTM Buy");
     }}
   else if(signal == -1) // Sell Signal
     {{
      sl = symbol.Bid() + atr_val[0] * InpSLMultiplier;
      tp = symbol.Bid() - atr_val[0] * InpTPMultiplier;
      trade.Sell(lot_size, _Symbol, symbol.Bid(), sl, tp, "CNN-LSTM Sell");
     }}
  }}

//+------------------------------------------------------------------+
//| Get prediction from Python API server                            |
//+------------------------------------------------------------------+
int GetPrediction()
  {{
   string json_payload = BuildJsonPayload();
   if(json_payload == "") return 0;

   char post_data[], result_data[];
   string headers = "Content-Type: application/json\\r\\n";
   int timeout = 5000; // 5 seconds

   StringToCharArray(json_payload, post_data);

   ResetLastError();
   int res = WebRequest("POST", InpApiEndpoint, NULL, timeout, post_data, result_data, headers);

   if(res == -1)
     {{
      printf("WebRequest failed. Error code: %d", GetLastError());
      return 0;
     }}

   string result_str = CharArrayToString(result_data);
   
   //--- Simple JSON parsing to find the signal value
   int signal_pos = StringFind(result_str, "\\"signal\\":");
   if(signal_pos < 0)
     {{
      printf("Could not find 'signal' in API response: %s", result_str);
      return 0;
     }}
     
   string signal_substr = StringSubstr(result_str, signal_pos + 9); // 9 is len of "signal":
   int signal = (int)StringToInteger(StringSubstr(signal_substr, 0, StringFind(signal_substr, "}}")));

   Comment("Received signal: " + (string)signal);
   return signal;
  }}

//+------------------------------------------------------------------+
//| Build the JSON payload with feature data                         |
//+------------------------------------------------------------------+
string BuildJsonPayload()
  {{
   string payload = "{{\\"features\\": [";
   
   // Buffers for all features
   double ema[], rsi[], stoch_k[], stoch_d[], atr_val[]; // MACD arrays removed
   MqlRates rates[];

   // Copy data for the entire look_back period
   int data_to_copy = InpLookBack + 1;
   
   // Patiently check if data is ready. If not, abort and wait for the next tick.
   if(CopyBuffer(ema_handle, 0, 0, data_to_copy, ema) < data_to_copy ||
      // CopyBuffer(macd_handle, 0, 0, data_to_copy, macd_main) < data_to_copy ||
      // CopyBuffer(macd_handle, 2, 0, data_to_copy, macd_hist) < data_to_copy ||
      // CopyBuffer(macd_handle, 1, 0, data_to_copy, macd_sig) < data_to_copy ||
      CopyBuffer(rsi_handle, 0, 0, data_to_copy, rsi) < data_to_copy ||
      CopyBuffer(stoch_handle, 0, 0, data_to_copy, stoch_k) < data_to_copy ||
      CopyBuffer(stoch_handle, 1, 0, data_to_copy, stoch_d) < data_to_copy ||
      CopyBuffer(atr_handle, 0, 0, data_to_copy, atr_val) < data_to_copy ||
      CopyRates(_Symbol, _Period, 0, data_to_copy, rates) < data_to_copy)
     {{
      Comment("Indicator data not yet ready. Waiting for next tick.");
      return "";
     }}

   for(int i = InpLookBack - 1; i >= 0; i--)
     {{
      double atr_perc = (rates[i].close > 0) ? (atr_val[i] / rates[i].close) * 100 : 0;
      string feature_set = StringFormat(
          "{{ \\"EMA_{'d'}\\":%.5f, \\"RSI_{'d'}\\":%.5f, \\"STOCHk_{'d'}_{'d'}_{'d'}\\":%.5f, \\"STOCHd_{'d'}_{'d'}_{'d'}\\":%.5f, \\"ATRr_{'d'}\\":%.5f }}",
          InpMAPeriod, ema[i],
          InpRSIPeriod, rsi[i],
          InpStochK, InpStochD, InpStochSlowing, stoch_k[i],
          InpStochK, InpStochD, InpStochSlowing, stoch_d[i],
          InpATRPeriod, atr_perc
      );
      payload += feature_set;
      if(i > 0) payload += ",";
     }}

   payload += "]}}";
   return payload;
  }}

//+------------------------------------------------------------------+
//| Calculate Lot Size based on risk                                 |
//+------------------------------------------------------------------+
double CalculateLotSize(double atr_value)
  {{
   double account_balance = AccountInfoDouble(ACCOUNT_BALANCE);
   double risk_amount = account_balance * InpRiskPerTrade;
   double sl_pips = atr_value * InpSLMultiplier;
   if(sl_pips == 0) return 0.01;
   double tick_value = symbol.TickValue();
   double lot_size = risk_amount / (sl_pips * tick_value);
   lot_size = NormalizeDouble(lot_size, 2);
   if(lot_size < symbol.LotsMin()) lot_size = symbol.LotsMin();
   if(lot_size > symbol.LotsMax()) lot_size = symbol.LotsMax();
   return lot_size;
  }}

//+------------------------------------------------------------------+
//| Check for a new bar                                              |
//+------------------------------------------------------------------+
bool IsNewBar()
  {{
   datetime server_time = TimeCurrent();
   if(lastBarTime != iTime(_Symbol, _Period, 0))
     {{
      lastBarTime = iTime(_Symbol, _Period, 0);
      return(true);
     }}
   return(false);
  }}
//+------------------------------------------------------------------+
"""

    def _generate_pinescript_for_cnn_lstm(self, strategy_name: str, best_params: Dict[str, Any]) -> str:
        look_back = self.config.get('modeling', {}).get('look_back', 60)
        api_endpoint = self._get_api_endpoint()
        symbol = self.config.get('symbol', 'default_symbol')
        timeframe = self.config.get('timeframe', 'H1')

        # Feature configurations from the project
        ema_len = 200
        macd_fast = 12
        macd_slow = 26
        macd_signal = 9
        rsi_len = 14
        stoch_k = 14
        stoch_d = 3
        stoch_slowing = 3
        atr_len = 14

        # PineScript does not have a native way to build a nested JSON object easily.
        # We will construct the JSON string manually.
        # This is complex and prone to errors, but it's the only way.
        
        return f"""
//@version=5
indicator("{strategy_name} - API Signal Generator", overlay=false)

// --- Inputs ---
inp_webhook_url = input.string("{api_endpoint}", "Webhook URL")
inp_lookback = {look_back}

// --- Indicator Calculations (must match training) ---
ema = ta.ema(close, {ema_len})
[macd_line, signal_line, macd_hist] = ta.macd(close, {macd_fast}, {macd_slow}, {macd_signal})
rsi = ta.rsi(close, {rsi_len})
stoch_k_line = ta.sma(ta.stoch(close, high, low, {stoch_k}), {stoch_slowing})
stoch_d_line = ta.sma(stoch_k_line, {stoch_d})
atr_val = ta.atr({atr_len})
atr_perc = (atr_val / close) * 100

// --- Webhook Logic ---
// We trigger an alert on every new bar to send data to the external API.
if barstate.isconfirmed
    // Build the JSON payload string manually
    string features_json_array = ""
    for i = 0 to inp_lookback - 1
        string feature_set = "{{'EMA_{ema_len}':" + str.tostring(ema[i]) + 
                             ",'MACD_{macd_fast}_{macd_slow}_{macd_signal}':" + str.tostring(macd_line[i]) + 
                             ",'MACDh_{macd_fast}_{macd_slow}_{macd_signal}':" + str.tostring(macd_hist[i]) + 
                             ",'MACDs_{macd_fast}_{macd_slow}_{macd_signal}':" + str.tostring(signal_line[i]) + 
                             ",'RSI_{rsi_len}':" + str.tostring(rsi[i]) + 
                             ",'STOCHk_{stoch_k}_{stoch_d}_{stoch_slowing}':" + str.tostring(stoch_k_line[i]) + 
                             ",'STOCHd_{stoch_k}_{stoch_d}_{stoch_slowing}':" + str.tostring(stoch_d_line[i]) + 
                             ",'ATRr_{atr_len}':" + str.tostring(atr_perc[i]) + "}}"
        features_json_array := features_json_array + feature_set + (i < inp_lookback - 1 ? "," : "")

    string json_payload = "{{'symbol':'{symbol}','timeframe':'{timeframe}','features':[" + features_json_array + "]}}"
    
    // Send the data to the webhook URL
    alert(json_payload, freq = alert.freq_once_per_bar_close)

// --- Plotting a placeholder to show the EA is active ---
plot(1, "API Signal Status", color=barstate.isconfirmed ? color.green : color.gray)
"""