"""Ollama LLM Provider"""
from typing import List, Optional
import requests
from app.config import settings
from app.llm.base import LLMProvider


class OllamaProvider(LLMProvider):
    """Ollama Provider 구현 (로컬)"""
    
    def __init__(self):
        self.base_url = settings.ollama_base_url
        self.model = settings.ollama_model
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """텍스트 생성"""
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system_prompt or "",
            "stream": False
        }
        
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json().get("response", "")
    
    def embedding(self, texts: List[str]) -> List[List[float]]:
        """임베딩 생성"""
        url = f"{self.base_url}/api/embeddings"
        embeddings = []
        
        for text in texts:
            payload = {
                "model": self.model,
                "prompt": text
            }
            response = requests.post(url, json=payload)
            response.raise_for_status()
            embeddings.append(response.json().get("embedding", []))
        
        return embeddings

