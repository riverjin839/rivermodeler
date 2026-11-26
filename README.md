# AI Platform MVP

CRISP-DM 방법론 기반 통합 AI 플랫폼. 로컬 Mac `kind` 클러스터 위에 MSA + 헥사고날 아키텍처로 구축.

> 전통적 ML의 Drift 모니터링과 LLM Agent(GraphRAG + Vector RAG)를 하나의 플랫폼에서 통합 운영

---

## 아키텍처

> **draw.io 파일**: [`docs/architecture.drawio`](docs/architecture.drawio)
>
> draw.io 앱 또는 [app.diagrams.net](https://app.diagrams.net)에서 열어 확인할 수 있습니다.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    kind Cluster (ai-platform namespace)                    │
│                                                                             │
│  ┌──────────────────────── Ingress-NGINX ──────────────────────────────┐    │
│  │  dashboard.ai-platform.local    ai-platform.local/api|ml|mlflow    │    │
│  └──────┬──────────────────────────┬─────────────────┬────────────────┘    │
│         │                          │                 │                      │
│         ▼                          ▼                 ▼                      │
│  ┌──────────────┐   ┌──────────────────────────────────────────────┐       │
│  │  Dashboard   │   │        Backend Service Layer                 │       │
│  │  (Next.js)   │   │                                              │       │
│  │  :3000       │   │  ┌─────────────────────────────────────────┐ │       │
│  │              │   │  │ Agent Service (FastAPI+LangGraph) :8080 │ │       │
│  │ ┌──────────┐ │   │  │                                         │ │       │
│  │ │ 대시보드 │ │   │  │  Inbound    Domain       Outbound      │ │       │
│  │ │ AI 채팅  │ │──▶│  │  Adapter ─▶ Service ─▶ Ports/Adapters │─┼──┐    │
│  │ │ ML모니터 │ │BFF│  │  (Routes)   (LangGraph)  (구현체)       │ │  │    │
│  │ └──────────┘ │   │  └─────────────────────────────────────────┘ │  │    │
│  │              │   │                                              │  │    │
│  │  BFF Proxy   │   │  ┌──────────────────────┐ ┌──────────────┐  │  │    │
│  │  (API Routes)│──▶│  │ ML Serving     :8081 │ │ Evidently AI │  │  │    │
│  └──────────────┘   │  │ (FastAPI)            │─│ Drift Detect │  │  │    │
│                     │  └──────────────────────┘ └──────────────┘  │  │    │
│                     └──────────────────────────────────────────────┘  │    │
│                                                                       │    │
│  ┌───────────────────── Data & Infra Layer ──────────────────────┐   │    │
│  │                                                                │   │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐     │   │    │
│  │  │  Neo4j   │  │ ChromaDB │  │  Ollama  │  │  MLflow  │     │◀──┘    │
│  │  │  :7687   │  │  :8000   │  │  :11434  │  │  :5000   │     │        │
│  │  │ GraphRAG │  │ VectorDB │  │ EXAONE3  │  │ Registry │     │        │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘     │        │
│  └────────────────────────────────────────────────────────────────┘        │
└─────────────────────────────────────────────────────────────────────────────┘
```

### LangGraph 오케스트레이션 흐름

```
                    ┌──── Vector RAG (ChromaDB) ────┐
                    │                                │
[사용자 질문] ─▶ [Classify] ──── Graph RAG (Neo4j) ────▶ [Synthesize] ─▶ [응답]
                    │                                │
                    └──── ML Prediction ────────────┘
                                                     ▲
                                               Ollama (EXAONE)
```

### 헥사고날 아키텍처 (Agent Service)

```
 ┌────────────────────────────────────────────────────────────────┐
 │                    Agent Service                               │
 │                                                                │
 │  Inbound Adapter     Domain           Outbound Port → Adapter │
 │  ┌──────────┐    ┌──────────────┐    ┌───────────────────────┐│
 │  │ FastAPI  │───▶│ Orchestrator │───▶│ VectorDBPort  → Chroma││
 │  │ Routes   │    │ (LangGraph)  │    │ GraphDBPort   → Neo4j ││
 │  └──────────┘    └──────────────┘    │ LLMPort       → Ollama││
 │                                      │ MLServingPort → HTTP   ││
 │                                      └───────────────────────┘│
 └────────────────────────────────────────────────────────────────┘
```

---

## 기술 스택

| 영역 | 기술 | 용도 |
|------|------|------|
| **인프라** | kind, Ingress-NGINX | 로컬 K8s 클러스터, 트래픽 라우팅 |
| **프론트엔드** | Next.js 14 (App Router), Tailwind CSS | 대시보드 UI, BFF 프록시 |
| **백엔드** | Python FastAPI, LangGraph | Agent 오케스트레이션, REST API |
| **LLM** | Ollama (LG EXAONE 3.0) | 텍스트 생성, 답변 합성 |
| **Graph DB** | Neo4j | Ontology, Knowledge Graph (GraphRAG) |
| **Vector DB** | ChromaDB | 문서 임베딩, 유사도 검색 (Vector RAG) |
| **ML Registry** | MLflow | 모델 버전 관리, 실험 추적 |
| **Drift 감지** | Evidently AI | Data/Concept Drift 실시간 모니터링 |
| **아키텍처** | 헥사고날 (Ports & Adapters) | 도메인 로직 보호, 인프라 교체 용이 |

---

## 프로젝트 구조

```
rivermodeler/
├── kind-config.yaml                          # kind 클러스터 설정
├── k8s/base/                                 # K8s 매니페스트
│   ├── namespace.yaml                        #   ai-platform 네임스페이스
│   ├── neo4j.yaml                            #   Neo4j StatefulSet + Service
│   ├── chromadb.yaml                         #   ChromaDB Deployment + Service
│   ├── ollama.yaml                           #   Ollama Deployment + Service
│   ├── mlflow.yaml                           #   MLflow Deployment + Service
│   ├── agent-service.yaml                    #   Agent Service Deployment + Service
│   ├── ml-serving.yaml                       #   ML Serving Deployment + Service
│   ├── dashboard.yaml                        #   Dashboard Deployment + Service
│   └── ingress.yaml                          #   Ingress 라우팅 규칙
│
├── scripts/
│   ├── 01-create-cluster.sh                  # kind 클러스터 생성 + Ingress 설치
│   ├── 02-deploy-platform.sh                 # 이미지 빌드 → 로드 → K8s 배포
│   ├── 03-load-exaone.sh                     # EXAONE 3.0 모델 적재
│   ├── backup.sh                             # 데이터 백업 (Pod → 호스트 tar.gz)
│   └── restore.sh                            # 데이터 복구 (tar.gz → Pod)
│
├── docs/
│   └── architecture.drawio                   # 아키텍처 다이어그램 (draw.io)
│
└── services/
    ├── agent-service/                        # Agent 오케스트레이션 서비스
    │   ├── Dockerfile
    │   ├── requirements.txt
    │   └── app/
    │       ├── main.py                       #   FastAPI 엔트리포인트
    │       ├── config.py                     #   환경변수 설정
    │       ├── core/
    │       │   └── container.py              #   의존성 주입 컨테이너
    │       ├── domain/
    │       │   ├── models/query.py           #   도메인 모델 (UserQuery, AgentResponse)
    │       │   └── services/orchestrator.py  #   LangGraph 오케스트레이터
    │       ├── ports/
    │       │   ├── inbound/query_port.py     #   Inbound Port (추상)
    │       │   └── outbound/                 #   Outbound Ports (추상)
    │       │       ├── vector_db_port.py
    │       │       ├── graph_db_port.py
    │       │       ├── llm_port.py
    │       │       └── ml_serving_port.py
    │       └── adapters/
    │           ├── inbound/api/routes.py     #   FastAPI 라우터 (Inbound Adapter)
    │           └── outbound/                 #   Outbound Adapters (구현체)
    │               ├── vectordb/chroma_adapter.py
    │               ├── neo4j/graph_db_adapter.py
    │               ├── ollama/llm_adapter.py
    │               └── mlflow/ml_serving_adapter.py
    │
    ├── ml-serving/                           # ML 추론 + Drift 감지 서비스
    │   ├── Dockerfile
    │   ├── requirements.txt
    │   └── app/
    │       ├── main.py                       #   FastAPI + 추론/Drift API
    │       └── drift/detector.py             #   Evidently AI Drift 감지기
    │
    └── dashboard/                            # Next.js 풀스택 대시보드
        ├── Dockerfile
        ├── package.json
        ├── next.config.ts                    #   output: "standalone"
        ├── tailwind.config.ts
        └── src/
            ├── app/
            │   ├── layout.tsx                #   루트 레이아웃 + 사이드바
            │   ├── page.tsx                  #   대시보드 (/) - 시스템 개요
            │   ├── chat/page.tsx             #   AI 에이전트 채팅 (/chat)
            │   ├── ml/page.tsx               #   ML 모니터링 (/ml)
            │   └── api/                      #   BFF 프록시 (6개 라우트)
            │       ├── agent/{query,tools,health}/route.ts
            │       └── ml/{predict,drift,model-info}/route.ts
            ├── components/                   #   재사용 UI 컴포넌트
            │   ├── sidebar.tsx
            │   ├── chat-message.tsx
            │   ├── health-badge.tsx
            │   ├── metric-card.tsx
            │   └── drift-chart.tsx
            └── lib/
                ├── api.ts                    #   클라이언트 fetch 헬퍼
                └── constants.ts              #   환경변수, Tool 설정
```

---

## MSA 서비스 간 통신

| From | To | Protocol | 용도 |
|------|----|----------|------|
| Ingress | Dashboard | `http://dashboard-service:3000` | 프론트엔드 UI 서빙 |
| Ingress | Agent Service | `http://agent-service:8080` | API 요청 |
| Ingress | ML Serving | `http://ml-serving-service:8081` | ML 추론 API |
| Dashboard (BFF) | Agent Service | `http://agent-service:8080` | 서버 사이드 프록시 |
| Dashboard (BFF) | ML Serving | `http://ml-serving-service:8081` | 서버 사이드 프록시 |
| Agent Service | ChromaDB | `http://chromadb-service:8000` | 벡터 유사도 검색 |
| Agent Service | Neo4j | `bolt://neo4j-service:7687` | Knowledge Graph 질의 |
| Agent Service | Ollama | `http://ollama-service:11434` | LLM 텍스트 생성 |
| Agent Service | ML Serving | `http://ml-serving-service:8081` | ML 예측 결과 조회 |
| ML Serving | MLflow | `http://mlflow-service:5000` | 모델 레지스트리 |

---

## 빠른 시작

### 사전 요구사항

- Docker Desktop (Mac)
- [kind](https://kind.sigs.k8s.io/) (`brew install kind`)
- [kubectl](https://kubernetes.io/docs/tasks/tools/) (`brew install kubectl`)

### 1. 클러스터 생성

```bash
./scripts/01-create-cluster.sh
```

kind 클러스터 생성 + Ingress-NGINX 컨트롤러 설치

### 2. 플랫폼 배포

```bash
./scripts/02-deploy-platform.sh
```

Docker 이미지 빌드 → kind 로드 → K8s 매니페스트 적용

### 3. EXAONE 모델 적재 (선택)

```bash
./scripts/03-load-exaone.sh
```

Ollama Pod 내부에서 EXAONE 3.0 모델 다운로드

### 4. 호스트 파일 설정

```bash
echo "127.0.0.1 ai-platform.local dashboard.ai-platform.local" | sudo tee -a /etc/hosts
```

### 5. 접속

| 서비스 | URL |
|--------|-----|
| **Dashboard UI** | http://dashboard.ai-platform.local/ |
| Agent API | http://ai-platform.local/api/v1/query |
| ML API | http://ai-platform.local/ml/predict |
| MLflow UI | http://ai-platform.local/mlflow/ |
| Neo4j Browser | http://ai-platform.local/neo4j/ |

### 6. API 테스트

```bash
# Agent 질의
curl -X POST http://ai-platform.local/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"question": "고객과 제품 간의 관계를 분석해 줘"}'

# ML 추론
curl -X POST http://ai-platform.local/ml/predict \
  -H "Content-Type: application/json" \
  -d '{"features": {"feature_1": 0.5, "feature_2": -0.3, "feature_3": 1.2, "feature_4": 0.8}}'

# Drift 상태
curl http://ai-platform.local/ml/drift/status
```

---

## 데이터 영속화

kind 클러스터를 삭제/재생성해도 데이터가 보존되도록 **호스트 디렉토리 마운트** 방식을 사용합니다.

### 동작 원리

```
Mac 호스트                       kind 노드                    K8s Pod
~/.ai-platform-data/neo4j   →   /data/ai-platform/neo4j   →  /data (Neo4j)
~/.ai-platform-data/chromadb →  /data/ai-platform/chromadb →  /chroma/chroma
~/.ai-platform-data/ollama   →  /data/ai-platform/ollama   →  /root/.ollama
~/.ai-platform-data/mlflow   →  /data/ai-platform/mlflow   →  /mlflow
```

| 계층 | 메커니즘 | 설명 |
|------|----------|------|
| kind extraMounts | Docker bind mount | 호스트 디렉토리 → kind 노드 (클러스터 삭제 시에도 보존) |
| K8s hostPath | 노드 디렉토리 → Pod | kind 노드 경로를 Pod 내부에 마운트 |

### 클러스터 재생성 시나리오

```bash
# 1. (선택) 사전 백업
./scripts/backup.sh

# 2. 클러스터 재생성 — 데이터는 호스트에 보존됨
./scripts/01-create-cluster.sh

# 3. 재배포 — 기존 데이터가 자동으로 연결됨
./scripts/02-deploy-platform.sh
```

데이터를 완전히 초기화하려면:
```bash
./scripts/01-create-cluster.sh --clean
```

### 데이터 디렉토리 커스터마이징

```bash
# 환경변수로 데이터 경로 변경 가능
export AI_PLATFORM_DATA_DIR=/path/to/custom/data
./scripts/01-create-cluster.sh
```

---

## 백업 & 복구

호스트 디렉토리 영속화와 별개로, **이동/공유 가능한 포터블 백업**을 생성할 수 있습니다.

### 백업

```bash
# 기본: backups/YYYYMMDD_HHMMSS/ 에 저장
./scripts/backup.sh

# 지정 경로에 저장
./scripts/backup.sh /path/to/backup/dir
```

백업 대상:

| 서비스 | 백업 파일 | 내용 |
|--------|-----------|------|
| Neo4j | `neo4j-data.tar.gz` | `/data` 디렉토리 (그래프 DB 전체) |
| ChromaDB | `chromadb-data.tar.gz` | `/chroma/chroma` (벡터 임베딩) |
| MLflow | `mlflow-data.tar.gz` | SQLite DB + 모델 아티팩트 |
| Ollama | `ollama-data.tar.gz` | 모델 파일 (EXAONE 등) |
| Ollama | `ollama-models.txt` | 적재된 모델 목록 (파일 복구 실패 시 재다운로드용) |

### 복구

```bash
# 특정 백업에서 복구
./scripts/restore.sh backups/20260101_120000

# 최신 백업 자동 선택
./scripts/restore.sh
```

### 전체 재구축 플로우

```bash
# 1. 기존 클러스터에서 백업
./scripts/backup.sh

# 2. 클러스터 완전 초기화 (데이터 포함 삭제)
./scripts/01-create-cluster.sh --clean

# 3. 플랫폼 재배포
./scripts/02-deploy-platform.sh

# 4. 백업에서 복구
./scripts/restore.sh
```

---

## 리소스 제한 (Mac OOM 방지)

| 서비스 | Request | Limit | 비고 |
|--------|---------|-------|------|
| Neo4j | 512Mi / 250m | 1Gi / 500m | JVM 힙 256~512MB |
| ChromaDB | 256Mi / 200m | 512Mi / 500m | |
| Ollama | 2Gi / 1000m | 4Gi / 2000m | EXAONE 모델 크기에 따라 조절 |
| MLflow | 256Mi / 200m | 512Mi / 500m | SQLite 백엔드 |
| Agent Service | 256Mi / 200m | 512Mi / 500m | |
| ML Serving | 256Mi / 200m | 512Mi / 500m | Evidently 리포트 생성 포함 |
| Dashboard | 128Mi / 100m | 256Mi / 300m | Next.js standalone |
| **합계** | **~3.7Gi** | **~7.2Gi** | Mac 최소 16GB RAM 권장 |

---

## CRISP-DM 매핑

| CRISP-DM 단계 | 플랫폼 구현 |
|---------------|-------------|
| 1. Business Understanding | 도메인 모델 (`domain/models/query.py`) |
| 2. Data Understanding | GraphRAG (Neo4j) + VectorRAG (ChromaDB) |
| 3. Data Preparation | 임베딩 적재, Knowledge Graph 구축 |
| 4. Modeling | ML Serving + MLflow (Model Registry) |
| 5. Evaluation | Evidently AI (Data/Concept Drift 감지) |
| 6. Deployment | kind K8s + Ingress-NGINX + Docker |

---

## 상태 확인

```bash
# Pod 상태
kubectl get pods -n ai-platform

# 서비스 목록
kubectl get svc -n ai-platform

# 로그 확인
kubectl logs -n ai-platform deployment/agent-service
kubectl logs -n ai-platform deployment/ml-serving
kubectl logs -n ai-platform deployment/dashboard
```

---

## 클러스터 삭제

```bash
# 클러스터만 삭제 (데이터 보존)
kind delete cluster --name ai-platform

# 데이터까지 완전 삭제
./scripts/01-create-cluster.sh --clean

# 호스트 데이터 수동 삭제
rm -rf ~/.ai-platform-data
```
