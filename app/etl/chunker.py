"""Content Chunking"""
from typing import List, Dict, Any
from langchain.text_splitter import RecursiveCharacterTextSplitter
from app.config import settings


class Chunker:
    """텍스트 청킹 클래스"""
    
    def __init__(self):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
    
    def chunk_text(self, text: str) -> List[str]:
        """
        텍스트를 청크로 분할
        
        Args:
            text: 분할할 텍스트
            
        Returns:
            청크 리스트
        """
        chunks = self.splitter.split_text(text)
        return chunks
    
    def chunk_article(self, content: str) -> List[Dict[str, Any]]:
        """
        기사 본문을 청크로 분할하고 인덱스 추가
        
        Args:
            content: 기사 본문
            
        Returns:
            청크 딕셔너리 리스트 (text, chunk_index 포함)
        """
        chunks = self.chunk_text(content)
        return [
            {"text": chunk, "chunk_index": idx}
            for idx, chunk in enumerate(chunks)
        ]

