// API 기본 URL
const API_BASE_URL = 'http://localhost:8000';

// Cytoscape 인스턴스
let cy = null;

// 전체 그래프 데이터 (항상 유지)
let fullGraphData = { nodes: [], edges: [] };

// 검색 히스토리
let searchHistory = JSON.parse(localStorage.getItem('searchHistory') || '[]');

// 초기화
document.addEventListener('DOMContentLoaded', () => {
    initGraph();
    initEventListeners();
    loadHistory();
    // 페이지 최초 진입 시 전체 그래프 로드 (더 많은 노드 표시)
    loadGraph(200);
});

// 그래프 초기화
function initGraph() {
    cy = cytoscape({
        container: document.getElementById('cy'),
        elements: [],
        style: [
            {
                selector: 'node',
                style: {
                    'background-color': '#667eea',
                    'label': '',  // 레이블 숨김
                    'width': 30,
                    'height': 30,
                    'font-size': '10px',
                    'text-valign': 'center',
                    'text-halign': 'center',
                    'color': '#333',
                    'text-wrap': 'wrap',
                    'text-max-width': '100px',
                    'border-width': 2,
                    'border-color': '#fff'
                }
            },
            {
                selector: 'node[type="Article"]',
                style: {
                    'background-color': '#48bb78'
                }
            },
            {
                selector: 'node[type="Media"]',
                style: {
                    'background-color': '#ed8936'
                }
            },
            {
                selector: 'node[type="Category"]',
                style: {
                    'background-color': '#9f7aea'
                }
            },
            {
                selector: 'node[type="Content"]',
                style: {
                    'background-color': '#4299e1',
                    'width': 20,
                    'height': 20
                }
            },
            {
                selector: 'node.highlighted',
                style: {
                    'border-width': 3,
                    'border-color': '#f56565',
                    'opacity': 1
                }
            },
            {
                selector: 'node.inactive',
                style: {
                    'opacity': 0.3,
                    'background-color': '#999',
                    'border-color': '#666'
                }
            },
            {
                selector: 'edge',
                style: {
                    'width': 4,
                    'line-color': '#666',
                    'target-arrow-color': '#666',
                    'target-arrow-shape': 'triangle',
                    'target-arrow-size': 12,
                    'curve-style': 'bezier',
                    'label': 'data(relationship)',
                    'font-size': '11px',
                    'font-weight': 'bold',
                    'text-rotation': 'autorotate',
                    'text-margin-y': -10,
                    'text-background-color': '#fff',
                    'text-background-opacity': 0.9,
                    'text-background-padding': '4px',
                    'text-border-color': '#666',
                    'text-border-width': 1,
                    'opacity': 1.0,
                    'text-outline-color': '#fff',
                    'text-outline-width': 2,
                    'line-style': 'solid',
                    'z-index': 1,
                    'display': 'element',
                    'visibility': 'visible'
                }
            },
            {
                selector: 'edge:selected',
                style: {
                    'width': 4,
                    'line-color': '#f56565',
                    'target-arrow-color': '#f56565',
                    'opacity': 1
                }
            },
            {
                selector: 'edge.highlighted',
                style: {
                    'width': 4,
                    'line-color': '#f56565',
                    'target-arrow-color': '#f56565',
                    'opacity': 1
                }
            },
            {
                selector: 'edge.inactive',
                style: {
                    'opacity': 0.2,
                    'line-color': '#ccc',
                    'target-arrow-color': '#ccc'
                }
            },
            {
                selector: 'node:hover',
                style: {
                    'width': 40,
                    'height': 40,
                    'border-width': 3,
                    'border-color': '#f56565'
                }
            }
        ],
        layout: {
            name: 'cose-bilkent',
            idealEdgeLength: 100,
            nodeRepulsion: 4500,
            edgeElasticity: 0.45,
            nestingFactor: 0.1,
            gravity: 0.25,
            numIter: 2500,
            tile: true,
            animate: true,
            animationDuration: 1000,
            fit: true,
            padding: 30
        }
    });
    
    // 노드 호버 이벤트 추가
    setupNodeHoverEvents();
}

