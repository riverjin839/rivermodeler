#!/bin/bash
# =============================================================================
# AI Platform 데이터 복구
#
# 백업 디렉토리에서 데이터를 읽어 실행 중인 Pod에 복원
# 클러스터 재생성 후 02-deploy-platform.sh 실행 뒤 사용
#
# 사용법:
#   ./scripts/restore.sh backups/20260101_120000    # 특정 백업에서 복구
#   ./scripts/restore.sh                            # 최신 백업에서 복구
# =============================================================================
set -euo pipefail

NAMESPACE="ai-platform"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# 백업 디렉토리 결정 (인자 없으면 최신 백업 자동 선택)
if [ -n "${1:-}" ]; then
    BACKUP_DIR="$1"
else
    BACKUP_DIR=$(ls -dt "$PROJECT_DIR/backups"/*/ 2>/dev/null | head -1)
    if [ -z "$BACKUP_DIR" ]; then
        echo "[ERROR] 백업 디렉토리를 찾을 수 없습니다."
        echo "사용법: ./scripts/restore.sh <백업_디렉토리_경로>"
        exit 1
    fi
fi

# 절대 경로로 변환
BACKUP_DIR="$(cd "$BACKUP_DIR" 2>/dev/null && pwd)" || {
    echo "[ERROR] 백업 디렉토리가 존재하지 않습니다: $BACKUP_DIR"
    exit 1
}

echo "========================================="
echo " AI Platform - 데이터 복구"
echo " 소스: $BACKUP_DIR"
echo "========================================="

# 메타데이터 확인
if [ -f "$BACKUP_DIR/backup-metadata.json" ]; then
    echo ""
    echo " 백업 정보:"
    cat "$BACKUP_DIR/backup-metadata.json" 2>/dev/null | head -5
    echo "  ..."
fi

echo ""
echo " [주의] 기존 데이터가 백업 데이터로 덮어쓰기 됩니다."
echo " 계속하시겠습니까? (y/N)"
read -r CONFIRM
if [[ ! "$CONFIRM" =~ ^[yY]$ ]]; then
    echo " 복구를 취소합니다."
    exit 0
fi

# --- 헬퍼: Pod 이름 조회 ---
get_pod() {
    kubectl get pods -n "$NAMESPACE" -l "app=$1" -o jsonpath='{.items[0].metadata.name}' 2>/dev/null
}

wait_for_pod() {
    echo "  $1 Pod 준비 대기 중..."
    kubectl wait --namespace "$NAMESPACE" \
        --for=condition=ready pod \
        --selector="app=$1" \
        --timeout=120s 2>/dev/null || {
        echo "  [WARN] $1 Pod 준비 타임아웃"
        return 1
    }
}

FAILED=0
RESTORED=0

# =============================================================================
# 1. Neo4j 복구
# =============================================================================
echo ""
echo "[1/4] Neo4j 복구..."
if [ -f "$BACKUP_DIR/neo4j-data.tar.gz" ]; then
    wait_for_pod "neo4j" && {
        NEO4J_POD=$(get_pod "neo4j")
        echo "  Pod: $NEO4J_POD"

        # 기존 데이터 정리 후 복원
        kubectl cp "$BACKUP_DIR/neo4j-data.tar.gz" \
            "$NAMESPACE/$NEO4J_POD:/tmp/neo4j-backup.tar.gz" 2>/dev/null && \
        kubectl exec -n "$NAMESPACE" "$NEO4J_POD" -- \
            bash -c "cd /data && rm -rf databases transactions && tar xzf /tmp/neo4j-backup.tar.gz && rm -f /tmp/neo4j-backup.tar.gz" 2>/dev/null

        if [ $? -eq 0 ]; then
            echo "  [OK] Neo4j 데이터 복구 완료"
            echo "  [INFO] Neo4j를 재시작합니다..."
            kubectl rollout restart statefulset/neo4j -n "$NAMESPACE" 2>/dev/null
            RESTORED=$((RESTORED + 1))
        else
            echo "  [FAIL] Neo4j 복구 실패"
            FAILED=$((FAILED + 1))
        fi
    } || FAILED=$((FAILED + 1))
else
    echo "  [SKIP] neo4j-data.tar.gz 없음"
fi

# =============================================================================
# 2. ChromaDB 복구
# =============================================================================
echo ""
echo "[2/4] ChromaDB 복구..."
if [ -f "$BACKUP_DIR/chromadb-data.tar.gz" ]; then
    wait_for_pod "chromadb" && {
        CHROMA_POD=$(get_pod "chromadb")
        echo "  Pod: $CHROMA_POD"

        kubectl cp "$BACKUP_DIR/chromadb-data.tar.gz" \
            "$NAMESPACE/$CHROMA_POD:/tmp/chromadb-backup.tar.gz" 2>/dev/null && \
        kubectl exec -n "$NAMESPACE" "$CHROMA_POD" -- \
            bash -c "cd /chroma/chroma && rm -rf * && tar xzf /tmp/chromadb-backup.tar.gz && rm -f /tmp/chromadb-backup.tar.gz" 2>/dev/null

        if [ $? -eq 0 ]; then
            echo "  [OK] ChromaDB 데이터 복구 완료"
            echo "  [INFO] ChromaDB를 재시작합니다..."
            kubectl rollout restart deployment/chromadb -n "$NAMESPACE" 2>/dev/null
            RESTORED=$((RESTORED + 1))
        else
            echo "  [FAIL] ChromaDB 복구 실패"
            FAILED=$((FAILED + 1))
        fi
    } || FAILED=$((FAILED + 1))
else
    echo "  [SKIP] chromadb-data.tar.gz 없음"
fi

# =============================================================================
# 3. MLflow 복구
# =============================================================================
echo ""
echo "[3/4] MLflow 복구..."
if [ -f "$BACKUP_DIR/mlflow-data.tar.gz" ]; then
    wait_for_pod "mlflow" && {
        MLFLOW_POD=$(get_pod "mlflow")
        echo "  Pod: $MLFLOW_POD"

        kubectl cp "$BACKUP_DIR/mlflow-data.tar.gz" \
            "$NAMESPACE/$MLFLOW_POD:/tmp/mlflow-backup.tar.gz" 2>/dev/null && \
        kubectl exec -n "$NAMESPACE" "$MLFLOW_POD" -- \
            bash -c "cd /mlflow && rm -rf * && tar xzf /tmp/mlflow-backup.tar.gz && rm -f /tmp/mlflow-backup.tar.gz" 2>/dev/null

        if [ $? -eq 0 ]; then
            echo "  [OK] MLflow 데이터 복구 완료"
            echo "  [INFO] MLflow를 재시작합니다..."
            kubectl rollout restart deployment/mlflow -n "$NAMESPACE" 2>/dev/null
            RESTORED=$((RESTORED + 1))
        else
            echo "  [FAIL] MLflow 복구 실패"
            FAILED=$((FAILED + 1))
        fi
    } || FAILED=$((FAILED + 1))
else
    echo "  [SKIP] mlflow-data.tar.gz 없음"
fi

# =============================================================================
# 4. Ollama 복구 (모델 파일 복원 또는 재다운로드)
# =============================================================================
echo ""
echo "[4/4] Ollama 복구..."
if [ -f "$BACKUP_DIR/ollama-data.tar.gz" ]; then
    wait_for_pod "ollama" && {
        OLLAMA_POD=$(get_pod "ollama")
        echo "  Pod: $OLLAMA_POD"

        kubectl cp "$BACKUP_DIR/ollama-data.tar.gz" \
            "$NAMESPACE/$OLLAMA_POD:/tmp/ollama-backup.tar.gz" 2>/dev/null && \
        kubectl exec -n "$NAMESPACE" "$OLLAMA_POD" -- \
            bash -c "cd /root/.ollama && tar xzf /tmp/ollama-backup.tar.gz && rm -f /tmp/ollama-backup.tar.gz" 2>/dev/null

        if [ $? -eq 0 ]; then
            echo "  [OK] Ollama 모델 파일 복구 완료"
            RESTORED=$((RESTORED + 1))
            # 복구 후 모델 목록 확인
            echo "  [INFO] 복구된 모델 목록:"
            kubectl exec -n "$NAMESPACE" "$OLLAMA_POD" -- ollama list 2>/dev/null || true
        else
            echo "  [FAIL] Ollama 파일 복구 실패"
            FAILED=$((FAILED + 1))
        fi
    } || FAILED=$((FAILED + 1))
elif [ -f "$BACKUP_DIR/ollama-models.txt" ]; then
    # 모델 파일이 없으면 목록 기반 재다운로드
    wait_for_pod "ollama" && {
        OLLAMA_POD=$(get_pod "ollama")
        echo "  Pod: $OLLAMA_POD"
        echo "  [INFO] 모델 파일 없음. 목록 기반 재다운로드 시작..."

        while IFS= read -r line; do
            # 헤더 행과 빈 줄 건너뛰기
            [[ "$line" =~ ^NAME || -z "$line" ]] && continue
            MODEL_NAME=$(echo "$line" | awk '{print $1}')
            if [ -n "$MODEL_NAME" ]; then
                echo "  → $MODEL_NAME 다운로드 중..."
                kubectl exec -n "$NAMESPACE" "$OLLAMA_POD" -- \
                    ollama pull "$MODEL_NAME" 2>/dev/null || \
                    echo "    [WARN] $MODEL_NAME 다운로드 실패"
            fi
        done < "$BACKUP_DIR/ollama-models.txt"

        RESTORED=$((RESTORED + 1))
        echo "  [OK] Ollama 모델 재다운로드 완료"
    } || FAILED=$((FAILED + 1))
else
    echo "  [SKIP] ollama 백업 파일 없음"
fi

# =============================================================================
# 완료 리포트
# =============================================================================
echo ""
echo "========================================="
echo " 복구 완료!"
echo ""
echo " 소스:    $BACKUP_DIR"
echo " 성공:    $RESTORED / 4"
echo " 실패:    $FAILED / 4"
echo ""
echo " Pod 상태 확인:"
echo "   kubectl get pods -n $NAMESPACE"
echo "========================================="

exit "$FAILED"
