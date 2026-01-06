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
    Neo4j 그래프 데이터베이스 온톨로지 구조:
    
    ===== 노드 타입 =====
    
    1. Media (언론사)
       - 속성: id (문자열), name (문자열)
       - 예시: {id: "1", name: "조선일보"}
    
    2. Article (뉴스 기사)
       - 속성: id (문자열), title (문자열), url (문자열), created_at (문자열)
       - 예시: {id: "123", title: "AI 기술 발전", url: "https://...", created_at: "2024-01-01"}
    
    3. Category (카테고리)
       - 속성: id (문자열), name (문자열), label (문자열) - name과 label 둘 다 사용 가능
       - 예시: {id: "1", name: "경제", label: "경제"} 또는 {id: "1", label: "경제"}
    
    4. Content (기사 본문 청크)
       - 속성: id (문자열), text (문자열), chunk_index (정수), embedding (벡터)
       - 예시: {id: "uuid-123", text: "기사 본문 내용...", chunk_index: 0}
    
    ===== 관계 타입 =====
    
    1. (Media)-[:PUBLISHED]->(Article)
       - 의미: 언론사가 기사를 발행
       - 예시: (m:Media {name: "조선일보"})-[:PUBLISHED]->(a:Article {title: "..."})
    
    2. (Article)-[:BELONGS_TO]->(Category)
       - 의미: 기사가 카테고리에 속함
       - 예시: (a:Article)-[:BELONGS_TO]->(c:Category {name: "경제"}) 또는 (a:Article)-[:BELONGS_TO]->(c:Category {label: "경제"})
       - 주의: Category는 name 또는 label 속성을 사용할 수 있습니다. 둘 다 확인해야 합니다.
    
    3. (Article)-[:HAS_CHUNK]->(Content)
       - 의미: 기사가 본문 청크를 가짐
       - 예시: (a:Article)-[:HAS_CHUNK]->(c:Content {text: "..."})
    
    ===== 중요 사항 =====
    - 모든 노드의 id는 문자열 타입입니다
    - 관계는 방향성이 있습니다 (->)
    - OPTIONAL MATCH를 사용하여 선택적 관계를 조회할 수 있습니다
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
당신은 Neo4j Cypher 쿼리 전문가입니다. 사용자의 자연어 질의를 정확한 Cypher 쿼리로 변환하세요.

===== 데이터베이스 스키마 =====
{self.ONTOLOGY_SCHEMA}

===== 사용자 질의 =====
{query}

===== 쿼리 생성 규칙 =====
1. MATCH 절을 사용하여 노드와 관계를 찾습니다
2. WHERE 절을 사용하여 조건을 필터링합니다 (예: title CONTAINS '검색어')
3. RETURN 절에서 노드와 관계를 모두 반환해야 합니다 (예: RETURN a, r, b)
   - 중요: COUNT 같은 집계 함수를 사용할 때도 노드와 관계를 함께 반환하세요
   - 예: RETURN c, r, a, COUNT(a) AS count (집계 + 노드/관계 모두 반환)
4. 관계를 반환할 때는 관계 변수를 명시하세요 (예: MATCH (a)-[r:RELATIONSHIP]->(b) RETURN a, r, b)
5. 노드의 id는 문자열로 저장되어 있습니다
6. 쿼리는 간결하고 효율적으로 작성합니다
7. 검색어와 직접 관련된 노드와 관계만 반환하세요
8. LIMIT 절을 사용하여 결과를 최대 100개로 제한하세요
9. OPTIONAL MATCH를 사용하여 선택적 관계를 조회할 수 있습니다
10. Category 노드 검색 시: c.name = '값' OR c.label = '값' 형식으로 둘 다 확인하세요

===== 쿼리 예시 =====

예시 1: "모든 카테고리 목록"
MATCH (c:Category)
RETURN c

예시 2: "경제 카테고리에 속한 기사들"
MATCH (a:Article)-[r:BELONGS_TO]->(c:Category)
WHERE c.name = '경제' OR c.label = '경제'
RETURN a, r, c
LIMIT 100

예시 2-1: "경제 카테고리 기사 갯수" (집계 + 노드 반환)
MATCH (a:Article)-[r:BELONGS_TO]->(c:Category)
WHERE c.name = '경제' OR c.label = '경제'
RETURN c, r, a, COUNT(a) AS article_count
LIMIT 100

예시 3: "조선일보가 발행한 기사들"
MATCH (m:Media {{name: '조선일보'}})-[r1:PUBLISHED]->(a:Article)
OPTIONAL MATCH (a)-[r2:BELONGS_TO]->(c:Category)
RETURN m, r1, a, r2, c
LIMIT 100

예시 4: "AI 관련 기사"
MATCH (a:Article)-[r1:HAS_CHUNK]->(c:Content)
WHERE c.text CONTAINS 'AI' OR a.title CONTAINS 'AI'
OPTIONAL MATCH (a)-[r2:BELONGS_TO]->(cat:Category)
OPTIONAL MATCH (m:Media)-[r3:PUBLISHED]->(a)
RETURN a, r1, c, r2, cat, r3, m
LIMIT 100

