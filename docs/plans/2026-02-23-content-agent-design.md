# CreateContentAgent — 설계 문서

**작성일**: 2026-02-23
**목적**: 부수입 창출을 위한 반자동 컨텐츠 생산 에이전트
**상태**: 승인됨

---

## 1. 프로젝트 목표

- 수익성 높은 제품 리뷰 니치를 자동 분석
- 한국어(쿠팡파트너스) + 영어(Amazon Associates) 컨텐츠 동시 생산
- 사람이 검토/승인 후 WordPress에 자동 게시
- OpenClaw(Claude Code)에서 MCP Server로 트리거

---

## 2. 수익화 전략

| 시장 | 플랫폼 | 수익 모델 |
|---|---|---|
| 한국어 | WordPress + 쿠팡파트너스 | 어필리에이트 커미션 (구매 전환) |
| 영어 | WordPress + Amazon Associates | 어필리에이트 커미션 (구매 전환) |

**컨텐츠 타입**: 구매 의도(buyer intent) 키워드 타겟 제품 리뷰
예: "쿠팡 에어프라이어 추천", "best air fryer under $100 2026"

---

## 3. 전체 아키텍처

```
OpenClaw (Claude Code)
    ↓ MCP Tool 호출
MCP Server (server.py)
    ↓
LangGraph Pipeline
    ├─ product_researcher   → Gemini 2.0 Flash (Google Search grounding)
    ├─ keyword_analyzer     → Gemini 2.0 Flash (Google Search grounding)
    ├─ review_outline       → Ollama / llama3.2
    ├─ content_writer_ko    → Claude Sonnet 4.6
    ├─ content_writer_en    → GPT-4o          (병렬 실행)
    ├─ translator           → Gemini 2.0 Flash
    ├─ affiliate_linker     → Ollama / llama3.2
    ├─ seo_optimizer        → Ollama / qwen2.5
    ├─ social_snippets      → Claude Haiku (KO) / GPT-4o-mini (EN)
    ├─ [HUMAN REVIEW GATE]  ← LangGraph interrupt()
    └─ wordpress_publisher  → WordPress REST API
```

---

## 4. LLM 라우팅 매트릭스

| 노드 | 모델 | 선택 이유 |
|---|---|---|
| product_researcher | gemini-2.0-flash | Google Search grounding으로 실시간 제품 데이터 수집 |
| keyword_analyzer | gemini-2.0-flash | 실제 검색 트렌드 기반 키워드 추출 |
| review_outline | ollama/llama3.2 | 단순 구조화, 비용 0 |
| content_writer_ko | claude-sonnet-4-6 | 한국어 장문 품질 최우선 |
| content_writer_en | gpt-4o | 영어 이커머스 콘텐츠 학습 데이터 풍부 |
| translator | gemini-2.0-flash | 다국어 강점, 무료 티어 활용 |
| affiliate_linker | ollama/llama3.2 | 단순 링크 삽입, 비용 0 |
| seo_optimizer | ollama/qwen2.5 | 메타데이터 생성, 비용 0 |
| social_snippets_ko | claude-haiku-4-5 | 짧고 빠른 한국어 생성 |
| social_snippets_en | gpt-4o-mini | 짧고 저렴한 영어 생성 |

---

## 5. MCP Server Tool 정의

| Tool | 설명 | 파라미터 |
|---|---|---|
| `run_pipeline` | 전체 파이프라인 실행 | `category?: str` (제품 카테고리 힌트) |
| `get_review_queue` | 검토 대기 초안 목록 조회 | 없음 |
| `approve_and_publish` | 초안 승인 후 WordPress 게시 | `draft_id: str` |
| `reject_draft` | 초안 거절 및 재생성 요청 | `draft_id: str, reason?: str` |

---

## 6. 프로젝트 구조

```
CreateContentAgent/
├── server.py                      # MCP Server 진입점
├── pipeline/
│   ├── graph.py                   # LangGraph StateGraph 정의
│   ├── state.py                   # TypedDict 상태 스키마
│   ├── llm_router.py              # 모델 선택 로직
│   └── nodes/
│       ├── product_researcher.py  # 제품 조사 (Gemini + Google Search)
│       ├── keyword_analyzer.py    # 키워드 분석 (Gemini)
│       ├── review_writer.py       # 리뷰 본문 작성 (Claude/GPT)
│       ├── translator.py          # 번역 (Gemini)
│       ├── affiliate_linker.py    # 어필리에이트 링크 삽입
│       ├── seo.py                 # SEO 메타데이터 최적화
│       ├── social_snippets.py     # 소셜 미디어 스니펫
│       └── wordpress_publisher.py # WordPress REST API 게시
├── tools/
│   ├── gemini_search.py           # Google Search grounding 래퍼
│   ├── amazon_paapi.py            # Amazon Product Advertising API
│   ├── coupang.py                 # 쿠팡 제품 링크 (반자동)
│   └── wordpress.py               # WordPress REST API 클라이언트
├── queue/
│   └── reviews.json               # 검토 대기 초안 저장소
├── docs/
│   └── plans/
│       └── 2026-02-23-content-agent-design.md
├── config.py                      # API 키 및 설정
├── requirements.txt
└── .env.example
```

---

## 7. 기술 스택

| 영역 | 라이브러리 |
|---|---|
| 워크플로우 | `langgraph` |
| LLM 통합 | `langchain-anthropic`, `langchain-openai`, `langchain-google-genai`, `langchain-ollama` |
| MCP Server | `mcp` (Anthropic 공식 Python SDK) |
| Amazon API | `python-amazon-paapi` |
| WordPress | `python-wordpress-xmlrpc` or REST API |
| 환경 관리 | `python-dotenv` |

---

## 8. 예상 비용 (포스트 1개 기준)

| 작업 | 모델 | 비용 |
|---|---|---|
| 제품/키워드 조사 | Gemini Flash 무료 티어 | $0 |
| 구조/SEO/링크 | Ollama | $0 |
| KO 본문 (~2,000자) | Claude Sonnet | ~$0.03 |
| EN 본문 (~2,000자) | GPT-4o | ~$0.04 |
| 번역/스니펫 | Gemini/Claude Haiku | ~$0.01 |
| **총합** | | **~$0.08/포스트** |

---

## 9. 주요 제약 및 고려사항

- **Amazon PA-API**: Associates 계정 + 180일 내 3건 판매 실적 승인 조건
- **쿠팡파트너스**: 공식 API 없음 → 제품 링크 반자동 생성
- **WordPress**: 셀프호스팅 필요 (월 $5~15)
- **Google AI 정책**: "helpful content" 기준 충족 → Human Review Gate 필수
- **Ollama 모델**: llama3.2, qwen2.5 사전 설치 필요 (`ollama pull llama3.2`)
