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
