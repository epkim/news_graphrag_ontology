"""FastAPI 서버"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.models.schema import QueryRequest, QueryResponse, GraphResponse
from app.retrievers.selector import RetrieverSelector
from app.llm.factory import get_llm_provider

app = FastAPI(title="News GraphRAG Ontology Platform")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 정적 파일 서빙 (프론트엔드)
try:
    app.mount("/static", StaticFiles(directory="frontend"), name="static")
except Exception:
    pass  # frontend 폴더가 없을 수 있음


@app.get("/health")
async def health():
    """헬스 체크"""
    return {"status": "ok"}


@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """
    자연어 질의 처리
    
    Args:
        request: 질의 요청
        
    Returns:
        질의 응답 (답변, 노드, 엣지)
    """
    try:
        # 1. Retriever 선택
        retriever, retriever_name = RetrieverSelector.select(request.query)
        
        # 2. 검색 수행
        nodes, edges, context = retriever.retrieve(request.query)
        
        # 사용된 쿼리 정보 가져오기 (retriever에 쿼리 정보가 있는 경우)
        used_query = getattr(retriever, 'last_query', None) or getattr(retriever, 'last_cypher', None)
        
        # 검색 결과 로깅 (상세 정보)
        try:
            print(f"\n{'='*80}")
            print(f"[SEARCH] 질의: {request.query}")
            print(f"[SEARCH] 사용된 Retriever: {retriever_name}")
            if used_query:
                print(f"[SEARCH] 사용된 쿼리:\n{used_query}")
            print(f"[SEARCH] 초기 검색 결과: 노드 {len(nodes)}개, 엣지 {len(edges)}개")
            
            # 각 노드 정보 로깅
            for i, node in enumerate(nodes, 1):
                try:
                    score = node.properties.get("similarity_score") or node.properties.get("relevance_score")
                    label = str(node.label) if node.label else "N/A"
                    label_display = label[:50] + "..." if len(label) > 50 else label
                    score_display = f"{score:.3f}" if score is not None and isinstance(score, (int, float)) else "N/A"
                    print(f"  노드 {i}: ID={node.id}, 타입={node.type}, 레이블={label_display}, 점수={score_display}")
                except Exception as e:
                    print(f"  노드 {i}: 로깅 오류 - {str(e)}")
        except Exception as e:
            print(f"[SEARCH] 로깅 오류: {str(e)}")
        
        # 3. 검색 결과 필터링 (관련성 높은 노드만 유지)
        # 유사도 점수가 있는 노드만 필터링
        filtered_nodes = []
        filtered_edges = []
        
        for node in nodes:
            try:
                # 유사도 점수가 있으면 임계값 확인, 없으면 포함
                score = node.properties.get("similarity_score") or node.properties.get("relevance_score")
                if score is None or (isinstance(score, (int, float)) and score >= 0.5):  # 기본 임계값
                    filtered_nodes.append(node)
                else:
                    score_display = f"{score:.3f}" if isinstance(score, (int, float)) else str(score)
                    print(f"[FILTER] 노드 제외: ID={node.id}, 타입={node.type}, 점수={score_display} (임계값 미만)")
            except Exception as e:
                # 에러 발생 시 노드 포함 (안전장치)
                print(f"[FILTER] 노드 필터링 오류 (포함): ID={node.id}, 오류={str(e)}")
                filtered_nodes.append(node)
        
        # 필터링된 노드와 연결된 엣지만 유지
        filtered_node_ids = {node.id for node in filtered_nodes}
        for edge in edges:
            if edge.source in filtered_node_ids and edge.target in filtered_node_ids:
                filtered_edges.append(edge)
        
        nodes = filtered_nodes
        edges = filtered_edges
        
        try:
            print(f"[SEARCH] 필터링 후: 노드 {len(nodes)}개, 엣지 {len(edges)}개")
            node_ids = [str(node.id) for node in nodes]
            print(f"[SEARCH] 최종 반환 노드 ID 목록: {node_ids}")
            print(f"{'='*80}\n")
        except Exception as e:
            print(f"[SEARCH] 로깅 오류: {str(e)}")
        
        # 4. LLM으로 답변 생성
        llm = get_llm_provider()
        
        system_prompt = """당신은 뉴스 데이터를 분석하는 AI 어시스턴트입니다.