// 노드 호버 이벤트 설정
function setupNodeHoverEvents() {
    if (!cy) return;
    
    let tooltip = null;
    
    // 툴팁 생성
    function createTooltip() {
        if (tooltip) return tooltip;
        tooltip = document.createElement('div');
        tooltip.id = 'node-tooltip';
        tooltip.style.cssText = `
            position: absolute;
            background: rgba(0, 0, 0, 0.9);
            color: white;
            padding: 12px;
            border-radius: 6px;
            font-size: 12px;
            max-width: 300px;
            z-index: 10000;
            pointer-events: none;
            display: none;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        `;
        document.body.appendChild(tooltip);
        return tooltip;
    }
    
    // 노드 호버 시
    cy.on('mouseover', 'node', function(evt) {
        const node = evt.target;
        const nodeData = node.data();
        const nodeProps = nodeData.properties || {};
        
        // 툴팁 내용 생성
        let tooltipContent = `<div style="font-weight: bold; margin-bottom: 8px; color: #667eea;">${nodeData.type || 'Node'}</div>`;
        tooltipContent += `<div style="margin-bottom: 4px;"><strong>ID:</strong> ${nodeData.id}</div>`;
        
        if (nodeData.label && nodeData.label !== nodeData.id) {
            tooltipContent += `<div style="margin-bottom: 4px;"><strong>Label:</strong> ${nodeData.label}</div>`;
        }
        
        // 속성 표시
        const importantProps = ['name', 'title', 'text', 'url', 'category', 'media_name'];
        const displayedProps = {};
        
        importantProps.forEach(prop => {
            if (nodeProps[prop] !== undefined && nodeProps[prop] !== null) {
                let value = String(nodeProps[prop]);
                if (value.length > 100) {
                    value = value.substring(0, 100) + '...';
                }
                displayedProps[prop] = value;
            }
        });
        
        // 나머지 속성도 표시 (최대 5개)
        const otherProps = Object.keys(nodeProps).filter(p => !importantProps.includes(p)).slice(0, 5);
        otherProps.forEach(prop => {
            if (nodeProps[prop] !== undefined && nodeProps[prop] !== null) {
                let value = String(nodeProps[prop]);
                if (value.length > 50) {
                    value = value.substring(0, 50) + '...';
                }
                displayedProps[prop] = value;
            }
        });
        
        Object.entries(displayedProps).forEach(([key, value]) => {
            tooltipContent += `<div style="margin-bottom: 4px;"><strong>${key}:</strong> ${value}</div>`;
        });
        
        // 툴팁 표시
        const tooltipEl = createTooltip();
        tooltipEl.innerHTML = tooltipContent;
        tooltipEl.style.display = 'block';
        
        // 마우스 위치에 툴팁 배치
        const pos = evt.renderedPosition || evt.position;
        const containerPos = document.getElementById('cy').getBoundingClientRect();
        tooltipEl.style.left = (containerPos.left + pos.x + 15) + 'px';
        tooltipEl.style.top = (containerPos.top + pos.y - 15) + 'px';
    });
    
    // 노드에서 마우스 벗어날 때
    cy.on('mouseout', 'node', function() {
        if (tooltip) {
            tooltip.style.display = 'none';
        }
    });
    
    // 엣지 호버 시
    cy.on('mouseover', 'edge', function(evt) {
        const edge = evt.target;
        const edgeData = edge.data();
        
        const tooltipEl = createTooltip();
        let tooltipContent = `<div style="font-weight: bold; margin-bottom: 8px; color: #667eea;">관계</div>`;
        tooltipContent += `<div style="margin-bottom: 4px;"><strong>Type:</strong> ${edgeData.relationship || 'RELATED'}</div>`;
        tooltipContent += `<div style="margin-bottom: 4px;"><strong>From:</strong> ${edgeData.source}</div>`;
        tooltipContent += `<div style="margin-bottom: 4px;"><strong>To:</strong> ${edgeData.target}</div>`;
        
        if (edgeData.properties) {
            Object.entries(edgeData.properties).forEach(([key, value]) => {
                tooltipContent += `<div style="margin-bottom: 4px;"><strong>${key}:</strong> ${value}</div>`;
            });
        }
        
        tooltipEl.innerHTML = tooltipContent;
        tooltipEl.style.display = 'block';
        
        const pos = evt.renderedPosition || evt.position;
        const containerPos = document.getElementById('cy').getBoundingClientRect();
        tooltipEl.style.left = (containerPos.left + pos.x + 15) + 'px';
        tooltipEl.style.top = (containerPos.top + pos.y - 15) + 'px';
    });
    
    cy.on('mouseout', 'edge', function() {
        if (tooltip) {
            tooltip.style.display = 'none';
        }
    });
    
    // 그래프에서 마우스 이동 시 툴팁 위치 업데이트
    cy.on('tap', 'node', function(evt) {
        // 클릭 시에도 툴팁 표시 (선택적)
    });
}

