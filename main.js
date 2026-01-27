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

// API Base URL (Relative for unified server)
const API_BASE_URL = '';

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

        // Listen for trade added events to refresh chart with new markers
        window.addEventListener('tradeAdded', () => {
            console.log('Trade added, refreshing chart...');
            renderDetailView(currentTicker);
        });
    }

    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            body.classList.toggle('light-theme');
            body.classList.toggle('dark-theme');
            const isDark = body.classList.contains('dark-theme');
            themeToggle.querySelector('.theme-icon').textContent = isDark ? '🌙' : '☀️';
            if (stockChart) updateChartTheme();
        });
    }

    // Chart Filters logic
    const setupChartFilters = () => {
        const rangeBtns = document.querySelectorAll('.range-filters .filter-btn');
        const intervalBtns = document.querySelectorAll('.interval-filters .filter-btn');

        console.log('setupChartFilters: range buttons found:', rangeBtns.length, 'interval buttons found:', intervalBtns.length);

        rangeBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                console.log('Range button clicked:', btn.dataset.range);
                currentRange = btn.dataset.range;
                toggleFilterActive(rangeBtns, btn);
                refreshChartData();
            });
        });

        intervalBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                console.log('Interval button clicked:', btn.dataset.interval);
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
        console.log('refreshChartData called:', { isMainPage, isChartPage, currentTicker, currentRange, currentInterval });
        if (isMainPage) {
            renderDashboard(currentTicker);
        } else if (isChartPage) {
            renderDetailView(currentTicker);
        }
    };

    const handleSearch = (input) => {
        const ticker = input.value.trim().toUpperCase();
        if (!ticker) return;

        // 마지막 검색 티커를 localStorage에 저장
        localStorage.setItem('lastSearchedTicker', ticker);

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

    // 메인 페이지 로드 시 마지막 검색 티커 복원
    if (isMainPage) {
        const urlParams = new URLSearchParams(window.location.search);
        const urlTicker = urlParams.get('ticker');
        const savedTicker = localStorage.getItem('lastSearchedTicker');

        if (urlTicker) {
            // URL에서 티커가 전달된 경우
            tickerInput.value = urlTicker;
            handleSearch(tickerInput);
        } else if (savedTicker) {
            // localStorage에 저장된 티커가 있는 경우
            tickerInput.value = savedTicker;
            handleSearch(tickerInput);
        }
    }

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

        // Determine API Base URL based on environment
        // Since we are serving via Flask on both local and potentially prod (or via rewrite), use relative path
        const API_BASE_URL = '';

        try {
            console.log(`Fetching data for ${ticker} from ${API_BASE_URL}/api/historical...`);
            const response = await fetch(`${API_BASE_URL}/api/historical?ticker=${ticker}&range=${currentRange}&interval=${currentInterval}`);
            if (response.ok) {
                stockData = await response.json();
                console.log('FinanceDataReader Data Fetched:', stockData);
            } else {
                console.warn(`Fetch failed with status: ${response.status}`);
            }
        } catch (e) {
            console.warn('Backend Fetch failed, falling back to mock data', e);
        }

        const mock = MOCK_DATA[ticker] || MOCK_DATA['AAPL'];

        // Data Sources: Prioritize Backend Data > Mock Data > Fallback
        const displayPrice = stockData?.current_price ? `$${parseFloat(stockData.current_price).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : (mock.price ? `$${mock.price}` : 'Data pending...');
        const changeVal = stockData?.change !== undefined ? parseFloat(stockData.change) : 0;
        const changePct = stockData?.change_percent !== undefined ? stockData.change_percent : 'Live';

        // Metadata from YFinance (or Fallback to Mock)
        const meta = stockData?.meta || {};
        const companyName = meta.name || mock.name || ticker;
        const companyDesc = meta.description || mock.desc || '기업 설명을 준비 중입니다.';

        // Market Cap Formatting
        let marketCapDisplay = '-';
        if (meta.marketCap) {
            const rawCap = parseFloat(meta.marketCap.replace(/,/g, ''));
            if (!isNaN(rawCap)) {
                marketCapDisplay = `$${(rawCap / 1000000).toLocaleString(undefined, { maximumFractionDigits: 0 })}M`;
            } else {
                marketCapDisplay = meta.marketCap;
            }
        } else if (mock.marketCap) {
            marketCapDisplay = mock.marketCap;
        }

        const sector = meta.sector || mock.sector || '-';
        const peRatio = meta.peRatio !== '-' ? parseFloat(meta.peRatio).toFixed(2) : (mock.ntmPe || '-');
        const irWeb = meta.website || mock.irWeb || '#';
        const irPage = meta.irWebsite || irWeb;

        // Description Toggle Logic
        const shortDesc = companyDesc.length > 150 ? companyDesc.substring(0, 150) + '...' : companyDesc;
        const descHtml = companyDesc.length > 150
            ? `<span id="desc-short">${shortDesc}</span><span id="desc-full" style="display:none;">${companyDesc}</span> <button onclick="toggleDescription()" id="desc-btn" class="text-btn" style="color: var(--accent-color); background: none; border: none; cursor: pointer; padding: 0; font-size: 0.95rem; font-weight: 600;">더보기</button>`
            : companyDesc;

        window.toggleDescription = () => {
            const short = document.getElementById('desc-short');
            const full = document.getElementById('desc-full');
            const btn = document.getElementById('desc-btn');
            if (short.style.display === 'none') {
                short.style.display = 'inline';
                full.style.display = 'none';
                btn.textContent = '더보기';
            } else {
                short.style.display = 'none';
                full.style.display = 'inline';
                btn.textContent = '접기';
            }
        };

        document.getElementById('company-info').innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div>
                    <h2 class="ticker-name" style="margin-bottom: 0.25rem;">${companyName} <span class="ticker-code">(${ticker})</span></h2>
                    <div class="current-price-display" style="font-size: 3rem; font-weight: 800; color: var(--text-main); letter-spacing: -0.02em;">${displayPrice}</div>
                </div>
                <div class="sentiment-badge ${changeVal >= 0 ? 'strongly-positive' : 'negative'}" style="font-size: 1.1rem; padding: 0.6rem 1.2rem;">
                    ${changeVal > 0 ? '▲' : '▼'} ${Math.abs(changeVal).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} (${changePct}%)
                </div>
            </div>
            <p style="margin-top: 1.5rem; color: var(--text-muted); font-size: 1.05rem; line-height: 1.7; display: block;">${descHtml}</p>
            <div class="overview-details">
                <div class="detail-item clickable" onclick="window.location.href='company-analysis.html?ticker=${ticker}'" style="cursor: pointer; transition: all 0.2s ease;" onmouseover="this.style.background='rgba(99,102,241,0.15)'" onmouseout="this.style.background=''"><span class="detail-label">시가총액</span><span class="detail-value">${marketCapDisplay}</span></div>
                <div class="detail-item"><span class="detail-label">섹터</span><span class="detail-value">${sector}</span></div>
                <div class="detail-item"><span class="detail-label">웹사이트</span><span class="detail-value">
                    <a href="${irWeb}" class="ir-link" target="_blank">공식</a> <span style="color: var(--text-muted);">|</span> <a href="${irPage}" class="ir-link" target="_blank">IR</a>
                </span></div>
                <div class="detail-item"><span class="detail-label">Next P/E</span><span class="detail-value">${peRatio}</span></div>
            </div>
        `;

        // Fetch Earnings Calls from local folder
        try {
            const earningsRes = await fetch(`/api/earningcalls?ticker=${ticker}`);
            if (earningsRes.ok) {
                const earningsData = await earningsRes.json();
                const earningsHTML = (earningsData.files || []).length > 0
                    ? earningsData.files.map(e => `
                        <li>
                            <span class="earnings-date">${e.date} Transcript</span>
                            <a href="${e.link}" class="ir-link" target="_blank">View</a>
                        </li>
                    `).join('')
                    : '<li>어닝콜 파일이 없습니다. earningcall/' + ticker + '/ 폴더에 파일을 추가하세요.</li>';
                document.getElementById('earnings-list').innerHTML = earningsHTML;
            } else {
                document.getElementById('earnings-list').innerHTML = '<li>어닝콜 정보를 불러올 수 없습니다.</li>';
            }
        } catch (e) {
            console.warn('Earnings call fetch failed', e);
            document.getElementById('earnings-list').innerHTML = '<li>어닝콜 정보를 불러올 수 없습니다.</li>';
        }

        // News from YFinance
        const newsItems = stockData?.news || mock.news || [];
        const newsHTML = newsItems.length > 0 ? newsItems.map(n => {
            // Handle yfinance timestamp
            let dateStr = n.date;
            if (n.providerPublishTime) {
                const d = new Date(n.providerPublishTime * 1000);
                dateStr = d.toLocaleDateString() + ' ' + d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            }
            // Default placeholder image (gradient) if no thumbnail
            const bgStyle = n.thumbnail
                ? `background-image: url('${n.thumbnail}')`
                : `background: linear-gradient(135deg, rgba(99,102,241,0.1) 0%, rgba(168,85,247,0.1) 100%)`;

            return `
            <div class="news-card" onclick="window.open('${n.link}', '_blank')">
                <div class="news-image" style="${bgStyle}"></div>
                <div class="news-content">
                    <div class="news-title">${n.title}</div>
                    <div class="news-meta">
                        <span>${n.publisher || n.source || 'News'}</span>
                        <span>${dateStr || ''}</span>
                    </div>
                </div>
            </div>
            `;
        }).join('') : '<div style="grid-column: 1/-1; text-align: center; color: var(--text-muted);">뉴스를 불러올 수 없습니다.</div>';
        document.getElementById('news-grid').innerHTML = newsHTML;

        // Financial Highlights (Time Series Table)
        const financials = stockData?.financials || { annual: [], quarterly: [] };

        // Data is already in chronological order (oldest to newest) from backend
        // Only reverse quarterly to show newest first, then reverse back for display
        // Helper functions
        const formatNumber = (num) => {
            if (!num && num !== 0) return '-';
            const absNum = Math.abs(num);
            if (absNum >= 1e9) return `$${(num / 1e9).toFixed(2)}B`;
            else if (absNum >= 1e6) return `$${(num / 1e6).toFixed(2)}M`;
            else return `$${num.toLocaleString()}`;
        };

        const formatPercent = (num) => {
            if (!num && num !== 0) return '-';
            const color = num >= 0 ? '#22c55e' : '#ef4444';
            return `\u003cspan style="color: ${color}; font-weight: 600;"\u003e${num.toFixed(2)}%\u003c/span\u003e`;
        };

        const formatPeriod = (period) => {
            if (!period) return '-';
            // Check if it's an estimate year (ends with E)
            if (typeof period === 'string' && period.endsWith('E')) {
                return period;  // Return as-is (e.g., "2025E")
            }
            // Check if it's a quarterly format (YYYY-QX)
            if (typeof period === 'string' && period.includes('-Q')) {
                return period;  // Return as-is (e.g., "2024-Q3")
            }
            // Check if it's just a year number
            if (typeof period === 'string' && /^\d{4}$/.test(period)) {
                return period;  // Return as-is (e.g., "2024")
            }
            // Format YYYY-MM-DD to readable format
            const date = new Date(period);
            if (!isNaN(date.getTime())) {
                return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short' });
            }
            return period;
        };

        // Build table HTML
        const buildFinancialsTable = (data, type) => {
            if (!data || data.length === 0) {
                return '\u003cp\u003e재무 데이터를 불러올 수 없습니다.\u003c/p\u003e';
            }

            // Table header with periods
            const periods = data.map(d => formatPeriod(d.period));
            const isQuarterly = type === 'quarterly';
            const minColWidth = isQuarterly ? '120px' : 'auto';

            const headerHTML = `
                \u003cthead\u003e
                    \u003ctr\u003e
                        \u003cth style="text-align: left; padding: 1rem; border-bottom: 2px solid var(--border-color); font-weight: 700; position: sticky; left: 0; background: var(--card-bg); z-index: 10; min-width: 180px;"\u003eMetric\u003c/th\u003e
                        ${data.map((d, idx) => {
                const isEstimate = d.isEstimate || false;
                const style = isEstimate ? 'font-style: italic; opacity: 0.85;' : '';
                return `\u003cth style="text-align: right; padding: 1rem; border-bottom: 2px solid var(--border-color); font-weight: 700; min-width: ${minColWidth}; white-space: nowrap; ${style}"\u003e${periods[idx]}\u003c/th\u003e`;
            }).join('')}
                    \u003c/tr\u003e
                \u003c/thead\u003e
            `;

            // Table rows
            const metrics = [
                { label: 'Revenue', key: 'revenue', formatter: formatNumber },
                { label: 'Revenue YoY Growth', key: 'revenueGrowth', formatter: formatPercent },
                { label: 'Gross Profit Margin', key: 'gpm', formatter: formatPercent },
                { label: 'EBITDA Margin', key: 'ebitdaMargin', formatter: formatPercent },
                { label: 'Net Income', key: 'netIncome', formatter: formatNumber },
                { label: 'EPS', key: 'eps', formatter: (v) => v ? `$${v.toFixed(2)}` : '-' },
                { label: 'EPS YoY Growth', key: 'epsGrowth', formatter: formatPercent },
                { label: 'Free Cash Flow', key: 'freeCashFlow', formatter: formatNumber },
                { label: 'FCF YoY Growth', key: 'fcfGrowth', formatter: formatPercent }
            ];

            const rowsHTML = metrics.map((metric, idx) => {
                const bgColor = idx % 2 === 0 ? 'var(--card-bg)' : 'transparent';
                return `
                    \u003ctr style="background: ${bgColor};"\u003e
                        \u003ctd style="padding: 0.875rem 1rem; font-weight: 600; color: var(--text-main); position: sticky; left: 0; background: ${bgColor}; z-index: 5; min-width: 180px;"\u003e${metric.label}\u003c/td\u003e
                        ${data.map((d, colIdx) => {
                    const isEstimate = d.isEstimate || false;
                    const cellStyle = isEstimate ? 'font-style: italic; opacity: 0.85;' : '';
                    return `\u003ctd style="padding: 0.875rem 1rem; text-align: right; color: var(--text-main); min-width: ${minColWidth}; white-space: nowrap; ${cellStyle}"\u003e${metric.formatter(d[metric.key])}\u003c/td\u003e`;
                }).join('')}
                    \u003c/tr\u003e
                `;
            }).join('');

            return `
                \u003ctable style="width: 100%; border-collapse: collapse; font-size: 0.95rem;"\u003e
                    ${headerHTML}
                    \u003ctbody\u003e
                        ${rowsHTML}
                    \u003c/tbody\u003e
                \u003c/table\u003e
            `;
        };

        const financialsHTML = `
            \u003cdiv class="financial-highlights" style="margin-top: 2rem;"\u003e
                \u003ch3 style="margin-bottom: 1.5rem; font-size: 1.5rem; font-weight: 700;"\u003eFinancial Highlights\u003c/h3\u003e
                
                \u003c!-- Tabs --\u003e
                \u003cdiv class="financial-tabs" style="display: flex; gap: 1rem; margin-bottom: 1.5rem; border-bottom: 2px solid var(--border-color);"\u003e
                    \u003cbutton id="annual-tab" class="financial-tab active" onclick="switchFinancialTab('annual')" 
                        style="padding: 0.75rem 1.5rem; background: none; border: none; border-bottom: 3px solid var(--accent-color); 
                        color: var(--accent-color); font-weight: 700; cursor: pointer; transition: all 0.2s;"\u003e
                        Annual
                    \u003c/button\u003e
                    \u003cbutton id="quarterly-tab" class="financial-tab" onclick="switchFinancialTab('quarterly')" 
                        style="padding: 0.75rem 1.5rem; background: none; border: none; border-bottom: 3px solid transparent; 
                        color: var(--text-muted); font-weight: 600; cursor: pointer; transition: all 0.2s;"\u003e
                        Quarterly
                    \u003c/button\u003e
                \u003c/div\u003e
                
                \u003c!-- Table Container --\u003e
                \u003cdiv class="card" style="padding: 1.5rem;"\u003e
                    \u003cdiv id="annual-table" class="financial-table-content" style="overflow-x: auto;"\u003e
                        ${buildFinancialsTable(financials.annual, 'annual')}
                    \u003c/div\u003e
                    \u003cdiv id="quarterly-table" class="financial-table-content" style="display: none; overflow-x: auto; max-width: 100%;"\u003e
                        ${buildFinancialsTable(financials.quarterly, 'quarterly')}
                    \u003c/div\u003e
                \u003c/div\u003e
            \u003c/div\u003e
        `;

        // Tab switching function
        window.switchFinancialTab = (tab) => {
            // Update tab styles
            const annualTab = document.getElementById('annual-tab');
            const quarterlyTab = document.getElementById('quarterly-tab');
            const annualTable = document.getElementById('annual-table');
            const quarterlyTable = document.getElementById('quarterly-table');

            if (tab === 'annual') {
                annualTab.style.borderBottom = '3px solid var(--accent-color)';
                annualTab.style.color = 'var(--accent-color)';
                quarterlyTab.style.borderBottom = '3px solid transparent';
                quarterlyTab.style.color = 'var(--text-muted)';
                annualTable.style.display = 'block';
                quarterlyTable.style.display = 'none';
            } else {
                quarterlyTab.style.borderBottom = '3px solid var(--accent-color)';
                quarterlyTab.style.color = 'var(--accent-color)';
                annualTab.style.borderBottom = '3px solid transparent';
                annualTab.style.color = 'var(--text-muted)';
                quarterlyTable.style.display = 'block';
                annualTable.style.display = 'none';
            }
        };

        // Insert Financial Highlights after news section
        // Insert Financial Highlights after news section
        const existingHighlights = document.querySelector('.financial-highlights');
        if (existingHighlights) existingHighlights.remove();

        const newsSection = document.querySelector('.news-section');
        if (newsSection) {
            newsSection.insertAdjacentHTML('afterend', financialsHTML);
        }

        // Legacy mock table rendering removed


        if (stockData && stockData.prices) {
            renderChart(stockData.prices, stockData.labels);
        } else {
            renderChart(mock.chartData || [0, 0, 0, 0, 0, 0, 0], ['-', '-', '-', '-', '-', '-', '-']);
        }

        setupDashboardInteractions(ticker);
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    function generateMockOHLC(prices) {
        return prices.map((price, i) => {
            const volatility = price * 0.02;
            const open = price + (Math.random() - 0.5) * volatility;
            const close = price;
            const high = Math.max(open, close) + Math.random() * volatility;
            const low = Math.min(open, close) - Math.random() * volatility;
            // Generate dates going back from today
            const date = luxon.DateTime.now().minus({ days: prices.length - 1 - i }).toISODate();
            return { x: date, o: open, h: high, l: low, c: close };
        });
    }

    async function renderDetailView(ticker) {
        const mock = MOCK_DATA[ticker] || MOCK_DATA['AAPL'];
        const titleEl = document.getElementById('detail-ticker-title');
        if (titleEl) titleEl.innerText = `${ticker} 주가 차트 상세`;

        if (isChartPage) {
            let ohlcData = null;
            let chartPrices = mock.chartData || [];
            let chartLabels = [];

            try {
                const res = await fetch(`/api/historical?ticker=${ticker}&range=${currentRange}&interval=${currentInterval}`);
                if (!res.ok) throw new Error(`API Error ${res.status}`);
                const data = await res.json();

                ohlcData = data.ohlc;
                chartPrices = data.prices;
                chartLabels = data.labels;

                // Volume and Moving Averages
                const volumeData = data.volume || [];
                const ma10Data = data.ma10 || [];
                const ma20Data = data.ma20 || [];
                const ma50Data = data.ma50 || [];

                // Load trade markers from localStorage
                const tradesData = localStorage.getItem('insight_trades');
                const allTrades = tradesData ? JSON.parse(tradesData) : {};
                const tickerTrades = allTrades[ticker] || [];

                if (ohlcData) {
                    renderChart(chartPrices, chartLabels, ohlcData, {
                        volume: volumeData,
                        ma10: ma10Data,
                        ma20: ma20Data,
                        ma50: ma50Data,
                        trades: tickerTrades
                    });
                    return;
                }
            } catch (e) {
                console.warn('Detail view fetch failed, switching to mock data', e);
                if (titleEl) titleEl.innerHTML = `${ticker} 주가 차트 상세 <span style="font-size:0.8rem; color:#ef4444; background:rgba(239,68,68,0.1); padding:2px 8px; border-radius:4px;">(Live Data Unavailable)</span>`;

                // Fallback: Generate OHLC from mock prices
                if (!ohlcData && chartPrices.length > 0) {
                    ohlcData = generateMockOHLC(chartPrices);
                    // Generate daily labels
                    chartLabels = ohlcData.map(d => d.x);
                }
            }

            if (ohlcData) {
                renderChart(chartPrices, chartLabels, ohlcData, {});
            } else {
                // Last resort if even mock data is missing
                const chartElement = document.getElementById('stock-chart');
                if (chartElement) {
                    const ctx = chartElement.getContext('2d');
                    ctx.fillStyle = '#94a3b8';
                    ctx.fillText('데이터가 없습니다.', chartElement.width / 2, chartElement.height / 2);
                }
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

    function renderChart(prices, labels, ohlc = null, extras = {}) {
        const chartElement = document.getElementById('stock-chart');
        if (!chartElement) return;

        const ctx = chartElement.getContext('2d');
        if (stockChart) stockChart.destroy();

        // Check if candlestick is already registered (chartjs-chart-financial auto-registers)
        const isCandlestickAvailable = typeof Chart !== 'undefined' &&
            Chart.registry &&
            Chart.registry.controllers &&
            Chart.registry.controllers.get('candlestick');

        console.log('Candlestick controller available:', !!isCandlestickAvailable);

        if (!isCandlestickAvailable) {
            console.warn('CRITICAL: Candlestick controller not found. Make sure chartjs-chart-financial is loaded after Chart.js');
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

            // Prepare Moving Average datasets
            const datasets = [{
                label: '주가 (Candlestick)',
                data: formattedOhlc,
                type: 'candlestick',
                color: {
                    up: '#22c55e',
                    down: '#ef4444',
                    unchanged: '#94a3b8'
                },
                borderColor: isDark ? '#ffffff33' : '#0000001a',
                yAxisID: 'y'
            }];

            // Add Moving Average lines
            if (extras.ma10 && extras.ma10.length > 0) {
                datasets.push({
                    label: 'MA10',
                    type: 'line',
                    data: extras.ma10.filter(d => d.y !== null).map(d => ({ x: luxon.DateTime.fromISO(d.x).valueOf(), y: d.y })),
                    borderColor: '#f59e0b',
                    borderWidth: 1.5,
                    pointRadius: 0,
                    fill: false,
                    tension: 0.1,
                    yAxisID: 'y'
                });
            }
            if (extras.ma20 && extras.ma20.length > 0) {
                datasets.push({
                    label: 'MA20',
                    type: 'line',
                    data: extras.ma20.filter(d => d.y !== null).map(d => ({ x: luxon.DateTime.fromISO(d.x).valueOf(), y: d.y })),
                    borderColor: '#3b82f6',
                    borderWidth: 1.5,
                    pointRadius: 0,
                    fill: false,
                    tension: 0.1,
                    yAxisID: 'y'
                });
            }
            if (extras.ma50 && extras.ma50.length > 0) {
                datasets.push({
                    label: 'MA50',
                    type: 'line',
                    data: extras.ma50.filter(d => d.y !== null).map(d => ({ x: luxon.DateTime.fromISO(d.x).valueOf(), y: d.y })),
                    borderColor: '#a855f7',
                    borderWidth: 1.5,
                    pointRadius: 0,
                    fill: false,
                    tension: 0.1,
                    yAxisID: 'y'
                });
            }

            // Add Volume bars on secondary axis
            if (extras.volume && extras.volume.length > 0) {
                datasets.push({
                    label: '거래량',
                    type: 'bar',
                    data: extras.volume.map(d => ({ x: luxon.DateTime.fromISO(d.x).valueOf(), y: d.y })),
                    backgroundColor: extras.volume.map(d => d.color + '80'),
                    borderColor: extras.volume.map(d => d.color),
                    borderWidth: 0,
                    yAxisID: 'volume',
                    barPercentage: 0.8,
                    categoryPercentage: 1
                });
            }

            // Add Buy/Sell trade markers
            if (extras.trades && extras.trades.length > 0) {
                const buyTrades = extras.trades.filter(t => t.type === 'buy');
                const sellTrades = extras.trades.filter(t => t.type === 'sell');

                if (buyTrades.length > 0) {
                    datasets.push({
                        label: '📈 매수',
                        type: 'scatter',
                        data: buyTrades.map(t => ({
                            x: luxon.DateTime.fromISO(t.date).valueOf(),
                            y: t.price
                        })),
                        backgroundColor: '#22c55e',
                        borderColor: '#16a34a',
                        borderWidth: 2,
                        pointRadius: 8,
                        pointStyle: 'triangle',
                        yAxisID: 'y'
                    });
                }

                if (sellTrades.length > 0) {
                    datasets.push({
                        label: '📉 매도',
                        type: 'scatter',
                        data: sellTrades.map(t => ({
                            x: luxon.DateTime.fromISO(t.date).valueOf(),
                            y: t.price
                        })),
                        backgroundColor: '#ef4444',
                        borderColor: '#dc2626',
                        borderWidth: 2,
                        pointRadius: 8,
                        pointStyle: 'rectRot',
                        yAxisID: 'y'
                    });
                }
            }

            console.log('Chart datasets:', datasets.length, 'items');

            stockChart = new Chart(ctx, {
                type: 'candlestick',
                data: { datasets },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: {
                        mode: 'index',
                        intersect: false
                    },
                    plugins: {
                        legend: {
                            display: true,
                            position: 'top',
                            labels: {
                                color: isDark ? '#94a3b8' : '#64748b',
                                usePointStyle: true,
                                padding: 15,
                                font: { size: 11 }
                            },
                            onClick: (e, legendItem, legend) => {
                                const index = legendItem.datasetIndex;
                                const ci = legend.chart;
                                const meta = ci.getDatasetMeta(index);
                                meta.hidden = meta.hidden === null ? !ci.data.datasets[index].hidden : null;
                                ci.update();
                            }
                        },
                        tooltip: {
                            callbacks: {
                                label: (context) => {
                                    const d = context.raw;
                                    if (context.dataset.type === 'candlestick' || context.dataset.label.includes('Candlestick')) {
                                        return [
                                            `O: $${d.o.toFixed(2)}`,
                                            `H: $${d.h.toFixed(2)}`,
                                            `L: $${d.l.toFixed(2)}`,
                                            `C: $${d.c.toFixed(2)}`
                                        ];
                                    } else if (context.dataset.label === '거래량') {
                                        return `Vol: ${(d.y / 1000000).toFixed(2)}M`;
                                    }
                                    return `${context.dataset.label}: $${d.y.toFixed(2)}`;
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
                            position: 'right',
                            grid: { color: isDark ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.05)' },
                            ticks: { color: isDark ? '#94a3b8' : '#64748b' }
                        },
                        volume: {
                            type: 'linear',
                            position: 'left',
                            beginAtZero: true,
                            max: extras.volume ? Math.max(...extras.volume.map(d => d.y)) * 4 : 1000000,
                            grid: { display: false },
                            ticks: { display: false }
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

    // ==================== WATCHLIST FUNCTIONALITY ====================

    const WATCHLIST_KEY = 'insight_watchlist';
    let currentWatchlistFilter = 'all';

    // Load watchlist from localStorage
    function loadWatchlist() {
        const data = localStorage.getItem(WATCHLIST_KEY);
        if (data) {
            return JSON.parse(data);
        }
        return { groups: ['기본'], stocks: [] };
    }

    // Save watchlist to localStorage
    function saveWatchlist(data) {
        localStorage.setItem(WATCHLIST_KEY, JSON.stringify(data));
    }

    // Add stock to watchlist
    function addToWatchlist(ticker, buyPrice, group) {
        const watchlist = loadWatchlist();

        // Check if ticker already exists
        if (watchlist.stocks.find(s => s.ticker === ticker.toUpperCase())) {
            alert(`${ticker.toUpperCase()}는 이미 Watchlist에 있습니다.`);
            return false;
        }

        watchlist.stocks.push({
            ticker: ticker.toUpperCase(),
            name: '', // Will be fetched
            buyPrice: parseFloat(buyPrice),
            group: group,
            addedAt: new Date().toISOString()
        });

        // Add new group if doesn't exist
        if (!watchlist.groups.includes(group)) {
            watchlist.groups.push(group);
        }

        saveWatchlist(watchlist);
        return true;
    }

    // Remove stock from watchlist
    function removeFromWatchlist(ticker) {
        const watchlist = loadWatchlist();
        watchlist.stocks = watchlist.stocks.filter(s => s.ticker !== ticker);
        saveWatchlist(watchlist);
    }

    // Add new group
    function addGroup(groupName) {
        const watchlist = loadWatchlist();
        if (!watchlist.groups.includes(groupName)) {
            watchlist.groups.push(groupName);
            saveWatchlist(watchlist);
        }
    }

    // Fetch current price for a ticker
    async function fetchCurrentPrice(ticker) {
        try {
            const res = await fetch(`/api/historical?ticker=${ticker}&range=1m`);
            if (res.ok) {
                const data = await res.json();
                return {
                    price: data.current_price,
                    name: data.meta?.name || ticker
                };
            }
        } catch (e) {
            console.warn(`Failed to fetch price for ${ticker}`, e);
        }
        return { price: null, name: ticker };
    }

    // Render watchlist tabs
    function renderWatchlistTabs() {
        const tabsContainer = document.getElementById('watchlist-tabs');
        if (!tabsContainer) return;

        const watchlist = loadWatchlist();

        let tabsHTML = `<button class="watchlist-tab ${currentWatchlistFilter === 'all' ? 'active' : ''}" data-group="all">전체</button>`;
        watchlist.groups.forEach(group => {
            tabsHTML += `<button class="watchlist-tab ${currentWatchlistFilter === group ? 'active' : ''}" data-group="${group}">${group}</button>`;
        });

        tabsContainer.innerHTML = tabsHTML;

        // Add click handlers
        tabsContainer.querySelectorAll('.watchlist-tab').forEach(tab => {
            tab.addEventListener('click', () => {
                currentWatchlistFilter = tab.dataset.group;
                renderWatchlistTabs();
                renderWatchlistTable();
            });
        });
    }

    // Render watchlist group select dropdown
    function renderGroupSelect() {
        const select = document.getElementById('watchlist-group');
        if (!select) return;

        const watchlist = loadWatchlist();

        select.innerHTML = watchlist.groups.map(g =>
            `<option value="${g}">${g}</option>`
        ).join('');
    }

    // Render watchlist table
    async function renderWatchlistTable() {
        const tbody = document.getElementById('watchlist-body');
        if (!tbody) return;

        const watchlist = loadWatchlist();
        let stocks = watchlist.stocks;

        // Apply group filter
        if (currentWatchlistFilter !== 'all') {
            stocks = stocks.filter(s => s.group === currentWatchlistFilter);
        }

        if (stocks.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="7" class="watchlist-empty">
                        <p>📭 Watchlist가 비어있습니다</p>
                        <p style="font-size: 0.9rem;">상단의 '+ 종목 추가' 버튼을 클릭하여 관심 종목을 추가하세요</p>
                    </td>
                </tr>
            `;
            return;
        }

        // Show loading state
        tbody.innerHTML = `
            <tr>
                <td colspan="7" style="text-align: center; padding: 2rem; color: var(--text-muted);">
                    ⏳ 가격 정보를 불러오는 중...
                </td>
            </tr>
        `;

        // Fetch current prices for all stocks
        const pricePromises = stocks.map(stock => fetchCurrentPrice(stock.ticker));
        const prices = await Promise.all(pricePromises);

        // Build table rows
        let rowsHTML = '';
        stocks.forEach((stock, idx) => {
            const priceData = prices[idx];
            const currentPrice = priceData.price;
            const name = priceData.name || stock.name || stock.ticker;

            let returnValue = null;
            let returnClass = '';
            let returnDisplay = '-';

            if (currentPrice && stock.buyPrice && stock.buyPrice > 0) {
                returnValue = ((currentPrice - stock.buyPrice) / stock.buyPrice) * 100;
                returnClass = returnValue >= 0 ? 'return-positive' : 'return-negative';
                returnDisplay = `${returnValue >= 0 ? '+' : ''}${returnValue.toFixed(2)}%`;
            }

            rowsHTML += `
                <tr data-ticker="${stock.ticker}">
                    <td class="ticker-cell" onclick="window.location.href='index.html?ticker=${stock.ticker}'">${stock.ticker}</td>
                    <td>${name}</td>
                    <td>${currentPrice ? `$${currentPrice.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '-'}</td>
                    <td>$${stock.buyPrice.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
                    <td class="${returnClass}">${returnDisplay}</td>
                    <td><span class="group-badge">${stock.group}</span></td>
                    <td><button class="delete-btn" onclick="handleDeleteWatchlistItem('${stock.ticker}')">🗑</button></td>
                </tr>
            `;
        });

        tbody.innerHTML = rowsHTML;
    }

    // Delete watchlist item handler (global)
    window.handleDeleteWatchlistItem = function (ticker) {
        if (confirm(`${ticker}를 Watchlist에서 삭제하시겠습니까?`)) {
            removeFromWatchlist(ticker);
            renderWatchlistTable();
        }
    };

    // Setup watchlist event handlers
    function setupWatchlistHandlers() {
        const addBtn = document.getElementById('add-watchlist-btn');
        const form = document.getElementById('watchlist-add-form');
        const saveBtn = document.getElementById('save-watchlist-btn');
        const cancelBtn = document.getElementById('cancel-watchlist-btn');
        const toggleNewGroupBtn = document.getElementById('toggle-new-group');
        const newGroupInput = document.getElementById('watchlist-new-group');
        const groupSelect = document.getElementById('watchlist-group');

        if (!addBtn || !form) return;

        // Show/hide add form
        addBtn.addEventListener('click', () => {
            form.classList.toggle('hidden');
            if (!form.classList.contains('hidden')) {
                document.getElementById('watchlist-ticker').focus();
            }
        });

        // Cancel button
        cancelBtn?.addEventListener('click', () => {
            form.classList.add('hidden');
            document.getElementById('watchlist-ticker').value = '';
            document.getElementById('watchlist-buy-price').value = '';
            newGroupInput?.classList.add('hidden');
        });

        // Toggle new group input
        toggleNewGroupBtn?.addEventListener('click', () => {
            newGroupInput?.classList.toggle('hidden');
            if (!newGroupInput?.classList.contains('hidden')) {
                newGroupInput.focus();
                groupSelect.disabled = true;
            } else {
                groupSelect.disabled = false;
                newGroupInput.value = '';
            }
        });

        // Save button
        saveBtn?.addEventListener('click', async () => {
            const tickerInput = document.getElementById('watchlist-ticker');
            const priceInput = document.getElementById('watchlist-buy-price');

            const ticker = tickerInput.value.trim().toUpperCase();
            const buyPrice = parseFloat(priceInput.value);
            let group = groupSelect.value;

            // Check for new group
            if (!newGroupInput?.classList.contains('hidden') && newGroupInput.value.trim()) {
                group = newGroupInput.value.trim();
                addGroup(group);
                renderGroupSelect();
            }

            if (!ticker) {
                alert('티커를 입력해주세요.');
                return;
            }
            if (isNaN(buyPrice) || buyPrice <= 0) {
                alert('유효한 매수가를 입력해주세요.');
                return;
            }

            if (addToWatchlist(ticker, buyPrice, group)) {
                // Clear form
                tickerInput.value = '';
                priceInput.value = '';
                newGroupInput.value = '';
                newGroupInput?.classList.add('hidden');
                groupSelect.disabled = false;
                form.classList.add('hidden');

                // Refresh UI
                renderWatchlistTabs();
                await renderWatchlistTable();
            }
        });

        // Enter key to save
        document.getElementById('watchlist-buy-price')?.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') saveBtn?.click();
        });
    }

    // Initialize watchlist on main page
    if (isMainPage) {
        renderGroupSelect();
        renderWatchlistTabs();
        renderWatchlistTable();
        setupWatchlistHandlers();
    }

});
