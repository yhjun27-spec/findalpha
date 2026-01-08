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
        
        # Calculate start date (last 1 year for chart)
        start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        
        try:
            # Fetch data using FinanceDataReader
            df = fdr.DataReader(ticker, start_date)
            
            # Format data for Chart.js
            df_reset = df.reset_index()
            
            # Extract Current Info from the last row
            last_row = df.iloc[-1]
            prev_close = df.iloc[-2]['Close'] if len(df) > 1 else last_row['Close']
            
            current_price = float(last_row['Close'])
            change = float(current_price - prev_close)
            change_percent = float((change / prev_close) * 100) if prev_close != 0 else 0
            
            chart_data = {
                "ticker": ticker,
                "current_price": current_price,
                "change": change,
                "change_percent": round(change_percent, 2),
                "labels": df.index.strftime('%Y-%m-%d').tolist(),
                "prices": df['Close'].tolist()
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
