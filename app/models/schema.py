"""Pydantic 스키마 정의"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class QueryRequest(BaseModel):
    """질의 요청 모델"""
    query: str


class Node(BaseModel):
    """그래프 노드 모델"""
    id: str
    label: str
    type: str
    properties: Dict[str, Any]


class Edge(BaseModel):
    """그래프 엣지 모델"""
    source: str
    target: str
    relationship: str
    properties: Optional[Dict[str, Any]] = None


class QueryResponse(BaseModel):
    """질의 응답 모델"""
    answer: str
    nodes: List[Node]
    edges: List[Edge]
    retriever_used: str
    context: Optional[str] = None


class GraphResponse(BaseModel):
    """그래프 데이터 응답 모델"""
    nodes: List[Node]
    edges: List[Edge]

