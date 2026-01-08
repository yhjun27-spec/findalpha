// Mock Data for AI analysis
const MOCK_DATA = {
    'AAPL': {
        name: 'Apple Inc.',
        price: '185.92',
        sentiment: 'Positive',
        summary: '애플은 탄탄한 생태계와 안정적인 현금 흐름을 바탕으로 강한 시장 지배력을 유지하고 있습니다. 최근 AI 하드웨어 가속화 전략이 긍정적으로 평가받고 있습니다.',
        risks: ['규제 강화 리스크', '아이폰 판매 둔화 우려', '하드웨어 공급망 리스크'],
        growth: ['서비스 부문 매출 증가', '차세대 AI 통합 디바이스', '자율주행 소프트웨어 투자']
    },
    'TSLA': {
        name: 'Tesla, Inc.',
        price: '238.45',
        sentiment: 'Mixed',
        summary: '테슬라는 전기차 시장의 선두주자이나, 금리 인상과 글로벌 경쟁 심화로 수익성 압박을 받고 있습니다. FSD(Full Self-Driving) 기술의 완성도가 향후 주가 향방을 결정할 것입니다.',
        risks: ['자동차 시장 경쟁 격화', 'CEO 리스크', '마진율 하락'],
        growth: ['FSD 라이선싱 가능성', '에너지 저장 장치 부문 성장', '사이버트럭 생산 확대']
    },
    'NVDA': {
        name: 'NVIDIA Corp.',
        price: '522.53',
        sentiment: 'Strongly Positive',
        desc: '엔비디아는 게이밍 및 가속 컴퓨팅을 위한 그래픽 처리 장치(GPU)와 데이터 센터를 위한 시스템 온 칩 유닛(SoC)을 설계합니다.',
        sector: 'Technology',
        marketCap: '1.29T',
        irWeb: 'https://investor.nvidia.com',
        ntmPe: '45.2x',
        earnings: [
            { date: '2024 Q1', link: '#' },
            { date: '2023 Q4', link: '#' }
        ],
        news: [
            { title: 'Blackwell 아키텍처 기반의 차세대 AI 칩 발표', source: 'The Verge', date: '1시간 전' },
            { title: '클라우드 서비스 제공업체들의 GPU 수요 폭증', source: 'WSJ', date: '4시간 전' }
        ],
        financials: {
            years: ['2020', '2021', '2022', '2023', '2024'],
            revenue: ['10.9B', '16.7B', '26.9B', '27.0B', '60.9B'],
            netIncome: ['2.8B', '4.3B', '9.7B', '4.4B', '29.7B'],
            eps: ['1.13', '1.73', '3.85', '1.74', '11.93']
        },
        chartData: [300, 350, 420, 410, 480, 510, 522.53]
    }
};

let stockChart = null;
let currentTicker = 'AAPL';
let currentRange = '1y';
let currentInterval = 'd';

