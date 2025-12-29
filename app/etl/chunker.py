"""Content Chunking"""
import re
from typing import List, Dict, Any
from langchain.text_splitter import RecursiveCharacterTextSplitter
from app.config import settings


class Chunker:
    """텍스트 청킹 클래스 - 문맥 기반 분할"""
    
    def __init__(self):
        # 한국어 문맥을 고려한 구분자 우선순위
        # 문단 > 문장 끝(한국어 마침표 포함) > 문장 중간 > 단어 > 문자
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            length_function=len,
            # 한국어 문맥을 고려한 구분자 순서
            separators=[
                "\n\n",           # 문단 구분
                "\n",             # 줄바꿈
                ". ",             # 마침표 + 공백 (한국어/영어)
                "! ",             # 느낌표 + 공백
                "? ",             # 물음표 + 공백
                "。",             # 한국어 마침표
                "！",             # 한국어 느낌표
                "？",             # 한국어 물음표
                " ",              # 공백
                ""                # 문자 단위 (최후의 수단)
            ]
        )
    
    def _split_by_sentence_boundary(self, text: str) -> List[str]:
        """
        문장 경계를 기준으로 텍스트 분할 (한국어 문맥 고려)
        
        Args:
            text: 분할할 텍스트
            
        Returns:
            문장 리스트 (종결 기호 포함)
        """
        # 한국어 문장 종결 기호 패턴 (종결 기호 포함)
        # 마침표, 느낌표, 물음표 (한국어/영어 모두 포함)
        # 종결 기호를 포함하여 분할
        sentence_endings = r'([.!?。！？]\s+)'
        
        # 문장 경계로 분할 (종결 기호 포함)
        parts = re.split(sentence_endings, text)
        
        sentences = []
        current_sentence = ""
        
        for part in parts:
            if not part.strip():
                continue
            
            # 종결 기호인지 확인
            if re.match(r'^[.!?。！？]\s*$', part):
                current_sentence += part
                if current_sentence.strip():
                    sentences.append(current_sentence.strip())
                current_sentence = ""
            else:
                current_sentence += part
        
        # 마지막 문장 추가 (종결 기호가 없는 경우)
        if current_sentence.strip():
            sentences.append(current_sentence.strip())
        
        return sentences
    
    def _merge_sentences_to_chunks(self, sentences: List[str], max_chunk_size: int, overlap: int) -> List[str]:
        """
        문장들을 청크 크기에 맞게 병합 (문맥 보존)
        
        Args:
            sentences: 문장 리스트
            max_chunk_size: 최대 청크 크기
            overlap: 청크 간 겹치는 문자 수
            
        Returns:
            청크 리스트
        """
        if not sentences:
            return []
        
        chunks = []
        current_chunk = []
        current_size = 0
        
        for sentence in sentences:
            sentence_size = len(sentence)
            
            # 현재 청크에 문장을 추가할 수 있는지 확인
            if current_size + sentence_size <= max_chunk_size:
                current_chunk.append(sentence)
                current_size += sentence_size + 1  # +1은 공백
            else:
                # 현재 청크 저장
                if current_chunk:
                    chunk_text = " ".join(current_chunk)
                    chunks.append(chunk_text)
                
                # 오버랩 처리: 이전 청크의 마지막 부분을 포함
                if overlap > 0 and chunks:
                    prev_chunk = chunks[-1]
                    overlap_text = prev_chunk[-overlap:] if len(prev_chunk) > overlap else prev_chunk
                    # 오버랩 텍스트에서 문장 경계 찾기
                    overlap_sentences = self._split_by_sentence_boundary(overlap_text)
                    if overlap_sentences:
                        current_chunk = overlap_sentences[-1:] + [sentence]
                    else:
                        current_chunk = [sentence]
                else:
                    current_chunk = [sentence]
                
                current_size = sentence_size
        
        # 마지막 청크 추가
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            chunks.append(chunk_text)
        
        return chunks
    
    def chunk_text(self, text: str) -> List[str]:
        """
        텍스트를 청크로 분할 (문맥 기반)
        
        Args:
            text: 분할할 텍스트
            
        Returns:
            청크 리스트
        """
        # 1. 문장 경계로 분할
        sentences = self._split_by_sentence_boundary(text)
        
        # 2. 문장들을 청크 크기에 맞게 병합
        chunks = self._merge_sentences_to_chunks(
            sentences,
            max_chunk_size=settings.chunk_size,
            overlap=settings.chunk_overlap
        )
        
        # 3. 만약 청킹이 제대로 안 되었다면 (예: 문장이 너무 긴 경우)
        # 또는 청크가 생성되지 않은 경우 RecursiveCharacterTextSplitter를 대체로 사용
        if not chunks:
            # 청크가 없으면 RecursiveCharacterTextSplitter 사용
            chunks = self.splitter.split_text(text)
        elif any(len(chunk) > settings.chunk_size * 1.5 for chunk in chunks):
            # 너무 긴 청크가 있으면 해당 청크만 RecursiveCharacterTextSplitter로 재분할
            refined_chunks = []
            for chunk in chunks:
                if len(chunk) > settings.chunk_size * 1.5:
                    # 긴 청크를 재분할
                    sub_chunks = self.splitter.split_text(chunk)
                    refined_chunks.extend(sub_chunks)
                else:
                    refined_chunks.append(chunk)
            chunks = refined_chunks
        
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

