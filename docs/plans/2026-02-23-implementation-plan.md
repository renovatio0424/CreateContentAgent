# CreateContentAgent Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** LangGraph 기반 반자동 컨텐츠 생산 에이전트 — 제품 리뷰를 자동 생성하여 WordPress에 게시하고 어필리에이트 수익을 창출한다.

**Architecture:** MCP Server가 OpenClaw의 진입점이 되며, 내부적으로 LangGraph StateGraph를 실행한다. 각 노드는 작업 특성에 맞는 LLM(Gemini/Claude/GPT/Ollama)을 라우팅하여 비용을 최소화한다. LangGraph의 `interrupt()`로 Human Review Gate를 구현한다.

**Tech Stack:** Python 3.11+, langgraph, langchain-anthropic, langchain-openai, langchain-google-genai, langchain-ollama, mcp, pytest, pytest-asyncio

---

## Task 1: 프로젝트 기반 설정

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `config.py`
- Create: `tests/__init__.py`
- Create: `pipeline/__init__.py`
- Create: `pipeline/nodes/__init__.py`
- Create: `tools/__init__.py`
- Create: `queue/__init__.py`

**Step 1: 디렉토리 구조 생성**

```bash
mkdir -p pipeline/nodes tools queue tests
touch pipeline/__init__.py pipeline/nodes/__init__.py tools/__init__.py queue/__init__.py tests/__init__.py
```

**Step 2: requirements.txt 작성**

```
langgraph>=0.2.0
langchain-anthropic>=0.3.0
langchain-openai>=0.3.0
langchain-google-genai>=2.0.0
langchain-ollama>=0.2.0
langchain-core>=0.3.0
mcp>=1.0.0
python-dotenv>=1.0.0
requests>=2.31.0
pytest>=8.0.0
pytest-asyncio>=0.23.0
```

**Step 3: .env.example 작성**

```
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=AIza...
WORDPRESS_KO_URL=https://your-ko-blog.com
WORDPRESS_KO_USER=admin
WORDPRESS_KO_PASSWORD=your-app-password
WORDPRESS_EN_URL=https://your-en-blog.com
WORDPRESS_EN_USER=admin
WORDPRESS_EN_PASSWORD=your-app-password
AMAZON_ACCESS_KEY=...
AMAZON_SECRET_KEY=...
AMAZON_PARTNER_TAG=your-tag-20
COUPANG_AFFILIATE_ID=your-id
OLLAMA_BASE_URL=http://localhost:11434
```

**Step 4: config.py 작성**

```python
import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

WORDPRESS_KO_URL = os.getenv("WORDPRESS_KO_URL", "")
WORDPRESS_KO_USER = os.getenv("WORDPRESS_KO_USER", "")
WORDPRESS_KO_PASSWORD = os.getenv("WORDPRESS_KO_PASSWORD", "")

WORDPRESS_EN_URL = os.getenv("WORDPRESS_EN_URL", "")
WORDPRESS_EN_USER = os.getenv("WORDPRESS_EN_USER", "")
WORDPRESS_EN_PASSWORD = os.getenv("WORDPRESS_EN_PASSWORD", "")

AMAZON_ACCESS_KEY = os.getenv("AMAZON_ACCESS_KEY", "")
AMAZON_SECRET_KEY = os.getenv("AMAZON_SECRET_KEY", "")
AMAZON_PARTNER_TAG = os.getenv("AMAZON_PARTNER_TAG", "")

COUPANG_AFFILIATE_ID = os.getenv("COUPANG_AFFILIATE_ID", "")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

QUEUE_FILE = "queue/reviews.json"
```

**Step 5: 의존성 설치**

```bash
pip install -r requirements.txt
```

**Step 6: .env 파일 생성 (로컬용)**

```bash
cp .env.example .env
# .env 파일에 실제 API 키 입력 (git에 커밋하지 않음)
```

**Step 7: 커밋**

```bash
git add requirements.txt .env.example config.py pipeline/ tools/ queue/ tests/
git commit -m "chore: project scaffold and dependencies"
```

---

## Task 2: State 스키마 정의

**Files:**
- Create: `pipeline/state.py`
- Create: `tests/test_state.py`

**Step 1: 테스트 작성**

```python
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
```

**Step 2: 테스트 실행 (실패 확인)**

```bash
pytest tests/test_state.py -v
```
Expected: `ModuleNotFoundError: No module named 'pipeline.state'`

**Step 3: state.py 구현**

