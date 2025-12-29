"""Text2Cypher Retriever"""
from typing import List, Tuple
from neo4j import GraphDatabase
from app.config import settings
from app.llm.factory import get_llm_provider
from app.models.schema import Node, Edge
from app.retrievers.base import BaseRetriever


class Text2CypherRetriever(BaseRetriever):
    """자연어를 Cypher로 변환하여 검색"""
    
    ONTOLOGY_SCHEMA = """
    온톨로지 구조:
    
    노드 타입:
    - Media: 언론사 (속성: id, name)
    - Article: 뉴스 기사 (속성: id, title, url, created_at)
    - Category: 카테고리 (속성: id, name)
    - Content: 기사 본문 청크 (속성: id, text, chunk_index, embedding)
    
    관계:
    - (Media)-[:PUBLISHED]->(Article): 언론사가 기사를 발행
    - (Article)-[:BELONGS_TO]->(Category): 기사가 카테고리에 속함
    - (Article)-[:HAS_CHUNK]->(Content): 기사가 본문 청크를 가짐
    """
    
    def __init__(self):
        self.driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_username, settings.neo4j_password)
        )
        self.llm = get_llm_provider()
    
    def close(self):
        """드라이버 종료"""
        self.driver.close()
    
    def _generate_cypher(self, query: str) -> str:
        """자연어 질의를 Cypher로 변환"""
        prompt = f"""
        다음은 Neo4j 그래프 데이터베이스의 온톨로지 구조입니다:
        
        {self.ONTOLOGY_SCHEMA}
        
        사용자 질의: {query}
        
        위 질의에 대한 Cypher 쿼리를 생성하세요. 다음 규칙을 따르세요:
        1. MATCH 절을 사용하여 노드와 관계를 찾습니다
        2. RETURN 절에서 노드와 관계를 모두 반환합니다 (예: RETURN a, r, b)
        3. 관계를 반환할 때는 관계 변수를 명시하세요 (예: MATCH (a)-[r:RELATIONSHIP]->(b) RETURN a, r, b)
        4. 노드의 id는 문자열로 저장되어 있습니다
        5. 쿼리는 간결하고 효율적으로 작성합니다
        6. 검색어와 직접 관련된 노드와 관계만 반환하세요
        7. LIMIT 절을 사용하여 결과를 최대 20개로 제한하세요
        
        Cypher 쿼리만 반환하세요 (설명 없이):
        """
        
        cypher = self.llm.generate(prompt).strip()
        
        # ```cypher 또는 ``` 제거
        if cypher.startswith("```"):
            lines = cypher.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines[-1].strip() == "```":
                lines = lines[:-1]
            cypher = "\n".join(lines).strip()
        
        return cypher
    
    def retrieve(self, query: str) -> Tuple[List[Node], List[Edge], str]:
        """Cypher 쿼리를 생성하고 실행하여 결과 반환"""
        try:
            cypher = self._generate_cypher(query)
            print(f"[TEXT2CYPHER] 생성된 Cypher 쿼리:\n{cypher}")
        except Exception as e:
            print(f"[TEXT2CYPHER] LLM 오류: {e}, 기본 쿼리 사용")
            # LLM 오류 시 기본 쿼리 사용 (관계 포함)
            cypher = """
            MATCH (a:Article)-[r1:HAS_CHUNK]->(c:Content)
            OPTIONAL MATCH (a)-[r2:BELONGS_TO]->(cat:Category)
            OPTIONAL MATCH (m:Media)-[r3:PUBLISHED]->(a)
            RETURN a, r1, c, r2, cat, r3, m
            LIMIT 20
            """
        
        # 쿼리 정보 저장 (로깅용)
        self.last_cypher = cypher
        
        try:
            with self.driver.session() as session:
                result = session.run(cypher)
                records = list(result)
            print(f"[TEXT2CYPHER] 쿼리 실행 결과: {len(records)}개 레코드")
        except Exception as e:
            print(f"[TEXT2CYPHER] Cypher 실행 오류: {e}")
            return [], [], f"Cypher 쿼리 실행 오류: {str(e)}"
        
        nodes = []
        edges = []
        node_ids = set()
        
        # 관계를 먼저 수집하여 노드 ID 추출
        relationship_nodes = set()
        
        for record in records:
            for key in record.keys():
                value = record[key]
                if value is None:
                    continue
                
                # Neo4j Relationship 객체 처리 (먼저 처리하여 관련 노드 ID 수집)
                if hasattr(value, "type") and hasattr(value, "start_node") and hasattr(value, "end_node"):
                    rel_type = value.type
                    start_id = str(value.start_node.id)
                    end_id = str(value.end_node.id)
                    relationship_nodes.add(start_id)
                    relationship_nodes.add(end_id)
                    
                    # 중복 엣지 방지
                    edge_key = f"{start_id}-{end_id}-{rel_type}"
                    if edge_key not in {f"{e.source}-{e.target}-{e.relationship}" for e in edges}:
                        edges.append(Edge(
                            source=start_id,
                            target=end_id,
                            relationship=rel_type,
                            properties=dict(value) if hasattr(value, "__dict__") else None
                        ))
        
        # 노드 처리
        for record in records:
            for key in record.keys():
                value = record[key]
                if value is None:
                    continue
                
                # Neo4j Node 객체 처리
                if hasattr(value, "id") and hasattr(value, "labels"):
                    node_id = str(value.id)
                    if node_id not in node_ids:
                        node_ids.add(node_id)
                        labels = list(value.labels)
                        node_type = labels[0] if labels else "Unknown"
                        properties = dict(value)
                        
                        nodes.append(Node(
                            id=node_id,
                            label=properties.get("name") or properties.get("title") or properties.get("text", "")[:50] or node_id,
                            type=node_type,
                            properties=properties
                        ))
        
        # 컨텍스트 생성
        context = f"검색된 노드 수: {len(nodes)}, 관계 수: {len(edges)}"
        if nodes:
            context += "\n관련 기사:\n"
            for node in nodes[:5]:
                if node.type == "Article":
                    context += f"- {node.properties.get('title', '')}\n"
        
        return nodes, edges, context