// 이벤트 리스너 초기화
function initEventListeners() {
    document.getElementById('searchBtn').addEventListener('click', handleSearch);
    document.getElementById('queryInput').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            handleSearch();
        }
    });
    document.getElementById('refreshGraphBtn').addEventListener('click', () => loadGraph(200));
    document.getElementById('clearGraphBtn').addEventListener('click', clearGraph);
}

// 검색 처리
async function handleSearch() {
    const query = document.getElementById('queryInput').value.trim();
    if (!query) {
        alert('질의를 입력하세요.');
        return;
    }
    
    const searchBtn = document.getElementById('searchBtn');
    const loading = document.getElementById('loading');
    const answerBox = document.getElementById('answer');
    const retrieverInfo = document.getElementById('retrieverInfo');
    
    // UI 업데이트
    searchBtn.disabled = true;
    loading.style.display = 'block';
    answerBox.innerHTML = '';
    retrieverInfo.textContent = '';
    
    try {
        const response = await fetch(`${API_BASE_URL}/query`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ query })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // 검색 결과 상세 로깅
        console.log('[SEARCH] 검색 결과:', {
            query: query,
            retriever: data.retriever_used,
            nodes_count: data.nodes?.length || 0,
            edges_count: data.edges?.length || 0,
            nodes: data.nodes?.map(n => ({
                id: n.id,
                type: n.type,
                label: n.label,
                score: n.properties?.similarity_score || n.properties?.relevance_score || 'N/A'
            })) || []
        });
        
        // 답변 표시
        answerBox.innerHTML = `<p>${data.answer.replace(/\n/g, '<br>')}</p>`;
        
        // Retriever 정보 표시
        retrieverInfo.textContent = `사용된 검색 전략: ${data.retriever_used} | 검색된 노드: ${data.nodes?.length || 0}개`;
        
        // 검색 결과 노드 하이라이팅 (전체 그래프 유지)
        highlightSearchResults(data.nodes, data.edges);
        
        // 히스토리에 추가
        addToHistory(query, data.answer);
        
    } catch (error) {
        console.error('Error:', error);
        answerBox.innerHTML = `<p style="color: red;">에러 발생: ${error.message}</p>`;
    } finally {
        searchBtn.disabled = false;
        loading.style.display = 'none';
    }
}

