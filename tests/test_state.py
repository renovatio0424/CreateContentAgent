# tests/test_state.py
from pipeline.state import ContentState

def test_state_has_required_fields():
    state = ContentState(
        category="electronics",
        products=[],
        keywords=[],
        outline="",
        content_ko="",
        content_en="",
        affiliate_links_ko=[],
        affiliate_links_en=[],
        seo_meta={},
        social_ko="",
        social_en="",
        draft_id="",
        status="pending",
        error=None,
    )
    assert state["status"] == "pending"
    assert state["category"] == "electronics"

def test_state_default_status_is_pending():
    state = ContentState(
        category="test",
        products=[],
        keywords=[],
        outline="",
        content_ko="",
        content_en="",
        affiliate_links_ko=[],
        affiliate_links_en=[],
        seo_meta={},
        social_ko="",
        social_en="",
        draft_id="",
        status="pending",
        error=None,
    )
    assert state["error"] is None
