"""LLM Provider Factory"""
from app.config import settings
from app.llm.base import LLMProvider
from app.llm.openai_provider import OpenAIProvider
from app.llm.anthropic_provider import AnthropicProvider
from app.llm.ollama_provider import OllamaProvider


def get_llm_provider() -> LLMProvider:
    """설정에 따라 LLM Provider 인스턴스 반환"""
    provider_name = settings.llm_provider.lower()
    
    if provider_name == "openai":
        return OpenAIProvider()
    elif provider_name == "anthropic":
        return AnthropicProvider()
    elif provider_name == "ollama":
        return OllamaProvider()
    else:
        raise ValueError(f"지원하지 않는 LLM Provider: {provider_name}")

