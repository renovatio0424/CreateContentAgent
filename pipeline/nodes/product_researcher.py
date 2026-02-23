# pipeline/nodes/product_researcher.py
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