// 검색 결과 하이라이팅 (전체 그래프 유지)
function highlightSearchResults(searchNodes, searchEdges) {
    if (!cy) return;
    
    console.log('[HIGHLIGHT] 하이라이팅 시작:', {
        search_nodes_count: searchNodes?.length || 0,
        search_edges_count: searchEdges?.length || 0,
        total_nodes_in_graph: cy.nodes().length,
        total_edges_in_graph: cy.edges().length
    });
    
    if (!searchNodes || searchNodes.length === 0) {
        console.warn('[HIGHLIGHT] 검색 결과 노드가 없습니다!');
        return;
    }
    
    // 검색 결과 노드 ID 집합
    const searchNodeIds = new Set(searchNodes.map(n => String(n.id)));
    
    console.log('[HIGHLIGHT] 검색 결과 노드 ID:', Array.from(searchNodeIds));
    
    // Cytoscape 그래프에 있는 노드 ID 집합
    const existingNodeIds = new Set(cy.nodes().map(n => n.id()));
    console.log('[HIGHLIGHT] Cytoscape 그래프 노드 ID 샘플:', Array.from(existingNodeIds).slice(0, 10));
    
    // 검색 결과 노드 중 그래프에 없는 노드 찾기
    const missingNodeIds = Array.from(searchNodeIds).filter(id => !existingNodeIds.has(id));
    console.log('[HIGHLIGHT] 그래프에 없는 검색 결과 노드:', missingNodeIds);
    
    // 없는 노드들을 그래프에 추가
    if (missingNodeIds.length > 0) {
        const nodesToAdd = searchNodes.filter(n => missingNodeIds.includes(String(n.id)));
        const cyNodesToAdd = nodesToAdd.map(node => {
            const nodeId = String(node.id);
            const { id: originalId, ...restProperties } = node.properties || {};
            return {
                data: {
                    id: nodeId,
                    label: node.label || nodeId,
                    type: node.type || 'Unknown',
                    originalId: originalId,
                    ...restProperties
                },
                classes: ''
            };
        });
        
        console.log('[HIGHLIGHT] 그래프에 추가할 노드:', cyNodesToAdd.length, '개');
        cy.add(cyNodesToAdd);
        
        // 추가된 노드의 엣지도 추가
        if (searchEdges && searchEdges.length > 0) {
            const edgesToAdd = searchEdges
                .filter(edge => {
                    const sourceId = String(edge.source);
                    const targetId = String(edge.target);
                    return searchNodeIds.has(sourceId) && searchNodeIds.has(targetId);
                })
                .map((edge, index) => {
                    const sourceId = String(edge.source);
                    const targetId = String(edge.target);
                    const relationship = edge.relationship || 'RELATED';
                    const edgeId = `${sourceId}-${targetId}-${relationship}-${index}`;
                    
                    // 엣지가 이미 존재하는지 확인
                    const existingEdge = cy.edges().filter(e => 
                        e.source().id() === sourceId && 
                        e.target().id() === targetId &&
                        e.data('relationship') === relationship
                    );
                    
                    if (existingEdge.length > 0) {
                        return null; // 이미 존재
                    }
                    
                    return {
                        data: {
                            id: edgeId,
                            source: sourceId,
                            target: targetId,
                            relationship: relationship,
                            label: relationship
                        }
                    };
                })
                .filter(e => e !== null);
            
            if (edgesToAdd.length > 0) {
                console.log('[HIGHLIGHT] 그래프에 추가할 엣지:', edgesToAdd.length, '개');
                cy.add(edgesToAdd);
            }
        }
        
        // 노드 추가 후 즉시 레이아웃은 실행하지 않음 (마지막에 통합 처리)
        // 대신 노드가 추가되었음을 표시
        if (missingNodeIds.length > 0) {
            console.log('[HIGHLIGHT] 추가된 노드:', missingNodeIds.length, '개 (레이아웃은 마지막에 통합 처리)');
        }
    }
    
    // 검색 결과 노드의 관련성 점수 추출
    const nodeScores = {};
    searchNodes.forEach(node => {
        const score = node.properties?.similarity_score || node.properties?.relevance_score || 1.0;
        nodeScores[String(node.id)] = score;
    });
    
    console.log('[HIGHLIGHT] 노드 점수:', nodeScores);
    
    // 모든 노드의 하이라이팅 상태 업데이트
    let highlightedCount = 0;
    let inactiveCount = 0;
    
    cy.nodes().forEach(node => {
        const nodeId = node.id();
        if (searchNodeIds.has(nodeId)) {
            // 검색 결과 노드: 관련성 점수에 따라 하이라이팅 강도 조절
            node.removeClass('inactive');
            node.addClass('highlighted');
            highlightedCount++;
            
            // 관련성 점수가 높으면 더 강하게 표시
            const score = nodeScores[nodeId] || 1.0;
            if (score >= 0.7) {
                node.style({
                    'border-width': 4,
                    'border-color': '#f56565',
                    'width': 35,
                    'height': 35
                });
            } else {
                node.style({
                    'border-width': 3,
                    'border-color': '#f56565',
                    'width': 30,
                    'height': 30
                });
            }
        } else {
            // 검색 결과가 아닌 노드: 비활성화
            node.removeClass('highlighted');
            node.addClass('inactive');
            inactiveCount++;
            node.style({
                'border-width': 2,
                'width': 30,
                'height': 30
            });
        }
    });
    
    console.log('[HIGHLIGHT] 하이라이팅 완료:', {
        highlighted_nodes: highlightedCount,
        inactive_nodes: inactiveCount,
        expected_highlighted: searchNodeIds.size
    });
    
    if (highlightedCount === 0) {
        console.error('[HIGHLIGHT] 경고: 하이라이팅된 노드가 없습니다!');
        console.error('[HIGHLIGHT] Cytoscape 노드 ID 샘플:', cy.nodes().slice(0, 5).map(n => n.id()));
        console.error('[HIGHLIGHT] 검색 결과 노드 ID:', Array.from(searchNodeIds));
    }
    
    // 검색 결과 엣지 하이라이팅
    const searchEdgeIds = new Set();
    searchEdges.forEach(edge => {
        const edgeId = `${edge.source}-${edge.target}-${edge.relationship}`;
        searchEdgeIds.add(edgeId);
    });
    
    cy.edges().forEach(edge => {
        const sourceId = edge.source().id();
        const targetId = edge.target().id();
        const relationship = edge.data('relationship') || '';
        const edgeId = `${sourceId}-${targetId}-${relationship}`;
        
        const isSearchEdge = searchNodeIds.has(sourceId) && searchNodeIds.has(targetId);
        
        if (isSearchEdge) {
            edge.removeClass('inactive');
            edge.addClass('highlighted');
            edge.style({
                'width': 4,
                'opacity': 1,
                'line-color': '#f56565',
                'target-arrow-color': '#f56565'
            });
        } else {
            edge.removeClass('highlighted');
            edge.addClass('inactive');
            edge.style({
                'width': 3,
                'opacity': 0.2,
                'line-color': '#ccc',
                'target-arrow-color': '#ccc'
            });
        }
    });
    
    // 관련성 높은 노드로 줌 인
    const highlightedNodes = cy.nodes('.highlighted');
    if (highlightedNodes.length > 0) {
        console.log('[HIGHLIGHT] 하이라이팅된 노드로 줌 인:', highlightedNodes.length, '개');
        cy.animate({
            fit: {
                eles: highlightedNodes,
                padding: 150
            },
            duration: 500
        });
    } else {
        // 하이라이팅된 노드가 없으면 전체 그래프에 맞춤
        console.log('[HIGHLIGHT] 하이라이팅된 노드가 없어 전체 그래프에 맞춤');
        cy.fit(undefined, 50);
    }
    
    // 노드가 추가된 경우 강제로 레이아웃 업데이트 및 표시
    if (missingNodeIds.length > 0) {
        console.log('[HIGHLIGHT] 추가된 노드 표시를 위한 최종 레이아웃 실행');
        // 짧은 레이아웃 실행으로 추가된 노드가 보이도록
        setTimeout(() => {
            const quickLayout = cy.layout({
                name: 'cose-bilkent',
                idealEdgeLength: 80,
                nodeRepulsion: 4000,
                numIter: 500,
                animate: true,
                animationDuration: 300,
                fit: highlightedNodes.length > 0 ? {
                    eles: highlightedNodes,
                    padding: 100
                } : true
            });
            quickLayout.run();
        }, 100);
    }
}