```python
# pipeline/state.py
from typing import TypedDict, Optional, Any


class ProductInfo(TypedDict):
    name: str
    price: str
    rating: str
    url: str
    platform: str  # "coupang" | "amazon"


class SeoMeta(TypedDict):
    title: str
    description: str
    keywords: list[str]


class ContentState(TypedDict):
    category: str                        # 제품 카테고리
    products: list[ProductInfo]          # 조사된 제품 목록
    keywords: list[str]                  # 타겟 키워드
    outline: str                         # 리뷰 구조
    content_ko: str                      # 한국어 본문
    content_en: str                      # 영어 본문
    affiliate_links_ko: list[str]        # 쿠팡파트너스 링크
    affiliate_links_en: list[str]        # Amazon Associates 링크
    seo_meta: SeoMeta                    # SEO 메타데이터
    social_ko: str                       # 한국어 소셜 스니펫
    social_en: str                       # 영어 소셜 스니펫
    draft_id: str                        # 검토 큐 ID
    status: str                          # pending|reviewing|approved|published
    error: Optional[str]                 # 에러 메시지
```

**Step 4: 테스트 실행 (통과 확인)**

```bash
pytest tests/test_state.py -v
```
Expected: `2 passed`

**Step 5: 커밋**

```bash
git add pipeline/state.py tests/test_state.py
git commit -m "feat: add ContentState TypedDict schema"
```

---

## Task 3: LLM 라우터

**Files:**
- Create: `pipeline/llm_router.py`
- Create: `tests/test_llm_router.py`

**Step 1: 테스트 작성**

```python
# tests/test_llm_router.py
from unittest.mock import patch
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
```

**Step 2: 테스트 실행 (실패 확인)**

```bash
pytest tests/test_llm_router.py -v
```
Expected: `ModuleNotFoundError`

**Step 3: llm_router.py 구현**

```python
# pipeline/llm_router.py
from enum import Enum
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
import config


class LLMTask(str, Enum):
    PRODUCT_RESEARCH = "product_research"
    KEYWORD_ANALYSIS = "keyword_analysis"
    REVIEW_OUTLINE = "review_outline"
    CONTENT_WRITER_KO = "content_writer_ko"
    CONTENT_WRITER_EN = "content_writer_en"
    TRANSLATOR = "translator"
    AFFILIATE_LINKER = "affiliate_linker"
    SEO_OPTIMIZER = "seo_optimizer"
    SOCIAL_SNIPPETS_KO = "social_snippets_ko"
    SOCIAL_SNIPPETS_EN = "social_snippets_en"


_ROUTING = {
    LLMTask.PRODUCT_RESEARCH:   lambda: ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=config.GOOGLE_API_KEY),
    LLMTask.KEYWORD_ANALYSIS:   lambda: ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=config.GOOGLE_API_KEY),
    LLMTask.REVIEW_OUTLINE:     lambda: ChatOllama(model="llama3.2", base_url=config.OLLAMA_BASE_URL),
    LLMTask.CONTENT_WRITER_KO:  lambda: ChatAnthropic(model="claude-sonnet-4-6", api_key=config.ANTHROPIC_API_KEY),
    LLMTask.CONTENT_WRITER_EN:  lambda: ChatOpenAI(model="gpt-4o", api_key=config.OPENAI_API_KEY),
    LLMTask.TRANSLATOR:         lambda: ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=config.GOOGLE_API_KEY),
    LLMTask.AFFILIATE_LINKER:   lambda: ChatOllama(model="llama3.2", base_url=config.OLLAMA_BASE_URL),
    LLMTask.SEO_OPTIMIZER:      lambda: ChatOllama(model="qwen2.5", base_url=config.OLLAMA_BASE_URL),
    LLMTask.SOCIAL_SNIPPETS_KO: lambda: ChatAnthropic(model="claude-haiku-4-5-20251001", api_key=config.ANTHROPIC_API_KEY),
    LLMTask.SOCIAL_SNIPPETS_EN: lambda: ChatOpenAI(model="gpt-4o-mini", api_key=config.OPENAI_API_KEY),
}


def get_llm(task: LLMTask):
    if task not in _ROUTING:
        raise ValueError(f"Unknown LLM task: {task}")
    return _ROUTING[task]()
```

**Step 4: 테스트 실행 (통과 확인)**

```bash
pytest tests/test_llm_router.py -v
```
Expected: `5 passed`

**Step 5: 커밋**

```bash
git add pipeline/llm_router.py tests/test_llm_router.py
git commit -m "feat: add LLM routing matrix for all pipeline nodes"
```

---

## Task 4: 검토 큐(Review Queue) 시스템

**Files:**
- Create: `queue/manager.py`
- Create: `tests/test_queue.py`

**Step 1: 테스트 작성**

```python
# tests/test_queue.py
import json
import os
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
```

**Step 2: 테스트 실행 (실패 확인)**

```bash
pytest tests/test_queue.py -v
```
Expected: `ModuleNotFoundError`

**Step 3: queue/manager.py 구현**

