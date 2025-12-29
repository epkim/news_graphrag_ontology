"""Vector Retriever"""
from typing import List, Tuple
from neo4j import GraphDatabase
from app.config import settings
from app.etl.embedding_generator import EmbeddingGenerator
from app.models.schema import Node, Edge
from app.retrievers.base import BaseRetriever


class VectorRetriever(BaseRetriever):
    """벡터 유사도 기반 검색"""
    
    def __init__(self, top_k: int = 5, similarity_threshold: float = 0.5):
        self.driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_username, settings.neo4j_password)
        )
        self.embedding_generator = EmbeddingGenerator()
        self.top_k = top_k
        self.similarity_threshold = similarity_threshold  # 유사도 임계값
    
    def close(self):
        """드라이버 종료"""
        self.driver.close()
    
    def retrieve(self, query: str) -> Tuple[List[Node], List[Edge], str]:
        """벡터 검색 수행"""
        # 쿼리 임베딩 생성
        query_embedding = self.embedding_generator.generate_single(query)
        
        # Vector Index를 사용한 검색 (Neo4j 5.x 이상)
        cypher = """
        CALL db.index.vector.queryNodes('content-embeddings', $k, $queryVector)
        YIELD node, score
        MATCH (node:Content)
        RETURN node, score
        ORDER BY score DESC
        LIMIT $k
        """
        
        scored_records = []  # 초기화
        used_query = None
        
        try:
            with self.driver.session() as session:
                result = session.run(cypher, queryVector=query_embedding, k=self.top_k)
                records = list(result)
                used_query = f"CALL db.index.vector.queryNodes('content-embeddings', {self.top_k}, [queryVector])"
                
                # Vector Index를 사용하는 경우: score가 이미 반환됨
                for record in records:
                    node = record["node"]
                    score = record["score"]
                    scored_records.append(({"node": node}, score))
                
                # 점수 순으로 정렬
                scored_records.sort(key=lambda x: x[1], reverse=True)
        except Exception as e:
            print(f"[VECTOR] Vector Index 오류: {e}, 대체 쿼리 사용")
            # Vector Index가 없는 경우 대체 쿼리
            # 모든 Content 노드의 embedding과 비교
            cypher = """
            MATCH (c:Content)
            WHERE c.embedding IS NOT NULL
            RETURN c, c.embedding as embedding
            LIMIT 100
            """
            used_query = cypher.strip()
            
            with self.driver.session() as session:
                result = session.run(cypher)
                records = list(result)
            
            # 코사인 유사도 계산
            import numpy as np
            query_vec = np.array(query_embedding)
            
            for record in records:
                content_embedding = record["embedding"]
                if content_embedding:
                    content_vec = np.array(content_embedding)
                    similarity = np.dot(query_vec, content_vec) / (
                        np.linalg.norm(query_vec) * np.linalg.norm(content_vec)
                    )
                    scored_records.append(({"node": record["c"]}, similarity))
            
            # 상위 K개 선택 (유사도 점수 기준)
            scored_records.sort(key=lambda x: x[1], reverse=True)
        
        # 쿼리 정보 저장 (로깅용)
        self.last_query = used_query
        
        nodes = []
        edges = []
        context_parts = []
        
        # 유사도 점수 기반 필터링 및 정렬
        filtered_scored_records = []
        seen_node_ids = set()  # 중복 제거용
        for record_dict, score in scored_records:
            # 유사도 임계값 이상인 것만 포함
            if score >= self.similarity_threshold:
                node_id = str(record_dict["node"].id)
                # 중복 노드 제거
                if node_id not in seen_node_ids:
                    seen_node_ids.add(node_id)
                    filtered_scored_records.append((record_dict, score))
        
        # 상위 K개만 선택
        for record_dict, score in filtered_scored_records[:self.top_k]:
            content_node = record_dict["node"]
            node_id = str(content_node.id)
            properties = dict(content_node)
            
            nodes.append(Node(
                id=node_id,
                label=properties.get("text", "")[:50] + "...",
                type="Content",
                properties={**properties, "similarity_score": score}  # 유사도 점수 포함
            ))
            
            context_parts.append(properties.get("text", ""))
        
        # Content 노드에서 Article로 확장하여 노드와 엣지 추가
        if nodes:
            content_ids = [int(node.id) for node in nodes]
            cypher_expand = """
            MATCH (c:Content)
            WHERE id(c) IN $content_ids
            MATCH (a:Article)-[r:HAS_CHUNK]->(c)
            OPTIONAL MATCH (a)-[:BELONGS_TO]->(cat:Category)
            OPTIONAL MATCH (m:Media)-[:PUBLISHED]->(a)
            RETURN DISTINCT a, cat, m, r, c
            """
            
            try:
                with self.driver.session() as session:
                    result = session.run(cypher_expand, content_ids=content_ids)
                    expand_records = list(result)
                
                # Article, Category, Media 노드 추가
                added_article_ids = set()
                for record in expand_records:
                    # Article 노드 추가
                    article = record.get("a")
                    if article:
                        article_id = str(article.id)
                        if article_id not in added_article_ids:
                            added_article_ids.add(article_id)
                            article_props = dict(article)
                            nodes.append(Node(
                                id=article_id,
                                label=article_props.get("title", article_id),
                                type="Article",
                                properties=article_props
                            ))
                    
                    # Category 노드 추가
                    category = record.get("cat")
                    if category:
                        cat_id = str(category.id)
                        # 중복 체크 (이미 추가된 노드인지 확인)
                        if not any(n.id == cat_id for n in nodes):
                            cat_props = dict(category)
                            nodes.append(Node(
                                id=cat_id,
                                label=cat_props.get("name", cat_id),
                                type="Category",
                                properties=cat_props
                            ))
                    
                    # Media 노드 추가
                    media = record.get("m")
                    if media:
                        media_id = str(media.id)
                        if not any(n.id == media_id for n in nodes):
                            media_props = dict(media)
                            nodes.append(Node(
                                id=media_id,
                                label=media_props.get("name", media_id),
                                type="Media",
                                properties=media_props
                            ))
                    
                    # 엣지 추가
                    rel = record.get("r")
                    if rel:
                        start_id = str(rel.start_node.id)
                        end_id = str(rel.end_node.id)
                        edges.append(Edge(
                            source=start_id,
                            target=end_id,
                            relationship=rel.type,
                            properties=None
                        ))
                
                print(f"[VECTOR] 그래프 확장: Article {len(added_article_ids)}개, 엣지 {len(edges)}개 추가")
            except Exception as e:
                print(f"[VECTOR] 엣지 확장 오류: {e}")
                import traceback
                traceback.print_exc()
        
        # 컨텍스트 생성 (상위 3개만 사용)
        context = "\n\n".join(context_parts[:3])
        if not context:
            context = "검색어와 관련된 콘텐츠를 찾을 수 없습니다."
        
        return nodes, edges, context

