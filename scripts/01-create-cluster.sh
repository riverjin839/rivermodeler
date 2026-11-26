#!/bin/bash
# =============================================================================
# 1단계: kind 클러스터 생성 및 Ingress-NGINX 설치
#
# 데이터 영속화:
#   호스트의 ~/.ai-platform-data/ 에 각 서비스 데이터를 보존
#   클러스터를 삭제/재생성해도 이 디렉토리의 데이터는 유지됩니다.
#
# 사용법:
#   ./scripts/01-create-cluster.sh              # 기본 (기존 클러스터 삭제 후 재생성)
#   ./scripts/01-create-cluster.sh --clean      # 데이터까지 모두 초기화
# =============================================================================
set -euo pipefail

CLUSTER_NAME="ai-platform"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# 데이터 디렉토리 (환경변수로 오버라이드 가능)
DATA_DIR="${AI_PLATFORM_DATA_DIR:-$HOME/.ai-platform-data}"

# 옵션 파싱
CLEAN_DATA=false
for arg in "$@"; do
    case "$arg" in
        --clean)
            CLEAN_DATA=true
            ;;
    esac
done

echo "========================================="
echo " AI Platform - kind 클러스터 생성"
echo " 데이터 디렉토리: $DATA_DIR"
echo "========================================="

# =============================================================================
# 1. 기존 클러스터 처리
# =============================================================================
if kind get clusters 2>/dev/null | grep -q "$CLUSTER_NAME"; then
    echo ""
    echo "[INFO] 기존 클러스터 '$CLUSTER_NAME' 발견."

    if [ "$CLEAN_DATA" = true ]; then
        echo "[WARN] --clean 옵션: 데이터를 포함하여 모두 삭제합니다."
    else
        echo "[INFO] 클러스터만 삭제합니다. 데이터는 $DATA_DIR 에 보존됩니다."
        echo ""
        echo "  ※ 데이터까지 초기화하려면: ./scripts/01-create-cluster.sh --clean"
        echo "  ※ 사전 백업 권장:          ./scripts/backup.sh"
    fi

    kind delete cluster --name "$CLUSTER_NAME"
fi

# =============================================================================
# 2. 호스트 데이터 디렉토리 준비
# =============================================================================
echo ""
echo "[STEP 1/4] 호스트 데이터 디렉토리 준비..."

if [ "$CLEAN_DATA" = true ] && [ -d "$DATA_DIR" ]; then
    echo "  → 기존 데이터 삭제 중: $DATA_DIR"
    rm -rf "$DATA_DIR"
fi

# 각 서비스별 데이터 디렉토리 생성
for SVC in neo4j chromadb ollama mlflow; do
    if [ -d "$DATA_DIR/$SVC" ]; then
        echo "  [존재] $DATA_DIR/$SVC (기존 데이터 보존)"
    else
        mkdir -p "$DATA_DIR/$SVC"
        echo "  [생성] $DATA_DIR/$SVC"
    fi
done

# =============================================================================
# 3. kind-config.yaml의 환경변수를 실제 경로로 치환하여 임시 config 생성
# =============================================================================
echo ""
echo "[STEP 2/4] kind 클러스터 설정 생성..."

# kind는 환경변수 치환을 지원하지 않으므로 sed로 실제 경로 삽입
TEMP_CONFIG=$(mktemp)
sed "s|\${AI_PLATFORM_DATA_DIR:-\${HOME}/.ai-platform-data}|$DATA_DIR|g" \
    "$PROJECT_DIR/kind-config.yaml" > "$TEMP_CONFIG"

echo "  → 데이터 마운트 경로: $DATA_DIR → /data/ai-platform/"

# =============================================================================
# 4. kind 클러스터 생성
# =============================================================================
echo ""
echo "[STEP 3/4] kind 클러스터 생성 중..."
kind create cluster \
    --config "$TEMP_CONFIG" \
    --name "$CLUSTER_NAME"

rm -f "$TEMP_CONFIG"

echo ""
kubectl cluster-info --context "kind-$CLUSTER_NAME"

# =============================================================================
# 5. Ingress-NGINX 컨트롤러 설치
# =============================================================================
echo ""
echo "[STEP 4/4] Ingress-NGINX 컨트롤러 설치 중..."
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml

echo ""
echo "[INFO] Ingress 컨트롤러 Pod 준비 대기 중..."
kubectl wait --namespace ingress-nginx \
    --for=condition=ready pod \
    --selector=app.kubernetes.io/component=controller \
    --timeout=120s

echo ""
echo "========================================="
echo " 클러스터 생성 완료!"
echo ""
echo " 데이터 영속화:"
echo "   $DATA_DIR/neo4j     → Neo4j 그래프 데이터"
echo "   $DATA_DIR/chromadb  → ChromaDB 벡터 데이터"
echo "   $DATA_DIR/ollama    → Ollama LLM 모델 파일"
echo "   $DATA_DIR/mlflow    → MLflow 실험/모델 데이터"
echo ""
if [ "$(ls -A "$DATA_DIR/neo4j" 2>/dev/null)" ] || \
   [ "$(ls -A "$DATA_DIR/chromadb" 2>/dev/null)" ]; then
    echo " [INFO] 기존 데이터가 감지되었습니다."
    echo "        배포 후 자동으로 기존 데이터가 연결됩니다."
fi
echo ""
echo " 다음 단계: ./scripts/02-deploy-platform.sh"
echo "========================================="