// 그래프 업데이트 (전체 그래프 로드)
function updateGraph(nodes, edges) {
    if (!cy) return;
    
    try {
        // 기존 요소 제거
        cy.elements().remove();
        
        if (!nodes || nodes.length === 0) {
            console.warn('노드 데이터가 없습니다.');
            return;
        }
        
        // 노드 ID 집합 생성 (엣지 검증용)
        const nodeIdSet = new Set(nodes.map(node => String(node.id)));
        
        // 노드 추가 (모든 ID를 문자열로 통일)
        // 주의: properties에 'id'가 있으면 덮어쓰지 않도록 처리
        const cyNodes = nodes.map(node => {
            const nodeId = String(node.id);
            const properties = { ...(node.properties || {}) };
            // properties의 id를 제거 (Cytoscape의 data.id와 충돌 방지)
            const { id: originalId, ...restProperties } = properties;
            
            return {
                data: {
                    id: nodeId,  // 항상 API에서 받은 node.id 사용 (Neo4j 내부 ID)
                    label: node.label || nodeId,
                    type: node.type || 'Unknown',
                    ...restProperties,  // id를 제외한 나머지 properties
                    originalId: originalId || nodeId  // 원본 UUID는 별도로 저장
                },
                classes: ''  // 기본 클래스 없음
            };
        });
        
        // 노드를 먼저 추가하고 ID 집합 업데이트
        if (cyNodes.length > 0) {
            cy.add(cyNodes);
        }
        
        // Cytoscape에 추가된 노드 ID 집합 생성 (실제 추가된 노드만)
        // 모든 노드 ID를 문자열로 통일하여 비교
        const addedNodeIds = new Set(cyNodes.map(n => String(n.data.id)));
        
        // 실제 Cytoscape에 추가된 노드 ID도 확인
        const cytoscapeNodeIds = new Set(cy.nodes().map(n => String(n.id())));
        
        console.log('[DEBUG] 엣지 필터링 시작:', {
            total_edges: (edges || []).length,
            node_ids_count: addedNodeIds.size,
            cytoscape_node_ids_count: cytoscapeNodeIds.size,
            node_ids_sample: Array.from(addedNodeIds).slice(0, 10),
            cytoscape_ids_sample: Array.from(cytoscapeNodeIds).slice(0, 10)
        });
        
        // 엣지 샘플 확인
        if (edges && edges.length > 0) {
            console.log('[DEBUG] 엣지 샘플 (처음 5개):', edges.slice(0, 5).map(e => ({
                source: String(e.source),
                target: String(e.target),
                source_exists: addedNodeIds.has(String(e.source)),
                target_exists: addedNodeIds.has(String(e.target))
            })));
        }
        
        // 엣지 필터링: source와 target 노드가 모두 존재하는 엣지만 추가
        // Cytoscape에 실제로 추가된 노드 ID 사용
        const validEdges = (edges || []).filter((edge, index) => {
            const sourceId = String(edge.source);
            const targetId = String(edge.target);
            
            // Cytoscape에 실제로 추가된 노드 ID로 확인
            const sourceExists = cytoscapeNodeIds.has(sourceId);
            const targetExists = cytoscapeNodeIds.has(targetId);
            const isValid = sourceExists && targetExists;
            
            // 처음 5개만 상세 로그
            if (!isValid && index < 5) {
                console.warn(`[DEBUG] 엣지 건너뜀 [${index}]: source(${sourceId}, 존재: ${sourceExists}) 또는 target(${targetId}, 존재: ${targetExists})`);
                console.warn(`  - sourceId 타입: ${typeof sourceId}, 값: "${sourceId}"`);
                console.warn(`  - targetId 타입: ${typeof targetId}, 값: "${targetId}"`);
                console.warn(`  - cytoscapeNodeIds 샘플:`, Array.from(cytoscapeNodeIds).slice(0, 5));
            }
            
            return isValid;
        });
        
        console.log('[DEBUG] 유효한 엣지:', validEdges.length, '개');
        
        // 엣지 추가 (유효한 엣지만, 고유 ID 생성)
        const cyEdges = validEdges.map((edge, index) => {
            const sourceId = String(edge.source);
            const targetId = String(edge.target);
            const relationship = edge.relationship || 'RELATED';
            const edgeId = `${sourceId}-${targetId}-${relationship}-${index}`;
            
            return {
                data: {
                    id: edgeId,
                    source: sourceId,
                    target: targetId,
                    relationship: relationship,
                    label: relationship  // 엣지 레이블로 사용
                }
            };
        });
        
        // 엣지 추가
        if (cyEdges.length > 0) {
            console.log(`[DEBUG] 엣지 ${cyEdges.length}개 추가 시도 (노드 ${cyNodes.length}개)`);
            console.log('[DEBUG] 엣지 샘플:', cyEdges.slice(0, 3));
            console.log('[DEBUG] Cytoscape 현재 상태:', {
                nodes: cy.nodes().length,
                edges: cy.edges().length
            });
            try {
                cy.add(cyEdges);
                const addedEdges = cy.edges().length;
                console.log(`[DEBUG] 엣지 ${addedEdges}개 추가 완료 (요청: ${cyEdges.length}개)`);
                
                // 추가된 엣지 확인
                const sampleEdges = cy.edges().slice(0, 3);
                console.log('[DEBUG] 추가된 엣지 샘플:', sampleEdges.map(e => ({
                    id: e.id(),
                    source: e.source().id(),
                    target: e.target().id(),
                    data: e.data(),
                    visible: e.visible(),
                    rendered: e.rendered()
                })));
                
                // 엣지가 보이도록 강제 설정
                cy.edges().forEach(edge => {
                    edge.style({
                        'opacity': 1,
                        'width': 4,
                        'line-color': '#666',
                        'display': 'element',
                        'visibility': 'visible'
                    });
                });
                
                console.log('[DEBUG] 엣지 스타일 강제 적용 완료');
            } catch (edgeError) {
                console.error('엣지 추가 중 오류:', edgeError);
                // 실패한 엣지들을 하나씩 추가 시도
                cyEdges.forEach(edge => {
                    try {
                        // 노드 존재 여부 재확인
                        const sourceNode = cy.getElementById(edge.data.source);
                        const targetNode = cy.getElementById(edge.data.target);
                        if (sourceNode.length > 0 && targetNode.length > 0) {
                            cy.add(edge);
                        } else {
                            console.warn(`엣지 추가 실패: ${edge.data.source} -> ${edge.data.target} (노드 없음)`);
                        }
                    } catch (e) {
                        console.warn(`엣지 추가 실패:`, edge, e);
                    }
                });
            }
        } else {
            console.warn('추가할 유효한 엣지가 없습니다.');
        }
        
        // 레이아웃 적용 (더 유기적인 구조)
        // 엣지가 추가된 후 레이아웃 실행
        if (cyNodes.length > 0) {
            console.log('[DEBUG] 레이아웃 실행 전:', {
                nodes: cy.nodes().length,
                edges: cy.edges().length
            });
            
            const layout = cy.layout({
                name: 'cose-bilkent',
                idealEdgeLength: 100,
                nodeRepulsion: 4500,
                edgeElasticity: 0.45,
                nestingFactor: 0.1,
                gravity: 0.25,
                numIter: 2500,
                tile: true,
                animate: true,
                animationDuration: 1000,
                fit: true,
                padding: 30
            });
            
            layout.one('layoutstop', () => {
                console.log('[DEBUG] 레이아웃 완료 후:', {
                    nodes: cy.nodes().length,
                    edges: cy.edges().length,
                    visible_edges: cy.edges().filter(e => e.visible()).length
                });
                
                // 엣지가 보이지 않으면 강제로 표시
                cy.edges().forEach(edge => {
                    edge.style('opacity', 1);
                    edge.style('width', 4);
                });
            });
            
            layout.run();
        }
        
        // 노드 클릭 이벤트 (중복 방지)
        cy.off('tap', 'node');  // 기존 이벤트 제거
        cy.on('tap', 'node', (evt) => {
            const node = evt.target;
            const data = node.data();
            const props = Object.entries(data)
                .filter(([key]) => !['id', 'label', 'type'].includes(key))
                .map(([key, value]) => `${key}: ${value}`)
                .join('\n');
            
            alert(`노드 정보:\n타입: ${data.type}\n라벨: ${data.label}\nID: ${data.id}${props ? '\n\n속성:\n' + props : ''}`);
        });
        
        console.log(`그래프 업데이트 완료: ${cyNodes.length}개 노드, ${cyEdges.length}개 엣지`);
        
    } catch (error) {
        console.error('그래프 업데이트 중 오류:', error);
        alert(`그래프 업데이트 실패: ${error.message}`);
    }
}

