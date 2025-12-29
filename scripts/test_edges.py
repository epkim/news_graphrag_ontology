#!/usr/bin/env python3
"""
Neo4j에서 엣지(관계)가 있는지 확인하는 스크립트
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from neo4j import GraphDatabase
from app.config import settings

def test_edges():
    """Neo4j에서 엣지 확인"""
    driver = GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_username, settings.neo4j_password)
    )
    
    try:
        with driver.session() as session:
            # 전체 관계 수 확인
            result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
            total_edges = result.single()["count"]
            print(f"전체 관계 수: {total_edges}")
            
            # 노드 수 확인
            result = session.run("MATCH (n) RETURN count(n) as count")
            total_nodes = result.single()["count"]
            print(f"전체 노드 수: {total_nodes}")
            
            # 관계 타입별 개수
            result = session.run("""
                MATCH ()-[r]->()
                RETURN type(r) as rel_type, count(r) as count
                ORDER BY count DESC
            """)
            print("\n관계 타입별 개수:")
            for record in result:
                print(f"  {record['rel_type']}: {record['count']}개")
            
            # 샘플 관계 조회
            result = session.run("""
                MATCH (a)-[r]->(b)
                RETURN id(a) as source_id, id(b) as target_id, type(r) as rel_type, 
                       labels(a) as source_labels, labels(b) as target_labels
                LIMIT 10
            """)
            print("\n샘플 관계 (최대 10개):")
            for record in result:
                print(f"  {record['source_id']} ({record['source_labels']}) -[{record['rel_type']}]-> {record['target_id']} ({record['target_labels']})")
            
            # 최근 10개 노드 간의 관계 확인
            result = session.run("""
                MATCH (n)
                RETURN id(n) as node_id
                LIMIT 10
            """)
            node_ids = [record["node_id"] for record in result]
            
            if node_ids:
                result = session.run("""
                    MATCH (a)-[r]->(b)
                    WHERE id(a) IN $node_ids AND id(b) IN $node_ids
                    RETURN count(r) as count
                """, node_ids=node_ids)
                edge_count = result.single()["count"]
                print(f"\n최근 10개 노드 간의 관계 수: {edge_count}")
                
                if edge_count > 0:
                    result = session.run("""
                        MATCH (a)-[r]->(b)
                        WHERE id(a) IN $node_ids AND id(b) IN $node_ids
                        RETURN id(a) as source_id, id(b) as target_id, type(r) as rel_type
                        LIMIT 5
                    """, node_ids=node_ids)
                    print("샘플 관계:")
                    for record in result:
                        print(f"  {record['source_id']} -[{record['rel_type']}]-> {record['target_id']}")
                else:
                    print("⚠️  최근 10개 노드 간에 관계가 없습니다!")
                    print("   전체 그래프에서 관계를 확인해보세요.")
            
    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()
    finally:
        driver.close()

if __name__ == "__main__":
    test_edges()