```python
# queue/manager.py
import json
import uuid
import os
from typing import Optional
import config


class ReviewQueue:
    def __init__(self, queue_file: str = config.QUEUE_FILE):
        self.queue_file = queue_file
        self._ensure_file()

    def _ensure_file(self):
        os.makedirs(os.path.dirname(self.queue_file), exist_ok=True)
        if not os.path.exists(self.queue_file):
            self._write({})

    def _read(self) -> dict:
        with open(self.queue_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write(self, data: dict):
        with open(self.queue_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def add(self, content_ko: str, content_en: str, seo_meta: dict,
            social_ko: str, social_en: str,
            affiliate_links_ko: list, affiliate_links_en: list) -> str:
        draft_id = str(uuid.uuid4())[:8]
        data = self._read()
        data[draft_id] = {
            "id": draft_id,
            "status": "pending",
            "content_ko": content_ko,
            "content_en": content_en,
            "seo_meta": seo_meta,
            "social_ko": social_ko,
            "social_en": social_en,
            "affiliate_links_ko": affiliate_links_ko,
            "affiliate_links_en": affiliate_links_en,
        }
        self._write(data)
        return draft_id

    def list_pending(self) -> list[dict]:
        data = self._read()
        return [v for v in data.values() if v["status"] == "pending"]

    def get(self, draft_id: str) -> Optional[dict]:
        data = self._read()
        return data.get(draft_id)

    def approve(self, draft_id: str):
        data = self._read()
        if draft_id in data:
            data[draft_id]["status"] = "approved"
            self._write(data)

    def reject(self, draft_id: str):
        data = self._read()
        if draft_id in data:
            del data[draft_id]
            self._write(data)
```

**Step 4: 테스트 실행 (통과 확인)**

```bash
pytest tests/test_queue.py -v
```
Expected: `5 passed`

**Step 5: 커밋**

```bash
git add queue/manager.py tests/test_queue.py
git commit -m "feat: add JSON-based review queue manager"
```

---

## Task 5: Product Researcher 노드

**Files:**
- Create: `pipeline/nodes/product_researcher.py`
- Create: `tests/test_product_researcher.py`

**Step 1: 테스트 작성 (LLM mock)**

```python
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
```

**Step 2: 테스트 실행 (실패 확인)**

```bash
pytest tests/test_product_researcher.py -v
```
Expected: `ModuleNotFoundError`

**Step 3: product_researcher.py 구현**

```python
# pipeline/nodes/product_researcher.py
import re
from pipeline.state import ContentState
from pipeline.llm_router import get_llm, LLMTask
from langchain_core.messages import HumanMessage


RESEARCH_PROMPT = """당신은 이커머스 제품 조사 전문가입니다.
다음 카테고리에서 쿠팡(한국)과 Amazon(미국)의 인기 제품을 각 3개씩 조사하세요.

카테고리: {category}

각 제품을 다음 형식으로 작성하세요:
제품명: [제품명]
가격: [가격]
평점: [평점]
URL: [URL 또는 검색 키워드]
플랫폼: [coupang 또는 amazon]
---

실제 검색 결과 기반으로 현재 인기 있고 수익성 높은 제품을 선택하세요."""


def _parse_products(text: str) -> list[dict]:
    products = []
    blocks = text.strip().split("---")
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        product = {}
        for line in block.split("\n"):
            if "제품명:" in line:
                product["name"] = line.split(":", 1)[1].strip()
            elif "가격:" in line:
                product["price"] = line.split(":", 1)[1].strip()
            elif "평점:" in line:
                product["rating"] = line.split(":", 1)[1].strip()
            elif "URL:" in line:
                product["url"] = line.split(":", 1)[1].strip()
            elif "플랫폼:" in line:
                product["platform"] = line.split(":", 1)[1].strip()
        if "name" in product:
            products.append(product)
    return products


async def product_researcher_node(state: ContentState) -> ContentState:
    try:
        llm = get_llm(LLMTask.PRODUCT_RESEARCH)
        prompt = RESEARCH_PROMPT.format(category=state["category"])
        response = await llm.ainvoke([HumanMessage(content=prompt)])
        products = _parse_products(response.content)
        return {**state, "products": products, "error": None}
    except Exception as e:
        return {**state, "error": str(e)}
```

**Step 4: 테스트 실행 (통과 확인)**

```bash
pytest tests/test_product_researcher.py -v
```
Expected: `2 passed`

**Step 5: 커밋**

```bash
git add pipeline/nodes/product_researcher.py tests/test_product_researcher.py
git commit -m "feat: add product researcher node with Gemini"
```

---

## Task 6: Keyword Analyzer 노드

**Files:**
- Create: `pipeline/nodes/keyword_analyzer.py`
- Create: `tests/test_keyword_analyzer.py`

**Step 1: 테스트 작성**

```python
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
```

**Step 2: 테스트 실행 (실패 확인)**

```bash
pytest tests/test_keyword_analyzer.py -v
```
Expected: `ModuleNotFoundError`

**Step 3: keyword_analyzer.py 구현**

