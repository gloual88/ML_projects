## matplotlib.use('Agg')  # Tkinter 없이 파일로만 저장 (주석 처리: 화면 출력용)
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

# 1. 데이터 수집
# 역외 위안화 (CNH) 데이터
cnh = yf.download('CNH=X', start='2024-07-01', end='2025-12-27', interval='1d')

# PBOC 고시환율은 yfinance에서 직접 제공하지 않음
# 대안: investing.com API, FRED, 또는 수동 데이터
# 여기서는 CNY=X (역내 위안화)를 PBOC fixing 프록시로 사용
cny = yf.download('CNY=X', start='2024-07-01', end='2025-12-27', interval='1d')

# 2. 데이터 정리 (index 기준으로 병합)
if cnh.empty or cny.empty:
    raise ValueError('다운로드된 데이터가 비어 있습니다. 날짜 범위 또는 티커를 확인하세요.')

# 날짜 기준으로 데이터프레임 병합
df = pd.merge(
    cnh[['Close', 'Open', 'High', 'Low']].rename(columns={
        'Close': 'CNH_Close',
        'Open': 'CNH_Open',
        'High': 'CNH_High',
        'Low': 'CNH_Low',
    }),
    cny[['Close']].rename(columns={'Close': 'CNY_Fixing'}),
    left_index=True, right_index=True, how='inner'
)
df = df.dropna()

# 3. Bloomberg 스타일 차트 생성
fig, ax = plt.subplots(figsize=(14, 8), facecolor='white')

# 캔들스틱 스타일 (간소화: 라인 + 범위)
dates = df.index

# 역외 위안화 - 캔들스틱 스타일 (high-low 범위)
for i, date in enumerate(dates):
    # 단일 색상 사용 (조건문 불필요)
    ax.plot([date, date], [df['CNH_Low'].iloc[i], df['CNH_High'].iloc[i]], 
            color='#8B0000', linewidth=0.8, alpha=0.7)

# PBOC 고시환율 - 검은 실선
ax.plot(dates, df['CNY_Fixing'], color='black', linewidth=1.5, label='PBOC yuan fixing')

# 7.00 기준선 (점선)
ax.axhline(y=7.00, color='#8B0000', linestyle='--', linewidth=1, alpha=0.7)

# 스타일링
ax.set_ylabel('Yuan per dollar', fontsize=12, fontweight='bold')
ax.yaxis.set_label_position('right')
ax.yaxis.tick_right()

# Y축 범위 설정
ax.set_ylim(6.95, 7.45)
ax.set_yticks([7.00, 7.10, 7.20, 7.30, 7.40])

# X축 포맷
ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%b\n%Y'))

# 그리드 & 스파인
ax.grid(True, axis='y', alpha=0.3, linestyle='-')
ax.spines['top'].set_visible(False)
ax.spines['left'].set_visible(False)

# 제목
plt.title('Offshore Yuan Gains Past 7 Per Dollar After Strong PBOC Fix', 
          fontsize=16, fontweight='bold', loc='left', pad=20)

# 범례
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
legend_elements = [
    Patch(facecolor='#8B0000', alpha=0.7, label='Offshore yuan spot'),
    Line2D([0], [0], color='black', linewidth=2, label='PBOC yuan fixing')
]
ax.legend(handles=legend_elements, loc='upper left', frameon=False)

# 출처
fig.text(0.02, 0.02, 'Source: Yahoo Finance (Bloomberg style recreation)', 
         fontsize=9, color='gray')

plt.tight_layout()
plt.savefig('cnh_pboc_chart.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.show()

print(f"데이터 기간: {df.index[0].strftime('%Y-%m-%d')} ~ {df.index[-1].strftime('%Y-%m-%d')}")
print(f"최신 CNH: {df['CNH_Close'].iloc[-1].item():.4f}")
print(f"최신 CNY Fixing: {df['CNY_Fixing'].iloc[-1].item():.4f}")