#!/bin/bash
# =============================================================================
# AI Platform 데이터 백업
#
# 실행 중인 Pod에서 데이터를 추출하여 타임스탬프 디렉토리에 저장
# hostPath 영속화와 별개로, 이동/공유 가능한 포터블 백업을 생성
#
# 백업 대상:
#   - Neo4j:   neo4j-admin database dump → .dump 파일
#   - ChromaDB: /chroma/chroma 디렉토리 → tar.gz
#   - MLflow:  /mlflow 디렉토리 (DB + artifacts) → tar.gz
#   - Ollama:  모델 목록 기록 + /root/.ollama/models → tar.gz
#
# 사용법:
#   ./scripts/backup.sh                    # backups/YYYYMMDD_HHMMSS/ 에 저장
#   ./scripts/backup.sh /path/to/dir       # 지정 디렉토리에 저장
# =============================================================================
set -euo pipefail

NAMESPACE="ai-platform"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_DIR="${1:-$PROJECT_DIR/backups/$TIMESTAMP}"

echo "========================================="
echo " AI Platform - 데이터 백업"
echo " 대상: $BACKUP_DIR"
echo "========================================="

mkdir -p "$BACKUP_DIR"

# --- 헬퍼: Pod 이름 조회 ---
get_pod() {
    kubectl get pods -n "$NAMESPACE" -l "app=$1" -o jsonpath='{.items[0].metadata.name}' 2>/dev/null
}

# --- 헬퍼: Pod 존재 확인 ---
check_pod() {
    local pod
    pod=$(get_pod "$1")
    if [ -z "$pod" ]; then
        echo "  [SKIP] $1 Pod이 실행 중이 아닙니다."
        return 1
    fi
    echo "$pod"
    return 0
}

FAILED=0
BACKED=0

# =============================================================================
# 1. Neo4j 백업 (neo4j-admin database dump)
# =============================================================================
echo ""
echo "[1/4] Neo4j 백업..."
NEO4J_POD=$(check_pod "neo4j") && {
    # neo4j-admin dump은 DB가 중지된 상태에서만 작동하므로
    # 대신 cypher-shell로 전체 노드/관계를 JSON export
    echo "  Pod: $NEO4J_POD"

    # 방법 A: 파일시스템 직접 복사 (가장 안전)
    kubectl exec -n "$NAMESPACE" "$NEO4J_POD" -- \
        bash -c "cd /data && tar czf /tmp/neo4j-backup.tar.gz ." 2>/dev/null && \
    kubectl cp "$NAMESPACE/$NEO4J_POD:/tmp/neo4j-backup.tar.gz" \
        "$BACKUP_DIR/neo4j-data.tar.gz" 2>/dev/null && \
    kubectl exec -n "$NAMESPACE" "$NEO4J_POD" -- rm -f /tmp/neo4j-backup.tar.gz 2>/dev/null

    if [ -f "$BACKUP_DIR/neo4j-data.tar.gz" ]; then
        SIZE=$(du -h "$BACKUP_DIR/neo4j-data.tar.gz" | cut -f1)
        echo "  [OK] neo4j-data.tar.gz ($SIZE)"
        BACKED=$((BACKED + 1))
    else
        echo "  [FAIL] Neo4j 백업 실패"
        FAILED=$((FAILED + 1))
    fi
} || FAILED=$((FAILED + 1))

# =============================================================================
# 2. ChromaDB 백업 (파일시스템 tar)
# =============================================================================
echo ""
echo "[2/4] ChromaDB 백업..."
CHROMA_POD=$(check_pod "chromadb") && {
    echo "  Pod: $CHROMA_POD"

    kubectl exec -n "$NAMESPACE" "$CHROMA_POD" -- \
        tar czf /tmp/chromadb-backup.tar.gz -C /chroma/chroma . 2>/dev/null && \
    kubectl cp "$NAMESPACE/$CHROMA_POD:/tmp/chromadb-backup.tar.gz" \
        "$BACKUP_DIR/chromadb-data.tar.gz" 2>/dev/null && \
    kubectl exec -n "$NAMESPACE" "$CHROMA_POD" -- rm -f /tmp/chromadb-backup.tar.gz 2>/dev/null

    if [ -f "$BACKUP_DIR/chromadb-data.tar.gz" ]; then
        SIZE=$(du -h "$BACKUP_DIR/chromadb-data.tar.gz" | cut -f1)
        echo "  [OK] chromadb-data.tar.gz ($SIZE)"
        BACKED=$((BACKED + 1))
    else
        echo "  [FAIL] ChromaDB 백업 실패"
        FAILED=$((FAILED + 1))
    fi
} || FAILED=$((FAILED + 1))

