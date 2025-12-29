// 전역 변수
let allETFs = [];
let selectedTickers = [];
let etfList = {};

// DOM 요소 캐시
const domCache = {
    analysisTypeRadios: document.querySelectorAll('input[name="analysis-type"]'),
    customSection: document.getElementById('custom-section'),
    searchETF: document.getElementById('search-etf'),
    etfCheckboxList: document.getElementById('etf-checkbox-list'),
    periodSelect: document.getElementById('period-select'),
    refreshBtn: document.getElementById('refresh-btn'),
    updateTime: document.getElementById('update-time'),
    performanceCards: document.getElementById('performance-cards'),
    priceChart: document.getElementById('price-chart'),
    ytdChart: document.getElementById('ytd-chart'),
    technicalEtfSelect: document.getElementById('technical-etf-select'),
    technicalSignals: document.getElementById('technical-signals'),
    technicalChart: document.getElementById('technical-chart'),
    dataTable: document.getElementById('data-table'),
};

// 페이지 로드 시 초기화
document.addEventListener('DOMContentLoaded', async () => {
    await initializeDashboard();
});

// 대시보드 초기화
async function initializeDashboard() {
    try {
        // ETF 목록 로드
        await loadETFList();
        
        // 이벤트 리스너 설정
        setupEventListeners();
        
        // 초기 데이터 로드
        await updateDashboard();
    } catch (error) {
        console.error('초기화 오류:', error);
        alert('대시보드 초기화 실패');
    }
}

// ETF 목록 로드
async function loadETFList() {
    try {
        const response = await fetch('/api/etf-list');
        const data = await response.json();
        
        etfList = {
            sector_etfs: data.sector_etfs,
            theme_etfs: data.theme_etfs,
            broad_market_etfs: data.broad_market_etfs
        };
        
        allETFs = data.all_etfs;
        
        // 초기 선택 (섹터 ETF)
        selectedTickers = data.sector_etfs.map(e => e.Ticker);
        
        // 기술적 분석 선택 옵션 채우기
        populateTechnicalSelect(selectedTickers);
    } catch (error) {
        console.error('ETF 목록 로드 오류:', error);
    }
}

// 이벤트 리스너 설정
function setupEventListeners() {
    // 분석 타입 변경
    domCache.analysisTypeRadios.forEach(radio => {
        radio.addEventListener('change', handleAnalysisTypeChange);
    });
    
    // 기간 변경
    domCache.periodSelect.addEventListener('change', updateDashboard);
    
    // 새로고침 버튼
    domCache.refreshBtn.addEventListener('click', updateDashboard);
    
    // ETF 검색
    domCache.searchETF.addEventListener('input', filterETFList);
    
    // 기술적 분석 ETF 선택
    domCache.technicalEtfSelect.addEventListener('change', handleTechnicalETFChange);
}

// 분석 타입 변경 핸들러
async function handleAnalysisTypeChange(e) {
    const type = e.target.value;
    
    if (type === 'sector') {
        selectedTickers = etfList.sector_etfs.map(e => e.Ticker);
    } else if (type === 'theme') {
        selectedTickers = etfList.theme_etfs.map(e => e.Ticker);
    } else if (type === 'broad') {
        selectedTickers = etfList.broad_market_etfs.map(e => e.Ticker);
    } else if (type === 'custom') {
        domCache.customSection.style.display = 'block';
        renderCustomETFList();
        return;
    }
    
    domCache.customSection.style.display = 'none';
    populateTechnicalSelect(selectedTickers);
    await updateDashboard();
}

// 커스텀 ETF 목록 렌더링
function renderCustomETFList() {
    domCache.etfCheckboxList.innerHTML = '';
    
    allETFs.forEach(etf => {
        const label = document.createElement('label');
        label.className = 'etf-checkbox-label';
        label.innerHTML = `
            <input type="checkbox" value="${etf.Ticker}" 
                   ${selectedTickers.includes(etf.Ticker) ? 'checked' : ''}>
            <span>${etf.Ticker} - ${etf.Name}</span>
        `;
        
        label.querySelector('input').addEventListener('change', handleCustomETFChange);
        domCache.etfCheckboxList.appendChild(label);
    });
}

// 커스텀 ETF 변경
function handleCustomETFChange(e) {
    const ticker = e.target.value;
    
    if (e.target.checked) {
        if (!selectedTickers.includes(ticker)) {
            selectedTickers.push(ticker);
        }
    } else {
        selectedTickers = selectedTickers.filter(t => t !== ticker);
    }
    
    populateTechnicalSelect(selectedTickers);
    updateDashboard();
}

// ETF 목록 필터링
function filterETFList(e) {
    const searchTerm = e.target.value.toLowerCase();
    const checkboxes = domCache.etfCheckboxList.querySelectorAll('label');
    
    checkboxes.forEach(checkbox => {
        const text = checkbox.textContent.toLowerCase();
        checkbox.style.display = text.includes(searchTerm) ? 'flex' : 'none';
    });
}

