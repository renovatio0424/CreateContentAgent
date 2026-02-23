# tests/test_wordpress.py
import pytest
from unittest.mock import patch, MagicMock
from tools.wordpress import WordPressClient
from pipeline.nodes.wordpress_publisher import wordpress_publisher_node
from pipeline.state import ContentState


def base_state():
    return ContentState(
        category="에어프라이어", products=[], keywords=[],
        outline="", content_ko="# KO 리뷰\n내용",
        content_en="# EN Review\nContent",
        affiliate_links_ko=[], affiliate_links_en=[],
        seo_meta={"title": "테스트", "description": "설명", "keywords": ["키워드"]},
        social_ko="소셜", social_en="Social",
        draft_id="abc123", status="approved", error=None,
    )


def test_wordpress_client_builds_post_payload():
    client = WordPressClient("https://example.com", "user", "pass")
    payload = client._build_payload(
        title="Test",
        content="Content",
        seo_meta={"title": "Test", "description": "Desc", "keywords": ["k"]},
        status="publish",
    )
    assert payload["title"] == "Test"
    assert payload["content"] == "Content"
    assert payload["status"] == "publish"


@pytest.mark.asyncio
async def test_wordpress_publisher_node_publishes():
    state = base_state()
    with patch("pipeline.nodes.wordpress_publisher.WordPressClient") as mock_cls:
        mock_client = MagicMock()
        mock_client.publish.return_value = {"id": 42, "link": "https://blog.com/post/42"}
        mock_cls.return_value = mock_client

        result = await wordpress_publisher_node(state)

    assert result["status"] == "published"
    assert result["error"] is None
