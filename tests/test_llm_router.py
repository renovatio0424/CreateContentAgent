# tests/test_llm_router.py
from pipeline.llm_router import get_llm, LLMTask


def test_product_research_uses_gemini():
    llm = get_llm(LLMTask.PRODUCT_RESEARCH)
    assert "gemini" in type(llm).__name__.lower() or "google" in str(type(llm)).lower()


def test_content_writer_ko_uses_claude():
    llm = get_llm(LLMTask.CONTENT_WRITER_KO)
    assert "anthropic" in str(type(llm)).lower() or "claude" in str(type(llm)).lower()


def test_content_writer_en_uses_openai():
    llm = get_llm(LLMTask.CONTENT_WRITER_EN)
    assert "openai" in str(type(llm)).lower()


def test_outline_uses_ollama():
    llm = get_llm(LLMTask.REVIEW_OUTLINE)
    assert "ollama" in str(type(llm)).lower()


def test_unknown_task_raises_value_error():
    import pytest
    with pytest.raises(ValueError):
        get_llm("unknown_task")
