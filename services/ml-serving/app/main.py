"""
ML Serving Service - FastAPI 엔트리포인트
전통적 ML 모델 추론 + Evidently AI 기반 실시간 Drift 감지

통신:
  Inbound: Agent Service → http://ml-serving-service:8081/predict
  Internal: Evidently AI 리포트 생성 (in-process)
  Outbound: MLflow Registry → http://mlflow-service:5000 (모델 로드)

추론 파이프라인:
  1. /predict 요청 수신
  2. 입력 전처리 → ML 모델 추론
  3. 입력 데이터를 DriftDetector 버퍼에 적재
  4. 윈도우 크기 도달 시 Evidently Drift 검사 자동 실행
  5. Drift 감지 시 경고 로그 + 메트릭 노출
"""

import logging
from contextlib import asynccontextmanager

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.drift.detector import DriftDetector

logger = logging.getLogger(__name__)

# --- MVP: 샘플 Reference 데이터 및 모델 (실제로는 MLflow에서 로드) ---
FEATURE_COLUMNS = ["feature_1", "feature_2", "feature_3", "feature_4"]

# 학습 시 기준 데이터 (MVP: 랜덤 생성, 실제로는 학습 데이터셋에서 추출)
np.random.seed(42)
REFERENCE_DATA = pd.DataFrame(
    np.random.randn(500, len(FEATURE_COLUMNS)),
    columns=FEATURE_COLUMNS,
)

# Drift 감지기 인스턴스
drift_detector: DriftDetector | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 수명 주기 관리"""
    global drift_detector
    drift_detector = DriftDetector(
        reference_data=REFERENCE_DATA,
        feature_columns=FEATURE_COLUMNS,
        window_size=50,       # 50건 수집 후 Drift 검사
        drift_threshold=0.3,  # 30% 이상 피처 드리프트 시 알림
    )
    logger.info("DriftDetector 초기화 완료")
    yield
    logger.info("ML Serving 종료")


app = FastAPI(
    title="ML Serving Service",
    description="전통 ML 모델 추론 + Evidently AI Drift 모니터링",
    version="0.1.0",
    lifespan=lifespan,
)


# --- Request/Response 모델 ---
class PredictRequest(BaseModel):
    """추론 요청"""
    input_text: str | None = None
    features: dict[str, float] | None = None


class PredictResponse(BaseModel):
    """추론 응답"""
    prediction: float
    confidence: float
    drift_alert: dict | None = None


class DriftStatusResponse(BaseModel):
    """Drift 상태 조회 응답"""
    buffer_size: int
    window_size: int
    total_predictions: int
    drift_detected_count: int
    drift_threshold: float
    monitored_features: list[str]


# --- API 엔드포인트 ---
@app.get("/health")
async def health_check():
    """K8s liveness/readiness probe"""
    return {"status": "healthy", "service": "ml-serving"}


@app.post("/predict", response_model=PredictResponse)
async def predict(request: PredictRequest):
    """
    ML 모델 추론 + 실시간 Drift 감지

    1. 입력 피처로 모델 추론 수행
    2. 입력 데이터를 DriftDetector에 적재
    3. 윈도우 크기 도달 시 자동 Drift 검사 결과 반환
    """
    # MVP: 피처가 없으면 랜덤 생성 (실제로는 입력 전처리 파이프라인)
    if request.features:
        input_features = {col: request.features.get(col, 0.0) for col in FEATURE_COLUMNS}
    else:
        input_features = {col: float(np.random.randn()) for col in FEATURE_COLUMNS}

    # --- 1. ML 모델 추론 (MVP: Mock 추론) ---
    # 실제로는 MLflow에서 로드한 모델로 predict
    prediction = float(np.mean(list(input_features.values())))
    confidence = float(np.random.uniform(0.7, 0.99))

    # --- 2. Drift 감지기에 데이터 적재 ---
    drift_result = None
    if drift_detector:
        drift_result = drift_detector.record_prediction(input_features)

    return PredictResponse(
        prediction=prediction,
        confidence=confidence,
        drift_alert=drift_result,
    )


@app.get("/drift/status", response_model=DriftStatusResponse)
async def drift_status():
    """현재 Drift 감지기 상태 조회"""
    if drift_detector is None:
        raise HTTPException(status_code=503, detail="DriftDetector 미초기화")
    return DriftStatusResponse(**drift_detector.get_status())


@app.get("/model-info")
async def model_info():
    """서빙 중인 모델 정보 (MVP: Mock)"""
    return {
        "model_name": "sample_classifier_v1",
        "model_version": "1.0.0",
        "framework": "scikit-learn",
        "features": FEATURE_COLUMNS,
        "mlflow_run_id": "mock-run-id-001",
        "status": "serving",
    }
