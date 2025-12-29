# News GraphRAG Ontology Platform

Supabase에 저장된 뉴스 데이터를 기반으로 Neo4j 온톨로지를 구성하고, GraphRAG 기반의 지능형 뉴스 검색 및 질의응답 서비스를 제공하는 플랫폼입니다.

## 주요 기능

- **ETL 파이프라인**: Supabase 뉴스 데이터를 Neo4j 온톨로지로 변환
- **GraphRAG 검색**: Text2Cypher, Vector, VectorCypher 3가지 검색 전략 자동 선택
- **LLM Provider 추상화**: OpenAI, Anthropic, Ollama 지원
- **웹 인터페이스**: 자연어 질의 및 그래프 시각화

## 설치

### 0. 가상 환경 설정 (권장)

```bash
# 가상 환경 생성 (이미 venv 폴더가 있으면 생략)
python -m venv venv

# 가상 환경 활성화
# macOS/Linux:
source venv/bin/activate

# Windows:
# venv\Scripts\activate
```

가상 환경이 활성화되면 터미널 프롬프트 앞에 `(venv)`가 표시됩니다.

### 1. 의존성 설치

```bash
# 가상 환경이 활성화된 상태에서 실행
pip install -r requirements.txt
```

**중요**: 서버 실행 전에 가상 환경이 활성화되어 있는지 확인하세요.

### 2. 환경변수 설정

프로젝트 루트에 `.env` 파일을 생성하고 다음 내용을 추가하세요:

```bash
# ============================================
# Supabase 설정 (REST API 방식)
# ============================================
# Supabase 대시보드 > Settings > API에서 확인 가능
# Project URL과 anon key를 입력하세요
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key

# ============================================
# Neo4j 설정
# ============================================
# Neo4j 데이터베이스 연결 정보
# 로컬 Neo4j: bolt://localhost:7687
# Neo4j Aura: neo4j+s://your-instance.databases.neo4j.io
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_neo4j_password
NEO4J_DATABASE=neo4j

# ============================================
# LLM Provider 설정
# ============================================
# 사용할 LLM Provider 선택: openai, anthropic, ollama
LLM_PROVIDER=openai

# OpenAI 설정 (LLM_PROVIDER=openai일 때 필요)
# https://platform.openai.com/api-keys 에서 발급
OPENAI_API_KEY=sk-your-openai-api-key

# Anthropic 설정 (LLM_PROVIDER=anthropic일 때 필요)
# https://console.anthropic.com/ 에서 발급
ANTHROPIC_API_KEY=sk-ant-your-anthropic-api-key

# Ollama 설정 (LLM_PROVIDER=ollama일 때 사용)
# 로컬 Ollama 서버 주소
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2

# ============================================
# Embedding 설정
# ============================================
# 임베딩 Provider 선택: local, openai
# local: sentence-transformers (로컬 실행, 비용 없음)
# openai: OpenAI 임베딩 API (유료)
EMBEDDING_PROVIDER=local

# 로컬 임베딩 모델 (EMBEDDING_PROVIDER=local일 때 사용)
# 한국어 지원 모델: paraphrase-multilingual-MiniLM-L12-v2
# 영어 전용 모델: all-MiniLM-L6-v2 (더 빠름)
EMBEDDING_MODEL=paraphrase-multilingual-MiniLM-L12-v2

# OpenAI 임베딩 모델 (EMBEDDING_PROVIDER=openai일 때 사용)
# text-embedding-3-small: 저렴하고 빠름 (1536 차원)
# text-embedding-3-large: 더 정확함 (3072 차원, 비용 높음)
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# ============================================
# Chunking 설정
# ============================================
# 기사 본문을 청크로 나눌 때 사용하는 설정
# CHUNK_SIZE: 각 청크의 최대 토큰 수
# CHUNK_OVERLAP: 청크 간 겹치는 토큰 수 (문맥 유지)
CHUNK_SIZE=500
CHUNK_OVERLAP=50
```

**중요**: 실제 값으로 채워야 하는 항목:
- `SUPABASE_URL`, `SUPABASE_KEY`: Supabase 대시보드 > Settings > API에서 확인
  - Project URL: `https://your-project.supabase.co` 형식
  - anon key: 공개 API Key (일반적으로 사용)
  - service_role key: 관리자 권한이 필요한 경우 (주의: 보안에 민감)
