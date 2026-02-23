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
        run_config = {"configurable": {"thread_id": "pipeline-1"}}
        initial_state = get_initial_state(category)

        result = await _graph.ainvoke(initial_state, run_config)
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
