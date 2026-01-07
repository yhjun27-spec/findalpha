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
        summary: '엔비디아는 AI 가속기 시장의 사실상 독점 체제를 유지하고 있습니다. 데이터 센터 수요의 폭발적인 증가가 실적 성장을 견인하고 있습니다.',
        risks: ['높은 밸류에이션 부담', '대중국 수출 규제', '후발 주자들의 추격'],
        growth: ['생성형 AI 인프라 확충', '옴니버스 플랫폼 확장', '차세대 블랙웰 아키텍처 기대감']
    }
};

document.addEventListener('DOMContentLoaded', () => {
    const searchBtn = document.getElementById('search-btn');
    const tickerInput = document.getElementById('ticker-input');
    const resultSection = document.getElementById('result-section');
    const themeToggle = document.getElementById('theme-toggle');
    const body = document.body;

    // Theme Toggle Logic
    themeToggle.addEventListener('click', () => {
        body.classList.toggle('light-theme');
        body.classList.toggle('dark-theme');
        const isDark = body.classList.contains('dark-theme');
        themeToggle.querySelector('.theme-icon').textContent = isDark ? '🌙' : '☀️';
    });

    const handleSearch = () => {
        const ticker = tickerInput.value.trim().toUpperCase();
        if (!ticker) {
            alert('티커를 입력해 주세요.');
            return;
        }

        // Show loading state (simple)
        searchBtn.disabled = true;
        searchBtn.textContent = '분석 중...';

        setTimeout(() => {
            renderResult(ticker);
            searchBtn.disabled = false;
            searchBtn.textContent = '분석하기';
        }, 1200);
    };

    searchBtn.addEventListener('click', handleSearch);
    tickerInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleSearch();
    });

    function renderResult(ticker) {
        const data = MOCK_DATA[ticker] || {
            name: ticker,
            price: 'N/A',
            sentiment: 'Unknown',
            summary: `현재 ${ticker}에 대한 상세 데이터가 시스템에 등록되어 있지 않습니다. 실시간 분석 모드로 전환 중입니다...`,
            risks: ['데이터 부족'],
            growth: ['데이터 업데이트 필요']
        };

        resultSection.innerHTML = `
            <div class="result-card" style="animation: fadeInUp 0.6s ease-out">
                <div class="result-header">
                    <div>
                        <h2 class="ticker-name">${data.name} <span class="ticker-code">(${ticker})</span></h2>
                        <p class="current-price">$${data.price}</p>
                    </div>
                    <div class="sentiment-badge ${data.sentiment.toLowerCase().replace(' ', '-')}">
                        ${data.sentiment}
                    </div>
                </div>

                <div class="analysis-grid">
                    <div class="analysis-box summary-box">
                        <h3>AI 총평</h3>
                        <p>${data.summary}</p>
                    </div>
                    
                    <div class="analysis-box">
                        <h3>주요 리스크</h3>
                        <ul>
                            ${data.risks.map(r => `<li>${r}</li>`).join('')}
                        </ul>
                    </div>

                    <div class="analysis-box">
                        <h3>성장 모멘텀</h3>
                        <ul>
                            ${data.growth.map(g => `<li>${g}</li>`).join('')}
                        </ul>
                    </div>
                </div>
            </div>
        `;

        resultSection.classList.remove('hidden');
        resultSection.scrollIntoView({ behavior: 'smooth' });
    }
});
