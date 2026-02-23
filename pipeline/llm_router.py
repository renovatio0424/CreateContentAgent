# pipeline/llm_router.py
from enum import Enum
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
import config


class LLMTask(str, Enum):
    PRODUCT_RESEARCH = "product_research"
    KEYWORD_ANALYSIS = "keyword_analysis"
    REVIEW_OUTLINE = "review_outline"
    CONTENT_WRITER_KO = "content_writer_ko"
    CONTENT_WRITER_EN = "content_writer_en"
    TRANSLATOR = "translator"
    AFFILIATE_LINKER = "affiliate_linker"
    SEO_OPTIMIZER = "seo_optimizer"
    SOCIAL_SNIPPETS_KO = "social_snippets_ko"
    SOCIAL_SNIPPETS_EN = "social_snippets_en"


_ROUTING = {
    LLMTask.PRODUCT_RESEARCH:   lambda: ChatOpenAI(model="gpt-4o-mini", api_key=config.OPENAI_API_KEY),
    LLMTask.KEYWORD_ANALYSIS:   lambda: ChatOpenAI(model="gpt-4o-mini", api_key=config.OPENAI_API_KEY),
    LLMTask.REVIEW_OUTLINE:     lambda: ChatOllama(model="llama3.1:latest", base_url=config.OLLAMA_BASE_URL),
    LLMTask.CONTENT_WRITER_KO:  lambda: ChatOpenAI(model="gpt-4o", api_key=config.OPENAI_API_KEY),
    LLMTask.CONTENT_WRITER_EN:  lambda: ChatOpenAI(model="gpt-4o", api_key=config.OPENAI_API_KEY),
    LLMTask.TRANSLATOR:         lambda: ChatOpenAI(model="gpt-4o-mini", api_key=config.OPENAI_API_KEY),
    LLMTask.AFFILIATE_LINKER:   lambda: ChatOllama(model="llama3.1:latest", base_url=config.OLLAMA_BASE_URL),
    LLMTask.SEO_OPTIMIZER:      lambda: ChatOllama(model="gemma2:9b", base_url=config.OLLAMA_BASE_URL),
    LLMTask.SOCIAL_SNIPPETS_KO: lambda: ChatOpenAI(model="gpt-4o-mini", api_key=config.OPENAI_API_KEY),
    LLMTask.SOCIAL_SNIPPETS_EN: lambda: ChatOpenAI(model="gpt-4o-mini", api_key=config.OPENAI_API_KEY),
}


def get_llm(task: LLMTask):
    if task not in _ROUTING:
        raise ValueError(f"Unknown LLM task: {task}")
    return _ROUTING[task]()