# =============================================================================
# 3. MLflow 백업 (SQLite DB + artifacts tar)
# =============================================================================
echo ""
echo "[3/4] MLflow 백업..."
MLFLOW_POD=$(check_pod "mlflow") && {
    echo "  Pod: $MLFLOW_POD"

    kubectl exec -n "$NAMESPACE" "$MLFLOW_POD" -- \
        tar czf /tmp/mlflow-backup.tar.gz -C /mlflow . 2>/dev/null && \
    kubectl cp "$NAMESPACE/$MLFLOW_POD:/tmp/mlflow-backup.tar.gz" \
        "$BACKUP_DIR/mlflow-data.tar.gz" 2>/dev/null && \
    kubectl exec -n "$NAMESPACE" "$MLFLOW_POD" -- rm -f /tmp/mlflow-backup.tar.gz 2>/dev/null

    if [ -f "$BACKUP_DIR/mlflow-data.tar.gz" ]; then
        SIZE=$(du -h "$BACKUP_DIR/mlflow-data.tar.gz" | cut -f1)
        echo "  [OK] mlflow-data.tar.gz ($SIZE)"
        BACKED=$((BACKED + 1))
    else
        echo "  [FAIL] MLflow 백업 실패"
        FAILED=$((FAILED + 1))
    fi
} || FAILED=$((FAILED + 1))

# =============================================================================
# 4. Ollama 백업 (모델 목록 + 모델 파일)
# =============================================================================
echo ""
echo "[4/4] Ollama 백업..."
OLLAMA_POD=$(check_pod "ollama") && {
    echo "  Pod: $OLLAMA_POD"

    # 모델 목록 저장 (복구 시 어떤 모델을 pull 해야 하는지 기록)
    kubectl exec -n "$NAMESPACE" "$OLLAMA_POD" -- \
        ollama list 2>/dev/null > "$BACKUP_DIR/ollama-models.txt" || true

    # 모델 blob 파일 백업 (대용량 주의)
    kubectl exec -n "$NAMESPACE" "$OLLAMA_POD" -- \
        tar czf /tmp/ollama-backup.tar.gz -C /root/.ollama . 2>/dev/null && \
    kubectl cp "$NAMESPACE/$OLLAMA_POD:/tmp/ollama-backup.tar.gz" \
        "$BACKUP_DIR/ollama-data.tar.gz" 2>/dev/null && \
    kubectl exec -n "$NAMESPACE" "$OLLAMA_POD" -- rm -f /tmp/ollama-backup.tar.gz 2>/dev/null

    if [ -f "$BACKUP_DIR/ollama-data.tar.gz" ]; then
        SIZE=$(du -h "$BACKUP_DIR/ollama-data.tar.gz" | cut -f1)
        echo "  [OK] ollama-data.tar.gz ($SIZE)"
        echo "  [OK] ollama-models.txt (복구용 모델 목록)"
        BACKED=$((BACKED + 1))
    else
        echo "  [WARN] Ollama 모델 파일 백업 실패 (모델이 없을 수 있음)"
        if [ -s "$BACKUP_DIR/ollama-models.txt" ]; then
            echo "  [OK] ollama-models.txt 저장 완료 (복구 시 모델 재다운로드)"
            BACKED=$((BACKED + 1))
        else
            FAILED=$((FAILED + 1))
        fi
    fi
} || FAILED=$((FAILED + 1))

# =============================================================================
# 메타데이터 기록
# =============================================================================
cat > "$BACKUP_DIR/backup-metadata.json" << METADATA
{
  "timestamp": "$TIMESTAMP",
  "date": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "namespace": "$NAMESPACE",
  "cluster": "$(kubectl config current-context 2>/dev/null || echo 'unknown')",
  "backed_up": $BACKED,
  "failed": $FAILED,
  "contents": [
    $([ -f "$BACKUP_DIR/neo4j-data.tar.gz" ] && echo '"neo4j-data.tar.gz",' || true)
    $([ -f "$BACKUP_DIR/chromadb-data.tar.gz" ] && echo '"chromadb-data.tar.gz",' || true)
    $([ -f "$BACKUP_DIR/mlflow-data.tar.gz" ] && echo '"mlflow-data.tar.gz",' || true)
    $([ -f "$BACKUP_DIR/ollama-data.tar.gz" ] && echo '"ollama-data.tar.gz",' || true)
    $([ -f "$BACKUP_DIR/ollama-models.txt" ] && echo '"ollama-models.txt",' || true)
    "backup-metadata.json"
  ]
}
METADATA

echo ""
echo "========================================="
echo " 백업 완료!"
echo ""
echo " 위치:    $BACKUP_DIR"
echo " 성공:    $BACKED / 4"
echo " 실패:    $FAILED / 4"
echo ""
if [ "$BACKED" -gt 0 ]; then
    echo " 백업 파일:"
    ls -lh "$BACKUP_DIR"/ 2>/dev/null | grep -v total
fi
echo ""
echo " 복구:    ./scripts/restore.sh $BACKUP_DIR"
echo "========================================="
