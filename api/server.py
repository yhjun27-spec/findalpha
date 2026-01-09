from flask import Flask, request, jsonify
from flask_cors import CORS
import FinanceDataReader as fdr
import json
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

app = Flask(__name__)
# Allow CORS for all domains on all routes
CORS(app, resources={r"/*": {"origins": "*"}}) 

@app.route('/api/historical', methods=['GET'])
def get_historical_data():
    try:
        ticker = request.args.get('ticker', 'AAPL')
        date_range = request.args.get('range', '1y') # 1m, 3m, 1y, 5y, max
        interval = request.args.get('interval', 'd') # d, w, m
        
        print(f"Fetching data for {ticker}, range: {date_range}, interval: {interval}")

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
        
        # Fetch data using FinanceDataReader
        print(f"[{datetime.now()}] Calling fdr.DataReader for {ticker}...")
        df = fdr.DataReader(ticker, start_date)
        print(f"[{datetime.now()}] fdr.DataReader returned {len(df)} rows.")
        
        if df.empty:
            print(f"No data found for {ticker}")
            return jsonify({"error": "No data found for this ticker"}), 404

        # Extract Current Info (Always from Daily data for accuracy)
        last_row = df.iloc[-1]
        prev_close = df.iloc[-2]['Close'] if len(df) > 1 else last_row['Close']
        current_price = float(last_row['Close'])
        change = float(current_price - prev_close)
        change_percent = float((change / prev_close) * 100) if prev_close != 0 else 0

        # Resample if needed (Daily is default)
        resampled_df = df.copy()
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
        
        # Prepare OHLC data
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
        
        return jsonify(chart_data)

    except Exception as e:
        print(f"Error fetching data: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("Starting Flask API Server on port 5002...")
    app.run(port=5002, debug=True, use_reloader=False)