- `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD`: Neo4j 연결 정보
- `OPENAI_API_KEY` 또는 `ANTHROPIC_API_KEY`: 사용할 LLM Provider의 API Key

**Supabase API Key 확인 방법**:
1. Supabase 대시보드 접속
2. Settings > API 메뉴
3. Project URL과 anon public key 확인
4. 일반적으로 anon key를 사용하며, 관리 작업이 필요한 경우에만 service_role key 사용

### 3. Neo4j Vector Index 생성

```bash
python scripts/setup_vector_index.py
```

### 4. 연결 테스트 (선택사항)

Supabase 연결을 테스트합니다:

```bash
python scripts/test_connection.py
```

또는 상세 디버깅:

```bash
python scripts/debug_supabase.py
```

### 5. 데이터 적재 (ETL)

```bash
# 전체 기사 처리
python scripts/run_etl.py

# 최근 200개 기사만 처리 (권장: 테스트용)
python scripts/run_etl.py --limit 200

# 배치 크기 조정
python scripts/run_etl.py --limit 200 --batch-size 20

# 기존 데이터 삭제 후 시작
python scripts/run_etl.py --clear --limit 200
```

**ETL 옵션:**
- `--limit N`: 처리할 최대 기사 수 (기본값: 전체)
- `--batch-size N`: 배치 처리 크기 (기본값: 10)
- `--clear`: 기존 Neo4j 데이터 삭제 후 시작

### 6. 서버 실행

**중요**: 가상 환경이 활성화된 상태에서 실행하세요.

```bash
# 가상 환경 활성화 확인 (터미널에 (venv) 표시)
source venv/bin/activate

# 서버 실행 (python -m uvicorn 사용 권장)
python -m uvicorn app.main:app --reload --port 8000

# 또는 직접 실행 (reload 없이)
python -m uvicorn app.main:app --port 8000
```

서버가 `http://localhost:8000`에서 실행됩니다.

**오류 발생 시**:
- `ModuleNotFoundError: No module named 'neo4j'` 등의 오류가 나오면:
  1. 가상 환경이 활성화되었는지 확인: `which python` (venv/bin/python 경로여야 함)
  2. `python -m uvicorn` 사용 (가상 환경의 Python 명시적 사용)
  3. 패키지 재설치: `pip install -r requirements.txt`

### 7. 프론트엔드 접속

브라우저에서 `frontend/index.html`을 열거나, 서버를 통해 정적 파일을 제공하도록 설정하세요.

## API 엔드포인트

### POST /query

자연어 질의를 처리합니다.

**Request:**
```json
{
  "query": "최근 AI 관련 뉴스 요약"
}
```

**Response:**
```json
{
  "answer": "...",
  "nodes": [...],
  "edges": [...],
  "retriever_used": "vector_cypher"
}
```

### GET /graph

그래프 데이터를 조회합니다 (시각화용).

### GET /health

헬스 체크 엔드포인트.

## Retriever 설명 및 테스트

### Retriever 개념 이해
- **[RETRIEVER_EXPLANATION.md](./RETRIEVER_EXPLANATION.md)**: Retriever의 개념과 3가지 Retriever (Text2Cypher, Vector, VectorCypher)에 대한 상세 설명
  - 각 Retriever의 작동 방식, 장단점, 적합한 질의 예시
  - 문제 해결 가이드

### Retriever 테스트 질의
- **[RETRIEVER_TEST_QUERIES.md](./RETRIEVER_TEST_QUERIES.md)**: 각 Retriever별 테스트 질의 예시
  - Retriever 선택 조건
  - 추천 질의 예시
  - 테스트 시나리오

## 프로젝트 구조

