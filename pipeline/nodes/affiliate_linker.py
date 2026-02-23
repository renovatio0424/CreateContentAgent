# pipeline/nodes/affiliate_linker.py
from pipeline.state import ContentState
from pipeline.llm_router import get_llm, LLMTask
from langchain_core.messages import HumanMessage

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
        ko_res = await llm.ainvoke([HumanMessage(content=LINK_PROMPT.format(
            urls="\n".join(coupang_urls), content=state["content_ko"],
        ))])
        en_res = await llm.ainvoke([HumanMessage(content=LINK_PROMPT.format(
            urls="\n".join(amazon_urls), content=state["content_en"],
        ))])
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
