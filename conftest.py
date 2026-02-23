# conftest.py
# Set dummy API keys for unit tests so LLM clients can be instantiated
# without real credentials (tests only check type, not actual API calls).
import os

os.environ.setdefault("ANTHROPIC_API_KEY", "test-anthropic-key")
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
os.environ.setdefault("GOOGLE_API_KEY", "test-google-key")
os.environ.setdefault("OLLAMA_BASE_URL", "http://localhost:11434")
