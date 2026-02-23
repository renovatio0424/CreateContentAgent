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
