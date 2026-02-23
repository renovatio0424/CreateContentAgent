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
