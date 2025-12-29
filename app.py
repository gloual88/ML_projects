from flask import Flask, render_template, jsonify, request
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from datetime import datetime, timedelta
import numpy as np
import os

app = Flask(__name__)

# ETF 목록 로드
def load_etf_list():
    try:
        etf_df = pd.read_csv('etf_list.csv')
        return etf_df
    except Exception as e:
        print(f"Error loading ETF list: {e}")
        return pd.DataFrame()

# 데이터 캐시 (간단한 메모리 캐시)
data_cache = {}
cache_time = {}

def fetch_etf_data(symbol, days=730):
    """Yahoo Finance에서 ETF 데이터 가져오기"""
    cache_key = f"{symbol}_{days}"
    
    # 캐시 확인 (1시간)
    if cache_key in cache_time:
        if datetime.now() - cache_time[cache_key] < timedelta(hours=1):
            return data_cache.get(cache_key, pd.DataFrame())
    
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days + 365)
        data = yf.download(symbol, start=start_date, end=end_date, progress=False, auto_adjust=True)
        
        if data.empty:
            return pd.DataFrame()
        
        # 최신 yfinance 버전 대응
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        
        # 캐시에 저장
        data_cache[cache_key] = data
        cache_time[cache_key] = datetime.now()
        
        return data
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        return pd.DataFrame()

def calculate_performance(df):
    """성과 지표 계산"""
    if df.empty or len(df) < 2:
        return None
    
    try:
        current_price = float(df['Close'].iloc[-1])
        prev_price = float(df['Close'].iloc[-2])
        change = current_price - prev_price
        pct_change = (change / prev_price) * 100
        
        # YTD 성과
        start_of_year = datetime(datetime.now().year, 1, 1)
        ytd_df = df[df.index >= start_of_year]
        if not ytd_df.empty:
            ytd_start = float(ytd_df['Close'].iloc[0])
            ytd_pct = ((current_price - ytd_start) / ytd_start) * 100
        else:
            ytd_pct = pct_change
        
        # 52주 최고/최저
        low_52 = float(df['Close'].iloc[-252:].min()) if len(df) >= 252 else float(df['Close'].min())
        high_52 = float(df['Close'].iloc[-252:].max()) if len(df) >= 252 else float(df['Close'].max())
        
        return {
            'current_price': current_price,
            'change': pct_change,
            'ytd': ytd_pct,
            'low_52': low_52,
            'high_52': high_52
        }
    except Exception as e:
        print(f"Error calculating performance: {e}")
        return None

@app.route('/')
def index():
    """메인 페이지"""
    return render_template('index.html')

@app.route('/api/etf-list', methods=['GET'])
def get_etf_list():
    """ETF 목록 API"""
    etf_df = load_etf_list()
    
    if etf_df.empty:
        return jsonify({'error': 'Failed to load ETF list'}), 500
    
    # 카테고리별 ETF 정렬
    sector_etfs = etf_df[etf_df['Type'] == 'S&P 500 Sector'].to_dict('records')
    theme_etfs = etf_df[etf_df['Type'] == 'Theme ETF'].to_dict('records')
    broad_market_etfs = etf_df[etf_df['Type'] == 'Broad Market'].to_dict('records')
    
    return jsonify({
        'sector_etfs': sector_etfs,
        'theme_etfs': theme_etfs,
        'broad_market_etfs': broad_market_etfs,
        'all_etfs': etf_df.to_dict('records')
    })

@app.route('/api/etf-performance', methods=['POST'])
def get_etf_performance():
    """선택한 ETF들의 성과 데이터"""
    data = request.json
    tickers = data.get('tickers', [])
    days = data.get('days', 730)
    
    if not tickers:
        return jsonify({'error': 'No tickers provided'}), 400
    
    etf_df = load_etf_list()
    performance_data = []
    
    for ticker in tickers:
        df = fetch_etf_data(ticker, days)
        if df.empty:
            continue
        
        perf = calculate_performance(df)
        if perf:
            etf_name = etf_df[etf_df['Ticker'] == ticker]['Name'].values
            etf_name = etf_name[0] if len(etf_name) > 0 else ticker
            
            performance_data.append({
                'ticker': ticker,
                'name': etf_name,
                **perf
            })
    
    return jsonify(performance_data)