```
news_graphrag_ontology/          # 프로젝트 루트 (여기에 .env 파일 생성)
├── .env                        # 환경변수 파일 (직접 생성 필요)
├── .gitignore                  # Git 제외 파일 목록
├── requirements.txt            # Python 의존성 패키지 목록
├── README.md                   # 프로젝트 문서
│
├── app/                        # 백엔드 애플리케이션 (FastAPI 서버)
│   ├── __init__.py
│   ├── main.py                # FastAPI 서버 진입점 (API 엔드포인트)
│   ├── config.py              # 환경변수 로드 및 설정 관리
│   │
│   ├── etl/                   # ETL 파이프라인 (데이터 온톨로지화)
│   │   ├── supabase_client.py    # Supabase에서 뉴스 데이터 조회
│   │   ├── chunker.py            # 기사 본문을 청크로 분할
│   │   ├── embedding_generator.py # 청크에 대한 임베딩 생성
│   │   └── neo4j_loader.py       # Neo4j에 노드/관계 적재
│   │
│   ├── retrievers/             # GraphRAG 검색 전략
│   │   ├── base.py               # Retriever 추상 클래스
│   │   ├── text2cypher.py        # 자연어 → Cypher 변환 검색
│   │   ├── vector.py             # 벡터 유사도 검색
│   │   ├── vector_cypher.py      # 벡터 + 그래프 확장 검색
│   │   └── selector.py           # 질의 유형별 Retriever 자동 선택
│   │
│   ├── llm/                    # LLM Provider 추상화
│   │   ├── base.py               # LLM Provider 인터페이스
│   │   ├── openai_provider.py    # OpenAI 구현
│   │   ├── anthropic_provider.py # Anthropic 구현
│   │   ├── ollama_provider.py    # Ollama 구현
│   │   └── factory.py           # Provider Factory
│   │
│   └── models/                  # 데이터 모델 (Pydantic 스키마)
│       └── schema.py            # API 요청/응답 모델
│
├── scripts/                     # 유틸리티 스크립트 (온톨로지화 작업)
│   ├── run_etl.py              # ETL 파이프라인 실행 (Supabase → Neo4j)
│   ├── setup_vector_index.py  # Neo4j Vector Index 생성
│   ├── test_connection.py     # Supabase 연결 테스트
│   └── debug_supabase.py      # Supabase 데이터 조회 디버깅
│
└── frontend/                    # 프론트엔드 웹페이지 (POC)
    ├── index.html              # 메인 HTML 페이지
    ├── style.css               # 스타일시트
    └── app.js                  # JavaScript (API 호출, 그래프 시각화)
```

### 폴더별 역할

- **`app/`**: 백엔드 서버 (FastAPI)
  - API 엔드포인트 제공
  - GraphRAG 검색 로직
  - LLM Provider 관리

- **`frontend/`**: 웹페이지 (프론트엔드)
  - 사용자 인터페이스
  - 그래프 시각화
  - API 호출 및 결과 표시

- **`scripts/`**: 온톨로지화 작업 스크립트
  - `run_etl.py`: Supabase 데이터를 Neo4j 온톨로지로 변환 (--limit 옵션 지원)
  - `setup_vector_index.py`: Neo4j Vector Index 생성
  - `test_connection.py`: Supabase 연결 테스트
  - `debug_supabase.py`: Supabase 데이터 조회 디버깅

- **`.env`**: 환경변수 파일 (프로젝트 루트에 생성)

## 기술 스택

- **Backend**: FastAPI, Python 3.9+
- **ASGI Server**: Uvicorn (FastAPI 실행을 위한 서버)
- **Database**: Supabase (REST API), Neo4j
- **LLM**: OpenAI (기본), Anthropic, Ollama
- **Embedding**: sentence-transformers (기본), OpenAI
- **Graph Visualization**: Cytoscape.js

## 진행 상황

### ✅ 완료된 기능

1. **프로젝트 기반 구조**
   - 프로젝트 디렉토리 구조 생성
   - 의존성 관리 (`requirements.txt`)
   - 환경변수 관리 시스템

2. **설정 관리**
   - `app/config.py`: 환경변수 로드 및 설정 관리
   - Pydantic Settings를 통한 타입 안전 설정

3. **LLM Provider 추상화**
   - 공통 인터페이스 정의 (`base.py`)
   - OpenAI Provider 구현
   - Anthropic Provider 구현
   - Ollama Provider 구현
   - Factory 패턴으로 Provider 선택

