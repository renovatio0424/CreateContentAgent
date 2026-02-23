# tests/test_product_researcher.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from pipeline.nodes.product_researcher import product_researcher_node
from pipeline.state import ContentState


def make_state(category="에어프라이어") -> ContentState:
    return ContentState(
        category=category,
        products=[], keywords=[], outline="",
        content_ko="", content_en="",
        affiliate_links_ko=[], affiliate_links_en=[],
        seo_meta={}, social_ko="", social_en="",
        draft_id="", status="pending", error=None,
    )


@pytest.mark.asyncio
async def test_product_researcher_populates_products():
    state = make_state("에어프라이어")
    mock_response = MagicMock()
    mock_response.content = """
    제품명: 필립스 에어프라이어 HD9252
    가격: 89,000원
    평점: 4.5
    URL: https://coupang.com/vp/products/1234
    플랫폼: coupang
    ---
    제품명: Philips Air Fryer HD9200
    가격: $79.99
    평점: 4.4
    URL: https://amazon.com/dp/B08EXAMPLE
    플랫폼: amazon
    """

    with patch("pipeline.nodes.product_researcher.get_llm") as mock_get_llm:
        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value = mock_response
        mock_get_llm.return_value = mock_llm
        result = await product_researcher_node(state)

    assert len(result["products"]) > 0
    assert result["error"] is None


@pytest.mark.asyncio
async def test_product_researcher_handles_error():
    state = make_state()
    with patch("pipeline.nodes.product_researcher.get_llm") as mock_get_llm:
        mock_llm = AsyncMock()
        mock_llm.ainvoke.side_effect = Exception("API error")
        mock_get_llm.return_value = mock_llm
        result = await product_researcher_node(state)

    assert result["error"] is not None
    assert "API error" in result["error"]