```python
# pipeline/nodes/keyword_analyzer.py
from pipeline.state import ContentState
from pipeline.llm_router import get_llm, LLMTask
from langchain_core.messages import HumanMessage

KEYWORD_PROMPT = """당신은 SEO 키워드 전문가입니다.
다음 제품 카테고리와 제품 목록을 분석하여 구매 의도(buyer intent) 키워드를 추출하세요.

카테고리: {category}
제품: {products}

한국어 키워드 5개와 영어 키워드 5개를 한 줄에 하나씩 작성하세요.
예: 에어프라이어 추천
형식: 키워드만, 설명 없이"""


async def keyword_analyzer_node(state: ContentState) -> ContentState:
    try:
        llm = get_llm(LLMTask.KEYWORD_ANALYSIS)
        product_names = [p["name"] for p in state["products"][:3]]
        prompt = KEYWORD_PROMPT.format(
            category=state["category"],
            products=", ".join(product_names)
        )
        response = await llm.ainvoke([HumanMessage(content=prompt)])
        keywords = [k.strip() for k in response.content.strip().split("\n") if k.strip()]
        return {**state, "keywords": keywords, "error": None}
    except Exception as e:
        return {**state, "error": str(e)}
```

**Step 4: 테스트 실행 (통과 확인)**

```bash
pytest tests/test_keyword_analyzer.py -v
```
Expected: `1 passed`

**Step 5: 커밋**

```bash
git add pipeline/nodes/keyword_analyzer.py tests/test_keyword_analyzer.py
git commit -m "feat: add keyword analyzer node with Gemini"
```

---

## Task 7: Review Writer 노드 (KO + EN 병렬)

**Files:**
- Create: `pipeline/nodes/review_writer.py`
- Create: `tests/test_review_writer.py`

**Step 1: 테스트 작성**

```python
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
async def test_review_writer_handles_ko_error():
    state = make_state()
    with patch("pipeline.nodes.review_writer.get_llm") as mock_get_llm:
        mock_llm = AsyncMock()
        mock_llm.ainvoke.side_effect = Exception("rate limit")
        mock_get_llm.return_value = mock_llm

        result = await review_writer_node(state)

    assert result["error"] is not None
```

**Step 2: 테스트 실행 (실패 확인)**

```bash
pytest tests/test_review_writer.py -v
```
Expected: `ModuleNotFoundError`

**Step 3: review_writer.py 구현 (asyncio.gather로 병렬 실행)**

```python
# pipeline/nodes/review_writer.py
import asyncio
from pipeline.state import ContentState
from pipeline.llm_router import get_llm, LLMTask
from langchain_core.messages import HumanMessage

KO_PROMPT = """당신은 한국어 제품 리뷰 전문 작가입니다.
다음 정보를 바탕으로 구매를 돕는 솔직하고 유익한 리뷰를 2,000자 이상 작성하세요.

제품: {products}
타겟 키워드: {keywords}
구조: {outline}

요구사항:
- 마크다운 형식
- 스펙 비교표 포함
- 장단점 명확히 제시
- 쿠팡 구매 유도 (자연스럽게)
- SEO 키워드를 자연스럽게 포함"""

EN_PROMPT = """You are an expert product review writer for Amazon affiliate content.
Write a helpful, honest review of 800+ words based on:

Products: {products}
Target keywords: {keywords}
Structure: {outline}

Requirements:
- Markdown format
- Include specs comparison table
- Clear pros and cons
- Natural Amazon purchase recommendation
- Include target keywords naturally"""


async def review_writer_node(state: ContentState) -> ContentState:
    try:
        ko_llm = get_llm(LLMTask.CONTENT_WRITER_KO)
        en_llm = get_llm(LLMTask.CONTENT_WRITER_EN)

        products_str = ", ".join([p["name"] for p in state["products"][:3]])
        keywords_str = ", ".join(state["keywords"][:5])

        ko_msg = HumanMessage(content=KO_PROMPT.format(
            products=products_str,
            keywords=keywords_str,
            outline=state["outline"],
        ))
        en_msg = HumanMessage(content=EN_PROMPT.format(
            products=products_str,
            keywords=keywords_str,
            outline=state["outline"],
        ))

        ko_res, en_res = await asyncio.gather(
            ko_llm.ainvoke([ko_msg]),
            en_llm.ainvoke([en_msg]),
        )

        return {**state, "content_ko": ko_res.content, "content_en": en_res.content, "error": None}
    except Exception as e:
        return {**state, "error": str(e)}
```

**Step 4: 테스트 실행 (통과 확인)**

```bash
pytest tests/test_review_writer.py -v
```
Expected: `2 passed`

**Step 5: 커밋**

```bash
git add pipeline/nodes/review_writer.py tests/test_review_writer.py
git commit -m "feat: add parallel KO/EN review writer node"
```

---

