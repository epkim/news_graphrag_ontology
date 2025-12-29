"""Embedding Generator"""
from typing import List
from app.config import settings
from sentence_transformers import SentenceTransformer
from openai import OpenAI


class EmbeddingGenerator:
    """임베딩 생성 클래스"""
    
    def __init__(self):
        self.provider = settings.embedding_provider
        
        if self.provider == "local":
            self.model = SentenceTransformer(settings.embedding_model)
            self.openai_client = None
        elif self.provider == "openai":
            if not settings.openai_api_key:
                raise ValueError("OpenAI 임베딩을 사용하려면 OPENAI_API_KEY가 필요합니다.")
            self.openai_client = OpenAI(api_key=settings.openai_api_key)
            self.model = None
        else:
            raise ValueError(f"지원하지 않는 임베딩 Provider: {self.provider}")
    
    def generate(self, texts: List[str]) -> List[List[float]]:
        """
        텍스트 리스트에 대한 임베딩 생성
        
        Args:
            texts: 임베딩할 텍스트 리스트
            
        Returns:
            임베딩 벡터 리스트
        """
        if self.provider == "local":
            embeddings = self.model.encode(texts, show_progress_bar=False)
            return embeddings.tolist()
        elif self.provider == "openai":
            response = self.openai_client.embeddings.create(
                model=settings.openai_embedding_model,
                input=texts
            )
            return [item.embedding for item in response.data]
        else:
            raise ValueError(f"지원하지 않는 임베딩 Provider: {self.provider}")
    
    def generate_single(self, text: str) -> List[float]:
        """
        단일 텍스트에 대한 임베딩 생성
        
        Args:
            text: 임베딩할 텍스트
            
        Returns:
            임베딩 벡터
        """
        return self.generate([text])[0]

