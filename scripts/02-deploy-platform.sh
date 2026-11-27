#!/bin/bash
# =============================================================================
# 2단계: AI Platform 컴포넌트 배포
# 로컬 Docker 이미지 빌드 → kind 클러스터 로드 → K8s 매니페스트 적용
# =============================================================================
set -euo pipefail

CLUSTER_NAME="ai-platform"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "========================================="
echo " AI Platform - 컴포넌트 배포"
echo "========================================="

# --- 1. Namespace 생성 ---
echo "[STEP 1/5] Namespace 생성..."
kubectl apply -f "$PROJECT_DIR/k8s/base/namespace.yaml"

# --- 2. 로컬 Docker 이미지 빌드 ---
echo "[STEP 2/5] Docker 이미지 빌드..."

echo "  → agent-service 빌드 중..."
docker build -t agent-service:latest "$PROJECT_DIR/services/agent-service"

echo "  → ml-serving 빌드 중..."
docker build -t ml-serving:latest "$PROJECT_DIR/services/ml-serving"

echo "  → dashboard 빌드 중..."
docker build -t dashboard:latest "$PROJECT_DIR/services/dashboard"

# --- 3. kind 클러스터에 이미지 로드 ---
echo "[STEP 3/5] kind 클러스터에 이미지 로드..."
kind load docker-image agent-service:latest --name "$CLUSTER_NAME"
kind load docker-image ml-serving:latest --name "$CLUSTER_NAME"
kind load docker-image dashboard:latest --name "$CLUSTER_NAME"

# --- 4. 인프라 컴포넌트 배포 (DB, LLM) ---
echo "[STEP 4/5] 인프라 컴포넌트 배포..."
kubectl apply -f "$PROJECT_DIR/k8s/base/neo4j.yaml"
kubectl apply -f "$PROJECT_DIR/k8s/base/chromadb.yaml"
kubectl apply -f "$PROJECT_DIR/k8s/base/ollama.yaml"
kubectl apply -f "$PROJECT_DIR/k8s/base/mlflow.yaml"

echo "  → 인프라 Pod 준비 대기 중 (최대 180초)..."
kubectl wait --namespace ai-platform \
    --for=condition=ready pod \
    --selector=component=graph-db \
    --timeout=180s || echo "  [WARN] Neo4j 준비 대기 타임아웃 (계속 진행)"

kubectl wait --namespace ai-platform \
    --for=condition=ready pod \
    --selector=component=vector-db \
    --timeout=120s || echo "  [WARN] ChromaDB 준비 대기 타임아웃 (계속 진행)"

# --- 5. 애플리케이션 서비스 배포 ---
echo "[STEP 5/5] 애플리케이션 서비스 배포..."
kubectl apply -f "$PROJECT_DIR/k8s/base/agent-service.yaml"
kubectl apply -f "$PROJECT_DIR/k8s/base/ml-serving.yaml"
kubectl apply -f "$PROJECT_DIR/k8s/base/dashboard.yaml"
kubectl apply -f "$PROJECT_DIR/k8s/base/ingress.yaml"

echo ""
echo "========================================="
echo " 배포 완료!"
echo ""
echo " /etc/hosts에 아래 항목 추가 필요:"
echo "   127.0.0.1 ai-platform.local dashboard.ai-platform.local"
echo ""
echo " 접속 URL:"
echo "   Dashboard:  http://dashboard.ai-platform.local/"
echo "   Agent API:  http://ai-platform.local/api/v1/query"
echo "   ML API:     http://ai-platform.local/ml/predict"
echo "   MLflow UI:  http://ai-platform.local/mlflow/"
echo "   Neo4j:      http://ai-platform.local/neo4j/"
echo ""
echo " 상태 확인:"
echo "   kubectl get pods -n ai-platform"
echo "   kubectl get svc -n ai-platform"
echo "========================================="
