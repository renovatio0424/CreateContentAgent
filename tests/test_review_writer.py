# tests/test_review_writer.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from pipeline.nodes.review_writer import review_writer_node
from pipeline.state import ContentState


def make_state():
    return ContentState(
        category="에어프라이어",
        products=[{"name": "필립스 에어프라이어", "price": "89000", "rating": "4.5", "url": "https://example.com", "platform": "coupang"}],
        keywords=["에어프라이어 추천", "best air fryer 2026"],
        outline="1. 소개\n2. 스펙\n3. 장단점\n4. 결론",
        content_ko="", content_en="",
        affiliate_links_ko=[], affiliate_links_en=[],
        seo_meta={}, social_ko="", social_en="",
        draft_id="", status="pending", error=None,
    )


@pytest.mark.asyncio
async def test_review_writer_generates_both_languages():
    state = make_state()
    ko_response = MagicMock()
    ko_response.content = "# 필립스 에어프라이어 추천 리뷰\n\n안녕하세요..."
    en_response = MagicMock()
    en_response.content = "# Philips Air Fryer Review\n\nHello..."

    with patch("pipeline.nodes.review_writer.get_llm") as mock_get_llm:
        mock_ko_llm = AsyncMock()
        mock_ko_llm.ainvoke.return_value = ko_response
        mock_en_llm = AsyncMock()
        mock_en_llm.ainvoke.return_value = en_response
        mock_get_llm.side_effect = [mock_ko_llm, mock_en_llm]
        result = await review_writer_node(state)

    assert len(result["content_ko"]) > 0
    assert len(result["content_en"]) > 0
    assert result["error"] is None


@pytest.mark.asyncio
async def test_review_writer_handles_error():
    state = make_state()
    with patch("pipeline.nodes.review_writer.get_llm") as mock_get_llm:
        mock_llm = AsyncMock()
        mock_llm.ainvoke.side_effect = Exception("rate limit")
        mock_get_llm.return_value = mock_llm
        result = await review_writer_node(state)

    assert result["error"] is not None
