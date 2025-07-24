# Data Import Guide

Complete guide for importing historical data from MetaTrader 5 and TradingView into the BKWF Trading Framework.

## 📊 Overview

The BKWF framework supports multiple data sources and formats:

- **MetaTrader 5**: Direct MT5 data export and Python API integration
- **TradingView**: CSV export and Pine Script data extraction
- **Supported Formats**: CSV, Parquet (recommended)
- **Required Columns**: `datetime`, `open`, `high`, `low`, `close`, `volume`

## 🔄 MetaTrader 5 Data Import

### Method 1: MT5 Terminal Export (Recommended)

#### Step 1: Open MT5 and Navigate to Data
1. Open MetaTrader 5 terminal
2. Press `F2` or go to **View → Market Watch**
3. Right-click on desired symbol → **Symbols**

#### Step 2: Export Historical Data
1. In Symbols window, select your instrument
2. Click **Data** tab
3. Select timeframe (M15, H1, H4, D1, etc.)
4. Choose date range:
   ```
   From: 2022-01-01 00:00
   To: 2025-01-24 23:59
   ```
5. Click **Export** button
6. Save as CSV format

#### Step 3: Verify Data Format
Exported CSV should have these columns:
```csv
Date,Time,Open,High,Low,Close,Volume
2022.01.03,00:00,1.13045,1.13056,1.13034,1.13048,100
2022.01.03,00:15,1.13048,1.13052,1.13041,1.13049,85
```

#### Step 4: Convert to Framework Format
```python
import pandas as pd

# Load MT5 exported data
df = pd.read_csv('EURUSD_M15_export.csv')

# Combine Date and Time columns
df['datetime'] = pd.to_datetime(df['Date'] + ' ' + df['Time'])

# Rename columns to match framework requirements
df = df.rename(columns={
    'Open': 'open',
    'High': 'high', 
    'Low': 'low',
    'Close': 'close',
    'Volume': 'volume'
})

# Select required columns
df = df[['datetime', 'open', 'high', 'low', 'close', 'volume']]

# Save in Parquet format (recommended)
df.to_parquet('ml_backtester/data/EURUSD_M15_2022_2025.parquet', index=False)

# Or save as CSV
df.to_csv('ml_backtester/data/EURUSD_M15_2022_2025.csv', index=False)
```

### Method 2: Python MT5 API (Advanced)

#### Prerequisites
```bash
pip install MetaTrader5
```

#### Python Script for Data Download
```python
import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime

def download_mt5_data(symbol, timeframe, start_date, end_date, save_path):
    """
    Download historical data from MT5 using Python API
    """
    # Initialize MT5 connection
    if not mt5.initialize():
        print("Failed to initialize MT5")
        return False
    
    # Convert timeframe string to MT5 constant
    timeframe_map = {
        'M15': mt5.TIMEFRAME_M15,
        'H1': mt5.TIMEFRAME_H1,
        'H4': mt5.TIMEFRAME_H4,
        'D1': mt5.TIMEFRAME_D1
    }
    
    if timeframe not in timeframe_map:
        print(f"Unsupported timeframe: {timeframe}")
        return False
    
    # Request historical data
    rates = mt5.copy_rates_range(
        symbol, 
        timeframe_map[timeframe],
        start_date,
        end_date
    )
    
    if rates is None:
        print(f"Failed to get data for {symbol}")
        return False
    
    # Convert to DataFrame
    df = pd.DataFrame(rates)
    df['datetime'] = pd.to_datetime(df['time'], unit='s')
    
    # Select and rename columns
    df = df[['time', 'open', 'high', 'low', 'close', 'tick_volume']]
    df = df.rename(columns={
        'time': 'datetime',
        'tick_volume': 'volume'
    })
    df['datetime'] = pd.to_datetime(df['datetime'], unit='s')
    
    # Save data
    if save_path.endswith('.parquet'):
        df.to_parquet(save_path, index=False)
    else:
        df.to_csv(save_path, index=False)
    
    print(f"Successfully downloaded {len(df)} bars for {symbol}")
    print(f"Date range: {df['datetime'].min()} to {df['datetime'].max()}")
    
    # Cleanup
    mt5.shutdown()
    return True

# Usage example
if __name__ == "__main__":
    success = download_mt5_data(
        symbol="EURUSD",
        timeframe="M15", 
        start_date=datetime(2022, 1, 1),
        end_date=datetime(2025, 1, 24),
        save_path="ml_backtester/data/EURUSD_M15_2022_2025.parquet"
    )
```