사용자의 질의에 대해 검색된 뉴스 정보를 바탕으로 정확하고 유용한 답변을 제공하세요.
검색된 정보를 최대한 활용하여 구체적이고 상세한 답변을 제공하세요."""
        
        # 검색된 노드 정보를 상세히 구성
        node_info_parts = []
        for i, node in enumerate(nodes[:10], 1):  # 상위 10개 노드 정보
            node_type = node.type
            node_label = node.label
            properties = node.properties or {}
            
            if node_type == "Article":
                title = properties.get("title", node_label)
                url = properties.get("url", "")
                created_at = properties.get("created_at", "")
                node_info_parts.append(f"{i}. 기사: {title}" + (f" ({created_at})" if created_at else ""))
            elif node_type == "Content":
                text = properties.get("text", node_label)
                score = properties.get("similarity_score") or properties.get("relevance_score")
                score_str = f" (유사도: {score:.3f})" if score else ""
                node_info_parts.append(f"{i}. 콘텐츠: {text[:100]}...{score_str}")
            elif node_type == "Category":
                name = properties.get("name", node_label)
                node_info_parts.append(f"{i}. 카테고리: {name}")
            elif node_type == "Media":
                name = properties.get("name", node_label)
                node_info_parts.append(f"{i}. 언론사: {name}")
        
        node_info = "\n".join(node_info_parts) if node_info_parts else "검색된 노드 정보가 없습니다."
        
        user_prompt = f"""
사용자 질의: {request.query}

검색된 노드 정보 (총 {len(nodes)}개):
{node_info}

검색된 콘텐츠:
{context}

