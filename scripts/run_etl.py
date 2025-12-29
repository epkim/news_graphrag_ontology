"""ETL 파이프라인 실행 스크립트"""
import sys
import os
from pathlib import Path

# tokenizers 경고 해결
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tqdm import tqdm
from app.etl.supabase_client import SupabaseClient
from app.etl.chunker import Chunker
from app.etl.embedding_generator import EmbeddingGenerator
from app.etl.neo4j_loader import Neo4jLoader
import uuid


def run_etl(batch_size: int = 10, clear_existing: bool = False, limit: int = None):
    """
    ETL 파이프라인 실행
    
    Args:
        batch_size: 배치 처리 크기
        clear_existing: 기존 데이터 삭제 여부
        limit: 처리할 최대 기사 수 (None이면 전체 처리)
    """
    print("ETL 파이프라인 시작...")
    
    # 클라이언트 초기화
    supabase = SupabaseClient()
    chunker = Chunker()
    embedding_gen = EmbeddingGenerator()
    loader = Neo4jLoader()
    
    try:
        # 기존 데이터 삭제 (옵션)
        if clear_existing:
            print("기존 데이터 삭제 중...")
            loader.clear_all()
        
        # 1. 카테고리 및 언론사 데이터 로드
        print("카테고리 및 언론사 데이터 로드 중...")
        categories = supabase.get_categories()
        media_companies = supabase.get_media_companies()
        
        # 카테고리 노드 생성
        for cat in tqdm(categories, desc="카테고리 생성"):
            loader.create_category(cat["id"], cat["name"])
        
        # 언론사 노드 생성
        for media in tqdm(media_companies, desc="언론사 생성"):
            loader.create_media(media["id"], media["name"])
        
        # 2. 기사 데이터 로드 및 처리
        print("기사 데이터 로드 중...")
        total_count = supabase.get_article_count()
        print(f"전체 기사 수: {total_count}")
        
        # limit이 지정된 경우 처리할 기사 수 제한
        if limit:
            total_count = min(total_count, limit)
            print(f"처리할 기사 수: {total_count}개 (최대 {limit}개로 제한)")
        
        offset = 0
        processed = 0
        
        while offset < total_count:
            # 남은 기사 수 계산
            remaining = total_count - offset
            current_batch_size = min(batch_size, remaining)
            
            articles = supabase.get_articles(limit=current_batch_size, offset=offset)
            
            if not articles:
                break
            
            # 배치 처리
            for article in tqdm(articles, desc=f"기사 처리 ({processed}/{total_count})"):
                # Article 노드 생성
                loader.create_article(
                    article["id"],
                    article["title"],
                    article["url"],
                    str(article["created_at"])
                )
                
                # 관계 생성
                if article.get("media_company_index"):
                    loader.create_published_relationship(
                        article["media_company_index"],
                        article["id"]
                    )
                
                if article.get("news_category_index"):
                    loader.create_belongs_to_relationship(
                        article["id"],
                        article["news_category_index"]
                    )
                
                # Content 청킹 및 임베딩
                if article.get("content"):
                    chunks = chunker.chunk_article(article["content"])
                    
                    if chunks:
                        # 청크 텍스트 추출
                        chunk_texts = [chunk["text"] for chunk in chunks]
                        
                        # 배치 임베딩 생성
                        embeddings = embedding_gen.generate(chunk_texts)
                        
                        # Content 노드 생성 및 관계 생성
                        for chunk, embedding in zip(chunks, embeddings):
                            content_id = str(uuid.uuid4())
                            
                            loader.create_content(
                                content_id,
                                chunk["text"],
                                chunk["chunk_index"],
                                embedding
                            )
                            
                            loader.create_has_chunk_relationship(
                                article["id"],
                                content_id
                            )
                
                processed += 1
            
            offset += batch_size
        
        print(f"\nETL 완료! 총 {processed}개 기사 처리됨.")
    
    except Exception as e:
        print(f"에러 발생: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        supabase.close()
        loader.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="ETL 파이프라인 실행")
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="배치 처리 크기 (기본값: 10)"
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="기존 데이터 삭제 후 시작"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="처리할 최대 기사 수 (기본값: 전체 처리, 예: --limit 200)"
    )
    
    args = parser.parse_args()
    
    run_etl(batch_size=args.batch_size, clear_existing=args.clear, limit=args.limit)

