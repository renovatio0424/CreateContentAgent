# tests/test_keyword_analyzer.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from pipeline.nodes.keyword_analyzer import keyword_analyzer_node
from pipeline.state import ContentState


def make_state():
    return ContentState(
        category="에어프라이어",
        products=[{"name": "필립스 에어프라이어", "price": "89000", "rating": "4.5", "url": "", "platform": "coupang"}],
        keywords=[], outline="", content_ko="", content_en="",
        affiliate_links_ko=[], affiliate_links_en=[],
        seo_meta={}, social_ko="", social_en="",
        draft_id="", status="pending", error=None,
    )


@pytest.mark.asyncio
async def test_keyword_analyzer_returns_keywords():
    state = make_state()
    mock_response = MagicMock()
    mock_response.content = "에어프라이어 추천\n쿠팡 에어프라이어\n가성비 에어프라이어\nbest air fryer 2026\nair fryer review"

    with patch("pipeline.nodes.keyword_analyzer.get_llm") as mock_get_llm:
        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value = mock_response
        mock_get_llm.return_value = mock_llm
        result = await keyword_analyzer_node(state)

    assert len(result["keywords"]) >= 3
    assert result["error"] is None