위 정보를 바탕으로 사용자의 질의에 대해 구체적이고 상세한 답변을 제공해주세요.
- 검색된 노드의 정보를 최대한 활용하세요
- 기사 제목, 카테고리, 언론사 등의 정보를 언급하세요
- 검색된 콘텐츠의 내용을 바탕으로 답변하세요
- 검색된 정보가 질의와 관련이 없다면, 그 사실을 명확히 알려주세요
"""
        
        answer = llm.generate(user_prompt, system_prompt=system_prompt)
        
        # LLM 답변 로깅
        try:
            answer_str = str(answer) if answer else ""
            print(f"[LLM] 생성된 답변 길이: {len(answer_str)}자")
            if answer_str:
                preview = answer_str[:200] + "..." if len(answer_str) > 200 else answer_str
                print(f"[LLM] 답변 미리보기: {preview}")
        except Exception as e:
            print(f"[LLM] 로깅 오류: {str(e)}")
        
        # 4. Retriever 종료
        if hasattr(retriever, "close"):
            retriever.close()
        
        # 최종 응답 로깅
        try:
            print(f"[RESPONSE] 최종 반환: 노드 {len(nodes)}개, 엣지 {len(edges)}개")
        except Exception as e:
            print(f"[RESPONSE] 로깅 오류: {str(e)}")
        
        return QueryResponse(
            answer=answer,
            nodes=nodes,
            edges=edges,
            retriever_used=retriever_name,
            context=context
        )
    
    except Exception as e:
        import traceback
        error_detail = str(e)
        error_traceback = traceback.format_exc()
        print(f"\n{'='*80}")
        print(f"[ERROR] 검색 중 오류 발생")
        print(f"[ERROR] 질의: {request.query}")
        print(f"[ERROR] 오류 메시지: {error_detail}")
        print(f"[ERROR] 상세 추적:")
        print(error_traceback)
        print(f"{'='*80}\n")
        raise HTTPException(status_code=500, detail=f"검색 중 오류 발생: {error_detail}")


@app.get("/graph", response_model=GraphResponse)
async def get_graph(limit: int = 100):
    """
    그래프 데이터 조회 (시각화용)
    
    Args:
        limit: 반환할 노드 수 제한
        
    Returns:
        그래프 데이터 (노드, 엣지)
    """
    from neo4j import GraphDatabase
    from app.config import settings
    from app.models.schema import Node, Edge
    
    driver = GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_username, settings.neo4j_password)
    )
    
    try:
        with driver.session() as session:
            # 노드 조회
            result = session.run(
                f"""
                MATCH (n)
                RETURN n
                LIMIT {limit}
                """
            )
            
            nodes = []
            node_ids = set()
            
            for record in result:
                node = record["n"]
                node_id = str(node.id)
                
                if node_id not in node_ids:
                    node_ids.add(node_id)
                    labels = list(node.labels)
                    node_type = labels[0] if labels else "Unknown"
                    properties = dict(node)
                    
                    label = (
                        properties.get("name") or 
                        properties.get("title") or 
                        properties.get("text", "")[:50] or
                        node_id
                    )
                    
                    nodes.append(Node(
                        id=node_id,
                        label=label,
                        type=node_type,
                        properties=properties
                    ))
            
            # 노드 ID 집합 생성
            node_ids_set = {node.id for node in nodes}
            
            # 조회된 노드들 간의 관계 조회
            node_ids_list = [int(n.id) for n in nodes if n.id.isdigit()]
            if not node_ids_list:
                # 노드가 없으면 빈 엣지 반환
                return GraphResponse(nodes=nodes, edges=[])
            
            # 관계 조회: 조회된 노드들 간의 관계 (더 많은 엣지 반환)
            # 먼저 전체 관계 수 확인
            count_result = session.run(
                """
                MATCH (a)-[r]->(b)
                WHERE id(a) IN $node_ids AND id(b) IN $node_ids
                RETURN count(r) as edge_count
                """,
                node_ids=node_ids_list
            )
            edge_count_record = count_result.single()
            total_edge_count = edge_count_record["edge_count"] if edge_count_record else 0
            print(f"[DEBUG] 조회된 노드 {len(node_ids_list)}개 간의 관계 수: {total_edge_count}")
            
            result = session.run(
                """
                MATCH (a)-[r]->(b)
                WHERE id(a) IN $node_ids AND id(b) IN $node_ids
                RETURN r, id(a) as source_id, id(b) as target_id, type(r) as rel_type
                ORDER BY id(r)
                LIMIT $limit
                """,
                node_ids=node_ids_list,
                limit=limit * 5  # 더 많은 엣지 반환
            )
            
            edges = []
            additional_node_ids = set()  # 엣지에서 발견된 추가 노드 ID
            
            for record in result:
                rel = record["r"]
                source_id = str(record["source_id"])
                target_id = str(record["target_id"])
                rel_type = record["rel_type"]
                
                # source와 target 노드가 모두 nodes에 있는지 확인
                if source_id not in node_ids_set:
                    additional_node_ids.add(source_id)
                if target_id not in node_ids_set:
                    additional_node_ids.add(target_id)
                
                # 엣지 추가
                edges.append(Edge(
                    source=source_id,
                    target=target_id,
                    relationship=rel_type,
                    properties=dict(rel) if hasattr(rel, "__dict__") else None
                ))
            
            print(f"[DEBUG] 조회된 엣지 수: {len(edges)}")
            
            # 누락된 노드들 조회 및 추가
            if additional_node_ids:
                missing_ids_list = [int(nid) for nid in additional_node_ids if nid.isdigit()]
                if missing_ids_list:
                    result = session.run(
                        """
                        MATCH (n)
                        WHERE id(n) IN $node_ids
                        RETURN n
                        """,
                        node_ids=missing_ids_list
                    )
                    
                    for record in result:
                        node = record["n"]
                        node_id = str(node.id)
                        
                        if node_id not in node_ids_set:
                            labels = list(node.labels)
                            node_type = labels[0] if labels else "Unknown"
                            properties = dict(node)
                            label = (
                                properties.get("name") or 
                                properties.get("title") or 
                                properties.get("text", "")[:50] or
                                node_id
                            )
                            nodes.append(Node(
                                id=node_id,
                                label=label,
                                type=node_type,
                                properties=properties
                            ))
                            node_ids_set.add(node_id)
            
            # 최종 검증: 엣지의 source/target가 모두 nodes에 있는지 확인
            final_node_ids = {node.id for node in nodes}
            valid_edges = []
            invalid_count = 0
            for edge in edges:
                if edge.source in final_node_ids and edge.target in final_node_ids:
                    valid_edges.append(edge)
                else:
                    invalid_count += 1
                    print(f"[DEBUG] 유효하지 않은 엣지: {edge.source} -> {edge.target} (source 존재: {edge.source in final_node_ids}, target 존재: {edge.target in final_node_ids})")
            
            print(f"[DEBUG] 유효한 엣지: {len(valid_edges)}개, 유효하지 않은 엣지: {invalid_count}개")
            edges = valid_edges
        
        print(f"[DEBUG] 최종 반환: 노드 {len(nodes)}개, 엣지 {len(edges)}개")
        return GraphResponse(nodes=nodes, edges=edges)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        driver.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

