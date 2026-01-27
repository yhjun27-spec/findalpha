# Notion Export Module for Earnings Call Analysis
# Exports analysis results to Notion pages

import os
from typing import Optional

# Notion API 설정 (환경변수에서 로드)
NOTION_API_KEY = os.environ.get('NOTION_API_KEY', '')
NOTION_DATABASE_ID = os.environ.get('NOTION_DATABASE_ID', '')


def is_notion_configured() -> bool:
    """노션 API가 설정되어 있는지 확인"""
    return bool(NOTION_API_KEY and NOTION_DATABASE_ID)


def export_to_notion(ticker: str, period: str, content: str, analyzed_at: str = "") -> dict:
    """
    어닝콜 분석 결과를 노션 페이지로 내보냅니다.
    
    Args:
        ticker: 종목 티커 (예: 'TSM')
        period: 분기 정보 (예: '2024 Q4')
        content: 분석 결과 (Markdown 형식)
        analyzed_at: 분석 일시
    
    Returns:
        dict with 'success', 'url' or 'error' keys
    """
    if not is_notion_configured():
        return {
            "success": False,
            "error": "Notion API가 설정되지 않았습니다. 환경변수 NOTION_API_KEY와 NOTION_DATABASE_ID를 설정해주세요."
        }
    
    try:
        from notion_client import Client
        
        notion = Client(auth=NOTION_API_KEY)
        
        # 먼저 데이터베이스 스키마를 확인
        try:
            db_info = notion.databases.retrieve(database_id=NOTION_DATABASE_ID)
            properties = db_info.get('properties', {})
            
            # title 속성 찾기
            title_prop_name = None
            for prop_name, prop_info in properties.items():
                if prop_info.get('type') == 'title':
                    title_prop_name = prop_name
                    break
            
            if not title_prop_name:
                title_prop_name = '이름'  # 기본값
                
        except Exception as e:
            print(f"Database schema fetch error: {e}")
            title_prop_name = '이름'  # 기본값
        
        # Markdown을 Notion 블록으로 변환
        blocks = markdown_to_notion_blocks(content)
        
        # 새 페이지 생성 (title 속성만 사용)
        page_title = f"{ticker} 어닝콜 분석 - {period}"
        
        new_page = notion.pages.create(
            parent={"database_id": NOTION_DATABASE_ID},
            properties={
                title_prop_name: {
                    "title": [
                        {
                            "text": {
                                "content": page_title
                            }
                        }
                    ]
                }
            },
            children=blocks
        )
        
        return {
            "success": True,
            "url": new_page.get("url", ""),
            "page_id": new_page.get("id", "")
        }
        
    except ImportError:
        return {
            "success": False,
            "error": "notion-client 패키지가 설치되지 않았습니다. pip install notion-client를 실행해주세요."
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def markdown_to_notion_blocks(markdown_text: str) -> list:
    """
    Markdown 텍스트를 Notion 블록 형식으로 변환합니다.
    간단한 변환 - 헤더, 불릿, 문단 지원
    """
    blocks = []
    lines = markdown_text.split('\n')
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        if not line:
            i += 1
            continue
        
        # 헤더 처리
        if line.startswith('## '):
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": line[3:]}}]
                }
            })
        elif line.startswith('### '):
            blocks.append({
                "object": "block",
                "type": "heading_3",
                "heading_3": {
                    "rich_text": [{"type": "text", "text": {"content": line[4:]}}]
                }
            })
        elif line.startswith('# '):
            blocks.append({
                "object": "block",
                "type": "heading_1",
                "heading_1": {
                    "rich_text": [{"type": "text", "text": {"content": line[2:]}}]
                }
            })
        # 불릿 리스트 처리
        elif line.startswith('- ') or line.startswith('* '):
            blocks.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"type": "text", "text": {"content": line[2:]}}]
                }
            })
        # 구분선 처리
        elif line == '---' or line == '***':
            blocks.append({
                "object": "block",
                "type": "divider",
                "divider": {}
            })
        # 일반 문단
        else:
            # 텍스트가 너무 길면 분할 (Notion 제한: 2000자)
            text = line
            while len(text) > 1900:
                blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": text[:1900]}}]
                    }
                })
                text = text[1900:]
            
            if text:
                blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": text}}]
                    }
                })
        
        i += 1
    
    # Notion API는 한 번에 100개 블록만 허용
    return blocks[:100]
