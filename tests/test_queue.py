# tests/test_queue.py
import pytest
from queue.manager import ReviewQueue


@pytest.fixture
def tmp_queue(tmp_path):
    queue_file = str(tmp_path / "test_reviews.json")
    return ReviewQueue(queue_file)


def test_add_draft_returns_id(tmp_queue):
    draft_id = tmp_queue.add(
        content_ko="한국어 리뷰",
        content_en="English review",
        seo_meta={"title": "test", "description": "desc", "keywords": []},
        social_ko="소셜 KO",
        social_en="Social EN",
        affiliate_links_ko=[],
        affiliate_links_en=[],
    )
    assert draft_id is not None
    assert len(draft_id) > 0


def test_list_returns_pending_drafts(tmp_queue):
    tmp_queue.add("KO", "EN", {}, "", "", [], [])
    tmp_queue.add("KO2", "EN2", {}, "", "", [], [])
    drafts = tmp_queue.list_pending()
    assert len(drafts) == 2


def test_approve_changes_status(tmp_queue):
    draft_id = tmp_queue.add("KO", "EN", {}, "", "", [], [])
    tmp_queue.approve(draft_id)
    draft = tmp_queue.get(draft_id)
    assert draft["status"] == "approved"


def test_reject_removes_draft(tmp_queue):
    draft_id = tmp_queue.add("KO", "EN", {}, "", "", [], [])
    tmp_queue.reject(draft_id)
    assert tmp_queue.get(draft_id) is None


def test_get_nonexistent_returns_none(tmp_queue):
    assert tmp_queue.get("nonexistent-id") is None
