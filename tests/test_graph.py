# tests/test_graph.py
import pytest
from unittest.mock import AsyncMock, patch
from pipeline.graph import build_graph


def test_graph_builds_without_error():
    graph = build_graph()
    assert graph is not None


def test_graph_has_expected_nodes():
    graph = build_graph()
    node_names = list(graph.nodes.keys())
    assert "product_researcher" in node_names
    assert "keyword_analyzer" in node_names
    assert "review_writer" in node_names
    assert "wordpress_publisher" in node_names
