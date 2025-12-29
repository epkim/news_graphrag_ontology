"""Neo4j Vector Index 생성 스크립트"""
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from neo4j import GraphDatabase
from app.config import settings


def create_vector_index():
    """Content 노드의 embedding 필드에 대한 Vector Index 생성"""
    driver = GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_username, settings.neo4j_password)
    )
    
    try:
        with driver.session() as session:
            # 기존 인덱스 삭제 (있는 경우)
            # 인덱스 이름에 하이픈이 있으면 백틱으로 감싸야 함
            try:
                session.run("DROP INDEX `content-embeddings` IF EXISTS")
                print("기존 인덱스 삭제됨")
            except Exception:
                pass
            
            # Vector Index 생성 (Neo4j 5.x 이상)
            # dimension은 임베딩 벡터 크기에 맞춰야 함
            # sentence-transformers 기본 모델은 보통 384 또는 768 차원
            # OpenAI text-embedding-3-small은 1536 차원
            
            # 먼저 샘플 임베딩으로 차원 확인
            result = session.run(
                """
                MATCH (c:Content)
                WHERE c.embedding IS NOT NULL
                RETURN c.embedding AS embedding
                LIMIT 1
                """
            )
            
            dimension = 384  # 기본값
            record = result.single()
            if record:
                embedding = record["embedding"]
                if embedding:
                    dimension = len(embedding)
                    print(f"임베딩 차원 감지: {dimension}")
            
            # Vector Index 생성
            # 인덱스 이름에 하이픈이 있으면 백틱으로 감싸야 함
            cypher = f"""
            CREATE VECTOR INDEX `content-embeddings` IF NOT EXISTS
            FOR (c:Content)
            ON c.embedding
            OPTIONS {{
                indexConfig: {{
                    `vector.dimensions`: {dimension},
                    `vector.similarity_function`: 'cosine'
                }}
            }}
            """
            
            session.run(cypher)
            print(f"Vector Index 생성 완료! (차원: {dimension})")
            
            # 인덱스 상태 확인
            result = session.run(
                """
                SHOW INDEXES
                YIELD name, type, state
                WHERE name = 'content-embeddings'
                RETURN name, type, state
                """
            )
            
            for record in result:
                print(f"인덱스 상태: {dict(record)}")
    
    except Exception as e:
        print(f"에러 발생: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        driver.close()


if __name__ == "__main__":
    create_vector_index()