// 대시보드 업데이트
async function updateDashboard() {
    updateTime();
    
    if (selectedTickers.length === 0) {
        alert('최소 1개의 ETF를 선택하세요.');
        return;
    }
    
    const days = parseInt(domCache.periodSelect.value);
    
    // 모든 업데이트 병렬 실행
    await Promise.all([
        updatePerformanceCards(days),
        updatePriceChart(days),
        updateYTDComparison(),
        updateTechnicalAnalysis(days)
    ]);
}

// 시간 업데이트
function updateTime() {
    const now = new Date();
    const time = now.toLocaleTimeString('ko-KR');
    domCache.updateTime.textContent = time;
}

// 성과 카드 업데이트
async function updatePerformanceCards(days) {
    try {
        domCache.performanceCards.innerHTML = '<div class="loading-spinner">로딩 중...</div>';
        
        const response = await fetch('/api/etf-performance', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ tickers: selectedTickers, days })
        });
        
        const data = await response.json();
        
        if (!Array.isArray(data)) {
            domCache.performanceCards.innerHTML = '<p>데이터를 불러올 수 없습니다.</p>';
            return;
        }
        
        domCache.performanceCards.innerHTML = data.map(etf => createPerformanceCard(etf)).join('');
    } catch (error) {
        console.error('성과 카드 오류:', error);
        domCache.performanceCards.innerHTML = '<p>오류가 발생했습니다.</p>';
    }
}

// 성과 카드 생성
function createPerformanceCard(etf) {
    const changeClass = etf.change >= 0 ? 'positive' : 'negative';
    const changeIcon = etf.change >= 0 ? '📈' : '📉';
    const ytdIcon = etf.ytd >= 0 ? '📈' : '📉';
    
    return `
        <div class="performance-card">
            <div class="card-ticker">${etf.ticker}</div>
            <div class="card-name">${etf.name}</div>
            <div class="card-price">$${etf.current_price.toFixed(2)}</div>
            <div class="card-change ${changeClass}">
                ${changeIcon} ${etf.change > 0 ? '+' : ''}${etf.change.toFixed(2)}%
            </div>
            <div class="card-ytd">
                ${ytdIcon} YTD: ${etf.ytd > 0 ? '+' : ''}${etf.ytd.toFixed(2)}%
            </div>
            <div class="card-52week">
                52주: $${etf.low_52.toFixed(2)} ~ $${etf.high_52.toFixed(2)}
            </div>
        </div>
    `;
}

// 가격 추이 차트 업데이트
async function updatePriceChart(days) {
    try {
        const response = await fetch('/api/etf-price-data', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ tickers: selectedTickers, days })
        });
        
        const priceData = await response.json();
        
        const traces = Object.entries(priceData).map(([ticker, data]) => ({
            x: data.dates,
            y: data.prices,
            name: ticker,
            type: 'scatter',
            mode: 'lines',
            line: { width: 2.5 }
        }));
        
        const layout = {
            title: '📈 ETF 가격 추이',
            xaxis: { title: '날짜' },
            yaxis: { title: '가격 (USD)' },
            hovermode: 'x unified',
            margin: { t: 50, l: 60, r: 20, b: 60 },
            plot_bgcolor: 'rgba(0,0,0,0)',
            paper_bgcolor: '#f5f7fa',
            font: { family: 'Arial, sans-serif', size: 12 }
        };
        
        Plotly.newPlot('price-chart', traces, layout, { responsive: true });
    } catch (error) {
        console.error('가격 차트 오류:', error);
    }
}

// YTD 성과 비교 업데이트
async function updateYTDComparison() {
    try {
        const response = await fetch('/api/etf-ytd-comparison', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ tickers: selectedTickers })
        });
        
        const ytdData = await response.json();
        
        const traces = Object.entries(ytdData).map(([ticker, data]) => ({
            x: data.dates,
            y: data.values,
            name: ticker,
            type: 'scatter',
            mode: 'lines',
            line: { width: 2.5 }
        }));
        
        const layout = {
            title: '📊 연초 이후 성과 비교 (기준점=100)',
            xaxis: { title: '날짜' },
            yaxis: { title: '성과 지수' },
            hovermode: 'x unified',
            margin: { t: 50, l: 60, r: 20, b: 60 },
            plot_bgcolor: 'rgba(0,0,0,0)',
            paper_bgcolor: '#f5f7fa',
            font: { family: 'Arial, sans-serif', size: 12 }
        };
        
        Plotly.newPlot('ytd-chart', traces, layout, { responsive: true });
    } catch (error) {
        console.error('YTD 차트 오류:', error);
    }
}

// 기술적 분석 ETF 선택 옵션 채우기
function populateTechnicalSelect(tickers) {
    domCache.technicalEtfSelect.innerHTML = tickers.map(ticker => 
        `<option value="${ticker}">${ticker}</option>`
    ).join('');
}

// 기술적 분석 ETF 변경
async function handleTechnicalETFChange(e) {
    const days = parseInt(domCache.periodSelect.value);
    await updateTechnicalAnalysis(days);
}