## Task 8: SEO, Social Snippets, Affiliate Linker 노드

**Files:**
- Create: `pipeline/nodes/seo.py`
- Create: `pipeline/nodes/social_snippets.py`
- Create: `pipeline/nodes/affiliate_linker.py`
- Create: `tests/test_seo_social_affiliate.py`

**Step 1: 테스트 작성**

```python
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
```

**Step 2: 테스트 실행 (실패 확인)**

```bash
pytest tests/test_seo_social_affiliate.py -v
```
Expected: `ModuleNotFoundError`

**Step 3: seo.py 구현**

```python
# pipeline/nodes/seo.py
import json
from pipeline.state import ContentState
from pipeline.llm_router import get_llm, LLMTask
from langchain_core.messages import HumanMessage

SEO_PROMPT = """다음 컨텐츠에 대한 SEO 메타데이터를 JSON으로 생성하세요.
키워드: {keywords}
컨텐츠 첫 200자: {preview}

JSON 형식으로만 응답하세요:
{{"title": "...", "description": "...", "keywords": ["...", "..."]}}"""


async def seo_optimizer_node(state: ContentState) -> ContentState:
    try:
        llm = get_llm(LLMTask.SEO_OPTIMIZER)
        preview = state["content_ko"][:200]
        prompt = SEO_PROMPT.format(
            keywords=", ".join(state["keywords"][:5]),
            preview=preview,
        )
        response = await llm.ainvoke([HumanMessage(content=prompt)])
        raw = response.content.strip()
        if "```" in raw:
            raw = raw.split("```")[1].replace("json", "").strip()
        seo_meta = json.loads(raw)
        return {**state, "seo_meta": seo_meta, "error": None}
    except Exception as e:
        return {**state, "seo_meta": {"title": "", "description": "", "keywords": []}, "error": str(e)}
```

**Step 4: social_snippets.py 구현**

```python
# pipeline/nodes/social_snippets.py
import asyncio
from pipeline.state import ContentState
from pipeline.llm_router import get_llm, LLMTask
from langchain_core.messages import HumanMessage

KO_SNIPPET_PROMPT = "다음 리뷰의 핵심을 140자 이내 인스타그램/트위터 포스트로 작성:\n\n{preview}"
EN_SNIPPET_PROMPT = "Write a compelling 280-char Twitter/Instagram post for this review:\n\n{preview}"


async def social_snippets_node(state: ContentState) -> ContentState:
    try:
        ko_llm = get_llm(LLMTask.SOCIAL_SNIPPETS_KO)
        en_llm = get_llm(LLMTask.SOCIAL_SNIPPETS_EN)
        ko_res, en_res = await asyncio.gather(
            ko_llm.ainvoke([HumanMessage(content=KO_SNIPPET_PROMPT.format(preview=state["content_ko"][:500]))]),
            en_llm.ainvoke([HumanMessage(content=EN_SNIPPET_PROMPT.format(preview=state["content_en"][:500]))]),
        )
        return {**state, "social_ko": ko_res.content, "social_en": en_res.content, "error": None}
    except Exception as e:
        return {**state, "error": str(e)}
```

**Step 5: affiliate_linker.py 구현**

```python
# pipeline/nodes/affiliate_linker.py
from pipeline.state import ContentState
from pipeline.llm_router import get_llm, LLMTask
from langchain_core.messages import HumanMessage
import config

LINK_PROMPT = """다음 리뷰 본문에 제품 구매 링크를 자연스럽게 삽입하세요.
제품 URL 목록:
{urls}

본문:
{content}

링크를 마크다운 형식으로 자연스럽게 삽입한 전체 본문을 반환하세요."""


async def affiliate_linker_node(state: ContentState) -> ContentState:
    try:
        llm = get_llm(LLMTask.AFFILIATE_LINKER)
        coupang_urls = [p["url"] for p in state["products"] if p.get("platform") == "coupang"]
        amazon_urls = [p["url"] for p in state["products"] if p.get("platform") == "amazon"]

        ko_prompt = LINK_PROMPT.format(
            urls="\n".join(coupang_urls),
            content=state["content_ko"],
        )
        en_prompt = LINK_PROMPT.format(
            urls="\n".join(amazon_urls),
            content=state["content_en"],
        )

        ko_res = await llm.ainvoke([HumanMessage(content=ko_prompt)])
        en_res = await llm.ainvoke([HumanMessage(content=en_prompt)])

        return {
            **state,
            "content_ko": ko_res.content,
            "content_en": en_res.content,
            "affiliate_links_ko": coupang_urls,
            "affiliate_links_en": amazon_urls,
            "error": None,
        }
    except Exception as e:
        return {**state, "error": str(e)}
