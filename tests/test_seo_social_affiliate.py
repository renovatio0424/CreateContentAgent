# tests/test_seo_social_affiliate.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from pipeline.nodes.seo import seo_optimizer_node
from pipeline.nodes.social_snippets import social_snippets_node
from pipeline.nodes.affiliate_linker import affiliate_linker_node
from pipeline.state import ContentState


def base_state():
    return ContentState(
        category="에어프라이어",
        products=[{"name": "필립스 에어프라이어", "price": "89000", "rating": "4.5", "url": "https://coupang.com/vp/1234", "platform": "coupang"}],
        keywords=["에어프라이어 추천"],
        outline="", content_ko="# 리뷰\n본문 내용입니다.", content_en="# Review\nContent here.",
        affiliate_links_ko=[], affiliate_links_en=[],
        seo_meta={}, social_ko="", social_en="",
        draft_id="", status="pending", error=None,
    )


@pytest.mark.asyncio
async def test_seo_optimizer_returns_meta():
    state = base_state()
    mock_resp = MagicMock()
    mock_resp.content = '{"title": "에어프라이어 추천", "description": "최고의 에어프라이어", "keywords": ["에어프라이어", "추천"]}'
    with patch("pipeline.nodes.seo.get_llm") as m:
        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value = mock_resp
        m.return_value = mock_llm
        result = await seo_optimizer_node(state)
    assert result["seo_meta"] != {}


@pytest.mark.asyncio
async def test_social_snippets_returns_both():
    state = base_state()
    mock_resp = MagicMock()
    mock_resp.content = "소셜 스니펫 테스트"
    with patch("pipeline.nodes.social_snippets.get_llm") as m:
        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value = mock_resp
        m.return_value = mock_llm
        result = await social_snippets_node(state)
    assert len(result["social_ko"]) > 0
    assert len(result["social_en"]) > 0


@pytest.mark.asyncio
async def test_affiliate_linker_inserts_links():
    state = base_state()
    mock_resp = MagicMock()
    mock_resp.content = "# 리뷰\n본문 내용입니다.\n[구매하기](https://coupang.com/vp/1234)"
    with patch("pipeline.nodes.affiliate_linker.get_llm") as m:
        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value = mock_resp
        m.return_value = mock_llm
        result = await affiliate_linker_node(state)
    assert result["affiliate_links_ko"] != [] or "coupang" in result["content_ko"]
