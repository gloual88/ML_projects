# 금리 민감 주식 분석 (Rate-Sensitive Stocks Analysis)

## 개요

이 프로젝트는 단기 금리 하락에 민감하게 반응하는 주식들을 실제 데이터를 통해 분석합니다.

CNBC PRO 기사에서 언급된 분석 방법론을 구현하여:
- 지난 5년간 2년물 국채 수익률이 가장 크게 하락한 월들을 식별
- 해당 기간 동안 S&P 500 종목들의 성과를 분석
- 금리 하락 시 가장 큰 상승을 보인 상위 25개 종목을 중간값 기준으로 순위 매김

## 분석 대상 주요 종목

기사에서 언급된 금리 민감주:
- **BX** (Blackstone) - 사모펀드/부동산
- **AVB** (AvalonBay Communities) - 아파트 REIT
- **LEN** (Lennar) - 주택건설
- **CARR** (Carrier Global) - HVAC 시스템
- **EFX** (Equifax) - 신용조회
- **RVTY** (Revvity) - 바이오테크
- **WAT** (Waters Corp) - 바이오테크 장비

## 설치 방법

### 필수 패키지 설치

```bash
pip install -r requirements_rate_analysis.txt
```

또는 개별 설치:

```bash
pip install yfinance pandas numpy matplotlib seaborn
```

## 사용 방법

### 기본 실행

```bash
python rate_sensitive_stocks_analysis.py
```

### Python 스크립트에서 사용

```python
from rate_sensitive_stocks_analysis import RateSensitiveStockAnalyzer

# 분석기 생성 (지난 5년 데이터)
analyzer = RateSensitiveStockAnalyzer(lookback_years=5)

# 전체 분석 실행
results = analyzer.run_full_analysis(top_n=25)

# 결과 확인
print(results[['Ticker', 'Median_Return', 'Win_Rate']].head(10))
```

### 고급 사용법

```python
# 1. 개별 단계 실행
analyzer = RateSensitiveStockAnalyzer(lookback_years=5)

# 2. 국채 수익률 데이터 다운로드
treasury_data = analyzer.download_treasury_data()

# 3. 금리 하락 월 식별
rate_drop_months = analyzer.identify_rate_drop_months(top_n=10)

# 4. 분석할 주식 티커 가져오기
tickers = analyzer.get_sp500_tickers()

# 5. 주식 성과 분석
results = analyzer.analyze_stock_performance(tickers)

# 6. 결과 표시
analyzer.display_top_performers(results, top_n=25)

# 7. 시각화 생성
analyzer.plot_results(results, top_n=25)
```

## 출력 파일

분석 실행 후 다음 파일들이 생성됩니다:

1. **rate_sensitive_stocks_results.csv**
   - 모든 분석된 주식의 성과 지표
   - 컬럼: Ticker, Median_Return, Mean_Return, Win_Rate, Total_Months

2. **rate_sensitive_stocks_analysis.png**
   - 4개의 차트를 포함한 시각화:
     - 상위 25개 종목의 중간값 수익률 막대 그래프
     - 승률 vs 중간값 수익률 산점도
     - 상위 10개 종목의 수익률 분포 박스플롯
     - 상위 20개 종목의 평균 vs 중간값 수익률 비교

## 분석 지표 설명

- **Median Return (%)**: 금리 하락 월 동안의 중간값 수익률
  - 이상치에 강건한 지표로, 일관된 성과를 나타냄

- **Mean Return (%)**: 금리 하락 월 동안의 평균 수익률
  - 전체적인 수익률 수준을 나타냄

- **Win Rate (%)**: 금리 하락 월 동안 양의 수익을 기록한 비율
  - 100%에 가까울수록 일관되게 상승

- **Total Months**: 분석에 사용된 금리 하락 월의 개수
  - 샘플 크기를 나타내며, 클수록 통계적으로 신뢰도가 높음

## 분석 방법론

### 1. 금리 하락 월 식별
- 2년물 국채 수익률의 월별 변화율 계산
- 가장 큰 하락폭을 보인 상위 10개월 선정

### 2. 주식 성과 계산
- 각 종목의 월별 수익률 계산
- 금리 하락 월에 해당하는 수익률 추출

### 3. 순위 산정
- 중간값 수익률 기준으로 정렬
- 상위 25개 종목 선정

## 주의사항

1. **데이터 출처**: Yahoo Finance를 사용하므로 인터넷 연결 필요
2. **표본 크기**: 5년간 데이터이므로 표본이 제한적일 수 있음
3. **과거 성과**: 과거 성과가 미래 수익을 보장하지 않음
4. **시장 상황**: 현재 시장 상황이 과거와 다를 수 있음

## 데이터 소스 이슈

Yahoo Finance에서 2년물 국채 수익률 직접 다운로드가 어려운 경우:
- `^FVX` (5-Year Treasury Yield) 사용
- 또는 `SHY` (iShares 1-3 Year Treasury Bond ETF)를 프록시로 사용

더 정확한 2년물 데이터가 필요한 경우 FRED API 사용 권장:
```bash
pip install fredapi
```

## 예상 실행 시간

- 네트워크 속도에 따라 다르지만 대략 5-10분 소요
- 약 70-80개 종목 데이터 다운로드 및 분석

## 문제 해결

### yfinance 오류
```bash
pip install --upgrade yfinance
```

### matplotlib 표시 오류
```python
# 스크립트 상단에 추가
import matplotlib
matplotlib.use('Agg')  # GUI 없이 저장만 하는 경우
```

### 데이터 다운로드 실패
- 인터넷 연결 확인
- Yahoo Finance API 제한 확인 (너무 많은 요청 시 일시적 차단)
- 시간을 두고 재시도

## 확장 가능성

1. **더 많은 종목 분석**: S&P 500 전체 종목으로 확대
2. **다른 금리 지표**: 10년물 국채, Fed Funds Rate 등
3. **섹터별 분석**: 금융, 부동산, 소비재 등 섹터별 민감도
4. **머신러닝 모델**: 금리 변화로부터 주가 예측 모델 구축
5. **리스크 조정 수익률**: Sharpe Ratio, Maximum Drawdown 등 추가

## 라이선스

MIT License

## 참고자료

- CNBC PRO: "These rate-sensitive stocks could surge as the Fed cuts"
- Yahoo Finance API Documentation
- Federal Reserve Economic Data (FRED)
