"""LLM Provider 추상 인터페이스"""
from abc import ABC, abstractmethod
from typing import List, Optional


class LLMProvider(ABC):
    """LLM Provider 기본 인터페이스"""
    
    @abstractmethod
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        텍스트 생성
        
        Args:
            prompt: 사용자 프롬프트
            system_prompt: 시스템 프롬프트 (선택)
            
        Returns:
            생성된 텍스트
        """
        pass
    
    @abstractmethod
    def embedding(self, texts: List[str]) -> List[List[float]]:
        """
        텍스트 임베딩 생성
        
        Args:
            texts: 임베딩할 텍스트 리스트
            
        Returns:
            임베딩 벡터 리스트
        """
        pass

