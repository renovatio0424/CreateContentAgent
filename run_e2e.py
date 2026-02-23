"""E2E 테스트 스크립트 — save_to_queue 단계까지 실행 (WordPress 게시 제외)"""
import asyncio
import sys
from pipeline.graph import build_graph, get_initial_state


async def main():
    category = sys.argv[1] if len(sys.argv) > 1 else "에어프라이어"
    print(f"\n{'='*60}")
    print(f"  CreateContentAgent E2E 테스트")
    print(f"  카테고리: {category}")
    print(f"{'='*60}\n")

    graph = build_graph()
    state = get_initial_state(category)
    run_config = {"configurable": {"thread_id": "e2e-test-1"}}

    print("[1/8] 제품 조사 시작...")
    async for event in graph.astream(state, run_config):
        for node_name, node_state in event.items():
            if node_name == "product_researcher":
                products = node_state.get("products", [])
                print(f"  ✅ 제품 조사 완료: {len(products)}개 발견")
                for p in products[:3]:
                    print(f"     - {p.get('name', '?')} ({p.get('platform', '?')})")

            elif node_name == "keyword_analyzer":
                keywords = node_state.get("keywords", [])
                print(f"  ✅ 키워드 분석 완료: {keywords[:5]}")

            elif node_name == "review_outline":
                outline = node_state.get("outline", "")
                print(f"  ✅ 리뷰 구조 생성 완료 ({len(outline)}자)")

            elif node_name == "review_writer":
                ko = node_state.get("content_ko", "")
                en = node_state.get("content_en", "")
                print(f"  ✅ 리뷰 작성 완료 — KO: {len(ko)}자, EN: {len(en)}자")

            elif node_name == "affiliate_linker":
                ko_links = node_state.get("affiliate_links_ko", [])
                en_links = node_state.get("affiliate_links_en", [])
                print(f"  ✅ 어필리에이트 링크 삽입 — KO: {len(ko_links)}개, EN: {len(en_links)}개")

            elif node_name == "seo_optimizer":
                seo = node_state.get("seo_meta", {})
                print(f"  ✅ SEO 메타 생성 — 제목: {seo.get('title', '?')}")

            elif node_name == "social_snippets":
                social_ko = node_state.get("social_ko", "")
                social_en = node_state.get("social_en", "")
                print(f"  ✅ 소셜 스니펫 생성 — KO: {len(social_ko)}자, EN: {len(social_en)}자")

            elif node_name == "save_to_queue":
                draft_id = node_state.get("draft_id", "")
                print(f"  ✅ 검토 큐 저장 완료 — 초안 ID: {draft_id}")

            elif node_name == "__interrupt__":
                # interrupt 발생 — human review gate 직전
                print(f"\n{'='*60}")
                print("  ⏸  Human Review Gate — 파이프라인 일시 중단")
                print("  검토 큐에 초안이 저장되었습니다.")
                print(f"{'='*60}")
                break

            if node_state.get("error"):
                print(f"  ❌ 오류 발생 ({node_name}): {node_state['error']}")
                return

    # 최종 상태 확인 (queue에서 읽기)
    from queue.manager import ReviewQueue
    queue = ReviewQueue()
    pending = queue.list_pending()
    if pending:
        draft = pending[-1]
        print(f"\n{'='*60}")
        print("  최종 생성 결과 미리보기")
        print(f"{'='*60}")
        print(f"\n  초안 ID  : {draft['id']}")
        print(f"\n  [SEO 메타]")
        seo = draft.get("seo_meta", {})
        print(f"  제목     : {seo.get('title', '')}")
        print(f"  설명     : {seo.get('description', '')}")
        print(f"  키워드   : {seo.get('keywords', [])}")
        print(f"\n  [KO 소셜 스니펫]")
        print(f"  {draft.get('social_ko', '')[:200]}")
        print(f"\n  [EN 소셜 스니펫]")
        print(f"  {draft.get('social_en', '')[:200]}")
        print(f"\n  [KO 본문 미리보기 (첫 400자)]")
        print(f"  {draft.get('content_ko', '')[:400]}")
        print(f"\n  [EN 본문 미리보기 (첫 400자)]")
        print(f"  {draft.get('content_en', '')[:400]}")
        print(f"\n{'='*60}")
        print(f"  approve_and_publish('{draft['id']}') 로 WordPress에 게시 가능")
        print(f"{'='*60}\n")


if __name__ == "__main__":
    asyncio.run(main())
