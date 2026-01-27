# AI Analysis API Module for Gemini
# Handles company analysis using Google Gemini API

import os
import google.generativeai as genai
from typing import Optional

# Gemini API Key (환경변수에서 로드)
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

# System Prompt (공통 프롬프트)
SYSTEM_PROMPT = """당신은 전문 기업 분석가입니다. 다음 원칙을 엄격히 준수하세요:

1. **1차 자료 기반**: 모든 주장은 10-K/10-Q, IR 자료, 애널리스트 리포트에 근거해야 합니다.
2. **항상 근거 필요**: 주장에는 반드시 출처를 명시하세요. 예: [출처: XYZ 10-K 2024 p.45]
3. **문체**: ~이다체를 사용하세요.
4. **언어**: 한국어로 답변하세요.
5. **포맷**: Markdown 형식으로 답변하세요. 헤더(##), 리스트(-), 강조(**) 등을 활용하세요."""

# Prompt Templates
PROMPTS = {
    "company_overview": """
{ticker} ({company_name})에 대해 다음 항목을 분석하세요:

## 1) 사업 개요 (Business Overview)
- 핵심 사업 영역 (3-5줄 요약)
- 주요 제품/서비스 라인업 및 매출 기여도
- 시장 포지션: 시장점유율, 순위 (정량 데이터)
- 고객 유형: B2B/B2C, 주요 고객 (Top 10 비중 명시)

## 2) 기업 역사 (Company History)
- 설립 배경 및 창업 스토리
- 주요 전환점 (제품 출시, 시장 진입, M&A 등)
- 최근 3년 내 중요 변화 - 사업 재편, M&A, 주요 파트너십
- CEO 교체 등 경영진 변화 - 역사적 맥락에서 현재 위치

## 3) 경영진 분석 (Organization Pillar)

### A. CEO 평가
- 비전 & 실행력: CEO가 비전가(visionary)인가, 실행가(executioner)인가? 창업자 CEO인가?
- 제품/서비스에 대한 intimate knowledge 보유 여부
- First-principles 사고 가능 여부
- Contrarian 결정을 내릴 수 있는 대담함
- Skin in the Game: 지분율 (경제적 소유권 %), 최근 1년 insider buying/selling 내역
- 보상 구조: SBC, 성과 연동 인센티브
- 장기적 사고: 10년 후에도 재임 가능? (나이, 건강 고려)
- 단기 실적 vs 장기 가치 중 어디에 집중?
- 회사 업무에 시간을 얼마나 할애? (다른 이사회 겸직 등)
- 커뮤니케이션: Earnings call 답변 품질, SNS를 통한 고객 소통
- Shareholder letter 품질
- 성장 의지: 큰 성장 야망 (huge growth ambition) 보유? Rational optimist인가?
- 세상에 새로운 가치 창출 의지?

### B. C-Suite & 경영진 평가
- COO, CFO, CTO 등 주요 임원 배경
- 지분 보유 (economic stake)
- CEO 비전과의 정렬
- 업계 경력 (industry veteran 여부)
- 재임 기간 (장기 tenure는 플러스)
- Engineering/Product 배경 보유 여부
- 최근 insider trading 활동

### C. 조직 문화 (Culture)
- Open-ended mission 보유?
- 강한 공동 정체성 (common identity)?
- 직원 만족도 지표 (Glassdoor 등)
- 직원이 회사에 자부심을 느끼는가?
- M&A Frankenstein vs 통합된 문화
- 보상 구조가 회사 성과와 정렬?
""",
    
    "business_model": """
{ticker} ({company_name})의 비즈니스 모델을 분석하세요:

## 1) 수익 창출 구조
- 어떻게 돈을 버는가? (Step-by-step)
- 사업부별로 어떤 제품을 팔아서 어떤 구조로 돈을 버는가?

## 2) 현금화 시점 (Cash Conversion Cycle)
- 매출 인식 시점과 현금 수취 시점
- 운전자본 요구량
- 선수금 vs 후불 구조

## 3) 주요 비용 구조 (COGS 구성)
- 매출원가 구성 요소
- 고정비 vs 변동비 비율
- 규모의 경제 존재 여부

## 4) 주요 고객 비중
- 고객 집중도 (Top 10 고객 매출 비중)
- 고객 이탈률
- 고객 획득 비용 (CAC)
- 고객 생애 가치 (LTV)
""",
    
    "product_analysis": """
{ticker} ({company_name})의 제품 포트폴리오를 분석하세요:

## 1) 사업부별 제품 현황
- 각 사업부별로 어떤 제품을 판매하는가?
- 각 제품의 시장 내 포지션

## 2) 마진 분석
- 제품별/사업부별 마진이 얼마나 나오는가?
- 고마진 제품 vs 저마진 제품 믹스
- 마진 추이 (개선/악화)

## 3) 제품 용도
- 어디에 쓰이는가?
- 최종 사용자 (End User) 특성
- 사용 사례 (Use Cases)

## 4) 혁신성 평가
- 완전히 새로운 시장을 만들고 있는가?
- 기존 패러다임을 바꾸는가? (Disruptive)
  - 예: Netflix vs Blockbuster - 만성적 문제를 해결하는가?
- **Zero-to-One (혁명적)** vs **One-to-Ten (점진적)**

## 5) 경쟁 우위
- 다른 경쟁사의 제품에 비해서 어떤 강점이 있는가?
- 기술적 차별화
- 가격 경쟁력
- 브랜드 파워
""",
    
    "revenue_analysis": """
{ticker} ({company_name})의 매출 분석을 수행하세요:

## 1) 매출 구성 분석
- 사업부별/제품별 매출 비중
- 지역별 매출 구성 (북미/유럽/아시아 등)
- 매출 집중도 (주요 고객 의존도)

## 2) 최근 매출 변동 요인
- 최근 2-3개 분기 매출 성장/하락 주요 원인
- Volume vs Price 효과 분해
- 일회성 요인 vs 구조적 변화 구분

## 3) 매출 성장 드라이버
- 신제품/서비스 출시 영향
- 시장 점유율 변화
- TAM (Total Addressable Market) 확대 여부
- 가격 정책 변화 영향

## 4) 향후 매출 전망
- 컨센서스 vs 경영진 가이던스 비교
- 성장 가속/둔화 가능성
- 리스크 요인 (경쟁 심화, 규제, 거시경제 등)
""",
    
    "margin_analysis": """
{ticker} ({company_name})의 마진 분석을 수행하세요:

## 1) GPM (Gross Profit Margin) 분석
- 현재 GPM 수준과 추이
- GPM에 영향을 주는 핵심 요소
  - 제품/서비스 믹스 변화
  - 원가 구조 (인건비, 원자재, 물류비 등)
  - 가격 결정력 (Pricing Power)
- 경쟁사 대비 GPM 수준 비교

## 2) OPEX 구조 분석
- R&D 투자율: 매출 대비 R&D 비중 및 추이
- SG&A 효율성: 매출 대비 SG&A 비중 변화
- 규모의 경제 실현 여부 (Operating Leverage)

## 3) 수익성 개선/악화 요인
- 최근 마진 변동의 주요 원인
- 일회성 비용 vs 구조적 변화 구분
- 향후 마진 개선 가능성

## 4) FCF (Free Cash Flow) 마진
- FCF 마진 추이와 분석
- 운전자본 변동 영향
- CAPEX 강도 및 전망
"""
}


