# pipeline/state.py
from typing import TypedDict, Optional


class ProductInfo(TypedDict):
    name: str
    price: str
    rating: str
    url: str
    platform: str  # "coupang" | "amazon"


class SeoMeta(TypedDict):
    title: str
    description: str
    keywords: list[str]


class ContentState(TypedDict):
    category: str
    products: list[ProductInfo]
    keywords: list[str]
    outline: str
    content_ko: str
    content_en: str
    affiliate_links_ko: list[str]
    affiliate_links_en: list[str]
    seo_meta: SeoMeta
    social_ko: str
    social_en: str
    draft_id: str
    status: str  # pending|reviewing|approved|published
    error: Optional[str]