// 기술적 분석 업데이트
async function updateTechnicalAnalysis(days) {
    try {
        const selectedTicker = domCache.technicalEtfSelect.value || selectedTickers[0];
        
        const response = await fetch('/api/etf-technical', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ticker: selectedTicker, days })
        });
        
        const data = await response.json();
        
        // 신호 표시
        renderSignals(data.signals);
        
        // 차트 그리기
        drawTechnicalChart(data, selectedTicker);
    } catch (error) {
        console.error('기술적 분석 오류:', error);
    }
}

// 신호 렌더링
function renderSignals(signals) {
    domCache.technicalSignals.innerHTML = signals.map(signal => 
        `<div class="signal ${signal.type}">${signal.text}</div>`
    ).join('');
}

// 기술적 분석 차트 그리기
function drawTechnicalChart(data, ticker) {
    const traces = [
        {
            x: data.dates,
            y: data.close,
            name: 'Price',
            type: 'scatter',
            mode: 'lines',
            line: { color: 'black', width: 2 },
            yaxis: 'y1'
        },
        {
            x: data.dates,
            y: data.ma20,
            name: 'MA20',
            type: 'scatter',
            mode: 'lines',
            line: { color: 'orange', dash: 'dot', width: 1.5 },
            yaxis: 'y1'
        },
        {
            x: data.dates,
            y: data.ma50,
            name: 'MA50',
            type: 'scatter',
            mode: 'lines',
            line: { color: 'blue', dash: 'dot', width: 1.5 },
            yaxis: 'y1'
        },
        {
            x: data.dates,
            y: data.ma200,
            name: 'MA200',
            type: 'scatter',
            mode: 'lines',
            line: { color: 'red', dash: 'dash', width: 1.5 },
            yaxis: 'y1'
        },
        {
            x: data.dates,
            y: data.rsi,
            name: 'RSI (14)',
            type: 'scatter',
            mode: 'lines',
            line: { color: 'purple', width: 2 },
            yaxis: 'y2'
        }
    ];
    
    const layout = {
        title: `🛠️ 기술적 분석 - ${ticker}`,
        xaxis: { title: '날짜' },
        yaxis: { title: '가격 (USD)', domain: [0.3, 1] },
        yaxis2: { 
            title: 'RSI', 
            overlaying: 'y',
            side: 'right',
            domain: [0, 0.25],
            range: [0, 100]
        },
        hovermode: 'x unified',
        margin: { t: 50, l: 70, r: 70, b: 60 },
        plot_bgcolor: 'rgba(0,0,0,0)',
        paper_bgcolor: '#f5f7fa',
        font: { family: 'Arial, sans-serif', size: 12 },
        shapes: [
            { type: 'line', x0: data.dates[0], x1: data.dates[data.dates.length-1], y0: 70, y1: 70, 
              xref: 'x', yref: 'y2', line: { color: 'red', width: 1, dash: 'dot' } },
            { type: 'line', x0: data.dates[0], x1: data.dates[data.dates.length-1], y0: 30, y1: 30,
              xref: 'x', yref: 'y2', line: { color: 'green', width: 1, dash: 'dot' } }
        ]
    };
    
    Plotly.newPlot('technical-chart', traces, layout, { responsive: true });
}

// 데이터 테이블 업데이트
async function updateDataTable(days) {
    try {
        const response = await fetch('/api/etf-performance', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ tickers: selectedTickers, days })
        });
        
        const data = await response.json();
        
        const tableHTML = `
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Ticker</th>
                        <th>이름</th>
                        <th>현재가</th>
                        <th>일일 변화</th>
                        <th>YTD</th>
                        <th>52주 최저</th>
                        <th>52주 최고</th>
                    </tr>
                </thead>
                <tbody>
                    ${data.map(etf => `
                        <tr>
                            <td><strong>${etf.ticker}</strong></td>
                            <td>${etf.name}</td>
                            <td>$${etf.current_price.toFixed(2)}</td>
                            <td class="${etf.change >= 0 ? 'table-positive' : 'table-negative'}">
                                ${etf.change > 0 ? '+' : ''}${etf.change.toFixed(2)}%
                            </td>
                            <td class="${etf.ytd >= 0 ? 'table-positive' : 'table-negative'}">
                                ${etf.ytd > 0 ? '+' : ''}${etf.ytd.toFixed(2)}%
                            </td>
                            <td>$${etf.low_52.toFixed(2)}</td>
                            <td>$${etf.high_52.toFixed(2)}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
        
        domCache.dataTable.innerHTML = tableHTML;
    } catch (error) {
        console.error('데이터 테이블 오류:', error);
        domCache.dataTable.innerHTML = '<p>오류가 발생했습니다.</p>';
    }
}

// 대시보드 업데이트 (모든 섹션)
async function updateDashboard() {
    updateTime();
    
    if (selectedTickers.length === 0) {
        alert('최소 1개의 ETF를 선택하세요.');
        return;
    }
    
    const days = parseInt(domCache.periodSelect.value);
    
    await Promise.all([
        updatePerformanceCards(days),
        updatePriceChart(days),
        updateYTDComparison(),
        updateTechnicalAnalysis(days),
        updateDataTable(days)
    ]);
}