4. **ETL 파이프라인**
   - Supabase REST API 클라이언트: 뉴스 데이터 조회 (API Key 방식)
   - Content Chunker: 500 tokens, 50 overlap 청킹
   - Embedding Generator: 로컬/OpenAI 임베딩 지원
   - Neo4j Loader: 노드 및 관계 적재
   - 배치 처리 지원
   - `--limit` 옵션으로 처리할 기사 수 제한 가능

5. **GraphRAG Retrievers**
   - Text2Cypher Retriever: 자연어 → Cypher 변환
   - Vector Retriever: 벡터 유사도 검색
   - VectorCypher Retriever: 벡터 + 그래프 확장
   - Retriever Selector: 질의 유형별 자동 선택

6. **FastAPI 서버**
   - `/query`: 자연어 질의 처리
   - `/graph`: 그래프 데이터 조회
   - `/health`: 헬스 체크
   - CORS 설정
   - 정적 파일 서빙

7. **프론트엔드 (POC)**
   - 검색 입력 UI
   - 검색 결과 표시
   - Cytoscape.js 그래프 시각화
   - 검색 히스토리 (로컬 스토리지)

8. **유틸리티 스크립트**
   - `run_etl.py`: ETL 파이프라인 실행 (--limit, --batch-size, --clear 옵션)
   - `setup_vector_index.py`: Neo4j Vector Index 생성
   - `test_connection.py`: Supabase 연결 테스트
   - `debug_supabase.py`: Supabase 데이터 조회 디버깅

### 🚧 추후 진행 예정

1. **성능 최적화**
   - [ ] Vector Index 최적화 및 성능 튜닝
   - [ ] 배치 처리 크기 최적화
   - [ ] 캐싱 전략 구현 (Redis 등)
   - [ ] 비동기 처리 개선

2. **에러 처리 및 안정성**
   - [ ] Text2Cypher 오류 시 Fallback 전략 개선
   - [ ] 재시도 로직 추가
   - [ ] 상세한 에러 로깅
   - [ ] 모니터링 및 알림 시스템

3. **기능 확장**
   - [ ] 뉴스 요약 자동 생성
   - [ ] 트렌드/이슈 클러스터링
   - [ ] 사용자별 질의 히스토리 학습
   - [ ] 멀티 언어 뉴스 지원
   - [ ] 실시간 뉴스 스트리밍 처리

4. **프론트엔드 개선**
   - [ ] 노드 클릭 시 상세 정보 모달
   - [ ] 그래프 필터링 기능
   - [ ] 검색 결과 정렬 및 필터
   - [ ] 반응형 디자인 개선
   - [ ] 다크 모드 지원

5. **테스트 및 문서화**
   - [ ] 단위 테스트 작성
   - [ ] 통합 테스트 작성
   - [ ] API 문서 자동 생성 (Swagger/OpenAPI)
   - [ ] 사용자 가이드 작성

6. **배포 및 운영**
   - [ ] Docker 컨테이너화
   - [ ] Docker Compose 설정
   - [ ] CI/CD 파이프라인 구축
   - [ ] 프로덕션 환경 설정 가이드

## 서버 실행 방법

### Uvicorn이란?

**Uvicorn**은 FastAPI 애플리케이션을 실행하기 위한 **ASGI (Asynchronous Server Gateway Interface) 서버**입니다.

- **역할**: FastAPI는 웹 프레임워크이고, Uvicorn은 실제로 HTTP 요청을 처리하고 FastAPI 애플리케이션을 실행하는 서버입니다
- **필요성**: FastAPI는 ASGI 프레임워크이므로 ASGI 서버가 반드시 필요합니다
- **대안**: Hypercorn, Daphne 등 다른 ASGI 서버도 사용 가능하지만, Uvicorn이 가장 널리 사용되고 FastAPI 공식 문서에서도 권장합니다

### 서버 실행 옵션

#### 1. Uvicorn 사용 (권장)

```bash
# 기본 실행 (python -m 사용 권장 - 가상 환경 Python 명시)
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# 개발 모드 (코드 변경 시 자동 재시작)
python -m uvicorn app.main:app --reload --port 8000

# 프로덕션 모드 (워커 프로세스 여러 개)
python -m uvicorn app.main:app --workers 4 --port 8000
```

**참고**: `python -m uvicorn`을 사용하면 가상 환경의 Python이 명시적으로 사용되어 모듈 import 오류를 방지할 수 있습니다.