### Method 3: MT5 Strategy Tester Export

#### Step 1: Open Strategy Tester
1. In MT5, press `Ctrl+R` or go to **View → Strategy Tester**
2. Select any EA or create a simple data export EA

#### Step 2: Configure Test Parameters
1. **Symbol**: Choose your trading pair
2. **Period**: Select timeframe (M15, H1, etc.)
3. **Date Range**: Set start and end dates
4. **Model**: Choose "Every tick" for highest accuracy

#### Step 3: Create Data Export EA
Create a simple EA to export data:
```mql5
//+------------------------------------------------------------------+
//|                                             DataExporter.mq5     |
//+------------------------------------------------------------------+
#property version   "1.00"

input string FileName = "exported_data.csv";

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
    int handle = FileOpen(FileName, FILE_WRITE|FILE_CSV);
    if(handle == INVALID_HANDLE)
    {
        Print("Failed to create file");
        return INIT_FAILED;
    }
    
    // Write header
    FileWrite(handle, "datetime", "open", "high", "low", "close", "volume");
    
    // Write historical data
    int bars_total = Bars(_Symbol, _Period);
    for(int i = bars_total - 1; i >= 0; i--)
    {
        datetime time = iTime(_Symbol, _Period, i);
        double open = iOpen(_Symbol, _Period, i);
        double high = iHigh(_Symbol, _Period, i);
        double low = iLow(_Symbol, _Period, i);
        double close = iClose(_Symbol, _Period, i);
        long volume = iTickVolume(_Symbol, _Period, i);
        
        FileWrite(handle, TimeToString(time, TIME_DATE|TIME_MINUTES),
                 open, high, low, close, volume);
    }
    
    FileClose(handle);
    Print("Data export completed: ", FileName);
    return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick() { }
```

## 📈 TradingView Data Import

### Method 1: Manual CSV Export