document.addEventListener('DOMContentLoaded', () => {
    const searchBtn = document.getElementById('search-btn');
    const tickerInput = document.getElementById('ticker-input');
    const headerTickerInput = document.getElementById('header-ticker-input');
    const heroSection = document.getElementById('hero-section');
    const dashboardSection = document.getElementById('dashboard-section');
    const headerSearch = document.getElementById('header-search');
    const themeToggle = document.getElementById('theme-toggle');
    const body = document.body;

    // Detect current page
    const isMainPage = !!document.getElementById('hero-section');
    const isChartPage = window.location.pathname.includes('chart-detail.html');
    const isEarningsPage = window.location.pathname.includes('earnings-detail.html');

    // Handle initial state for detail pages
    if (!isMainPage) {
        const urlParams = new URLSearchParams(window.location.search);
        currentTicker = urlParams.get('ticker') || 'AAPL';
        renderDetailView(currentTicker);
    }

    themeToggle.addEventListener('click', () => {
        body.classList.toggle('light-theme');
        body.classList.toggle('dark-theme');
        const isDark = body.classList.contains('dark-theme');
        themeToggle.querySelector('.theme-icon').textContent = isDark ? '🌙' : '☀️';
        if (stockChart) updateChartTheme();
    });

    // Chart Filters logic
    const setupChartFilters = () => {
        const rangeBtns = document.querySelectorAll('.range-filters .filter-btn');
        const intervalBtns = document.querySelectorAll('.interval-filters .filter-btn');

        rangeBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                currentRange = btn.dataset.range;
                toggleFilterActive(rangeBtns, btn);
                refreshChartData();
            });
        });

        intervalBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                currentInterval = btn.dataset.interval;
                toggleFilterActive(intervalBtns, btn);
                refreshChartData();
            });
        });
    };

    const toggleFilterActive = (group, activeBtn) => {
        group.forEach(btn => btn.classList.remove('active'));
        activeBtn.classList.add('active');
    };

    const refreshChartData = () => {
        if (isMainPage) {
            renderDashboard(currentTicker);
        } else if (isChartPage) {
            renderDetailView(currentTicker);
        }
    };

    const handleSearch = (input) => {
        const ticker = input.value.trim().toUpperCase();
        if (!ticker) return;

        if (!isMainPage) {
            window.location.href = `index.html?ticker=${ticker}`;
            return;
        }

        currentTicker = ticker;
        heroSection.classList.add('hidden');
        dashboardSection.classList.remove('hidden');
        headerSearch.classList.remove('hidden');

        renderDashboard(ticker);
    };

    if (searchBtn) {
        searchBtn.addEventListener('click', () => handleSearch(tickerInput));
        tickerInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') handleSearch(tickerInput);
        });
    }

    // Setup chart filters for both index and chart-detail pages
    setupChartFilters();

    if (headerTickerInput) {
        headerTickerInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') handleSearch(headerTickerInput);
        });
    }

    // Dashboard Interaction
    function setupDashboardInteractions(ticker) {
        const chartCard = document.getElementById('chart-card');
        const earningsCard = document.getElementById('earnings-card');

        if (chartCard && !isChartPage) {
            const filters = chartCard.querySelector('.chart-filters');
            if (filters) {
                filters.onclick = (e) => e.stopPropagation();
            }
            chartCard.onclick = () => window.location.href = `chart-detail.html?ticker=${ticker}`;
        }
        if (earningsCard) {
            earningsCard.onclick = () => window.location.href = `earnings-detail.html?ticker=${ticker}`;
        }
    }

    async function renderDashboard(ticker) {
        let stockData = null;

        try {
            const response = await fetch(`/api/historical?ticker=${ticker}&range=${currentRange}&interval=${currentInterval}`);
            if (response.ok) {
                stockData = await response.json();
            }
        } catch (e) {
            console.warn('Backend Fetch failed', e);
        }

        const mock = MOCK_DATA[ticker] || MOCK_DATA['AAPL'];
        const displayPrice = stockData?.current_price ? `$${parseFloat(stockData.current_price).toLocaleString()}` : (mock.price ? `$${mock.price}` : 'Data pending...');
        const changeVal = stockData?.change !== undefined ? parseFloat(stockData.change) : 0;
        const changePct = stockData?.change_percent !== undefined ? stockData.change_percent : 'Live';

        document.getElementById('company-info').innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div>
                    <h2 class="ticker-name" style="margin-bottom: 0.25rem;">${mock.name} <span class="ticker-code">(${ticker})</span></h2>
                    <div class="current-price-display" style="font-size: 3rem; font-weight: 800; color: var(--text-main); letter-spacing: -0.02em;">${displayPrice}</div>
                </div>
                <div class="sentiment-badge ${changeVal >= 0 ? 'strongly-positive' : 'negative'}" style="font-size: 1.1rem; padding: 0.6rem 1.2rem;">
                    ${changeVal > 0 ? '▲' : '▼'} ${Math.abs(changeVal).toLocaleString()} (${changePct}%)
                </div>
            </div>
            <p style="margin-top: 1.5rem; color: var(--text-muted); font-size: 1.05rem; line-height: 1.7;">${mock.desc || '기업 설명을 준비 중입니다.'}</p>
            <div class="overview-details">
                <div class="detail-item"><span class="detail-label">시가총액</span><span class="detail-value">${mock.marketCap || '-'}</span></div>
                <div class="detail-item"><span class="detail-label">섹터</span><span class="detail-value">${mock.sector || '-'}</span></div>
                <div class="detail-item"><span class="detail-label">IR 웹사이트</span><span class="detail-value"><a href="${mock.irWeb || '#'}" class="ir-link" target="_blank">방문하기</a></span></div>
                <div class="detail-item"><span class="detail-label">NTM P/E</span><span class="detail-value">${mock.ntmPe || '-'}</span></div>
            </div>
        `;

        const earningsHTML = (mock.earnings || []).map(e => `
            <li>
                <span class="earnings-date">${e.date} Transcript</span>
                <a href="${e.link}" class="ir-link">View</a>
            </li>
        `).join('') || '<li>어닝콜 정보를 불러올 수 없습니다.</li>';
        document.getElementById('earnings-list').innerHTML = earningsHTML;

        const newsHTML = (mock.news || []).map(n => `
            <div class="news-item">
                <div class="news-title">${n.title}</div>
                <div class="news-meta">${n.source} • ${n.date}</div>
            </div>
        `).join('') || '<p>최신 뉴스가 없습니다.</p>';
        document.getElementById('news-grid').innerHTML = newsHTML;

        const f = mock.financials || { years: [], revenue: [], netIncome: [], eps: [] };
        let tableHtml = `
            <thead>
                <tr>
                    <th>항목 (Annual)</th>
                    ${f.years.map(y => `<th>${y}</th>`).join('')}
                </tr>
            </thead>
            <tbody>
                <tr><td>Revenue (매출)</td>${f.revenue.map(v => `<td>${v}</td>`).join('')}</tr>
                <tr><td>Net Income (순이익)</td>${f.netIncome.map(v => `<td>${v}</td>`).join('')}</tr>
                <tr><td>EPS (주당순이익)</td>${f.eps.map(v => `<td>${v}</td>`).join('')}</tr>
            </tbody>
        `;
        document.getElementById('financials-table').innerHTML = tableHtml;

        if (stockData && stockData.prices) {
            renderChart(stockData.prices, stockData.labels);
        } else {
            renderChart(mock.chartData || [0, 0, 0, 0, 0, 0, 0], ['-', '-', '-', '-', '-', '-', '-']);
        }

        setupDashboardInteractions(ticker);
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    async function renderDetailView(ticker) {
        const mock = MOCK_DATA[ticker] || MOCK_DATA['AAPL'];
        const titleEl = document.getElementById('detail-ticker-title');
        if (titleEl) titleEl.innerText = `${ticker} 주가 차트 상세`;

        if (isChartPage) {
            try {
                const res = await fetch(`/api/historical?ticker=${ticker}&range=${currentRange}&interval=${currentInterval}`);
                const data = await res.json();
                renderChart(data.prices, data.labels, data.ohlc);
            } catch (e) {
                console.error('Detail view fetch failed', e);
            }
        } else if (isEarningsPage) {
            document.getElementById('earnings-list').innerHTML = (mock.earnings || []).map(e => `
                <li>
                    <span class="earnings-date">${e.date} Transcript</span>
                    <a href="${e.link}" class="ir-link">View</a>
                </li>
            `).join('');
            if (mock.earnings && mock.earnings[0]) {
                const dateEl = document.getElementById('last-earnings-date');
                if (dateEl) dateEl.innerText = mock.earnings[0].date;
            }
        }
    }

    function renderChart(prices, labels, ohlc = null) {
        const chartElement = document.getElementById('stock-chart');
        if (!chartElement) return;

        const ctx = chartElement.getContext('2d');
        if (stockChart) stockChart.destroy();

        if (typeof Chart !== 'undefined' && Chart.register) {
            // Register financial components if they exist in global scope (UMD)
            const financial = window['chartjs-chart-financial'];
            if (financial) {
                Chart.register(financial.CandlestickController, financial.CandlestickElement, financial.OhlcController, financial.OhlcElement);
            } else if (typeof CandlestickController !== 'undefined') {
                Chart.register(CandlestickController, CandlestickElement);
            }
        }

        const isDark = body.classList.contains('dark-theme');
        const accentColor = isDark ? '#818cf8' : '#4f46e5';

        if (isChartPage && ohlc && ohlc.length > 0) {
            // Filter out invalid OHLC data points
            const formattedOhlc = ohlc.map(d => ({
                x: luxon.DateTime.fromISO(d.x).valueOf(),
                o: parseFloat(d.o),
                h: parseFloat(d.h),
                l: parseFloat(d.l),
                c: parseFloat(d.c)
            }));

            // ERROR DEBUGGING START
            console.log('--- Chart Debugging ---');
            console.log('Chart global:', typeof Chart !== 'undefined');
            console.log('chartjs-adapter-luxon:', typeof DateTime !== 'undefined' || (typeof luxon !== 'undefined' && luxon.DateTime));
            console.log('window["chartjs-chart-financial"]:', window['chartjs-chart-financial']);
            console.log('Is candlestick registered?:', Chart.registry.controllers.items['candlestick'] !== undefined);
            console.log('OHLC Data sample:', formattedOhlc[0]);
            // ERROR DEBUGGING END

            stockChart = new Chart(ctx, {
                type: 'candlestick',
                data: {
                    datasets: [{
                        label: '주가 (Candlestick)',
                        data: formattedOhlc,
                        color: {
                            up: '#22c55e',
                            down: '#ef4444',
                            unchanged: '#94a3b8'
                        },
                        borderColor: isDark ? '#ffffff33' : '#0000001a'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            callbacks: {
                                label: (context) => {
                                    const d = context.raw;
                                    return [
                                        `Open: $${d.o.toFixed(2)}`,
                                        `High: $${d.h.toFixed(2)}`,
                                        `Low: $${d.l.toFixed(2)}`,
                                        `Close: $${d.c.toFixed(2)}`
                                    ];
                                }
                            }
                        }
                    },
                    scales: {
                        x: {
                            type: 'timeseries',
                            grid: { display: false },
                            ticks: {
                                color: isDark ? '#94a3b8' : '#64748b',
                                source: 'auto'
                            }
                        },
                        y: {
                            beginAtZero: false,
                            grid: { color: isDark ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.05)' },
                            ticks: { color: isDark ? '#94a3b8' : '#64748b' }
                        }
                    }
                }
            });
        } else {
            stockChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: '주가 (USD)',
                        data: prices,
                        borderColor: accentColor,
                        backgroundColor: 'rgba(129, 140, 248, 0.1)',
                        fill: true,
                        tension: 0.2,
                        pointRadius: (prices && prices.length > 50) ? 0 : 3,
                        pointBackgroundColor: accentColor
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        y: {
                            grid: { color: isDark ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.05)' },
                            ticks: { color: isDark ? '#94a3b8' : '#64748b' }
                        },
                        x: {
                            grid: { display: false },
                            ticks: {
                                color: isDark ? '#94a3b8' : '#64748b',
                                maxTicksLimit: 10
                            }
                        }
                    }
                }
            });
        }
    }

    function updateChartTheme() {
        const isDark = body.classList.contains('dark-theme');
        const color = isDark ? '#818cf8' : '#4f46e5';
        if (stockChart) {
            if (stockChart.config.type === 'line') {
                stockChart.data.datasets[0].borderColor = color;
                stockChart.data.datasets[0].pointBackgroundColor = color;
            }
            stockChart.options.scales.y.ticks.color = isDark ? '#94a3b8' : '#64748b';
            stockChart.options.scales.x.ticks.color = isDark ? '#94a3b8' : '#64748b';
            stockChart.update();
        }
    }

});
