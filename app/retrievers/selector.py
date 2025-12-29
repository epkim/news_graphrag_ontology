"""Retriever 자동 선택 로직"""
from typing import Tuple
from app.retrievers.base import BaseRetriever
from app.retrievers.text2cypher import Text2CypherRetriever
from app.retrievers.vector import VectorRetriever
from app.retrievers.vector_cypher import VectorCypherRetriever


class RetrieverSelector:
    """질의 유형에 따라 적절한 Retriever 선택"""
    
    # 구조적 질문 키워드
    STRUCTURAL_KEYWORDS = [
        "언론사", "카테고리", "분류", "속한", "발행", "관계",
        "어떤", "몇 개", "목록", "리스트", "모든"
    ]
    
    # 분석형 질문 키워드
    ANALYTICAL_KEYWORDS = [
        "요약", "분석", "비교", "트렌드", "패턴", "관련",
        "영향", "원인", "결과", "의미"
    ]
    
    @classmethod
    def select(cls, query: str) -> Tuple[BaseRetriever, str]:
        """
        질의에 따라 Retriever 선택
        
        Args:
            query: 사용자 질의
            
        Returns:
            (retriever, retriever_name) 튜플
        """
        query_lower = query.lower()
        query_length = len(query.split())
        
        # 구조적 질문 판단
        has_structural = any(keyword in query_lower for keyword in cls.STRUCTURAL_KEYWORDS)
        
        # 분석형 질문 판단
        has_analytical = any(keyword in query_lower for keyword in cls.ANALYTICAL_KEYWORDS)
        
        # 선택 로직
        if has_structural and not has_analytical:
            # 관계/구조 질문 → Text2Cypher
            return Text2CypherRetriever(), "text2cypher"
        elif query_length <= 5 and not has_analytical:
            # 짧은 의미 검색 → Vector
            return VectorRetriever(), "vector"
        else:
            # 긴 질문, 분석형 질문 → VectorCypher
            return VectorCypherRetriever(), "vector_cypher"