def analyze_company(ticker: str, company_name: str, category: str) -> dict:
    """
    Analyze a company using Gemini API.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'NVDA')
        company_name: Full company name (e.g., 'NVIDIA Corp.')
        category: Analysis category ('company_overview', 'business_model', 'product_analysis')
    
    Returns:
        dict with 'success', 'content' or 'error' keys
    """
    try:
        if category not in PROMPTS:
            return {"success": False, "error": f"Unknown category: {category}"}
        
        # Format the prompt
        prompt = PROMPTS[category].format(ticker=ticker, company_name=company_name)
        
        # Create model
        model = genai.GenerativeModel(
            model_name="gemini-2.0-flash",
            system_instruction=SYSTEM_PROMPT
        )
        
        # Generate response
        response = model.generate_content(prompt)
        
        return {
            "success": True,
            "content": response.text,
            "category": category
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def analyze_all(ticker: str, company_name: str) -> dict:
    """
    Run all analysis categories for a company.
    
    Returns:
        dict with results for each category
    """
    results = {}
    categories = ["company_overview", "business_model", "product_analysis"]
    
    for category in categories:
        results[category] = analyze_company(ticker, company_name, category)
    
    return results


# =====================================================
# 어닝콜 분석 (Earnings Call Analysis)
# =====================================================

EARNINGS_CALL_SYSTEM_PROMPT = """당신은 전문 Equity Fund Manager로서 어닝콜 트랜스크립트 분석을 전문으로 합니다.
제공된 PDF 텍스트를 분석하여 투자 의사결정을 지원하는 리포트를 생성해야 합니다.

**문체 규칙:**
- 명사형 문체 사용 (~함, ~임, ~됨)
- 한국어로 작성하되, 수치와 항목명은 정확히 영문 표기
- Markdown 형식으로 답변"""

EARNINGS_CALL_PROMPT = """다음 어닝콜 트랜스크립트를 분석하여 아래 형식으로 리포트를 작성하세요.

## 분석 대상
- **티커**: {ticker}
- **분기**: {period}

---

## 1. Financial Summary
**재무 데이터를 한국어로 정리하되, 수치와 항목명은 정확히 표기**

- **Total Revenue**: $X.XM (X% y/y) vs $X.XM - Beat/Miss/In-line
- **세부 부문별/지역별 매출**
- **Gross Profit**: $X.XM (margin X.X%)
- **Operating Income**: $X.XM (margin X.X%)
- **Adjusted EBITDA**: $X.XM (margin X.X%)
- **EPS**: $X.XX vs $X.XX
- **주요 KPI**: 업종별 핵심 지표들
- **현금흐름** (해당시): OCF, FCF, Cash 등

## 2. Guidance
**경영진이 제시한 전망을 명사형으로 정리**

- **다음 분기 매출 전망**: $X.X~X.XB (X%~X% y/y)
- **연간 매출 가이던스**: $X.XB (기존 전망 대비 상향/하향/유지)
- **마진 전망**: X.X% (전년 대비 개선/악화)
- **기타 중요 가이던스**

## 3. Management Summary
**⚠️ 중요: 경영진이 발언한 순서대로 괄호 안에 주제를 표시하여 정리**

**(주제1) 관련 경영진 발언 요약 - 명사형 문체로 작성**
**(주제2) 관련 경영진 발언 요약 - 명사형 문체로 작성**
**(주제3) 관련 경영진 발언 요약 - 명사형 문체로 작성**

**예시**:
- **(AI) Pinterest의 AI 기반 개인화 추천 시스템이 사용자 참여도를 크게 향상시키고 있음**
- **(Gen Z) Gen Z 사용자가 전체 MAU의 50%를 차지하며 차세대 성장 동력으로 확인됨**

## 4. Q&A Section
**⚠️ 중요: 어닝콜에서 진행된 모든 Q&A를 빠짐없이 포함하여 요약 정리**

각 Q&A는 다음 형식으로:
- **Q (애널리스트명, 소속)**: 질문 요약
- **A (경영진)**: 답변 요약

---

## 어닝콜 트랜스크립트:

{transcript}
"""


def extract_pdf_text(pdf_path: str) -> str:
    """
    PDF 파일에서 텍스트를 추출합니다.
    
    Args:
        pdf_path: PDF 파일의 전체 경로
    
    Returns:
        추출된 텍스트 문자열
    """
    try:
        import pdfplumber
        
        text_content = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_content.append(page_text)
        
        return "\n\n".join(text_content)
    
    except Exception as e:
        raise Exception(f"PDF 텍스트 추출 실패: {str(e)}")


def analyze_earnings_call(ticker: str, pdf_path: str, period: str = "", force_refresh: bool = False) -> dict:
    """
    어닝콜 PDF를 분석하여 투자 리포트를 생성합니다.
    분석 결과는 캐싱되어 다음 요청 시 API 호출 없이 반환됩니다.
    
    Args:
        ticker: 종목 티커 (예: 'PLTR')
        pdf_path: PDF 파일 경로
        period: 분기 정보 (예: '2024 Q4')
        force_refresh: True면 캐시 무시하고 재분석
    
    Returns:
        dict with 'success', 'content', 'cached' or 'error' keys
    """
    import os
    import json
    from datetime import datetime
    
    # 캐시 파일 경로 설정 (PDF와 같은 폴더에 .json으로 저장)
    pdf_dir = os.path.dirname(pdf_path)
    pdf_basename = os.path.splitext(os.path.basename(pdf_path))[0]
    cache_path = os.path.join(pdf_dir, f"{pdf_basename}_analysis.json")
    
    # 캐시 확인 (force_refresh가 아닌 경우)
    if not force_refresh and os.path.exists(cache_path):
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                cached_data = json.load(f)
                cached_data['cached'] = True
                cached_data['cache_date'] = cached_data.get('analyzed_at', 'Unknown')
                print(f"Cache hit: {cache_path}")
                return cached_data
        except Exception as e:
            print(f"Cache read error: {e}")
    
    try:
        # 1. PDF에서 텍스트 추출
        transcript = extract_pdf_text(pdf_path)
        
        if not transcript or len(transcript.strip()) < 100:
            return {
                "success": False,
                "error": "PDF에서 충분한 텍스트를 추출하지 못했습니다."
            }
        
        # 2. 프롬프트 구성
        prompt = EARNINGS_CALL_PROMPT.format(
            ticker=ticker,
            period=period,
            transcript=transcript
        )
        
        # 3. Gemini API 호출
        model = genai.GenerativeModel(
            model_name="gemini-2.0-flash",
            system_instruction=EARNINGS_CALL_SYSTEM_PROMPT
        )
        
        response = model.generate_content(prompt)
        
        result = {
            "success": True,
            "content": response.text,
            "ticker": ticker,
            "period": period,
            "analyzed_at": datetime.now().isoformat(),
            "cached": False
        }
        
        # 4. 캐시에 저장
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"Analysis cached: {cache_path}")
        except Exception as e:
            print(f"Cache write error: {e}")
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