#### Step 1: Open TradingView Chart
1. Go to [TradingView.com](https://www.tradingview.com)
2. Open chart for desired symbol (e.g., EURUSD)
3. Set timeframe (15m, 1h, 4h, 1D)

#### Step 2: Export Data
1. Right-click on chart
2. Select **Export chart data**
3. Choose date range
4. Click **Export** to download CSV

#### Step 3: Format Data for Framework
```python
import pandas as pd

# Load TradingView CSV
df = pd.read_csv('EURUSD_TradingView.csv')

# TradingView format: time,open,high,low,close,volume
# Already compatible with framework requirements

# Convert time column
df['time'] = pd.to_datetime(df['time'])
df = df.rename(columns={'time': 'datetime'})

# Ensure proper column order
df = df[['datetime', 'open', 'high', 'low', 'close', 'volume']]

# Save in framework format
df.to_parquet('ml_backtester/data/EURUSD_M15_2022_2025.parquet', index=False)
```

### Method 2: Pine Script Data Extraction

#### Pine Script for Data Export
```pinescript
//@version=5
indicator("Data Exporter", overlay=true)

// Input parameters
export_bars = input.int(1000, "Number of bars to export")

// Create data table
if barstate.islast
    var table data_table = table.new(position.top_right, 6, export_bars + 1, 
                                   bgcolor=color.white, border_width=1)
    
    // Headers
    table.cell(data_table, 0, 0, "DateTime", text_color=color.black)
    table.cell(data_table, 1, 0, "Open", text_color=color.black)
    table.cell(data_table, 2, 0, "High", text_color=color.black)
    table.cell(data_table, 3, 0, "Low", text_color=color.black)
    table.cell(data_table, 4, 0, "Close", text_color=color.black)
    table.cell(data_table, 5, 0, "Volume", text_color=color.black)
    
    // Export historical data
    for i = 0 to math.min(export_bars - 1, bar_index)
        row = i + 1
        bar_time = time[export_bars - 1 - i]
        
        table.cell(data_table, 0, row, str.tostring(bar_time), text_color=color.black)
        table.cell(data_table, 1, row, str.tostring(open[export_bars - 1 - i]), text_color=color.black)
        table.cell(data_table, 2, row, str.tostring(high[export_bars - 1 - i]), text_color=color.black)
        table.cell(data_table, 3, row, str.tostring(low[export_bars - 1 - i]), text_color=color.black)
        table.cell(data_table, 4, row, str.tostring(close[export_bars - 1 - i]), text_color=color.black)
        table.cell(data_table, 5, row, str.tostring(volume[export_bars - 1 - i]), text_color=color.black)
```

### Method 3: TradingView API (Premium Required)

#### Python Script for TradingView API
```python
import requests
import pandas as pd
import json

def get_tradingview_data(symbol, interval, start_time, end_time, api_key):
    """
    Get data from TradingView API (requires premium subscription)
    """
    url = "https://api.tradingview.com/v1/history"
    
    params = {
        'symbol': symbol,
        'resolution': interval,
        'from': start_time,
        'to': end_time,
        'token': api_key
    }
    
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        data = response.json()
        
        df = pd.DataFrame({
            'datetime': pd.to_datetime(data['t'], unit='s'),
            'open': data['o'],
            'high': data['h'], 
            'low': data['l'],
            'close': data['c'],
            'volume': data['v']
        })
        
        return df
    else:
        print(f"API request failed: {response.status_code}")
        return None

# Usage (requires TradingView Pro+ subscription)
# df = get_tradingview_data("EURUSD", "15", 1640995200, 1737686400, "your_api_key")
```

## 🔧 Data Processing Scripts

### Complete Data Import Script
```python
#!/usr/bin/env python3
"""
Complete data import script for BKWF Trading Framework
Supports MT5 and TradingView data sources
"""

import pandas as pd
import numpy as np
from pathlib import Path
import argparse
from datetime import datetime

def validate_data(df):
    """Validate imported data format and quality"""
    required_columns = ['datetime', 'open', 'high', 'low', 'close', 'volume']
    
    # Check required columns
    if not all(col in df.columns for col in required_columns):
        missing = [col for col in required_columns if col not in df.columns]
        raise ValueError(f"Missing required columns: {missing}")
    
    # Check data types
    df['datetime'] = pd.to_datetime(df['datetime'])
    for col in ['open', 'high', 'low', 'close', 'volume']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Check for missing values
    missing_count = df.isnull().sum().sum()
    if missing_count > 0:
        print(f"Warning: {missing_count} missing values found")
        df = df.dropna()
    
    # Validate OHLC logic
    invalid_bars = (
        (df['high'] < df['open']) | 
        (df['high'] < df['close']) |
        (df['low'] > df['open']) | 
        (df['low'] > df['close'])
    ).sum()
    
    if invalid_bars > 0:
        print(f"Warning: {invalid_bars} bars with invalid OHLC data")
    
    # Sort by datetime
    df = df.sort_values('datetime').reset_index(drop=True)
    
    return df

def convert_mt5_export(input_path, output_path):
    """Convert MT5 exported CSV to framework format"""
    print(f"Converting MT5 data from {input_path}")
    
    # Read MT5 export format
    df = pd.read_csv(input_path)
    
    # Handle different MT5 export formats
    if 'Date' in df.columns and 'Time' in df.columns:
        # Format 1: Separate Date and Time columns
        df['datetime'] = pd.to_datetime(df['Date'] + ' ' + df['Time'])
    elif 'DateTime' in df.columns:
        # Format 2: Combined DateTime column
        df['datetime'] = pd.to_datetime(df['DateTime'])
    else:
        raise ValueError("Unrecognized MT5 export format")
    
    # Rename columns
    column_mapping = {
        'Open': 'open', 'High': 'high', 'Low': 'low', 
        'Close': 'close', 'Volume': 'volume',
        'Tick Volume': 'volume'
    }
    df = df.rename(columns=column_mapping)
    
    # Select required columns
    df = df[['datetime', 'open', 'high', 'low', 'close', 'volume']]
    
    # Validate and clean data
    df = validate_data(df)
    
    # Save in framework format
    if output_path.suffix == '.parquet':
        df.to_parquet(output_path, index=False)
    else:
        df.to_csv(output_path, index=False)
    
    print(f"Successfully converted {len(df)} bars")
    print(f"Date range: {df['datetime'].min()} to {df['datetime'].max()}")

def convert_tradingview_export(input_path, output_path):
    """Convert TradingView CSV to framework format"""
    print(f"Converting TradingView data from {input_path}")
    
    df = pd.read_csv(input_path)
    
    # TradingView format: time,open,high,low,close,volume
    df = df.rename(columns={'time': 'datetime'})
    
    # Validate and clean data
    df = validate_data(df)
    
    # Save in framework format
    if output_path.suffix == '.parquet':
        df.to_parquet(output_path, index=False)
    else:
        df.to_csv(output_path, index=False)
    
    print(f"Successfully converted {len(df)} bars")
    print(f"Date range: {df['datetime'].min()} to {df['datetime'].max()}")

def main():
    parser = argparse.ArgumentParser(description="Import trading data for BKWF Framework")
    parser.add_argument('input_file', help='Input CSV file path')
    parser.add_argument('--output', '-o', help='Output file path')
    parser.add_argument('--source', '-s', choices=['mt5', 'tradingview'], 
                       help='Data source type')
    parser.add_argument('--format', '-f', choices=['csv', 'parquet'], 
                       default='parquet', help='Output format')
    
    args = parser.parse_args()
    
    input_path = Path(args.input_file)
    if not input_path.exists():
        print(f"Error: Input file {input_path} not found")
        return
    
    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = Path(f"ml_backtester/data/{input_path.stem}.{args.format}")
    
    # Create output directory
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert based on source
    try:
        if args.source == 'mt5':
            convert_mt5_export(input_path, output_path)
        elif args.source == 'tradingview':
            convert_tradingview_export(input_path, output_path)
        else:
            # Auto-detect format
            df = pd.read_csv(input_path, nrows=5)
            if 'Date' in df.columns or 'DateTime' in df.columns:
                convert_mt5_export(input_path, output_path)
            else:
                convert_tradingview_export(input_path, output_path)
        
        print(f"Data successfully imported to {output_path}")
        
    except Exception as e:
        print(f"Error during conversion: {e}")

if __name__ == "__main__":
    main()
```

### Usage Examples

#### Convert MT5 Export
```bash
python import_data.py mt5_export.csv --source mt5 --format parquet
```

#### Convert TradingView Export  
```bash
python import_data.py tradingview_export.csv --source tradingview --format csv
```

#### Auto-detect Format
```bash
python import_data.py data_export.csv --output ml_backtester/data/EURUSD_M15.parquet
```

## 📋 Data Quality Checklist

### Before Import
- [ ] Correct timeframe (M15, H1, H4, D1)
- [ ] Sufficient data range (min 1000 bars)
- [ ] No gaps in trading hours
- [ ] Consistent date format

### After Import
- [ ] All required columns present
- [ ] No missing values
- [ ] Valid OHLC relationships (High ≥ Open,Close ≥ Low)
- [ ] Chronological order
- [ ] Realistic volume values

### Framework Integration
- [ ] File saved in `ml_backtester/data/` directory
- [ ] Correct path in `config.yaml`
- [ ] File accessible by framework
- [ ] Parquet format for best performance

## 🚨 Common Issues & Solutions

### Issue: "File not found" error
**Solution**: Check file path in config.yaml matches actual location

### Issue: "Missing columns" error  
**Solution**: Ensure CSV has required columns: datetime, open, high, low, close, volume

### Issue: "Invalid datetime format"
**Solution**: Convert datetime to pandas datetime format:
```python
df['datetime'] = pd.to_datetime(df['datetime'])
```

### Issue: Poor backtest performance with real data vs MT5
**Solution**: 
- Check for data gaps during market hours
- Verify timezone consistency
- Account for broker-specific spread/commission

### Issue: Large file sizes
**Solution**: 
- Use Parquet format (50-80% smaller than CSV)
- Consider data compression
- Split very large datasets by year

### Issue: Memory errors with large datasets
**Solution**:
- Process data in chunks
- Use `pd.read_csv(chunksize=10000)`
- Increase system RAM or use smaller date ranges

This guide provides comprehensive instructions for importing historical data from major trading platforms into the BKWF framework. Follow the appropriate method for your data source and always validate data quality before running backtests.