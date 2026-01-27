from flask import Flask, send_from_directory, request, jsonify
from flask_cors import CORS
import FinanceDataReader as fdr
from datetime import datetime, timedelta
import pandas as pd
import os
import yfinance as yf
import math

# Translation support (using deep-translator which is Python 3.14 compatible)
try:
    from deep_translator import GoogleTranslator
    TRANSLATION_AVAILABLE = True
except ImportError:
    TRANSLATION_AVAILABLE = False
    print("Warning: deep-translator not installed. Translation will be disabled.")

app = Flask(__name__, static_url_path='', static_folder='.')
CORS(app)

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    if os.path.exists(path):
        return send_from_directory('.', path)
    return send_from_directory('.', 'index.html')

@app.route('/api/historical')
def historical():
    try:
        ticker_symbol = request.args.get('ticker', 'AAPL')
        date_range = request.args.get('range', '1y')
        interval = request.args.get('interval', 'd')
        
        print(f"Fetching {ticker_symbol} data...")

        # Calculate start date
        today = datetime.now()
        if date_range == '1m': start = (today - timedelta(days=30))
        elif date_range == '3m': start = (today - timedelta(days=90))
        elif date_range == '6m': start = (today - timedelta(days=180))
        elif date_range == '1y': start = (today - timedelta(days=365))
        elif date_range == '5y': start = (today - timedelta(days=365*5))
        elif date_range == 'max': start = datetime(1980, 1, 1)
        else: start = (today - timedelta(days=365))
        
        start_date = start.strftime('%Y-%m-%d')

        # 1. Price Data
        df = fdr.DataReader(ticker_symbol, start_date)
        
        if df.empty:
            return jsonify({"error": "No data found"}), 404

        last_row = df.iloc[-1]
        if len(df) > 1:
            prev_close = df.iloc[-2]['Close']
        else:
            prev_close = last_row['Open']
            
        current_price = float(last_row['Close'])
        change = float(current_price - prev_close)
        change_percent = float((change / prev_close) * 100) if prev_close != 0 else 0
        
        resampled_df = df
        if interval == 'w':
            resampled_df = df.resample('W').agg({'Open':'first','High':'max','Low':'min','Close':'last','Volume':'sum'}).dropna()
        elif interval == 'm':
            resampled_df = df.resample('M').agg({'Open':'first','High':'max','Low':'min','Close':'last','Volume':'sum'}).dropna()

        # Calculate Moving Averages
        resampled_df['MA10'] = resampled_df['Close'].rolling(window=10).mean()
        resampled_df['MA20'] = resampled_df['Close'].rolling(window=20).mean()
        resampled_df['MA50'] = resampled_df['Close'].rolling(window=50).mean()

        ohlc_data = []
        volume_data = []
        ma10_data = []
        ma20_data = []
        ma50_data = []
        
        for index, row in resampled_df.iterrows():
            date_str = index.strftime('%Y-%m-%d')
            ohlc_data.append({
                "x": date_str,
                "o": float(row['Open']), "h": float(row['High']), "l": float(row['Low']), "c": float(row['Close'])
            })
            volume_data.append({
                "x": date_str,
                "y": float(row['Volume']) if pd.notna(row['Volume']) else 0,
                "color": '#22c55e' if row['Close'] >= row['Open'] else '#ef4444'
            })
            ma10_data.append({"x": date_str, "y": float(row['MA10']) if pd.notna(row['MA10']) else None})
            ma20_data.append({"x": date_str, "y": float(row['MA20']) if pd.notna(row['MA20']) else None})
            ma50_data.append({"x": date_str, "y": float(row['MA50']) if pd.notna(row['MA50']) else None})
            

        # 2. Rich Metadata via yfinance
        ticker = yf.Ticker(ticker_symbol)
        info = {}
        financials_data = {"annual": [], "quarterly": []}
        
        try:
            info = ticker.info
            
            # Safe float helper
            def safe_float(val):
                if val is None: return None
                try:
                    f = float(val)
                    if math.isnan(f) or math.isinf(f): return None
                    return f
                except: return None
            
            # CY (Calendar Year) conversion helpers
            def get_cy_year(d):
                # If fiscal year ends in Jan-Mar, treat as previous calendar year
                if d.month <= 3: return d.year - 1
                return d.year
            
            def get_cy_q_label(d):
                # Adjust roughly to represent the calendar quarter based on end date
                mid = d - timedelta(days=45)
                q = (mid.month - 1) // 3 + 1
                return f"{mid.year}-Q{q}"

            # Helper function to calculate metrics for a period
            def calculate_period_metrics(income_stmt, cash_flow, period_col, prev_period_col=None, is_estimate=False, period_label=None):
                # Extract data
                revenue = safe_float(income_stmt.loc['Total Revenue', period_col]) if 'Total Revenue' in income_stmt.index else None
                gross_profit = safe_float(income_stmt.loc['Gross Profit', period_col]) if 'Gross Profit' in income_stmt.index else None
                ebitda = safe_float(income_stmt.loc['EBITDA', period_col]) if 'EBITDA' in income_stmt.index else None
                if ebitda is None:
                    ebitda = safe_float(income_stmt.loc['Normalized EBITDA', period_col]) if 'Normalized EBITDA' in income_stmt.index else None
                net_income = safe_float(income_stmt.loc['Net Income', period_col]) if 'Net Income' in income_stmt.index else None
                
                # OPEX 세부 항목
                operating_expense = safe_float(income_stmt.loc['Operating Expense', period_col]) if 'Operating Expense' in income_stmt.index else None
                rd_expense = safe_float(income_stmt.loc['Research And Development', period_col]) if 'Research And Development' in income_stmt.index else None
                sga_expense = safe_float(income_stmt.loc['Selling General And Administration', period_col]) if 'Selling General And Administration' in income_stmt.index else None
                
                # Operating Income
                operating_income = safe_float(income_stmt.loc['Operating Income', period_col]) if 'Operating Income' in income_stmt.index else None
                
                # Cash flow data
                operating_cf = None
                capex = None
                if period_col in cash_flow.columns:
                    operating_cf = safe_float(cash_flow.loc['Operating Cash Flow', period_col]) if 'Operating Cash Flow' in cash_flow.index else None
                    capex = safe_float(cash_flow.loc['Capital Expenditure', period_col]) if 'Capital Expenditure' in cash_flow.index else None
                
                # Calculate FCF
                free_cash_flow = None
                if operating_cf is not None and capex is not None:
                    free_cash_flow = operating_cf + capex
                
                # Get EPS
                eps = safe_float(income_stmt.loc['Basic EPS', period_col]) if 'Basic EPS' in income_stmt.index else None
                if eps is None:
                    eps = safe_float(income_stmt.loc['Diluted EPS', period_col]) if 'Diluted EPS' in income_stmt.index else None
                
                # Calculate margins
                gpm = (gross_profit / revenue * 100) if (revenue and gross_profit and revenue != 0) else None
                ebitda_margin = (ebitda / revenue * 100) if (revenue and ebitda and revenue != 0) else None
                opm = (operating_income / revenue * 100) if (revenue and operating_income and revenue != 0) else None
                fcf_margin = (free_cash_flow / revenue * 100) if (revenue and free_cash_flow and revenue != 0) else None
                
                # OPEX as % of revenue
                rd_pct = (rd_expense / revenue * 100) if (revenue and rd_expense and revenue != 0) else None
                sga_pct = (sga_expense / revenue * 100) if (revenue and sga_expense and revenue != 0) else None
                opex_pct = (operating_expense / revenue * 100) if (revenue and operating_expense and revenue != 0) else None
                
                # Calculate YoY Growth
                revenue_growth = None
                eps_growth = None
                fcf_growth = None
                
                if prev_period_col is not None and prev_period_col in income_stmt.columns:
                    prev_revenue = safe_float(income_stmt.loc['Total Revenue', prev_period_col]) if 'Total Revenue' in income_stmt.index else None
                    if revenue and prev_revenue and prev_revenue != 0:
                        revenue_growth = ((revenue - prev_revenue) / abs(prev_revenue) * 100)
                    
                    prev_eps = safe_float(income_stmt.loc['Basic EPS', prev_period_col]) if 'Basic EPS' in income_stmt.index else None
                    if prev_eps is None:
                        prev_eps = safe_float(income_stmt.loc['Diluted EPS', prev_period_col]) if 'Diluted EPS' in income_stmt.index else None
                    if eps and prev_eps and prev_eps != 0:
                        eps_growth = ((eps - prev_eps) / abs(prev_eps) * 100)
                
                if prev_period_col is not None and prev_period_col in cash_flow.columns:
                    prev_operating_cf = safe_float(cash_flow.loc['Operating Cash Flow', prev_period_col]) if 'Operating Cash Flow' in cash_flow.index else None
                    prev_capex = safe_float(cash_flow.loc['Capital Expenditure', prev_period_col]) if 'Capital Expenditure' in cash_flow.index else None
                    if prev_operating_cf is not None and prev_capex is not None:
                        prev_fcf = prev_operating_cf + prev_capex
                        if free_cash_flow and prev_fcf and prev_fcf != 0:
                            fcf_growth = ((free_cash_flow - prev_fcf) / abs(prev_fcf) * 100)
                
                if period_label:
                    year_str = period_label
                else:
                    year_str = str(period_col.year) if hasattr(period_col, 'year') else str(period_col)
                    
                if is_estimate and not year_str.endswith('E'):
                    year_str += "E"
                
                return {
                    "period": year_str,
                    "revenue": revenue,
                    "revenueGrowth": revenue_growth,
                    "gpm": gpm,
                    "opm": opm,
                    "ebitdaMargin": ebitda_margin,
                    "netIncome": net_income,
                    "eps": eps,
                    "epsGrowth": eps_growth,
                    "freeCashFlow": free_cash_flow,
                    "fcfGrowth": fcf_growth,
                    "fcfMargin": fcf_margin,
                    "operatingExpense": operating_expense,
                    "rdExpense": rd_expense,
                    "sgaExpense": sga_expense,
                    "rdPct": rd_pct,
                    "sgaPct": sga_pct,
                    "opexPct": opex_pct,
                    "isEstimate": is_estimate
                }

            # Annual Data
            annual_income = ticker.financials
            annual_cf = ticker.cashflow
            
            if not annual_income.empty:
                years = annual_income.columns[:5]
                
                # Historical Annual
                for i in range(len(years)):
                    period_col = years[i]
                    prev_period_col = years[i+1] if i + 1 < len(years) else None
                    
                    # CY Adjustment
                    cy_year = get_cy_year(period_col)
                    label = str(cy_year)
                    
                    metrics = calculate_period_metrics(annual_income, annual_cf, period_col, prev_period_col, is_estimate=False, period_label=label)
                    financials_data["annual"].append(metrics)
                
                # Estimates (Annual)
                last_hist_cy = get_cy_year(years[0])
                
                revenue_est = ticker.revenue_estimate
                earnings_est = ticker.earnings_estimate

                if revenue_est is not None and not revenue_est.empty and earnings_est is not None and not earnings_est.empty:
                    for period in revenue_est.index:
                        if 'y' in str(period):
                            offset = 0
                            if period == '0y': offset = 1 
                            elif period == '+1y': offset = 2
                            elif period == '+2y': offset = 3
                            elif period == '+3y': offset = 4
                            elif period == '+4y': offset = 5
                            else: continue
                            
                            est_year = last_hist_cy + offset
                            label = f"{est_year}"
                            
                            rev_val = safe_float(revenue_est.loc[period, 'avg']) if 'avg' in revenue_est.columns else None
                            eps_val = safe_float(earnings_est.loc[period, 'avg']) if 'avg' in earnings_est.columns else None
                            
                            if rev_val or eps_val:
                                metrics = {
                                    "period": label + "E",
                                    "revenue": rev_val,
                                    "revenueGrowth": None, 
                                    "gpm": None,
                                    "ebitdaMargin": None,
                                    "netIncome": None,
                                    "eps": eps_val,
                                    "epsGrowth": None,
                                    "freeCashFlow": None,
                                    "fcfGrowth": None,
                                    "isEstimate": True
                                }
                                financials_data["annual"].append(metrics)
            
            # Sort annual (Oldest -> Newest)
            financials_data["annual"].sort(key=lambda x: x['period'])

            # Quarterly Data
            quarterly_income = ticker.quarterly_financials
            quarterly_cash = ticker.quarterly_cashflow
                                          
            if not quarterly_income.empty:
                columns = quarterly_income.columns
                num_periods = min(8, len(columns))
                historical_quarters = []
                
                for i in range(num_periods):
                    period_col = columns[i]
                    prev_col = columns[i+1] if i + 1 < len(columns) else None
                    
                    label = get_cy_q_label(period_col)
                    
                    metrics = calculate_period_metrics(quarterly_income, quarterly_cash, period_col, prev_col, is_estimate=False, period_label=label)
                    historical_quarters.append(metrics)
            
                # Estimates (Quarterly)
                last_hist_label = historical_quarters[0]['period'] if historical_quarters else f"{datetime.now().year}-Q1"
                try:
                    l_year, l_q = map(int, last_hist_label.replace('Q','').split('-'))
                except:
                    l_year, l_q = datetime.now().year, 1 
                
                curr_y, curr_q = l_year, l_q
                
                estimate_quarters = []
                est_periods = ['0q', '+1q', '+2q', '+3q', '+4q']
                
                if revenue_est is not None and not revenue_est.empty and earnings_est is not None:
                    for p in est_periods:
                        if p in revenue_est.index:
                            curr_q += 1
                            if curr_q > 4:
                                curr_q = 1
                                curr_y += 1
                            
                            label = f"{curr_y}-Q{curr_q}"
                            
                            rev_val = safe_float(revenue_est.loc[p, 'avg']) if 'avg' in revenue_est.columns else None
                            eps_val = safe_float(earnings_est.loc[p, 'avg']) if 'avg' in earnings_est.columns else None
                            
                            if rev_val and eps_val:
                                metrics = {
                                    "period": label + "E",
                                    "revenue": rev_val,
                                    "revenueGrowth": None,
                                    "gpm": None,
                                    "ebitdaMargin": None,
                                    "netIncome": None,
                                    "eps": eps_val,
                                    "epsGrowth": None,
                                    "freeCashFlow": None,
                                    "fcfGrowth": None,
                                    "isEstimate": True
                                }
                                estimate_quarters.append(metrics)

                combined_quarters = list(reversed(historical_quarters)) + estimate_quarters
                financials_data["quarterly"] = sorted(combined_quarters, key=lambda x: x['period'])
            
            print(f"Financial time-series data: {len(financials_data['annual'])} annual, {len(financials_data['quarterly'])} quarterly")

        except Exception as e:
            print(f"YFinance Error: {e}")
            import traceback
            traceback.print_exc()

        # Get news from yfinance (new structure: content nested inside each news item)
        news_data = []
        try:
            news_list = ticker.news
            if news_list:
                for item in news_list[:10]:  # Limit to 10 news items
                    # New yfinance structure: data is inside 'content' object
                    content = item.get('content', item)  # Fallback to item if no content
                    
                    # Extract thumbnail URL from nested structure
                    thumbnail_url = ''
                    thumbnail_obj = content.get('thumbnail', {})
                    if thumbnail_obj:
                        resolutions = thumbnail_obj.get('resolutions', [])
                        if resolutions:
                            thumbnail_url = resolutions[-1].get('url', '')
                    
                    # Extract publisher from provider object
                    publisher = ''
                    provider = content.get('provider', {})
                    if provider:
                        publisher = provider.get('displayName', '')
                    
                    # Extract link from clickThroughUrl or canonicalUrl
                    link = ''
                    click_url = content.get('clickThroughUrl', {})
                    if click_url:
                        link = click_url.get('url', '')
                    if not link:
                        canonical = content.get('canonicalUrl', {})
                        if canonical:
                            link = canonical.get('url', '')
                    
                    # Parse pubDate to timestamp
                    pub_time = 0
                    pub_date = content.get('pubDate', '')
                    if pub_date:
                        try:
                            from datetime import datetime as dt
                            parsed = dt.fromisoformat(pub_date.replace('Z', '+00:00'))
                            pub_time = int(parsed.timestamp())
                        except:
                            pass
                    
                    news_item = {
                        "title": content.get('title', ''),
                        "link": link,
                        "publisher": publisher,
                        "providerPublishTime": pub_time,
                        "thumbnail": thumbnail_url
                    }
                    news_data.append(news_item)
                print(f"Fetched {len(news_data)} news items")
        except Exception as news_err:
            print(f"News fetch error: {news_err}")
            import traceback
            traceback.print_exc()

        # Get description and translate to Korean
        description_en = info.get('longBusinessSummary') or info.get('description', '')
        description_ko = description_en  # Default to English
        
        if description_en and TRANSLATION_AVAILABLE:
            try:
                description_ko = GoogleTranslator(source='en', target='ko').translate(description_en)
                print(f"Description translated to Korean successfully")
            except Exception as trans_err:
                print(f"Translation error: {trans_err}")
                # Keep original English description

        meta = {
            "name": info.get('shortName', ticker_symbol),
            "description": description_ko,
            "descriptionEn": description_en,
            "marketCap": str(info.get('marketCap', '-')), 
            "sector": info.get('sector', '-'),
            "peRatio": str(info.get('forwardPE', info.get('trailingPE', '-'))),
            "website": info.get('website', '#'),
            "irWebsite": info.get('irWebsite', '#')
        }

        response_data = {
            "ticker": ticker_symbol,
            "range": date_range,
            "interval": interval,
            "current_price": current_price,
            "change": change,
            "change_percent": round(change_percent, 2),
            "prices": resampled_df['Close'].tolist(),
            "labels": resampled_df.index.strftime('%Y-%m-%d').tolist(),
            "ohlc": ohlc_data,
            "volume": volume_data,
            "ma10": ma10_data,
            "ma20": ma20_data,
            "ma50": ma50_data,
            "meta": meta,
            "financials": financials_data,
            "news": news_data
        }
        
        return jsonify(response_data)

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/earningcalls')
def earningcalls():
    """List earnings call files for a given ticker from local folder."""
    try:
        ticker = request.args.get('ticker', '').upper()
        if not ticker:
            return jsonify({"error": "Ticker is required"}), 400
        
        # Base folder for earnings calls
        base_folder = os.path.join(os.path.dirname(__file__), 'earningcall', ticker)
        
        files = []
        if os.path.exists(base_folder) and os.path.isdir(base_folder):
            for filename in sorted(os.listdir(base_folder), reverse=True):
                filepath = os.path.join(base_folder, filename)
                if os.path.isfile(filepath):
                    # Extract date from filename (e.g., 2024-Q4.pdf -> 2024 Q4)
                    name_without_ext = os.path.splitext(filename)[0]
                    
                    files.append({
                        "filename": filename,
                        "date": name_without_ext.replace('-', ' '),  # e.g., "2024 Q4"
                        "link": f"/earningcall/{ticker}/{filename}"
                    })
        
        return jsonify({
            "ticker": ticker,
            "files": files
        })

    except Exception as e:
        print(f"Error listing earnings calls: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/ai-analysis')
def ai_analysis():
    """AI-powered company analysis using Gemini API."""
    try:
        from api.ai_analysis import analyze_company, analyze_all
        
        ticker = request.args.get('ticker', '').upper()
        company_name = request.args.get('name', ticker)
        category = request.args.get('category', '')  # Optional: specific category
        
        if not ticker:
            return jsonify({"error": "Ticker is required"}), 400
        
        print(f"AI Analysis requested for {ticker} ({company_name}), category: {category or 'all'}")
        
        if category:
            # Single category analysis
            result = analyze_company(ticker, company_name, category)
            return jsonify(result)
        else:
            # All categories
            results = analyze_all(ticker, company_name)
            return jsonify({
                "success": True,
                "ticker": ticker,
                "company_name": company_name,
                "analyses": results
            })
    
    except Exception as e:
        print(f"AI Analysis Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/api/analyze-earningcall')
def analyze_earningcall():
    """어닝콜 PDF를 분석하여 투자 리포트를 생성합니다."""
    try:
        from api.ai_analysis import analyze_earnings_call
        
        ticker = request.args.get('ticker', '').upper()
        filename = request.args.get('filename', '')
        force_refresh = request.args.get('refresh', '').lower() == 'true'
        
        if not ticker:
            return jsonify({"error": "Ticker is required"}), 400
        if not filename:
            return jsonify({"error": "Filename is required"}), 400
        
        # PDF 파일 경로 구성
        base_folder = os.path.join(os.path.dirname(__file__), 'earningcall', ticker)
        pdf_path = os.path.join(base_folder, filename)
        
        if not os.path.exists(pdf_path):
            return jsonify({"error": f"File not found: {filename}"}), 404
        
        # 파일명에서 기간 추출 (예: 2024-Q4.pdf -> 2024 Q4)
        period = os.path.splitext(filename)[0].replace('-', ' ')
        
        print(f"Analyzing earnings call: {ticker} - {period} (refresh={force_refresh})")
        
        # 분석 실행 (캐시 또는 새로 분석)
        result = analyze_earnings_call(ticker, pdf_path, period, force_refresh)
        
        return jsonify(result)
    
    except Exception as e:
        print(f"Earnings Call Analysis Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/api/notion-status')
def notion_status():
    """노션 API 설정 상태를 확인합니다."""
    try:
        from api.notion_export import is_notion_configured
        return jsonify({
            "configured": is_notion_configured()
        })
    except Exception as e:
        return jsonify({"configured": False, "error": str(e)})


@app.route('/api/export-to-notion', methods=['POST'])
def export_to_notion_endpoint():
    """어닝콜 분석 결과를 노션으로 내보냅니다."""
    try:
        from api.notion_export import export_to_notion, is_notion_configured
        
        if not is_notion_configured():
            return jsonify({
                "success": False,
                "error": "Notion API가 설정되지 않았습니다. 환경변수를 설정해주세요."
            }), 400
        
        data = request.get_json()
        ticker = data.get('ticker', '')
        period = data.get('period', '')
        content = data.get('content', '')
        analyzed_at = data.get('analyzed_at', '')
        
        if not ticker or not content:
            return jsonify({"error": "ticker와 content는 필수입니다."}), 400
        
        result = export_to_notion(ticker, period, content, analyzed_at)
        return jsonify(result)
        
    except Exception as e:
        print(f"Notion Export Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# ============================================
# Daily Summary APIs (하루 정리)
# ============================================

# 주요 지수 티커
MARKET_INDICES = {
    'SP500': '^GSPC',
    'NASDAQ': '^IXIC',
    'DOW': '^DJI',
    'VIX': '^VIX',
    'RUSSELL2000': '^RUT',
    '10Y_TREASURY': '^TNX'
}

# 섹터 ETF 티커
SECTOR_ETFS = {
    'Technology': 'XLK',
    'Healthcare': 'XLV',
    'Financials': 'XLF',
    'Consumer Discretionary': 'XLY',
    'Communication Services': 'XLC',
    'Industrials': 'XLI',
    'Consumer Staples': 'XLP',
    'Energy': 'XLE',
    'Utilities': 'XLU',
    'Real Estate': 'XLRE',
    'Materials': 'XLB'
}

# 시가총액 $800M 이상 주요 종목 (S&P 500 대표)
MAJOR_STOCKS = [
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'BRK-B', 'UNH', 'JNJ',
    'V', 'XOM', 'JPM', 'PG', 'MA', 'HD', 'CVX', 'MRK', 'ABBV', 'LLY',
    'PEP', 'KO', 'COST', 'AVGO', 'TMO', 'MCD', 'WMT', 'CSCO', 'ACN', 'ABT',
    'DHR', 'NEE', 'VZ', 'NKE', 'ADBE', 'TXN', 'PM', 'CRM', 'UPS', 'RTX',
    'AMD', 'INTC', 'QCOM', 'NFLX', 'ORCL', 'IBM', 'NOW', 'AMAT', 'INTU', 'ISRG'
]

# 섹터별 시가총액 상위 10개 종목
SECTOR_STOCKS = {
    'Technology': ['AAPL', 'MSFT', 'NVDA', 'AVGO', 'ORCL', 'CRM', 'ADBE', 'AMD', 'CSCO', 'INTC'],
    'Healthcare': ['LLY', 'UNH', 'JNJ', 'MRK', 'ABBV', 'TMO', 'PFE', 'ABT', 'DHR', 'ISRG'],
    'Financials': ['BRK-B', 'JPM', 'V', 'MA', 'BAC', 'WFC', 'GS', 'MS', 'SPGI', 'BLK'],
    'Consumer Discretionary': ['AMZN', 'TSLA', 'HD', 'MCD', 'NKE', 'LOW', 'SBUX', 'TJX', 'BKNG', 'CMG'],
    'Communication Services': ['META', 'GOOGL', 'NFLX', 'DIS', 'CMCSA', 'VZ', 'T', 'TMUS', 'CHTR', 'EA'],
    'Industrials': ['GE', 'CAT', 'UNP', 'RTX', 'HON', 'BA', 'DE', 'UPS', 'LMT', 'MMM'],
    'Consumer Staples': ['WMT', 'PG', 'COST', 'KO', 'PEP', 'PM', 'MO', 'MDLZ', 'CL', 'KHC'],
    'Energy': ['XOM', 'CVX', 'COP', 'SLB', 'EOG', 'MPC', 'PSX', 'VLO', 'OXY', 'PXD'],
    'Utilities': ['NEE', 'DUK', 'SO', 'D', 'AEP', 'SRE', 'XEL', 'ED', 'EXC', 'WEC'],
    'Real Estate': ['PLD', 'AMT', 'EQIX', 'PSA', 'CCI', 'SPG', 'O', 'WELL', 'DLR', 'AVB'],
    'Materials': ['LIN', 'APD', 'SHW', 'ECL', 'FCX', 'NEM', 'DOW', 'DD', 'NUE', 'VMC']
}


@app.route('/api/market-overview')
def market_overview():
    """주요 시장 지수 데이터 및 당일 변동률 반환."""
    try:
        results = {}
        today = datetime.now()
        start_date = (today - timedelta(days=30)).strftime('%Y-%m-%d')
        
        for name, ticker_symbol in MARKET_INDICES.items():
            try:
                ticker = yf.Ticker(ticker_symbol)
                hist = ticker.history(period='1mo')
                
                if hist.empty:
                    continue
                
                current_price = float(hist['Close'].iloc[-1])
                prev_close = float(hist['Close'].iloc[-2]) if len(hist) > 1 else current_price
                change = current_price - prev_close
                change_pct = (change / prev_close * 100) if prev_close != 0 else 0
                
                # 차트용 데이터 (최근 30일)
                chart_data = []
                for idx, row in hist.iterrows():
                    chart_data.append({
                        'date': idx.strftime('%Y-%m-%d'),
                        'close': float(row['Close'])
                    })
                
                results[name] = {
                    'ticker': ticker_symbol,
                    'name': name,
                    'price': current_price,
                    'change': change,
                    'changePct': round(change_pct, 2),
                    'chart': chart_data
                }
            except Exception as e:
                print(f"Error fetching {name}: {e}")
                continue
        
        return jsonify({
            'success': True,
            'date': today.strftime('%Y-%m-%d'),
            'indices': results
        })
    
    except Exception as e:
        print(f"Market Overview Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/sectors')
def sectors():
    """섹터별 ETF 성과 데이터 반환."""
    try:
        results = []
        
        for sector_name, etf_ticker in SECTOR_ETFS.items():
            try:
                ticker = yf.Ticker(etf_ticker)
                hist = ticker.history(period='5d')
                
                if hist.empty or len(hist) < 2:
                    continue
                
                current_price = float(hist['Close'].iloc[-1])
                prev_close = float(hist['Close'].iloc[-2])
                change_pct = ((current_price - prev_close) / prev_close * 100) if prev_close != 0 else 0
                
                # 주간 변동률
                week_start = float(hist['Close'].iloc[0])
                week_change_pct = ((current_price - week_start) / week_start * 100) if week_start != 0 else 0
                
                results.append({
                    'sector': sector_name,
                    'etf': etf_ticker,
                    'price': current_price,
                    'dailyChange': round(change_pct, 2),
                    'weeklyChange': round(week_change_pct, 2)
                })
            except Exception as e:
                print(f"Error fetching sector {sector_name}: {e}")
                continue
        
        # 일간 변동률 기준 정렬
        results.sort(key=lambda x: x['dailyChange'], reverse=True)
        
        return jsonify({
            'success': True,
            'date': datetime.now().strftime('%Y-%m-%d'),
            'sectors': results
        })
    
    except Exception as e:
        print(f"Sectors Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/movers')
def movers():
    """급등락 상위 종목 반환 (S&P 500 대표 종목 기준)."""
    try:
        movers_data = []
        
        for ticker_symbol in MAJOR_STOCKS:
            try:
                ticker = yf.Ticker(ticker_symbol)
                hist = ticker.history(period='2d')
                info = ticker.info
                
                if hist.empty or len(hist) < 2:
                    continue
                
                current_price = float(hist['Close'].iloc[-1])
                prev_close = float(hist['Close'].iloc[-2])
                change = current_price - prev_close
                change_pct = (change / prev_close * 100) if prev_close != 0 else 0
                
                movers_data.append({
                    'ticker': ticker_symbol,
                    'name': info.get('shortName', ticker_symbol),
                    'sector': info.get('sector', '-'),
                    'price': current_price,
                    'change': change,
                    'changePct': round(change_pct, 2),
                    'volume': int(hist['Volume'].iloc[-1]) if 'Volume' in hist else 0,
                    'marketCap': info.get('marketCap', 0)
                })
            except Exception as e:
                print(f"Error fetching mover {ticker_symbol}: {e}")
                continue
        
        # 변동률 절대값 기준 정렬
        movers_data.sort(key=lambda x: abs(x['changePct']), reverse=True)
        
        # 상승 TOP 10, 하락 TOP 10 분리
        gainers = [m for m in movers_data if m['changePct'] > 0][:10]
        losers = [m for m in movers_data if m['changePct'] < 0]
        losers.sort(key=lambda x: x['changePct'])  # 가장 많이 하락한 순
        losers = losers[:10]
        
        return jsonify({
            'success': True,
            'date': datetime.now().strftime('%Y-%m-%d'),
            'gainers': gainers,
            'losers': losers
        })
    
    except Exception as e:
        print(f"Movers Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/new-highs')
def new_highs():
    """52주 신고가 달성 종목 반환 (시가총액 $800M 이상)."""
    try:
        new_high_stocks = []
        min_market_cap = 800_000_000  # $800M
        
        for ticker_symbol in MAJOR_STOCKS:
            try:
                ticker = yf.Ticker(ticker_symbol)
                info = ticker.info
                
                # 시가총액 필터
                market_cap = info.get('marketCap', 0)
                if market_cap < min_market_cap:
                    continue
                
                # 52주 고가와 현재가 비교
                fifty_two_week_high = info.get('fiftyTwoWeekHigh', 0)
                current_price = info.get('currentPrice') or info.get('regularMarketPrice', 0)
                
                if not fifty_two_week_high or not current_price:
                    continue
                
                # 신고가 판정: 현재가가 52주 고가의 98% 이상
                if current_price >= fifty_two_week_high * 0.98:
                    new_high_stocks.append({
                        'ticker': ticker_symbol,
                        'name': info.get('shortName', ticker_symbol),
                        'sector': info.get('sector', '-'),
                        'price': current_price,
                        'fiftyTwoWeekHigh': fifty_two_week_high,
                        'marketCap': market_cap,
                        'pctFromHigh': round((current_price / fifty_two_week_high - 1) * 100, 2)
                    })
            except Exception as e:
                print(f"Error checking new high for {ticker_symbol}: {e}")
                continue
        
        # 섹터별 그룹핑
        sectors_grouped = {}
        for stock in new_high_stocks:
            sector = stock['sector']
            if sector not in sectors_grouped:
                sectors_grouped[sector] = []
            sectors_grouped[sector].append(stock)
        
        return jsonify({
            'success': True,
            'date': datetime.now().strftime('%Y-%m-%d'),
            'totalCount': len(new_high_stocks),
            'stocks': new_high_stocks,
            'bySector': sectors_grouped
        })
    
    except Exception as e:
        print(f"New Highs Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/market-news')
def market_news():
    """시장 전반 뉴스 (매크로, 지정학적 뉴스)."""
    try:
        all_news = []
        
        # 주요 지수/ETF에서 뉴스 수집
        news_sources = ['^GSPC', 'SPY', 'QQQ', 'DIA', 'IWM']
        
        for ticker_symbol in news_sources:
            try:
                ticker = yf.Ticker(ticker_symbol)
                news_list = ticker.news
                
                if news_list:
                    for item in news_list[:5]:
                        content = item.get('content', item)
                        
                        # 썸네일 추출
                        thumbnail_url = ''
                        thumbnail_obj = content.get('thumbnail', {})
                        if thumbnail_obj:
                            resolutions = thumbnail_obj.get('resolutions', [])
                            if resolutions:
                                thumbnail_url = resolutions[-1].get('url', '')
                        
                        # 퍼블리셔 추출
                        publisher = ''
                        provider = content.get('provider', {})
                        if provider:
                            publisher = provider.get('displayName', '')
                        
                        # 링크 추출
                        link = ''
                        click_url = content.get('clickThroughUrl', {})
                        if click_url:
                            link = click_url.get('url', '')
                        if not link:
                            canonical = content.get('canonicalUrl', {})
                            if canonical:
                                link = canonical.get('url', '')
                        
                        # 시간 파싱
                        pub_time = 0
                        pub_date = content.get('pubDate', '')
                        if pub_date:
                            try:
                                parsed = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
                                pub_time = int(parsed.timestamp())
                            except:
                                pass
                        
                        news_item = {
                            'title': content.get('title', ''),
                            'link': link,
                            'publisher': publisher,
                            'publishTime': pub_time,
                            'thumbnail': thumbnail_url,
                            'source': ticker_symbol
                        }
                        
                        # 중복 제거 (제목 기준)
                        if not any(n['title'] == news_item['title'] for n in all_news):
                            all_news.append(news_item)
                            
            except Exception as e:
                print(f"Error fetching news for {ticker_symbol}: {e}")
                continue
        
        # 최신순 정렬
        all_news.sort(key=lambda x: x['publishTime'], reverse=True)
        
        return jsonify({
            'success': True,
            'date': datetime.now().strftime('%Y-%m-%d'),
            'news': all_news[:20]  # 상위 20개만 반환
        })
    
    except Exception as e:
        print(f"Market News Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/sector-stocks')
def sector_stocks():
    """섹터별 대표 종목들의 주가 변동 반환 (기간별 수익률 포함)."""
    try:
        sector = request.args.get('sector', '')
        
        if not sector or sector not in SECTOR_STOCKS:
            return jsonify({
                'success': False,
                'error': f'Invalid sector: {sector}',
                'availableSectors': list(SECTOR_STOCKS.keys())
            }), 400
        
        stocks = SECTOR_STOCKS[sector]
        results = []
        
        for ticker_symbol in stocks:
            try:
                ticker = yf.Ticker(ticker_symbol)
                # 1년치 데이터로 모든 기간 계산
                hist = ticker.history(period='1y')
                info = ticker.info
                
                if hist.empty or len(hist) < 2:
                    continue
                
                current_price = float(hist['Close'].iloc[-1])
                
                # 일간 변동
                prev_close = float(hist['Close'].iloc[-2]) if len(hist) >= 2 else current_price
                daily_change = current_price - prev_close
                daily_pct = (daily_change / prev_close * 100) if prev_close != 0 else 0
                
                # 1주 수익률 (5 거래일 전)
                week_ago_idx = max(0, len(hist) - 6)
                week_ago_price = float(hist['Close'].iloc[week_ago_idx])
                week_pct = ((current_price - week_ago_price) / week_ago_price * 100) if week_ago_price != 0 else 0
                
                # 1개월 수익률 (~21 거래일 전)
                month_ago_idx = max(0, len(hist) - 22)
                month_ago_price = float(hist['Close'].iloc[month_ago_idx])
                month_pct = ((current_price - month_ago_price) / month_ago_price * 100) if month_ago_price != 0 else 0
                
                # 1년 수익률 (전체 기간의 첫 데이터)
                year_ago_price = float(hist['Close'].iloc[0])
                year_pct = ((current_price - year_ago_price) / year_ago_price * 100) if year_ago_price != 0 else 0
                
                results.append({
                    'ticker': ticker_symbol,
                    'name': info.get('shortName', ticker_symbol),
                    'price': round(current_price, 2),
                    'change': round(daily_change, 2),
                    'changePct': round(daily_pct, 2),
                    'week': round(week_pct, 2),
                    'month': round(month_pct, 2),
                    'year': round(year_pct, 2),
                    'marketCap': info.get('marketCap', 0),
                    'volume': int(hist['Volume'].iloc[-1]) if 'Volume' in hist else 0
                })
            except Exception as e:
                print(f"Error fetching {ticker_symbol}: {e}")
                continue
        
        # 시가총액 순 정렬
        results.sort(key=lambda x: x.get('marketCap', 0), reverse=True)
        
        return jsonify({
            'success': True,
            'sector': sector,
            'etf': SECTOR_ETFS.get(sector, ''),
            'stocks': results
        })
    
    except Exception as e:
        print(f"Sector Stocks Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    print(f"Starting Flask Server on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=False)


