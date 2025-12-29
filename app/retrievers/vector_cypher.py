"""VectorCypher Retriever"""
from typing import List, Tuple
from neo4j import GraphDatabase
from app.config import settings
from app.etl.embedding_generator import EmbeddingGenerator
from app.models.schema import Node, Edge
from app.retrievers.base import BaseRetriever
from app.retrievers.vector import VectorRetriever


class VectorCypherRetriever(BaseRetriever):
    """벡터 검색 결과를 기반으로 그래프 확장"""
    
    def __init__(self, top_k: int = 5, similarity_threshold: float = 0.5):
        self.driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_username, settings.neo4j_password)
        )
        self.vector_retriever = VectorRetriever(top_k=top_k, similarity_threshold=similarity_threshold)
        self.top_k = top_k
        self.similarity_threshold = similarity_threshold
    
    def close(self):
        """드라이버 종료"""
        self.driver.close()
        self.vector_retriever.close()
    
    def retrieve(self, query: str) -> Tuple[List[Node], List[Edge], str]:
        """벡터 검색 후 그래프 확장"""
        # 1. 벡터 검색으로 관련 Content 노드 찾기
        content_nodes, _, content_context = self.vector_retriever.retrieve(query)
        
        if not content_nodes:
            return [], [], "관련 콘텐츠를 찾을 수 없습니다."
        
        # 2. 찾은 Content 노드에서 Article로 확장
        # Content 노드의 유사도 점수 추출
        # Content 노드의 id는 Neo4j 내부 ID (숫자) 또는 properties.id (UUID 문자열)일 수 있음
        content_scores = {}
        content_neo4j_ids = []  # Neo4j 내부 ID
        content_property_ids = []  # properties.id (UUID)
        
        for node in content_nodes:
            # node.id는 Neo4j 내부 ID (숫자 문자열)
            content_neo4j_ids.append(int(node.id))
            # properties에 id가 있으면 UUID 문자열
            prop_id = node.properties.get("id")
            if prop_id:
                content_property_ids.append(str(prop_id))
            content_scores[node.id] = node.properties.get("similarity_score", 0.0)
        
        print(f"[VECTORCYPHER] Content 노드: Neo4j ID {len(content_neo4j_ids)}개, Property ID {len(content_property_ids)}개")
        
        # 관련 Article만 조회 (불필요한 확장 방지)
        # Content 노드는 Neo4j 내부 ID로 매칭
        cypher = """
        MATCH (c:Content)
        WHERE id(c) IN $content_neo4j_ids
        MATCH (a:Article)-[:HAS_CHUNK]->(c)
        OPTIONAL MATCH (a)-[:BELONGS_TO]->(cat:Category)
        OPTIONAL MATCH (m:Media)-[:PUBLISHED]->(a)
        RETURN DISTINCT a, cat, m, c, id(c) as content_neo4j_id
        ORDER BY id(c)
        """
        
        # 쿼리 정보 저장 (로깅용)
        self.last_query = cypher.strip()
        
        with self.driver.session() as session:
            result = session.run(cypher, content_neo4j_ids=content_neo4j_ids)
            records = list(result)
        print(f"[VECTORCYPHER] 그래프 확장 결과: {len(records)}개 레코드")
        
        nodes = []
        edges = []
        node_ids = set()
        
        # Content 노드 추가
        for node in content_nodes:
            if node.id not in node_ids:
                nodes.append(node)
                node_ids.add(node.id)
        
        # Article, Category, Media 노드 추가 (관련성 높은 것만)
        article_scores = {}  # Article별 최고 유사도 점수
        
        for record in records:
            content_neo4j_id = str(record.get("content_neo4j_id"))
            content_score = content_scores.get(content_neo4j_id, 0.0)
            
            # Article 노드 처리
            article = record.get("a")
            if article:
                article_id = str(article.id)
                # Article의 최고 유사도 점수 업데이트
                if article_id not in article_scores or content_score > article_scores[article_id]:
                    article_scores[article_id] = content_score
                
                if article_id not in node_ids:
                    node_ids.add(article_id)
                    properties = dict(article)
                    nodes.append(Node(
                        id=article_id,
                        label=properties.get("title", article_id),
                        type="Article",
                        properties={**properties, "relevance_score": article_scores[article_id]}
                    ))
            
            # Category 노드 추가 (관련 Article이 있는 경우만)
            if article:
                category = record.get("cat")
                if category:
                    cat_id = str(category.id)
                    if cat_id not in node_ids:
                        node_ids.add(cat_id)
                        properties = dict(category)
                        nodes.append(Node(
                            id=cat_id,
                            label=properties.get("name", cat_id),
                            type="Category",
                            properties=properties
                        ))
                
                # Media 노드 추가 (관련 Article이 있는 경우만)
                media = record.get("m")
                if media:
                    media_id = str(media.id)
                    if media_id not in node_ids:
                        node_ids.add(media_id)
                        properties = dict(media)
                        nodes.append(Node(
                            id=media_id,
                            label=properties.get("name", media_id),
                            type="Media",
                            properties=properties
                        ))
        
        # Content 노드는 이미 추가되어 있음
        
        # 관계 추가
        cypher_rels = """
        MATCH (c:Content)
        WHERE id(c) IN $content_neo4j_ids
        MATCH (a:Article)-[r1:HAS_CHUNK]->(c)
        OPTIONAL MATCH (a)-[r2:BELONGS_TO]->(cat:Category)
        OPTIONAL MATCH (m:Media)-[r3:PUBLISHED]->(a)
        RETURN r1, r2, r3, a, cat, m, c
        """
        
        with self.driver.session() as session:
            result = session.run(cypher_rels, content_neo4j_ids=content_neo4j_ids)
            records = list(result)
        
        for record in records:
            for rel_key in ["r1", "r2", "r3"]:
                rel = record.get(rel_key)
                if rel is None:
                    continue
                
                start_id = str(rel.start_node.id)
                end_id = str(rel.end_node.id)
                
                edges.append(Edge(
                    source=start_id,
                    target=end_id,
                    relationship=rel.type,
                    properties=dict(rel) if hasattr(rel, "__dict__") else None
                ))
        
        # 컨텍스트 생성
        context = content_context
        context += f"\n\n관련 기사 {len([n for n in nodes if n.type == 'Article'])}개 발견"
        
        return nodes, edges, context