===== 주의사항 =====
- 쿼리만 반환하세요 (설명이나 주석 없이)
- 잘못된 쿼리를 생성하지 않도록 주의하세요
- 사용자 질의의 의도를 정확히 파악하여 적절한 쿼리를 생성하세요

Cypher 쿼리:
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
            
            # 쿼리 검증: 기본적인 문법 체크
            if not cypher.strip().upper().startswith(('MATCH', 'CALL', 'WITH')):
                print(f"[TEXT2CYPHER] 잘못된 쿼리 형식 감지, 기본 쿼리 사용")
                raise ValueError("Invalid query format")
            
            # 쿼리 수정: RETURN 절이 없으면 추가
            if 'RETURN' not in cypher.upper():
                print(f"[TEXT2CYPHER] RETURN 절이 없어서 추가")
                # 간단한 수정 시도
                if 'MATCH' in cypher.upper():
                    # MATCH 절에서 변수 추출하여 RETURN 추가
                    import re
                    matches = re.findall(r'\((\w+):', cypher)
                    if matches:
                        variables = list(set(matches))
                        cypher += f"\nRETURN {', '.join(variables)}"
            
        except Exception as e:
            print(f"[TEXT2CYPHER] LLM 오류 또는 쿼리 생성 실패: {e}, 기본 쿼리 사용")
            # LLM 오류 시 기본 쿼리 사용 (관계 포함)
            # 사용자 질의에 키워드가 있으면 WHERE 절 추가
            if any(keyword in query.lower() for keyword in ['경제', '정치', '기술', '스포츠', '문화']):
                category_keyword = next((k for k in ['경제', '정치', '기술', '스포츠', '문화'] if k in query.lower()), None)
                # name과 label 둘 다 확인
                cypher = f"""
                MATCH (a:Article)-[r2:BELONGS_TO]->(cat:Category)
                WHERE cat.name = '{category_keyword}' OR cat.label = '{category_keyword}'
                OPTIONAL MATCH (a)-[r1:HAS_CHUNK]->(c:Content)
                OPTIONAL MATCH (m:Media)-[r3:PUBLISHED]->(a)
                RETURN a, r1, c, r2, cat, r3, m
                LIMIT 20
                """
            else:
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
            
            # 집계 함수만 반환하는 경우 처리
            if records and len(records[0].keys()) > 0:
                record_keys = list(records[0].keys())
                # COUNT 같은 집계 결과만 있고 노드/관계가 없는 경우 감지
                has_aggregation_only = any(
                    key.endswith('_count') or key.endswith('_COUNT') or 
                    'count' in key.lower() or 'COUNT' in key
                    for key in record_keys
                ) and not any(
                    key in ['a', 'c', 'm', 'cat', 'r', 'r1', 'r2', 'r3'] or 
                    ':' in str(records[0].get(key, ''))
                    for key in record_keys
                )
                
                if has_aggregation_only:
                    print(f"[TEXT2CYPHER] 집계 결과만 반환됨, 노드/관계를 포함하도록 쿼리 수정")
                    # 쿼리를 수정하여 노드와 관계도 반환하도록 재시도
                    import re
                    # MATCH 절에서 변수 추출
                    match_vars = re.findall(r'\((\w+):', cypher)
                    rel_vars = re.findall(r'\[(\w+):', cypher)
                    all_vars = list(set(match_vars + rel_vars))
                    
                    if all_vars:
                        # RETURN 절 수정: 노드/관계 + 집계 결과
                        return_match = re.search(r'RETURN\s+(.+?)(?:\s+LIMIT|\s*$)', cypher, re.IGNORECASE | re.DOTALL)
                        if return_match:
                            existing_return = return_match.group(1)
                            # 노드/관계가 없으면 추가
                            if not any(var in existing_return for var in all_vars):
                                new_return = ', '.join(all_vars) + ', ' + existing_return
                                modified_cypher = re.sub(
                                    r'RETURN\s+.+?(?=\s+LIMIT|\s*$)',
                                    f'RETURN {new_return}',
                                    cypher,
                                    flags=re.IGNORECASE | re.DOTALL
                                )
                                print(f"[TEXT2CYPHER] 쿼리 수정: {modified_cypher[:200]}...")
                                try:
                                    result = session.run(modified_cypher)
                                    records = list(result)
                                    cypher = modified_cypher
                                    print(f"[TEXT2CYPHER] 수정된 쿼리 실행 결과: {len(records)}개 레코드")
                                except Exception as e2:
                                    print(f"[TEXT2CYPHER] 수정된 쿼리 실행 오류: {e2}")
        except Exception as e:
            print(f"[TEXT2CYPHER] Cypher 실행 오류: {e}")
            import traceback
            traceback.print_exc()
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

