#!/bin/bash
# =============================================================================
# 1단계: kind 클러스터 생성 및 Ingress-NGINX 설치
# =============================================================================
set -euo pipefail

CLUSTER_NAME="ai-platform"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "========================================="
echo " AI Platform - kind 클러스터 생성"
echo "========================================="

# 기존 클러스터 확인
if kind get clusters 2>/dev/null | grep -q "$CLUSTER_NAME"; then
    echo "[INFO] 기존 클러스터 '$CLUSTER_NAME' 발견. 삭제 후 재생성합니다."
    kind delete cluster --name "$CLUSTER_NAME"
fi

# kind 클러스터 생성
echo "[STEP 1/3] kind 클러스터 생성 중..."
kind create cluster \
    --config "$PROJECT_DIR/kind-config.yaml" \
    --name "$CLUSTER_NAME"

echo "[STEP 2/3] kubectl context 확인..."
kubectl cluster-info --context "kind-$CLUSTER_NAME"

# Ingress-NGINX 컨트롤러 설치 (kind 전용 매니페스트)
echo "[STEP 3/3] Ingress-NGINX 컨트롤러 설치 중..."
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
echo " 다음 단계: ./scripts/02-deploy-platform.sh"
echo "========================================="
