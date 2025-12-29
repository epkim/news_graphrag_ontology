"""Base Retriever 추상 클래스"""
from abc import ABC, abstractmethod
from typing import List, Tuple, Dict, Any
from app.models.schema import Node, Edge


class BaseRetriever(ABC):
    """Retriever 기본 인터페이스"""
    
    @abstractmethod
    def retrieve(self, query: str) -> Tuple[List[Node], List[Edge], str]:
        """
        질의에 대한 검색 수행
        
        Args:
            query: 사용자 질의
            
        Returns:
            (nodes, edges, context) 튜플
            - nodes: 검색된 노드 리스트
            - edges: 검색된 엣지 리스트
            - context: 검색 컨텍스트 (LLM에 전달할 텍스트)
        """
        pass

