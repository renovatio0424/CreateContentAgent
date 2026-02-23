# queue/manager.py
import json
import uuid
import os
from typing import Optional
import config


class ReviewQueue:
    def __init__(self, queue_file: str = config.QUEUE_FILE):
        self.queue_file = queue_file
        self._ensure_file()

    def _ensure_file(self):
        parent = os.path.dirname(self.queue_file)
        if parent:
            os.makedirs(parent, exist_ok=True)
        if not os.path.exists(self.queue_file):
            self._write({})

    def _read(self) -> dict:
        with open(self.queue_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write(self, data: dict):
        with open(self.queue_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def add(self, content_ko: str, content_en: str, seo_meta: dict,
            social_ko: str, social_en: str,
            affiliate_links_ko: list, affiliate_links_en: list) -> str:
        draft_id = str(uuid.uuid4())[:8]
        data = self._read()
        data[draft_id] = {
            "id": draft_id,
            "status": "pending",
            "content_ko": content_ko,
            "content_en": content_en,
            "seo_meta": seo_meta,
            "social_ko": social_ko,
            "social_en": social_en,
            "affiliate_links_ko": affiliate_links_ko,
            "affiliate_links_en": affiliate_links_en,
        }
        self._write(data)
        return draft_id

    def list_pending(self) -> list[dict]:
        data = self._read()
        return [v for v in data.values() if v["status"] == "pending"]

    def get(self, draft_id: str) -> Optional[dict]:
        data = self._read()
        return data.get(draft_id)

    def approve(self, draft_id: str):
        data = self._read()
        if draft_id in data:
            data[draft_id]["status"] = "approved"
            self._write(data)

    def reject(self, draft_id: str):
        data = self._read()
        if draft_id in data:
            del data[draft_id]
            self._write(data)
