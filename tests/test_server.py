# tests/test_server.py
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from queue.manager import ReviewQueue


def test_review_queue_integration(tmp_path):
    """MCP 툴들이 사용하는 ReviewQueue 통합 테스트"""
    queue_file = str(tmp_path / "test.json")
    queue = ReviewQueue(queue_file)

    draft_id = queue.add("KO content", "EN content",
                         {"title": "t", "description": "d", "keywords": []},
                         "social ko", "social en", [], [])

    pending = queue.list_pending()
    assert len(pending) == 1
    assert pending[0]["id"] == draft_id

    queue.approve(draft_id)
    assert queue.get(draft_id)["status"] == "approved"
