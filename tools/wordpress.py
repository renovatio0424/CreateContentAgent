# tools/wordpress.py
import requests
from requests.auth import HTTPBasicAuth


class WordPressClient:
    def __init__(self, url: str, username: str, password: str):
        self.base_url = url.rstrip("/")
        self.auth = HTTPBasicAuth(username, password)

    def _build_payload(self, title: str, content: str, seo_meta: dict, status: str = "draft") -> dict:
        return {
            "title": title,
            "content": content,
            "status": status,
            "excerpt": seo_meta.get("description", ""),
            "meta": {
                "_yoast_wpseo_title": seo_meta.get("title", ""),
                "_yoast_wpseo_metadesc": seo_meta.get("description", ""),
            },
        }

    def publish(self, title: str, content: str, seo_meta: dict, status: str = "draft") -> dict:
        payload = self._build_payload(title, content, seo_meta, status)
        response = requests.post(
            f"{self.base_url}/wp-json/wp/v2/posts",
            json=payload,
            auth=self.auth,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()
