import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas_ta as ta
from datetime import datetime, timedelta

# 페이지 설정
st.set_page_config(page_title="Multi-Index Investment Dashboard", layout="wide")

# 사이드바 설정
st.sidebar.header("📊 대시보드 설정")

# 분석 대상 티커 설정
tickers = {
    "S&P 500": "^GSPC",
    "나스닥 (Nasdaq)": "^IXIC",
    "다우 (Dow)": "^DJI",
    "VIX (공포지수)": "^VIX",
    "10년물 국채금리": "^TNX",
    "금 (Gold)": "GC=F",
    "유가 (WTI)": "CL=F"
}

# 기간 설정
period_map = {"1개월": 30, "3개월": 90, "6개월": 180, "1년": 365, "2년": 730}
selected_period = st.sidebar.selectbox("조회 기간 선택", list(period_map.keys()), index=3)

# 데이터 캐싱 (속도 및 효율성)
@st.cache_data(ttl=3600)
def fetch_data(symbol, days=730):
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        # auto_adjust=True를 통해 구조 단순화, multi_level 인덱스 방지 시도
        data = yf.download(symbol, start=start_date, end=end_date, progress=False, auto_adjust=True)
        
        # 데이터가 비어있지 않은지 확인
        if data.empty:
            return pd.DataFrame()
            
        # 최신 yfinance 버전 대응: Multi-index 컬럼인 경우 단일 컬럼으로 변환
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
            
        return data
    except Exception as e:
        st.error(f"데이터 로드 실패 ({symbol}): {e}")
        return pd.DataFrame()

# 메인 타이틀
st.title("📊 2025 마켓 워치: 멀티 인덱스 투자 대시보드")
st.markdown(f"**현재 시각:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (데이터 소스: Yahoo Finance)")

# 1. 상단 퀵뷰 (주요 지표 카드)
st.subheader("📍 실시간 주요 지표 현황")
cols = st.columns(len(tickers))

data_dict = {}
for i, (name, symbol) in enumerate(tickers.items()):
    df = fetch_data(symbol)
    if not df.empty and len(df) > 1:
        # 데이터 추출 시 .iloc[-1]이 Series인 경우를 대비해 values[0] 또는 item() 사용
        try:
            current_val = df['Close'].iloc[-1]
            prev_val = df['Close'].iloc[-2]
            
            # 스칼라 값으로 확실히 변환 (오류 방지 핵심)
            current_price = float(current_val.iloc[0]) if isinstance(current_val, pd.Series) else float(current_val)
            prev_price = float(prev_val.iloc[0]) if isinstance(prev_val, pd.Series) else float(prev_val)
            
            change = current_price - prev_price
            pct_change = (change / prev_price) * 100
            
            low_52 = float(df['Close'].iloc[-252:].min()) if len(df) >= 252 else float(df['Close'].min())
            high_52 = float(df['Close'].iloc[-252:].max()) if len(df) >= 252 else float(df['Close'].max())
            
            with cols[i]:
                st.metric(label=name, value=f"{current_price:,.2f}", delta=f"{pct_change:.2f}%")
                st.caption(f"52주 L:{low_52:,.0f} / H:{high_52:,.0f}")
            data_dict[name] = df
        except Exception as e:
            with cols[i]:
                st.error("데이터 변환 오류")
                st.caption(str(e))

# 2. 메인 차트: 주가 지수와 변동성 지표
st.divider()
st.subheader("📈 S&P 500 흐름 및 공포지수(VIX) 비교")

if "S&P 500" in data_dict and "VIX (공포지수)" in data_dict:
    main_df = data_dict["S&P 500"].copy()
    vix_df = data_dict["VIX (공포지수)"].copy()

    # 기간 필터링
    days_to_show = period_map[selected_period]
    main_df = main_df.tail(days_to_show)
    vix_df = vix_df.tail(days_to_show)

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    fig.add_trace(
        go.Scatter(x=main_df.index, y=main_df['Close'], name="S&P 500", line=dict(color='#3366CC', width=2.5)),
        secondary_y=False,
    )
    
    fig.add_trace(
        go.Scatter(x=vix_df.index, y=vix_df['Close'], name="VIX (공포지수)", fill='tozeroy', line=dict(color='rgba(255, 75, 75, 0.4)'), opacity=0.3),
        secondary_y=True,
    )
    
    fig.update_layout(
        hovermode="x unified",
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=20, r=20, t=50, b=20)
    )
    fig.update_yaxes(title_text="<b>S&P 500</b> 가격", secondary_y=False)
    fig.update_yaxes(title_text="<b>VIX</b> 레벨", secondary_y=True)
    
    st.plotly_chart(fig, use_container_width=True)

