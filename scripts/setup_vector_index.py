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
            
            # 인덱스 상태 확인 및 완료 대기
            import time
            max_wait_time = 60  # 최대 60초 대기
            wait_interval = 2  # 2초마다 확인
            elapsed_time = 0
            
            while elapsed_time < max_wait_time:
                result = session.run(
                    """
                    SHOW INDEXES
                    YIELD name, type, state, populationPercent
                    WHERE name = 'content-embeddings'
                    RETURN name, type, state, populationPercent
                    """
                )
                
                record = result.single()
                if record:
                    state = record["state"]
                    percent = record.get("populationPercent", 0)
                    print(f"인덱스 상태: {state} ({percent}% 완료)")
                    
                    if state == "ONLINE":
                        print("✅ 인덱스가 준비되었습니다!")
                        break
                    elif state == "FAILED":
                        print("❌ 인덱스 생성 실패!")
                        break
                
                time.sleep(wait_interval)
                elapsed_time += wait_interval
            
            if elapsed_time >= max_wait_time:
                print("⚠️  인덱스 구축이 아직 진행 중입니다. 잠시 후 다시 시도해주세요.")
    
    except Exception as e:
        print(f"에러 발생: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        driver.close()


if __name__ == "__main__":
    create_vector_index()

