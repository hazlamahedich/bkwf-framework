import pandas as pd
from pathlib import Path
import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def convert_csv_to_parquet(csv_path: Path, parquet_path: Path):
    """
    Converts a CSV file to a Parquet file for faster I/O operations.

    This function checks if the Parquet file exists and is more recent than the CSV file.
    If so, it skips the conversion. Otherwise, it reads the CSV, cleans the data,
    and saves it as a Parquet file.

    Args:
        csv_path (Path): The path to the input CSV file.
        parquet_path (Path): The path where the output Parquet file will be saved.
    """
    if not csv_path.exists():
        logging.error(f"CSV file not found at: {csv_path}")
        raise FileNotFoundError(f"CSV file not found at: {csv_path}")

    # Check if conversion is necessary
    if parquet_path.exists() and parquet_path.stat().st_mtime > csv_path.stat().st_mtime:
        logging.info(f"Parquet file '{parquet_path}' is already up-to-date. Skipping conversion.")
        return

    logging.info(f"Converting '{csv_path}' to Parquet format...")

    try:
        # Read the CSV file
        df = pd.read_csv(csv_path, delimiter='\t')

        # --- Data Cleaning and Preparation ---
        # 1. Clean column names: remove '<', '>', and convert to lowercase
        df.columns = df.columns.str.replace(r'[<>]', '', regex=True).str.lower()

        # 2. Combine 'date' and 'time' columns into a single datetime object
        df['datetime'] = pd.to_datetime(df['date'] + ' ' + df['time'])
        df = df.drop(columns=['date', 'time'])

        # 3. Set the new 'datetime' column as the index
        df = df.set_index('datetime')

        # 4. Ensure all OHLCV and volume columns are numeric
        numeric_cols = ['open', 'high', 'low', 'close', 'tickvol', 'vol', 'spread']
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Drop rows with NaNs that might have been created during coercion
        df.dropna(inplace=True)

        # 5. Downcast numeric columns to save memory
        for col in ['open', 'high', 'low', 'close']:
            df[col] = pd.to_numeric(df[col], downcast='float')
        for col in ['tickvol', 'vol', 'spread']:
            df[col] = pd.to_numeric(df[col], downcast='integer')

        # Save to Parquet
        df.to_parquet(parquet_path)
        logging.info(f"Successfully converted and saved to '{parquet_path}'.")

    except Exception as e:
        logging.error(f"An error occurred during the CSV to Parquet conversion: {e}")
        raise

if __name__ == '__main__':
    # Example usage:
    # This allows the script to be run directly for testing or manual conversion.
    # Assumes the script is run from the root of the `bkwf framework` directory.
    
    # Create a data directory for the parquet files if it doesn't exist
    data_dir = Path('bkwf_framework/data')
    data_dir.mkdir(exist_ok=True)

    # Define paths for the historical data
    eurusd_csv = Path('EURUSD_m15_2022_2025.csv')
    gbpusd_csv = Path('GBPUSD_M15_202207180000_202507160730.csv')
    
    eurusd_parquet = data_dir / eurusd_csv.with_suffix('.parquet').name
    gbpusd_parquet = data_dir / gbpusd_csv.with_suffix('.parquet').name

    # Convert both files
    convert_csv_to_parquet(eurusd_csv, eurusd_parquet)
    convert_csv_to_parquet(gbpusd_csv, gbpusd_parquet)