# 3. 상세 분석 섹션
col_tech, col_ytd = st.columns([1, 1])

with col_tech:
    st.subheader("🛠️ 기술적 분석 (S&P 500)")
    # 보조지표 계산 (데이터가 충분할 때만)
    if len(main_df) > 20:
        main_df['RSI'] = ta.rsi(main_df['Close'], length=14)
        main_df['MA50'] = ta.sma(main_df['Close'], length=50)
        main_df['MA200'] = ta.sma(main_df['Close'], length=200)
        
        tech_fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08, row_heights=[0.7, 0.3])
        
        # 주가 및 이평선
        tech_fig.add_trace(go.Scatter(x=main_df.index, y=main_df['Close'], name="Price", line=dict(color='green')), row=1, col=1)
        if 'MA50' in main_df:
            tech_fig.add_trace(go.Scatter(x=main_df.index, y=main_df['MA50'], name="50일 이평선", line=dict(color='orange', dash='dot')), row=1, col=1)
        if 'MA200' in main_df:
            tech_fig.add_trace(go.Scatter(x=main_df.index, y=main_df['MA200'], name="200일 이평선", line=dict(color='red', dash='dash')), row=1, col=1)
        
        # RSI
        if 'RSI' in main_df:
            tech_fig.add_trace(go.Scatter(x=main_df.index, y=main_df['RSI'], name="RSI (14)", line=dict(color='purple')), row=2, col=1)
            tech_fig.add_hline(y=70, line_dash="dot", line_color="red", row=2, col=1)
            tech_fig.add_hline(y=30, line_dash="dot", line_color="green", row=2, col=1)
        
        tech_fig.update_layout(height=500, template="plotly_white", showlegend=False)
        st.plotly_chart(tech_fig, use_container_width=True)
    else:
        st.info("기술적 분석을 위한 데이터가 부족합니다.")

with col_ytd:
    st.subheader("🌍 자산군별 상대 성과 비교")
    
    comparison_df = pd.DataFrame()
    for name, df in data_dict.items():
        sub_df = df.tail(days_to_show)
        if not sub_df.empty:
            first_val = sub_df['Close'].iloc[0]
            first_price = float(first_val.iloc[0]) if isinstance(first_val, pd.Series) else float(first_val)
            comparison_df[name] = (sub_df['Close'] / first_price) * 100
        
    compare_fig = go.Figure()
    for col in comparison_df.columns:
        color = 'green' if col == "S&P 500" else None
        compare_fig.add_trace(
            go.Scatter(
                x=comparison_df.index,
                y=comparison_df[col],
                name=col,
                line=dict(color=color) if color else {}
            )
        )
        
    compare_fig.update_layout(
        title=f"선택 기간 내 상대적 변동률 (기준점=100)",
        yaxis_title="성과 지수",
        template="plotly_white",
        height=500
    )
    st.plotly_chart(compare_fig, use_container_width=True)

# 4. 리스크 알림
st.divider()
st.subheader("⚠️ 투자 리스크 모니터링")

vix_last = vix_df['Close'].iloc[-1]
vix_val = float(vix_last.iloc[0]) if isinstance(vix_last, pd.Series) else float(vix_last)

rsi_val = 50.0 # 기본값
if 'RSI' in main_df and not main_df['RSI'].empty:
    rsi_last = main_df['RSI'].iloc[-1]
    rsi_val = float(rsi_last.iloc[0]) if isinstance(rsi_last, pd.Series) else float(rsi_last)

a1, a2, a3 = st.columns(3)

with a1:
    if vix_val > 25:
        st.error(f"🚨 시장 불안정: VIX가 {vix_val:.2f}로 높습니다.")
    else:
        st.success(f"✅ 변동성 양호: VIX가 {vix_val:.2f}로 안정권입니다.")

with a2:
    if rsi_val > 70:
        st.warning(f"🔥 과매수 주의: RSI({rsi_val:.1f})가 70을 상회합니다.")
    elif rsi_val < 30:
        st.info(f"❄️ 과매도 구간: RSI({rsi_val:.1f})가 30을 하회합니다.")
    else:
        st.write(f"📊 심리 지표: RSI {rsi_val:.1f} (중립 구간)")

with a3:
    gold_df = data_dict.get("금 (Gold)")
    if gold_df is not None:
        gold_last = gold_df['Close'].iloc[-1]
        gold_price = float(gold_last.iloc[0]) if isinstance(gold_last, pd.Series) else float(gold_last)
        st.write(f"💰 **금 선물:** ${gold_price:,.2f}")
        st.caption("안전자산 흐름을 주시하세요.")

st.info("본 대시보드는 로컬 환경에서 Python 3.13 및 Streamlit을 사용하여 구동됩니다.")