@app.route('/api/etf-price-data', methods=['POST'])
def get_etf_price_data():
    """ETF 가격 추이 데이터"""
    data = request.json
    tickers = data.get('tickers', [])
    days = data.get('days', 730)
    
    if not tickers:
        return jsonify({'error': 'No tickers provided'}), 400
    
    price_data = {}
    
    for ticker in tickers[:5]:  # 최대 5개
        df = fetch_etf_data(ticker, days)
        if df.empty:
            continue
        
        df_filtered = df.tail(days)
        price_data[ticker] = {
            'dates': df_filtered.index.strftime('%Y-%m-%d').tolist(),
            'prices': df_filtered['Close'].tolist()
        }
    
    return jsonify(price_data)

@app.route('/api/etf-ytd-comparison', methods=['POST'])
def get_etf_ytd_comparison():
    """YTD 성과 비교 데이터"""
    data = request.json
    tickers = data.get('tickers', [])
    
    if not tickers:
        return jsonify({'error': 'No tickers provided'}), 400
    
    start_of_year = datetime(datetime.now().year, 1, 1)
    comparison_data = {}
    
    for ticker in tickers:
        df = fetch_etf_data(ticker, 730)
        if df.empty:
            continue
        
        ytd_df = df[df.index >= start_of_year]
        if not ytd_df.empty:
            first_val = float(ytd_df['Close'].iloc[0])
            ytd_index = ((ytd_df['Close'] / first_val) * 100).tolist()
            
            comparison_data[ticker] = {
                'dates': ytd_df.index.strftime('%Y-%m-%d').tolist(),
                'values': ytd_index
            }
    
    return jsonify(comparison_data)

@app.route('/api/etf-technical', methods=['POST'])
def get_etf_technical():
    """기술적 분석 데이터"""
    data = request.json
    ticker = data.get('ticker')
    days = data.get('days', 730)
    
    if not ticker:
        return jsonify({'error': 'No ticker provided'}), 400
    
    df = fetch_etf_data(ticker, days)
    if df.empty or len(df) < 200:
        return jsonify({'error': 'Not enough data'}), 400
    
    df = df.tail(days).copy()
    
    # 기술 지표 계산
    df['RSI'] = ta.rsi(df['Close'], length=14)
    df['MA20'] = ta.sma(df['Close'], length=20)
    df['MA50'] = ta.sma(df['Close'], length=50)
    df['MA200'] = ta.sma(df['Close'], length=200)
    
    # NaN 값 처리
    df = df.fillna(method='bfill')
    
    result = {
        'dates': df.index.strftime('%Y-%m-%d').tolist(),
        'close': df['Close'].tolist(),
        'rsi': df['RSI'].tolist(),
        'ma20': df['MA20'].tolist(),
        'ma50': df['MA50'].tolist(),
        'ma200': df['MA200'].tolist()
    }
    
    # 최신 값 가져오기
    result['current'] = {
        'price': float(df['Close'].iloc[-1]),
        'rsi': float(df['RSI'].iloc[-1]),
        'ma20': float(df['MA20'].iloc[-1]),
        'ma50': float(df['MA50'].iloc[-1]),
        'ma200': float(df['MA200'].iloc[-1])
    }
    
    # 신호 생성
    rsi_val = result['current']['rsi']
    price_val = result['current']['price']
    ma50_val = result['current']['ma50']
    ma200_val = result['current']['ma200']
    
    signals = []
    
    if rsi_val > 70:
        signals.append({'type': 'warning', 'text': f'🔥 과매수: RSI {rsi_val:.1f}'})
    elif rsi_val < 30:
        signals.append({'type': 'info', 'text': f'❄️ 과매도: RSI {rsi_val:.1f}'})
    else:
        signals.append({'type': 'success', 'text': f'📊 중립: RSI {rsi_val:.1f}'})
    
    if price_val > ma200_val:
        signals.append({'type': 'success', 'text': '📈 상승추세: 가격 > MA200'})
    else:
        signals.append({'type': 'warning', 'text': '📉 하락추세: 가격 < MA200'})
    
    if price_val > ma50_val:
        signals.append({'type': 'success', 'text': '✅ 단기 강세: 가격 > MA50'})
    else:
        signals.append({'type': 'warning', 'text': '⚠️ 단기 약세: 가격 < MA50'})
    
    result['signals'] = signals
    
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)