# api/historical.py
from http.server import BaseHTTPRequestHandler
import FinanceDataReader as fdr
import json
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timedelta

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        query_components = parse_qs(urlparse(self.path).query)
        ticker = query_components.get('ticker', ['AAPL'])[0]
        date_range = query_components.get('range', ['1y'])[0] # 1m, 3m, 1y, 5y, max
        interval = query_components.get('interval', ['d'])[0] # d, w, m
        
        # Calculate start date
        today = datetime.now()
        if date_range == '1m':
            start_date = (today - timedelta(days=30)).strftime('%Y-%m-%d')
        elif date_range == '3m':
            start_date = (today - timedelta(days=90)).strftime('%Y-%m-%d')
        elif date_range == '6m':
            start_date = (today - timedelta(days=180)).strftime('%Y-%m-%d')
        elif date_range == '5y':
            start_date = (today - timedelta(days=365*5)).strftime('%Y-%m-%d')
        elif date_range == 'max':
            start_date = '1980-01-01' # Fetch all available
        else: # Default 1y
            start_date = (today - timedelta(days=365)).strftime('%Y-%m-%d')
        
        try:
            # Fetch data using FinanceDataReader
            df = fdr.DataReader(ticker, start_date)
            
            if df.empty:
                raise ValueError("No data found for this ticker")

            # Extract Current Info (Always from Daily data for accuracy)
            last_row = df.iloc[-1]
            prev_close = df.iloc[-2]['Close'] if len(df) > 1 else last_row['Close']
            current_price = float(last_row['Close'])
            change = float(current_price - prev_close)
            change_percent = float((change / prev_close) * 100) if prev_close != 0 else 0

            # Resample if needed (Daily is default)
            resampled_df = df
            if interval == 'w':
                # Weekly resampling for OHLC
                resampled_df = df.resample('W').agg({
                    'Open': 'first',
                    'High': 'max',
                    'Low': 'min',
                    'Close': 'last'
                }).dropna()
            elif interval == 'm':
                # Monthly resampling for OHLC
                resampled_df = df.resample('M').agg({
                    'Open': 'first',
                    'High': 'max',
                    'Low': 'min',
                    'Close': 'last'
                }).dropna()
            
            # Prepare OHLC data for chartjs-chart-financial
            # Format: { x: timestamp, o: open, h: high, l: low, c: close }
            ohlc_data = []
            for index, row in resampled_df.iterrows():
                ohlc_data.append({
                    "x": index.strftime('%Y-%m-%d'),
                    "o": float(row['Open']),
                    "h": float(row['High']),
                    "l": float(row['Low']),
                    "c": float(row['Close'])
                })

            chart_data = {
                "ticker": ticker,
                "range": date_range,
                "interval": interval,
                "current_price": current_price,
                "change": change,
                "change_percent": round(change_percent, 2),
                "labels": resampled_df.index.strftime('%Y-%m-%d').tolist(),
                "prices": resampled_df['Close'].tolist(),
                "ohlc": ohlc_data
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(chart_data).encode('utf-8'))
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
        return
