"""Anthropic LLM Provider"""
from typing import List, Optional
from anthropic import Anthropic
from app.config import settings
from app.llm.base import LLMProvider


class AnthropicProvider(LLMProvider):
    """Anthropic Provider 구현"""
    
    def __init__(self):
        if not settings.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY가 설정되지 않았습니다.")
        self.client = Anthropic(api_key=settings.anthropic_api_key)
        self.model = "claude-3-sonnet-20240229"
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """텍스트 생성"""
        system = system_prompt or "You are a helpful assistant."
        
        message = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=system,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return message.content[0].text
    
    def embedding(self, texts: List[str]) -> List[List[float]]:
        """임베딩 생성 (Anthropic은 임베딩 API가 없으므로 OpenAI 사용)"""
        # Anthropic은 임베딩 API를 제공하지 않으므로
        # OpenAI 임베딩을 사용하거나 에러를 발생시킵니다
        raise NotImplementedError(
            "Anthropic은 임베딩 API를 제공하지 않습니다. "
            "임베딩은 OpenAI나 로컬 모델을 사용하세요."
        )

