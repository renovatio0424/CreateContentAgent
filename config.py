import os
from dotenv import load_dotenv

load_dotenv(override=True)

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

WORDPRESS_KO_URL = os.getenv("WORDPRESS_KO_URL", "")
WORDPRESS_KO_USER = os.getenv("WORDPRESS_KO_USER", "")
WORDPRESS_KO_PASSWORD = os.getenv("WORDPRESS_KO_PASSWORD", "")

WORDPRESS_EN_URL = os.getenv("WORDPRESS_EN_URL", "")
WORDPRESS_EN_USER = os.getenv("WORDPRESS_EN_USER", "")
WORDPRESS_EN_PASSWORD = os.getenv("WORDPRESS_EN_PASSWORD", "")

AMAZON_ACCESS_KEY = os.getenv("AMAZON_ACCESS_KEY", "")
AMAZON_SECRET_KEY = os.getenv("AMAZON_SECRET_KEY", "")
AMAZON_PARTNER_TAG = os.getenv("AMAZON_PARTNER_TAG", "")

COUPANG_AFFILIATE_ID = os.getenv("COUPANG_AFFILIATE_ID", "")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

QUEUE_FILE = "queue/reviews.json"
