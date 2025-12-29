"""Neo4j 데이터 로더"""
from typing import List, Dict, Any
import uuid
from neo4j import GraphDatabase
from app.config import settings


class Neo4jLoader:
    """Neo4j 데이터 적재 클래스"""
    
    def __init__(self):
        self.driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_username, settings.neo4j_password)
        )
    
    def close(self):
        """드라이버 종료"""
        self.driver.close()
    
    def create_media(self, media_id: int, name: str):
        """Media 노드 생성"""
        with self.driver.session() as session:
            session.run(
                """
                MERGE (m:Media {id: $id})
                SET m.name = $name
                """,
                id=str(media_id),
                name=name
            )
    
    def create_category(self, category_id: int, name: str):
        """Category 노드 생성"""
        with self.driver.session() as session:
            session.run(
                """
                MERGE (c:Category {id: $id})
                SET c.name = $name
                """,
                id=str(category_id),
                name=name
            )
    
    def create_article(self, article_id: int, title: str, url: str, created_at: str):
        """Article 노드 생성"""
        with self.driver.session() as session:
            session.run(
                """
                MERGE (a:Article {id: $id})
                SET a.title = $title,
                    a.url = $url,
                    a.created_at = $created_at
                """,
                id=str(article_id),
                title=title,
                url=url,
                created_at=created_at
            )
    
    def create_content(self, content_id: str, text: str, chunk_index: int, embedding: List[float]):
        """Content 노드 생성 (임베딩 포함)"""
        with self.driver.session() as session:
            session.run(
                """
                MERGE (c:Content {id: $id})
                SET c.text = $text,
                    c.chunk_index = $chunk_index,
                    c.embedding = $embedding
                """,
                id=content_id,
                text=text,
                chunk_index=chunk_index,
                embedding=embedding
            )
    
    def create_published_relationship(self, media_id: int, article_id: int):
        """PUBLISHED 관계 생성"""
        with self.driver.session() as session:
            session.run(
                """
                MATCH (m:Media {id: $media_id})
                MATCH (a:Article {id: $article_id})
                MERGE (m)-[:PUBLISHED]->(a)
                """,
                media_id=str(media_id),
                article_id=str(article_id)
            )
    
    def create_belongs_to_relationship(self, article_id: int, category_id: int):
        """BELONGS_TO 관계 생성"""
        with self.driver.session() as session:
            session.run(
                """
                MATCH (a:Article {id: $article_id})
                MATCH (c:Category {id: $category_id})
                MERGE (a)-[:BELONGS_TO]->(c)
                """,
                article_id=str(article_id),
                category_id=str(category_id)
            )
    
    def create_has_chunk_relationship(self, article_id: int, content_id: str):
        """HAS_CHUNK 관계 생성"""
        with self.driver.session() as session:
            session.run(
                """
                MATCH (a:Article {id: $article_id})
                MATCH (c:Content {id: $content_id})
                MERGE (a)-[:HAS_CHUNK]->(c)
                """,
                article_id=str(article_id),
                content_id=content_id
            )
    
    def batch_create_nodes(self, nodes: List[Dict[str, Any]]):
        """배치로 노드 생성 (성능 최적화)"""
        with self.driver.session() as session:
            for node in nodes:
                node_type = node["type"]
                if node_type == "Media":
                    self.create_media(node["id"], node["name"])
                elif node_type == "Category":
                    self.create_category(node["id"], node["name"])
                elif node_type == "Article":
                    self.create_article(
                        node["id"],
                        node["title"],
                        node["url"],
                        node["created_at"]
                    )
                elif node_type == "Content":
                    self.create_content(
                        node["id"],
                        node["text"],
                        node["chunk_index"],
                        node["embedding"]
                    )
    
    def clear_all(self):
        """모든 노드와 관계 삭제 (테스트용)"""
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")

