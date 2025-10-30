"""
간단한 금리 민감 주식 분석 예제
Simple Example for Rate-Sensitive Stocks Analysis
"""

from rate_sensitive_stocks_analysis import RateSensitiveStockAnalyzer
import warnings
warnings.filterwarnings('ignore')


def simple_analysis():
    """간단한 분석 실행"""

    print("="*80)
    print("금리 민감 주식 분석 시작")
    print("Rate-Sensitive Stocks Analysis")
    print("="*80)
    print()

    # 1. 분석기 생성
    print("1. 분석기 생성 중...")
    analyzer = RateSensitiveStockAnalyzer(lookback_years=5)
    print("   완료!\n")

    # 2. 전체 분석 실행
    print("2. 전체 분석 실행 중...")
    print("   (데이터 다운로드에 5-10분 정도 소요될 수 있습니다)")
    results = analyzer.run_full_analysis(top_n=25)
    print("   완료!\n")

    # 3. 추가 분석 - 기사에 언급된 주식들의 순위 확인
    print("="*80)
    print("추가 분석: 언급된 주식들의 상세 정보")
    print("="*80)
    print()

    mentioned_stocks = ['BX', 'AVB', 'LEN', 'CARR', 'EFX', 'RVTY', 'WAT']

    for stock in mentioned_stocks:
        stock_data = results[results['Ticker'] == stock]
        if not stock_data.empty:
            rank = results[results['Ticker'] == stock].index[0] + 1
            data = stock_data.iloc[0]

            print(f"\n{stock} ({get_stock_name(stock)})")
            print("-" * 40)
            print(f"  순위: {rank}위 / {len(results)}개 종목")
            print(f"  중간값 수익률: {data['Median_Return']:.2f}%")
            print(f"  평균 수익률: {data['Mean_Return']:.2f}%")
            print(f"  승률: {data['Win_Rate']:.1f}%")
            print(f"  분석 개월수: {data['Total_Months']}개월")

            # 해석
            if data['Median_Return'] > 5:
                print(f"  평가: 🟢 금리 하락 시 매우 강한 상승 경향")
            elif data['Median_Return'] > 2:
                print(f"  평가: 🟡 금리 하락 시 양호한 상승 경향")
            elif data['Median_Return'] > 0:
                print(f"  평가: 🟡 금리 하락 시 약한 상승 경향")
            else:
                print(f"  평가: 🔴 금리 하락 시 음의 수익률")

    print("\n" + "="*80)
    print("분석 완료!")
    print("="*80)
    print("\n생성된 파일:")
    print("  - rate_sensitive_stocks_results.csv (전체 결과)")
    print("  - rate_sensitive_stocks_analysis.png (시각화)")
    print()

    return results


def get_stock_name(ticker):
    """주식 티커의 회사명 반환"""
    names = {
        'BX': 'Blackstone',
        'AVB': 'AvalonBay Communities',
        'LEN': 'Lennar',
        'CARR': 'Carrier Global',
        'EFX': 'Equifax',
        'RVTY': 'Revvity',
        'WAT': 'Waters Corporation'
    }
    return names.get(ticker, ticker)


def quick_check_specific_stocks():
    """특정 주식들만 빠르게 확인하는 예제"""

    print("특정 주식들의 금리 민감도 빠른 확인")
    print("="*80)
    print()

    analyzer = RateSensitiveStockAnalyzer(lookback_years=3)  # 3년만 분석

    # Treasury 데이터 다운로드
    analyzer.download_treasury_data()

    # 금리 하락 월 식별
    analyzer.identify_rate_drop_months(top_n=5)  # 상위 5개월만

    # 특정 주식들만 분석
    specific_tickers = ['BX', 'AVB', 'LEN', 'CARR', 'EFX']

    print(f"\n분석 대상: {', '.join(specific_tickers)}")
    print()

    results = analyzer.analyze_stock_performance(specific_tickers)

    print("\n결과:")
    print(results[['Ticker', 'Median_Return', 'Mean_Return', 'Win_Rate']].to_string(index=False))

    return results


if __name__ == "__main__":
    # 전체 분석 실행
    results = simple_analysis()

    # 또는 빠른 확인만 원하면 아래 주석 해제:
    # results = quick_check_specific_stocks()
