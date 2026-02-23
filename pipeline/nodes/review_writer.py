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
            products=products_str, keywords=keywords_str, outline=state["outline"],
        ))
        en_msg = HumanMessage(content=EN_PROMPT.format(
            products=products_str, keywords=keywords_str, outline=state["outline"],
        ))
        ko_res, en_res = await asyncio.gather(
            ko_llm.ainvoke([ko_msg]),
            en_llm.ainvoke([en_msg]),
        )
        return {**state, "content_ko": ko_res.content, "content_en": en_res.content, "error": None}
    except Exception as e:
        return {**state, "error": str(e)}