#### 2. Python으로 직접 실행

`app/main.py`에 `if __name__ == "__main__"` 블록이 있어서 Python으로 직접 실행도 가능합니다:

```bash
python app/main.py
```

하지만 내부적으로는 uvicorn을 사용합니다.

#### 3. Gunicorn + Uvicorn (프로덕션)

프로덕션 환경에서는 Gunicorn을 워커 매니저로 사용하고 Uvicorn을 워커로 사용할 수 있습니다:

```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

이 경우 `gunicorn`을 `requirements.txt`에 추가해야 합니다.

## 빠른 시작 가이드

### 1단계: 환경 설정
```bash
# 1. 가상 환경 활성화
source venv/bin/activate  # macOS/Linux
# 또는 venv\Scripts\activate  # Windows

# 2. 의존성 설치
pip install -r requirements.txt

# 3. .env 파일 생성 및 설정
# Supabase URL, API Key, Neo4j 연결 정보 입력
```

### 2단계: 연결 확인
```bash
# Supabase 연결 테스트
python scripts/test_connection.py
```

### 3단계: Neo4j 준비
```bash
# Vector Index 생성
python scripts/setup_vector_index.py
```

### 4단계: 데이터 적재
```bash
# 최근 200개 기사로 테스트 (권장)
python scripts/run_etl.py --limit 200 --batch-size 20
```

### 5단계: 서버 실행
```bash
# 가상 환경 활성화 확인 후 실행
source venv/bin/activate  # 이미 활성화되어 있으면 생략
python -m uvicorn app.main:app --reload --port 8000
```

### 6단계: 프론트엔드 접속
브라우저에서 `http://localhost:8000/static/index.html` 접속

## 문제 해결

### Supabase 연결 문제

**증상**: 기사 수가 0으로 나오거나 데이터 조회 실패

**해결 방법**:
1. 디버깅 스크립트 실행:
   ```bash
   python scripts/debug_supabase.py
   ```

2. RLS 정책 확인:
   - Supabase 대시보드 > Authentication > Policies
   - `news_article`, `news_category`, `media_company` 테이블에 SELECT 정책 추가
   - 또는 `service_role` key 사용 (개발 환경)

3. API Key 확인:
   - `.env` 파일의 `SUPABASE_KEY`가 올바른지 확인
   - `anon public` key 또는 `service_role` key 사용

### 모듈을 찾을 수 없음 (ModuleNotFoundError)

**증상**: `ModuleNotFoundError: No module named 'neo4j'` 등의 오류

**해결 방법**:
1. 가상 환경 활성화 확인:
   ```bash
   source venv/bin/activate
   which python  # venv/bin/python 경로여야 함
   ```

2. 패키지 재설치:
   ```bash
   pip install -r requirements.txt
   ```

3. 특정 패키지가 누락된 경우:
   ```bash
   pip install neo4j==5.14.1
   pip install supabase>=2.3.0
   ```

### 의존성 충돌

**증상**: `pip install` 시 패키지 버전 충돌

**해결 방법**:
```bash
# requirements.txt의 버전 범위가 자동으로 해결하도록 설정됨
# 특정 패키지가 문제가 되면 개별 설치
pip install supabase>=2.3.0
pip install httpx>=0.25.0,<1.0.0
```

### Neo4j Vector Index 오류

**증상**: Vector Index 생성 실패

**해결 방법**:
- Neo4j 버전 확인 (5.x 이상 필요)
- 인덱스 이름에 하이픈이 있으면 백틱으로 감싸짐 (이미 수정됨)
- Neo4j가 실행 중인지 확인

### ETL 처리 속도가 느림

**해결 방법**:
- 배치 크기 증가: `--batch-size 20` 또는 `--batch-size 50`
- `--limit` 옵션으로 처리할 기사 수 제한
- 임베딩 모델이 로컬에서 다운로드되는 시간 고려

## 주요 변경 이력

- **Supabase 접근 방식**: PostgreSQL 직접 연결 → REST API (API Key 방식)
- **ETL 옵션**: `--limit` 옵션 추가로 처리할 기사 수 제한 가능
- **디버깅 도구**: `test_connection.py`, `debug_supabase.py` 추가

