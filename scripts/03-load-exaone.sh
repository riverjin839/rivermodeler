#!/bin/bash
# =============================================================================
# 3단계: Ollama에 EXAONE 3.0 모델 적재
# Ollama Pod 내부에서 모델 다운로드 실행
# =============================================================================
set -euo pipefail

echo "========================================="
echo " EXAONE 3.0 모델 적재"
echo "========================================="

# Ollama Pod 이름 조회
OLLAMA_POD=$(kubectl get pods -n ai-platform -l app=ollama -o jsonpath='{.items[0].metadata.name}')

if [ -z "$OLLAMA_POD" ]; then
    echo "[ERROR] Ollama Pod을 찾을 수 없습니다."
    exit 1
fi

echo "[INFO] Ollama Pod: $OLLAMA_POD"
echo "[INFO] EXAONE 3.0 모델 다운로드 시작 (시간이 소요됩니다)..."

# Ollama Pod 내부에서 모델 pull
kubectl exec -n ai-platform "$OLLAMA_POD" -- ollama pull exaone3

echo ""
echo "[INFO] 모델 적재 완료. 적재된 모델 목록:"
kubectl exec -n ai-platform "$OLLAMA_POD" -- ollama list

echo ""
echo "========================================="
echo " EXAONE 모델 적재 완료!"
echo " Agent Service에서 자동으로 사용 가능합니다."
echo "========================================="