```

**Step 6: 테스트 실행 (통과 확인)**

```bash
pytest tests/test_seo_social_affiliate.py -v
```
Expected: `3 passed`

**Step 7: 커밋**

```bash
git add pipeline/nodes/seo.py pipeline/nodes/social_snippets.py pipeline/nodes/affiliate_linker.py tests/test_seo_social_affiliate.py
git commit -m "feat: add SEO optimizer, social snippets, affiliate linker nodes"
```

---

## Task 9: WordPress Publisher 툴 + 노드

**Files:**
- Create: `tools/wordpress.py`
- Create: `pipeline/nodes/wordpress_publisher.py`
- Create: `tests/test_wordpress.py`

**Step 1: 테스트 작성**

```python
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
```

**Step 2: 테스트 실행 (실패 확인)**

```bash
pytest tests/test_wordpress.py -v
```
Expected: `ModuleNotFoundError`

**Step 3: tools/wordpress.py 구현**

```python
# tools/wordpress.py
import requests
from requests.auth import HTTPBasicAuth


class WordPressClient:
    def __init__(self, url: str, username: str, password: str):
        self.base_url = url.rstrip("/")
        self.auth = HTTPBasicAuth(username, password)

    def _build_payload(self, title: str, content: str, seo_meta: dict, status: str = "draft") -> dict:
        return {
            "title": title,
            "content": content,
            "status": status,
            "excerpt": seo_meta.get("description", ""),
            "meta": {
                "_yoast_wpseo_title": seo_meta.get("title", ""),
                "_yoast_wpseo_metadesc": seo_meta.get("description", ""),
            },
        }

    def publish(self, title: str, content: str, seo_meta: dict, status: str = "draft") -> dict:
        payload = self._build_payload(title, content, seo_meta, status)
        response = requests.post(
            f"{self.base_url}/wp-json/wp/v2/posts",
            json=payload,
            auth=self.auth,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()
```

**Step 4: pipeline/nodes/wordpress_publisher.py 구현**

```python
# pipeline/nodes/wordpress_publisher.py
from pipeline.state import ContentState
from tools.wordpress import WordPressClient
import config


async def wordpress_publisher_node(state: ContentState) -> ContentState:
    try:
        ko_client = WordPressClient(
            config.WORDPRESS_KO_URL,
            config.WORDPRESS_KO_USER,
            config.WORDPRESS_KO_PASSWORD,
        )
        en_client = WordPressClient(
            config.WORDPRESS_EN_URL,
            config.WORDPRESS_EN_USER,
            config.WORDPRESS_EN_PASSWORD,
        )

        title_ko = state["seo_meta"].get("title", state["category"])
        title_en = state["seo_meta"].get("title", state["category"])

        ko_client.publish(title_ko, state["content_ko"], state["seo_meta"])
        en_client.publish(title_en, state["content_en"], state["seo_meta"])

        return {**state, "status": "published", "error": None}
    except Exception as e:
        return {**state, "error": str(e)}
```

**Step 5: 테스트 실행 (통과 확인)**

```bash
pytest tests/test_wordpress.py -v
```
Expected: `2 passed`

**Step 6: 커밋**

```bash
git add tools/wordpress.py pipeline/nodes/wordpress_publisher.py tests/test_wordpress.py
git commit -m "feat: add WordPress REST API publisher"
```

---

## Task 10: LangGraph 파이프라인 조립

**Files:**
- Create: `pipeline/graph.py`
- Create: `tests/test_graph.py`

**Step 1: 테스트 작성**

```python
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
```

**Step 2: 테스트 실행 (실패 확인)**

```bash
pytest tests/test_graph.py -v
```
Expected: `ModuleNotFoundError`

**Step 3: graph.py 구현**

```python
# pipeline/graph.py
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt

from pipeline.state import ContentState
from pipeline.nodes.product_researcher import product_researcher_node
from pipeline.nodes.keyword_analyzer import keyword_analyzer_node
from pipeline.nodes.review_writer import review_writer_node
from pipeline.nodes.seo import seo_optimizer_node
from pipeline.nodes.social_snippets import social_snippets_node
from pipeline.nodes.affiliate_linker import affiliate_linker_node
from pipeline.nodes.wordpress_publisher import wordpress_publisher_node


async def review_outline_node(state: ContentState) -> ContentState:
    from pipeline.llm_router import get_llm, LLMTask
    from langchain_core.messages import HumanMessage
    llm = get_llm(LLMTask.REVIEW_OUTLINE)
    prompt = f"다음 제품의 리뷰 구조를 5개 섹션으로 만드세요: {state['category']}"
    response = await llm.ainvoke([HumanMessage(content=prompt)])
    return {**state, "outline": response.content}


async def human_review_gate(state: ContentState) -> ContentState:
    """Human review gate — LangGraph interrupt으로 일시 중단"""
    interrupt({
        "message": "컨텐츠 검토 후 승인/거절해주세요.",
        "draft_id": state["draft_id"],
        "content_ko_preview": state["content_ko"][:300],
        "content_en_preview": state["content_en"][:300],
    })
    return state


async def save_to_queue_node(state: ContentState) -> ContentState:
    from queue.manager import ReviewQueue
    queue = ReviewQueue()
    draft_id = queue.add(
        content_ko=state["content_ko"],
        content_en=state["content_en"],
        seo_meta=state["seo_meta"],
        social_ko=state["social_ko"],
        social_en=state["social_en"],
        affiliate_links_ko=state["affiliate_links_ko"],
        affiliate_links_en=state["affiliate_links_en"],
    )
    return {**state, "draft_id": draft_id, "status": "reviewing"}


def should_continue(state: ContentState) -> str:
    if state.get("error"):
        return END
    return "continue"


def build_graph():
    builder = StateGraph(ContentState)

    builder.add_node("product_researcher", product_researcher_node)
    builder.add_node("keyword_analyzer", keyword_analyzer_node)
    builder.add_node("review_outline", review_outline_node)
    builder.add_node("review_writer", review_writer_node)
    builder.add_node("affiliate_linker", affiliate_linker_node)
    builder.add_node("seo_optimizer", seo_optimizer_node)
    builder.add_node("social_snippets", social_snippets_node)
    builder.add_node("save_to_queue", save_to_queue_node)
    builder.add_node("human_review_gate", human_review_gate)
    builder.add_node("wordpress_publisher", wordpress_publisher_node)

    builder.set_entry_point("product_researcher")
    builder.add_edge("product_researcher", "keyword_analyzer")
    builder.add_edge("keyword_analyzer", "review_outline")
    builder.add_edge("review_outline", "review_writer")
    builder.add_edge("review_writer", "affiliate_linker")
    builder.add_edge("affiliate_linker", "seo_optimizer")
    builder.add_edge("seo_optimizer", "social_snippets")
    builder.add_edge("social_snippets", "save_to_queue")
    builder.add_edge("save_to_queue", "human_review_gate")
    builder.add_edge("human_review_gate", "wordpress_publisher")
    builder.add_edge("wordpress_publisher", END)

    checkpointer = MemorySaver()
    return builder.compile(checkpointer=checkpointer, interrupt_before=["human_review_gate"])


def get_initial_state(category: str = "") -> ContentState:
    return ContentState(
        category=category,
        products=[], keywords=[], outline="",
        content_ko="", content_en="",
        affiliate_links_ko=[], affiliate_links_en=[],
        seo_meta={}, social_ko="", social_en="",
        draft_id="", status="pending", error=None,
    )
```

**Step 4: 테스트 실행 (통과 확인)**

```bash
pytest tests/test_graph.py -v
```
Expected: `2 passed`

**Step 5: 커밋**

```bash
git add pipeline/graph.py tests/test_graph.py
git commit -m "feat: assemble LangGraph pipeline with human review interrupt"
```

---

## Task 11: MCP Server 구현

**Files:**
- Create: `server.py`
- Create: `tests/test_server.py`

**Step 1: 테스트 작성**

```python
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
```

**Step 2: 테스트 실행 (통과 확인 — queue는 이미 구현됨)**

```bash
pytest tests/test_server.py -v
```
Expected: `1 passed`

**Step 3: server.py 구현**

```python
# server.py
import asyncio
import json
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from pipeline.graph import build_graph, get_initial_state
from queue.manager import ReviewQueue
from pipeline.nodes.wordpress_publisher import wordpress_publisher_node

app = Server("content-agent")
_graph = build_graph()
_queue = ReviewQueue()


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="run_pipeline",
            description="컨텐츠 생산 파이프라인 실행. 제품 리뷰 초안을 생성하여 검토 큐에 추가합니다.",
            inputSchema={
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "제품 카테고리 힌트 (예: 에어프라이어, 노트북). 없으면 자동 선택.",
                    }
                },
            },
        ),
        types.Tool(
            name="get_review_queue",
            description="검토 대기 중인 컨텐츠 초안 목록을 조회합니다.",
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="approve_and_publish",
            description="초안을 승인하고 WordPress에 게시합니다.",
            inputSchema={
                "type": "object",
                "properties": {
                    "draft_id": {"type": "string", "description": "승인할 초안 ID"}
                },
                "required": ["draft_id"],
            },
        ),
        types.Tool(
            name="reject_draft",
            description="초안을 거절하고 큐에서 삭제합니다.",
            inputSchema={
                "type": "object",
                "properties": {
                    "draft_id": {"type": "string", "description": "거절할 초안 ID"},
                    "reason": {"type": "string", "description": "거절 이유 (선택)"},
                },
                "required": ["draft_id"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    if name == "run_pipeline":
        category = arguments.get("category", "")
        config = {"configurable": {"thread_id": "pipeline-1"}}
        initial_state = get_initial_state(category)

        result = await _graph.ainvoke(initial_state, config)
        draft_id = result.get("draft_id", "")

        return [types.TextContent(
            type="text",
            text=f"파이프라인 완료. 초안 ID: {draft_id}\n검토 후 approve_and_publish를 호출하세요.",
        )]

    elif name == "get_review_queue":
        pending = _queue.list_pending()
        if not pending:
            return [types.TextContent(type="text", text="검토 대기 중인 초안이 없습니다.")]
        summaries = []
        for draft in pending:
            summaries.append(
                f"ID: {draft['id']}\n"
                f"KO 미리보기: {draft['content_ko'][:150]}...\n"
                f"EN 미리보기: {draft['content_en'][:150]}...\n"
            )
        return [types.TextContent(type="text", text="\n---\n".join(summaries))]

    elif name == "approve_and_publish":
        draft_id = arguments["draft_id"]
        draft = _queue.get(draft_id)
        if not draft:
            return [types.TextContent(type="text", text=f"초안 {draft_id}를 찾을 수 없습니다.")]

        from pipeline.state import ContentState
        state = ContentState(
            category="", products=[], keywords=[], outline="",
            content_ko=draft["content_ko"],
            content_en=draft["content_en"],
            affiliate_links_ko=draft["affiliate_links_ko"],
            affiliate_links_en=draft["affiliate_links_en"],
            seo_meta=draft["seo_meta"],
            social_ko=draft["social_ko"],
            social_en=draft["social_en"],
            draft_id=draft_id,
            status="approved", error=None,
        )
        result = await wordpress_publisher_node(state)
        if result["error"]:
            return [types.TextContent(type="text", text=f"게시 실패: {result['error']}")]
        _queue.approve(draft_id)
        return [types.TextContent(type="text", text=f"초안 {draft_id} 게시 완료!")]

    elif name == "reject_draft":
        draft_id = arguments["draft_id"]
        reason = arguments.get("reason", "이유 없음")
        _queue.reject(draft_id)
        return [types.TextContent(type="text", text=f"초안 {draft_id} 거절됨. 이유: {reason}")]

    return [types.TextContent(type="text", text=f"알 수 없는 툴: {name}")]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
```

**Step 4: 테스트 실행**

```bash
pytest tests/ -v
```
Expected: 모든 테스트 통과

**Step 5: 커밋**

```bash
git add server.py tests/test_server.py
git commit -m "feat: add MCP server with run_pipeline, get_review_queue, approve_and_publish, reject_draft tools"
```

---

## Task 12: OpenClaw 연동 설정

**Files:**
- Create: `.claude/mcp_settings.md` (안내 문서)

**Step 1: OpenClaw에 MCP Server 등록**

`~/.claude/claude.json` 파일을 열어 아래 내용 추가:

```json
{
  "mcpServers": {
    "content-agent": {
      "command": "python",
      "args": ["/Users/reno/Desktop/ToyProject/CreateContentAgent/server.py"],
      "env": {
        "ANTHROPIC_API_KEY": "your-key",
        "OPENAI_API_KEY": "your-key",
        "GOOGLE_API_KEY": "your-key"
      }
    }
  }
}
```

**Step 2: Ollama 모델 확인**

```bash
ollama list
# llama3.2, qwen2.5 없으면:
ollama pull llama3.2
ollama pull qwen2.5
```

**Step 3: 전체 테스트 실행**

```bash
pytest tests/ -v --tb=short
```
Expected: 모든 테스트 통과

**Step 4: OpenClaw 재시작 후 동작 확인**

OpenClaw에서:
```
"컨텐츠 파이프라인 실행해줘"
→ run_pipeline 툴 자동 호출
→ 초안 생성 완료 메시지 수신

"검토할 컨텐츠 있어?"
→ get_review_queue 호출
→ 초안 목록 표시

"이 초안 게시해줘 (ID: abc123)"
→ approve_and_publish 호출
→ WordPress 게시 완료
```

**Step 5: 최종 커밋**

```bash
git add .
git commit -m "feat: complete CreateContentAgent MVP — LangGraph + MCP Server integration"
```

---

## 전체 테스트 실행 명령어

```bash
# 전체 테스트
pytest tests/ -v

# 특정 모듈만
pytest tests/test_graph.py -v
pytest tests/test_queue.py -v

# 커버리지
pytest tests/ --cov=pipeline --cov=tools --cov=queue --cov-report=term-missing
```

---

## 주의사항

1. `.env` 파일에 실제 API 키 입력 후 시작
2. `ollama pull llama3.2 && ollama pull qwen2.5` 먼저 실행
3. WordPress에서 Application Password 생성 필요 (설정 → 사용자 → 프로필)
4. Amazon PA-API는 Associates 계정 승인 후 사용 가능
5. 쿠팡파트너스 링크는 수동으로 `.env`에 `COUPANG_AFFILIATE_ID` 설정