// 그래프 로드
async function loadGraph(limit = 100) {
    const loadingIndicator = document.getElementById('loading');
    if (loadingIndicator) {
        loadingIndicator.style.display = 'block';
        loadingIndicator.textContent = '그래프 로딩 중...';
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/graph?limit=${limit}`);
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
        }
        
        const data = await response.json();
        
        console.log('[DEBUG] API 응답:', {
            nodes: data.nodes?.length || 0,
            edges: data.edges?.length || 0,
            edges_sample: data.edges?.slice(0, 3)
        });
        
        if (!data.nodes || data.nodes.length === 0) {
            console.warn('그래프 데이터가 없습니다. Neo4j에 데이터가 있는지 확인하세요.');
            if (loadingIndicator) {
                loadingIndicator.textContent = '그래프 데이터가 없습니다.';
            }
            return;
        }
        
        // 전체 그래프 데이터 저장
        fullGraphData = { nodes: data.nodes, edges: data.edges || [] };
        console.log('[DEBUG] 전체 그래프 데이터 저장:', {
            nodes: fullGraphData.nodes.length,
            edges: fullGraphData.edges.length
        });
        updateGraph(fullGraphData.nodes, fullGraphData.edges);
        
        if (loadingIndicator) {
            loadingIndicator.textContent = `그래프 로드 완료: ${data.nodes.length}개 노드, ${(data.edges || []).length}개 엣지`;
            setTimeout(() => {
                loadingIndicator.style.display = 'none';
            }, 2000);
        }
        
    } catch (error) {
        console.error('Error loading graph:', error);
        if (loadingIndicator) {
            loadingIndicator.style.display = 'block';
            loadingIndicator.textContent = `그래프 로드 실패: ${error.message}`;
            loadingIndicator.style.color = 'red';
        }
        alert(`그래프 로드 실패: ${error.message}\n\n서버가 실행 중인지 확인하세요.`);
    }
}

// 그래프 지우기 및 전체 그래프 다시 로드
function clearGraph() {
    if (cy) {
        cy.elements().remove();
        fullGraphData = { nodes: [], edges: [] };
        // 전체 그래프 다시 로드
        loadGraph(200);
    }
}

// 히스토리 추가
function addToHistory(query, answer) {
    const historyItem = {
        query,
        answer: answer.substring(0, 100) + '...',
        timestamp: new Date().toISOString()
    };
    
    searchHistory.unshift(historyItem);
    if (searchHistory.length > 10) {
        searchHistory = searchHistory.slice(0, 10);
    }
    
    localStorage.setItem('searchHistory', JSON.stringify(searchHistory));
    loadHistory();
}

// 히스토리 로드
function loadHistory() {
    const historyDiv = document.getElementById('history');
    historyDiv.innerHTML = '';
    
    if (searchHistory.length === 0) {
        historyDiv.innerHTML = '<p style="color: #999; font-size: 12px;">검색 히스토리가 없습니다.</p>';
        return;
    }
    
    searchHistory.forEach((item, index) => {
        const historyItem = document.createElement('div');
        historyItem.className = 'history-item';
        historyItem.innerHTML = `
            <strong>${item.query}</strong><br>
            <small style="color: #666;">${item.answer}</small>
        `;
        historyItem.addEventListener('click', () => {
            document.getElementById('queryInput').value = item.query;
            handleSearch();
        });
        historyDiv.appendChild(historyItem);
    });
}

