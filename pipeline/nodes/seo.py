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
