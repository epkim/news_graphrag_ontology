"""OpenAI LLM Provider"""
from typing import List, Optional
from openai import OpenAI
from app.config import settings
from app.llm.base import LLMProvider


class OpenAIProvider(LLMProvider):
    """OpenAI Provider 구현"""
    
    def __init__(self):
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다.")
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = "gpt-4o-mini"
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """텍스트 생성"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7
        )
        return response.choices[0].message.content
    
    def embedding(self, texts: List[str]) -> List[List[float]]:
        """임베딩 생성"""
        response = self.client.embeddings.create(
            model=settings.openai_embedding_model,
            input=texts
        )
        return [item.embedding for item in response.data]

