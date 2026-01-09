import FinanceDataReader as fdr
import time

print("Testing FDR for AAPL...")
start_time = time.time()
try:
    df = fdr.DataReader('AAPL', '2023-01-01')
    end_time = time.time()
    print(f"Success! Shape: {df.shape}")
    print(f"Time taken: {end_time - start_time:.2f} seconds")
    print(df.tail())
except Exception as e:
    print(f"Error: {e}")
