import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas_ta as ta
from datetime import datetime, timedelta
import numpy as np

# 페이지 설정
st.set_page_config(page_title="ETF Investment Dashboard", layout="wide")

# CSS 커스터마이징
st.markdown("""
<style>
    .sector-card {
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# 사이드바 설정
st.sidebar.header("⚙️ 대시보드 설정")

# ETF 목록 로드
@st.cache_data
def load_etf_list():
    try:
        etf_df = pd.read_csv('etf_list.csv')
        return etf_df
    except FileNotFoundError:
        st.error("❌ etf_list.csv 파일을 찾을 수 없습니다. 파일을 같은 디렉토리에 저장하세요.")
        return pd.DataFrame()

etf_df = load_etf_list()

if not etf_df.empty:
    # ETF 타입별 분류
    sector_etfs = etf_df[etf_df['Type'] == 'S&P 500 Sector']['Ticker'].tolist()
    theme_etfs = etf_df[etf_df['Type'] == 'Theme ETF']['Ticker'].tolist()
    broad_market_etfs = etf_df[etf_df['Type'] == 'Broad Market']['Ticker'].tolist()
    
    # 분석 대상 선택
    analysis_type = st.sidebar.radio(
        "분석 대상 선택",
        ["섹터 분석", "테마 분석", "광범위 지수", "커스텀 선택"],
        index=0
    )
    
    if analysis_type == "섹터 분석":
        selected_tickers = sector_etfs
        title_suffix = "S&P 500 섹터 ETF"
    elif analysis_type == "테마 분석":
        selected_tickers = theme_etfs
        title_suffix = "테마 ETF"
    elif analysis_type == "광범위 지수":
        selected_tickers = broad_market_etfs
        title_suffix = "광범위 지수 ETF"
    else:  # 커스텀
        all_tickers = etf_df['Ticker'].tolist()
        selected_tickers = st.sidebar.multiselect(
            "ETF 선택",
            all_tickers,
            default=sector_etfs[:3]
        )
        title_suffix = "선택한 ETF"
    
    # 기간 설정
    period_map = {"1개월": 30, "3개월": 90, "6개월": 180, "1년": 365, "2년": 730, "5년": 1825}
    selected_period = st.sidebar.selectbox("조회 기간 선택", list(period_map.keys()), index=3)
    days_to_fetch = period_map[selected_period]
    
    # 데이터 캐싱
    @st.cache_data(ttl=3600)
    def fetch_etf_data(symbol, days=730):
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days + 365)  # 충분한 데이터 확보
            data = yf.download(symbol, start=start_date, end=end_date, progress=False, auto_adjust=True)
            
            if data.empty:
                return pd.DataFrame()
            
            # 최신 yfinance 버전 대응
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)
            
            return data
        except Exception as e:
            st.warning(f"데이터 로드 실패 ({symbol}): {e}")
            return pd.DataFrame()
    
    # 메인 타이틀
    st.title(f"📊 ETF 투자 대시보드: {title_suffix}")
    st.markdown(f"**마지막 업데이트:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | **데이터 소스:** Yahoo Finance")
    
    # 1. 실시간 ETF 성과 현황 (카드)
    st.subheader("📍 실시간 ETF 성과 현황")
    
    # 데이터 로드
    data_dict = {}
    for ticker in selected_tickers:
        df = fetch_etf_data(ticker, days_to_fetch)
        if not df.empty and len(df) > 1:
            data_dict[ticker] = df
    
    if data_dict:
        # 성과 계산
        performance_data = []
        for ticker, df in data_dict.items():
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
                
                performance_data.append({
                    'Ticker': ticker,
                    'Name': etf_df[etf_df['Ticker'] == ticker]['Name'].values[0] if not etf_df.empty else ticker,
                    'Current': current_price,
                    'Change': pct_change,
                    'YTD': ytd_pct,
                    'Low_52': low_52,
                    'High_52': high_52
                })
            except Exception as e:
                st.warning(f"데이터 변환 오류 ({ticker}): {e}")
                continue
        
        if performance_data:
            perf_df = pd.DataFrame(performance_data)
            
            # 카드 형식으로 표시
            cols = st.columns(min(4, len(performance_data)))
            for idx, row in perf_df.iterrows():
                col = cols[idx % len(cols)]
                with col:
                    color = "🟢" if row['Change'] >= 0 else "🔴"
                    st.metric(
                        label=f"{row['Ticker']}",
                        value=f"${row['Current']:.2f}",
                        delta=f"{row['Change']:.2f}% (YTD: {row['YTD']:.2f}%)"
                    )
                    st.caption(f"52주: {row['Low_52']:.0f} ~ {row['High_52']:.0f}")
    
    # 2. 메인 차트: 가격 추이 및 성과 비교
    st.divider()
    st.subheader("📈 ETF 가격 추이")
    
    if data_dict:
        # 기간별 데이터 필터링
        main_df = data_dict[selected_tickers[0]].tail(days_to_fetch).copy()
        
        fig = go.Figure()
        
        for ticker, df in list(data_dict.items())[:5]:  # 최대 5개까지만 표시 (차트 복잡도)
            df_filtered = df.tail(days_to_fetch)
            fig.add_trace(
                go.Scatter(
                    x=df_filtered.index,
                    y=df_filtered['Close'],
                    name=ticker,
                    line=dict(width=2.5)
                )
            )
        
        fig.update_layout(
            title=f"ETF 가격 추이 ({selected_period})",
            xaxis_title="날짜",
            yaxis_title="가격 (USD)",
            hovermode="x unified",
            template="plotly_white",
            height=500,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # 3. YTD 성과 비교
    st.divider()
    st.subheader("📊 연초 이후 성과 비교 (YTD)")
    
    if data_dict:
        start_of_year = datetime(datetime.now().year, 1, 1)
        comparison_df = pd.DataFrame()
        
        for ticker, df in data_dict.items():
            sub_df = df[df.index >= start_of_year]
            if not sub_df.empty:
                first_val = float(sub_df['Close'].iloc[0])
                comparison_df[ticker] = (sub_df['Close'] / first_val) * 100
        
        if not comparison_df.empty:
            compare_fig = go.Figure()
            
            for ticker in comparison_df.columns:
                compare_fig.add_trace(
                    go.Scatter(
                        x=comparison_df.index,
                        y=comparison_df[ticker],
                        name=ticker,
                        line=dict(width=2.5)
                    )
                )
            
            compare_fig.update_layout(
                title="연초 대비 누적 성과 (기준점=100)",
                xaxis_title="날짜",
                yaxis_title="성과 지수",
                template="plotly_white",
                height=500,
                hovermode="x unified",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            
            st.plotly_chart(compare_fig, use_container_width=True)
    
    # 4. 기술적 분석 (첫 번째 선택된 ETF)
    st.divider()
    st.subheader("🛠️ 기술적 분석")
    
    if selected_tickers and selected_tickers[0] in data_dict:
        primary_ticker = selected_tickers[0]
        primary_df = data_dict[primary_ticker].tail(days_to_fetch).copy()
        
        if len(primary_df) > 20:
            # 기술 지표 계산
            primary_df['RSI'] = ta.rsi(primary_df['Close'], length=14)
            primary_df['MA20'] = ta.sma(primary_df['Close'], length=20)
            primary_df['MA50'] = ta.sma(primary_df['Close'], length=50)
            primary_df['MA200'] = ta.sma(primary_df['Close'], length=200)
            
            # 차트 생성
            tech_fig = make_subplots(
                rows=2, cols=1,
                shared_xaxes=True,
                vertical_spacing=0.1,
                row_heights=[0.7, 0.3]
            )
            
            # 주가 및 이동평균선
            tech_fig.add_trace(
                go.Scatter(x=primary_df.index, y=primary_df['Close'], name="Price", 
                          line=dict(color='black', width=2)),
                row=1, col=1
            )
            tech_fig.add_trace(
                go.Scatter(x=primary_df.index, y=primary_df['MA20'], name="MA20",
                          line=dict(color='orange', dash='dot')),
                row=1, col=1
            )
            tech_fig.add_trace(
                go.Scatter(x=primary_df.index, y=primary_df['MA50'], name="MA50",
                          line=dict(color='blue', dash='dot')),
                row=1, col=1
            )
            tech_fig.add_trace(
                go.Scatter(x=primary_df.index, y=primary_df['MA200'], name="MA200",
                          line=dict(color='red', dash='dash')),
                row=1, col=1
            )
            
            # RSI
            tech_fig.add_trace(
                go.Scatter(x=primary_df.index, y=primary_df['RSI'], name="RSI (14)",
                          line=dict(color='purple')),
                row=2, col=1
            )
            tech_fig.add_hline(y=70, line_dash="dot", line_color="red", row=2, col=1)
            tech_fig.add_hline(y=30, line_dash="dot", line_color="green", row=2, col=1)
            
            tech_fig.update_layout(
                height=600,
                template="plotly_white",
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            tech_fig.update_yaxes(title_text="가격 (USD)", row=1, col=1)
            tech_fig.update_yaxes(title_text="RSI", row=2, col=1)
            
            st.plotly_chart(tech_fig, use_container_width=True)
            
            # RSI 신호 표시
            rsi_val = primary_df['RSI'].iloc[-1]
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if rsi_val > 70:
                    st.warning(f"🔥 과매수: RSI {rsi_val:.1f}")
                elif rsi_val < 30:
                    st.info(f"❄️ 과매도: RSI {rsi_val:.1f}")
                else:
                    st.success(f"📊 중립: RSI {rsi_val:.1f}")
            
            with col2:
                current_price = primary_df['Close'].iloc[-1]
                ma200 = primary_df['MA200'].iloc[-1]
                if current_price > ma200:
                    st.success(f"📈 상승추세: 가격 > MA200")
                else:
                    st.warning(f"📉 하락추세: 가격 < MA200")
            
            with col3:
                ma50 = primary_df['MA50'].iloc[-1]
                if current_price > ma50:
                    st.success(f"✅ 단기 강세: 가격 > MA50")
                else:
                    st.warning(f"⚠️ 단기 약세: 가격 < MA50")
    
    # 5. 성과 테이블
    st.divider()
    st.subheader("📋 상세 성과 데이터")
    
    if performance_data:
        perf_table = pd.DataFrame(performance_data)
        perf_table['Current'] = perf_table['Current'].apply(lambda x: f"${x:.2f}")
        perf_table['Change'] = perf_table['Change'].apply(lambda x: f"{x:.2f}%")
        perf_table['YTD'] = perf_table['YTD'].apply(lambda x: f"{x:.2f}%")
        perf_table['Low_52'] = perf_table['Low_52'].apply(lambda x: f"${x:.2f}")
        perf_table['High_52'] = perf_table['High_52'].apply(lambda x: f"${x:.2f}")
        
        st.dataframe(
            perf_table[['Ticker', 'Current', 'Change', 'YTD', 'Low_52', 'High_52']],
            use_container_width=True,
            hide_index=True
        )
    
    st.info("💡 본 대시보드는 교육 목적으로 제공됩니다. 투자 결정은 자신의 판단과 전문가 상담 후 결정하세요.")

else:
    st.error("❌ ETF 데이터를 로드할 수 없습니다. etf_list.csv 파일을 확인하세요.")