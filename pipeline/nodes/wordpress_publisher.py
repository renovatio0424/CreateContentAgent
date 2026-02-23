# pipeline/nodes/wordpress_publisher.py
from pipeline.state import ContentState
from tools.wordpress import WordPressClient
import config


async def wordpress_publisher_node(state: ContentState) -> ContentState:
    try:
        ko_client = WordPressClient(
            config.WORDPRESS_KO_URL,
            config.WORDPRESS_KO_USER,
            config.WORDPRESS_KO_PASSWORD,
        )
        en_client = WordPressClient(
            config.WORDPRESS_EN_URL,
            config.WORDPRESS_EN_USER,
            config.WORDPRESS_EN_PASSWORD,
        )

        title_ko = state["seo_meta"].get("title", state["category"])
        title_en = state["seo_meta"].get("title", state["category"])

        ko_client.publish(title_ko, state["content_ko"], state["seo_meta"])
        en_client.publish(title_en, state["content_en"], state["seo_meta"])

        return {**state, "status": "published", "error": None}
    except Exception as e:
        return {**state, "error": str(e)}
