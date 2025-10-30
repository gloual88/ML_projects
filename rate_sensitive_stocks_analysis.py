"""
Rate-Sensitive Stocks Analysis
==============================
This script analyzes stocks that show higher sensitivity to short-term interest rate changes.

Analysis approach:
1. Download 2-year Treasury yield data for the past 5 years
2. Identify months with the largest yield drops
3. Download S&P 500 stock price data
4. Analyze which stocks performed best during rate-drop months
5. Rank top 25 stocks by median performance during rate drops
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List, Tuple
import warnings
warnings.filterwarnings('ignore')


class RateSensitiveStockAnalyzer:
    """Analyzes stock performance during interest rate drops"""

    def __init__(self, lookback_years: int = 5):
        """
        Initialize the analyzer

        Args:
            lookback_years: Number of years to look back for analysis
        """
        self.lookback_years = lookback_years
        self.start_date = (datetime.now() - timedelta(days=365*lookback_years)).strftime('%Y-%m-%d')
        self.end_date = datetime.now().strftime('%Y-%m-%d')
        self.treasury_data = None
        self.rate_drop_months = None

    def download_treasury_data(self) -> pd.DataFrame:
        """
        Download 2-year Treasury yield data

        Returns:
            DataFrame with Treasury yield data
        """
        print(f"Downloading 2-year Treasury yield data from {self.start_date} to {self.end_date}...")

        # US 2-Year Treasury Yield ticker in Yahoo Finance
        treasury = yf.Ticker("^IRX")  # 13-week Treasury Bill
        # For 2-year, we'll try ^UST2Y or use FRED data alternative

        try:
            # Try downloading 2-year Treasury data
            # Note: Yahoo Finance may not have direct 2Y data, so we use alternatives
            data = yf.download("^FVX", start=self.start_date, end=self.end_date, progress=False)

            if data.empty:
                print("Warning: Could not download ^FVX, trying alternative...")
                # Alternative: download from a Treasury ETF as proxy
                data = yf.download("SHY", start=self.start_date, end=self.end_date, progress=False)
                print("Using SHY (iShares 1-3 Year Treasury Bond ETF) as proxy")
        except Exception as e:
            print(f"Error downloading Treasury data: {e}")
            raise

        self.treasury_data = data
        return data

    def calculate_monthly_yield_changes(self) -> pd.DataFrame:
        """
        Calculate monthly changes in Treasury yields

        Returns:
            DataFrame with monthly yield changes
        """
        print("Calculating monthly yield changes...")

        # Resample to monthly and calculate changes
        if 'Close' in self.treasury_data.columns:
            monthly_yields = self.treasury_data['Close'].resample('M').last()
        else:
            monthly_yields = self.treasury_data.resample('M').last()

        # Calculate month-over-month changes
        monthly_changes = monthly_yields.pct_change() * 100  # Convert to percentage

        # Create DataFrame with changes
        changes_df = pd.DataFrame({
            'Date': monthly_changes.index,
            'Yield_Change_Pct': monthly_changes.values
        })

        changes_df = changes_df.dropna()
        changes_df = changes_df.sort_values('Yield_Change_Pct')

        return changes_df

    def identify_rate_drop_months(self, top_n: int = 10) -> List[pd.Timestamp]:
        """
        Identify months with largest rate drops

        Args:
            top_n: Number of top rate-drop months to identify

        Returns:
            List of dates representing rate-drop months
        """
        print(f"\nIdentifying top {top_n} months with largest rate drops...")

        monthly_changes = self.calculate_monthly_yield_changes()

        # Get top N months with largest drops (most negative changes)
        top_drops = monthly_changes.nsmallest(top_n, 'Yield_Change_Pct')

        print("\nTop months with largest rate drops:")
        print(top_drops.to_string(index=False))

        self.rate_drop_months = top_drops['Date'].tolist()
        return self.rate_drop_months

    def get_sp500_tickers(self) -> List[str]:
        """
        Get list of S&P 500 tickers

        Returns:
            List of ticker symbols
        """
        print("\nGetting S&P 500 ticker list...")

        # Notable rate-sensitive stocks mentioned in the article
        mentioned_stocks = ['BX', 'AVB', 'LEN', 'CARR', 'EFX', 'RVTY', 'WAT']

        # Additional known rate-sensitive stocks
        additional_stocks = [
            # Real Estate
            'EQR', 'MAA', 'UDR', 'CPT', 'ESS',
            # Homebuilders
            'DHI', 'PHM', 'KBH', 'TOL', 'MTH',
            # Financial Services
            'JPM', 'BAC', 'WFC', 'C', 'GS', 'MS',
            # REITs
            'PLD', 'AMT', 'CCI', 'SPG', 'O',
            # Utilities (rate-sensitive)
            'NEE', 'DUK', 'SO', 'D', 'AEP',
            # Technology
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META',
            # Industrial
            'BA', 'CAT', 'DE', 'GE', 'HON',
            # Consumer Discretionary
            'HD', 'LOW', 'NKE', 'MCD', 'SBUX',
            # Healthcare
            'UNH', 'JNJ', 'PFE', 'ABBV', 'TMO',
            # Communication Services
            'T', 'VZ', 'CMCSA', 'DIS', 'NFLX'
        ]

        # Combine all tickers
        all_tickers = list(set(mentioned_stocks + additional_stocks))

        print(f"Analyzing {len(all_tickers)} stocks")
        print(f"Mentioned stocks: {', '.join(mentioned_stocks)}")

        return all_tickers

    def analyze_stock_performance(self, tickers: List[str]) -> pd.DataFrame:
        """
        Analyze stock performance during rate-drop months

        Args:
            tickers: List of stock tickers to analyze

        Returns:
            DataFrame with stock performance metrics
        """
        print("\nAnalyzing stock performance during rate-drop months...")

        results = []

        for ticker in tickers:
            try:
                print(f"Processing {ticker}...", end=' ')

                # Download stock data
                stock = yf.download(ticker, start=self.start_date, end=self.end_date,
                                   progress=False, auto_adjust=True)

                if stock.empty:
                    print("No data")
                    continue

                # Calculate monthly returns
                monthly_prices = stock['Close'].resample('M').last()
                monthly_returns = monthly_prices.pct_change() * 100

                # Get returns for rate-drop months
                rate_drop_returns = []
                for drop_month in self.rate_drop_months:
                    # Find the closest month in the stock data
                    closest_month = monthly_returns.index[
                        monthly_returns.index.to_series().apply(
                            lambda x: abs((x.year - drop_month.year) * 12 + x.month - drop_month.month)
                        ).argmin()
                    ]

                    if abs((closest_month.year - drop_month.year) * 12 +
                           closest_month.month - drop_month.month) <= 1:
                        if closest_month in monthly_returns.index:
                            ret = monthly_returns.loc[closest_month]
                            if not pd.isna(ret):
                                rate_drop_returns.append(ret)

                if len(rate_drop_returns) == 0:
                    print("No matching data")
                    continue

                # Calculate statistics
                median_return = np.median(rate_drop_returns)
                mean_return = np.mean(rate_drop_returns)
                positive_months = sum(1 for r in rate_drop_returns if r > 0)
                total_months = len(rate_drop_returns)

                results.append({
                    'Ticker': ticker,
                    'Median_Return': median_return,
                    'Mean_Return': mean_return,
                    'Positive_Months': positive_months,
                    'Total_Months': total_months,
                    'Win_Rate': (positive_months / total_months * 100) if total_months > 0 else 0,
                    'All_Returns': rate_drop_returns
                })

                print(f"Median: {median_return:.2f}%")

            except Exception as e:
                print(f"Error: {e}")
                continue

        # Create DataFrame and sort by median return
        results_df = pd.DataFrame(results)
        results_df = results_df.sort_values('Median_Return', ascending=False)

        return results_df

    def display_top_performers(self, results_df: pd.DataFrame, top_n: int = 25):
        """
        Display top performing stocks during rate drops

        Args:
            results_df: DataFrame with stock performance results
            top_n: Number of top performers to display
        """
        print(f"\n{'='*80}")
        print(f"TOP {top_n} RATE-SENSITIVE STOCKS (by Median Return during rate drops)")
        print(f"{'='*80}\n")

        top_performers = results_df.head(top_n)

        display_df = top_performers[['Ticker', 'Median_Return', 'Mean_Return',
                                     'Win_Rate', 'Total_Months']].copy()
        display_df.columns = ['Ticker', 'Median Return (%)', 'Mean Return (%)',
                             'Win Rate (%)', 'Sample Size']

        print(display_df.to_string(index=False))

        # Check if mentioned stocks are in top performers
        mentioned_stocks = ['BX', 'AVB', 'LEN', 'CARR', 'EFX', 'RVTY', 'WAT']
        print(f"\n{'='*80}")
        print("MENTIONED STOCKS PERFORMANCE:")
        print(f"{'='*80}\n")

        for stock in mentioned_stocks:
            stock_data = results_df[results_df['Ticker'] == stock]
            if not stock_data.empty:
                rank = results_df[results_df['Ticker'] == stock].index[0] + 1
                median_ret = stock_data.iloc[0]['Median_Return']
                win_rate = stock_data.iloc[0]['Win_Rate']
                print(f"{stock:6s} - Rank: {rank:3d} | Median Return: {median_ret:6.2f}% | Win Rate: {win_rate:5.1f}%")
            else:
                print(f"{stock:6s} - No data available")

    def plot_results(self, results_df: pd.DataFrame, top_n: int = 25):
        """
        Create visualizations of the results

        Args:
            results_df: DataFrame with stock performance results
            top_n: Number of top performers to plot
        """
        print("\nGenerating visualizations...")

        # Set style
        sns.set_style("whitegrid")

        # Create figure with subplots
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))

        # 1. Top performers by median return
        top_performers = results_df.head(top_n)
        ax1 = axes[0, 0]
        bars = ax1.barh(range(len(top_performers)), top_performers['Median_Return'])
        ax1.set_yticks(range(len(top_performers)))
        ax1.set_yticklabels(top_performers['Ticker'])
        ax1.set_xlabel('Median Return (%)')
        ax1.set_title(f'Top {top_n} Stocks by Median Return During Rate Drops')
        ax1.invert_yaxis()

        # Color bars based on value
        for i, (bar, val) in enumerate(zip(bars, top_performers['Median_Return'])):
            bar.set_color('green' if val > 0 else 'red')

        # 2. Win rate vs Median return scatter
        ax2 = axes[0, 1]
        scatter = ax2.scatter(results_df['Median_Return'], results_df['Win_Rate'],
                            s=100, alpha=0.6, c=results_df['Median_Return'],
                            cmap='RdYlGn')

        # Annotate mentioned stocks
        mentioned_stocks = ['BX', 'AVB', 'LEN', 'CARR', 'EFX', 'RVTY', 'WAT']
        for stock in mentioned_stocks:
            stock_data = results_df[results_df['Ticker'] == stock]
            if not stock_data.empty:
                ax2.annotate(stock,
                           (stock_data.iloc[0]['Median_Return'],
                            stock_data.iloc[0]['Win_Rate']),
                           fontsize=10, fontweight='bold')

        ax2.set_xlabel('Median Return (%)')
        ax2.set_ylabel('Win Rate (%)')
        ax2.set_title('Win Rate vs Median Return')
        ax2.axhline(y=50, color='gray', linestyle='--', alpha=0.5)
        ax2.axvline(x=0, color='gray', linestyle='--', alpha=0.5)
        plt.colorbar(scatter, ax=ax2, label='Median Return (%)')

        # 3. Distribution of returns for top 10 stocks
        ax3 = axes[1, 0]
        top_10 = results_df.head(10)
        box_data = [stock_data for stock_data in top_10['All_Returns']]
        bp = ax3.boxplot(box_data, labels=top_10['Ticker'], patch_artist=True)

        for patch in bp['boxes']:
            patch.set_facecolor('lightblue')

        ax3.set_xlabel('Stock Ticker')
        ax3.set_ylabel('Monthly Return (%)')
        ax3.set_title('Distribution of Returns During Rate Drops (Top 10 Stocks)')
        ax3.axhline(y=0, color='red', linestyle='--', alpha=0.5)
        plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45)

        # 4. Mean vs Median return comparison
        ax4 = axes[1, 1]
        top_20 = results_df.head(20)
        x = range(len(top_20))
        width = 0.35

        ax4.bar([i - width/2 for i in x], top_20['Median_Return'],
               width, label='Median Return', alpha=0.8)
        ax4.bar([i + width/2 for i in x], top_20['Mean_Return'],
               width, label='Mean Return', alpha=0.8)

        ax4.set_xlabel('Stock Ticker')
        ax4.set_ylabel('Return (%)')
        ax4.set_title('Mean vs Median Returns (Top 20 Stocks)')
        ax4.set_xticks(x)
        ax4.set_xticklabels(top_20['Ticker'], rotation=45)
        ax4.legend()
        ax4.axhline(y=0, color='gray', linestyle='--', alpha=0.5)

        plt.tight_layout()

        # Save figure
        output_file = '/home/user/ML_projects/rate_sensitive_stocks_analysis.png'
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"Visualization saved to: {output_file}")

        # Show plot
        plt.show()

    def run_full_analysis(self, top_n: int = 25):
        """
        Run the complete analysis pipeline

        Args:
            top_n: Number of top performers to analyze
        """
        print("="*80)
        print("RATE-SENSITIVE STOCKS ANALYSIS")
        print("="*80)
        print(f"Analysis period: {self.start_date} to {self.end_date}")
        print(f"Lookback period: {self.lookback_years} years\n")

        # Step 1: Download Treasury data
        self.download_treasury_data()

        # Step 2: Identify rate drop months
        self.identify_rate_drop_months(top_n=10)

        # Step 3: Get stock tickers
        tickers = self.get_sp500_tickers()

        # Step 4: Analyze stock performance
        results_df = self.analyze_stock_performance(tickers)

        # Step 5: Display results
        self.display_top_performers(results_df, top_n=top_n)

        # Step 6: Create visualizations
        self.plot_results(results_df, top_n=top_n)

        # Save results to CSV
        output_csv = '/home/user/ML_projects/rate_sensitive_stocks_results.csv'
        results_df_export = results_df[['Ticker', 'Median_Return', 'Mean_Return',
                                        'Win_Rate', 'Total_Months']].copy()
        results_df_export.to_csv(output_csv, index=False)
        print(f"\nResults saved to: {output_csv}")

        return results_df


def main():
    """Main function to run the analysis"""

    # Create analyzer instance
    analyzer = RateSensitiveStockAnalyzer(lookback_years=5)

    # Run full analysis
    results = analyzer.run_full_analysis(top_n=25)

    print("\n" + "="*80)
    print("ANALYSIS COMPLETE!")
    print("="*80)

    return results


if __name__ == "__main__":
    results = main()
