"""
ML Drift 감지 파이프라인 - Evidently AI 기반
CRISP-DM의 '모니터링' 단계 구현

동작 원리:
1. 추론 요청마다 입력 데이터를 버퍼에 적재
2. 버퍼가 임계 크기(window_size)에 도달하면 Drift 검사 실행
3. Evidently AI가 Reference 데이터 대비 Current 데이터의 분포 변화 감지
4. Drift 임계치 초과 시 알림 (로그 + 메트릭)

Drift 유형:
- Data Drift: 입력 피처 분포 변화 (예: 고객 연령대 분포 변동)
- Concept Drift: 입력-출력 관계 변화 (예: 동일 피처인데 다른 결과)
"""

import logging
from collections import deque
from typing import Optional

import numpy as np
import pandas as pd
from evidently.report import Report
from evidently.metric_preset import DataDriftPreset, DataQualityPreset

logger = logging.getLogger(__name__)


class DriftDetector:
    """
    실시간 Drift 감지기

    추론 요청마다 데이터를 수집하고, 윈도우 크기에 도달하면
    Evidently AI를 사용해 Data Drift / Concept Drift 여부를 판단
    """

    def __init__(
        self,
        reference_data: pd.DataFrame,
        feature_columns: list[str],
        window_size: int = 100,
        drift_threshold: float = 0.3,
    ):
        """
        Args:
            reference_data: 학습 시 사용한 기준 데이터셋 (분포 비교 기준)
            feature_columns: 모니터링할 피처 컬럼명
            window_size: Drift 검사를 트리거할 데이터 수집 크기
            drift_threshold: Drift 판정 임계치 (0.0 ~ 1.0)
        """
        self._reference = reference_data[feature_columns]
        self._feature_columns = feature_columns
        self._window_size = window_size
        self._drift_threshold = drift_threshold

        # 슬라이딩 윈도우 버퍼 (메모리 효율적)
        self._buffer: deque[dict] = deque(maxlen=window_size)
        self._total_predictions = 0
        self._drift_detected_count = 0

    def record_prediction(self, input_features: dict) -> Optional[dict]:
        """
        추론 결과를 버퍼에 적재하고, 윈도우 크기 도달 시 Drift 검사 실행

        Args:
            input_features: 추론 입력 피처 딕셔너리
                예: {"age": 35, "income": 50000, "credit_score": 720}

        Returns:
            Drift 감지 결과 (검사 실행 시) 또는 None (버퍼 미충족 시)
        """
        self._total_predictions += 1

        # 1단계: 버퍼에 데이터 적재
        self._buffer.append(input_features)

        # 2단계: 윈도우 크기 도달 시 Drift 검사
        if len(self._buffer) >= self._window_size:
            drift_result = self._run_drift_check()
            self._buffer.clear()
            return drift_result

        return None

    def _run_drift_check(self) -> dict:
        """
        Evidently AI를 사용한 Data Drift 검사

        Returns:
            {
                "is_drifted": bool,
                "drift_score": float,          # 전체 드리프트 점수
                "drifted_features": list[str], # 드리프트된 피처 목록
                "total_features": int,
                "details": dict,               # 피처별 상세 결과
            }
        """
        # 현재 윈도우 데이터를 DataFrame으로 변환
        current_data = pd.DataFrame(list(self._buffer), columns=self._feature_columns)

        # Evidently Report 생성 (Data Drift + 데이터 품질)
        report = Report(metrics=[DataDriftPreset()])

        report.run(
            reference_data=self._reference,
            current_data=current_data,
        )

        # Report 결과 파싱
        report_dict = report.as_dict()
        drift_metrics = report_dict["metrics"][0]["result"]

        # 드리프트된 피처 추출
        drifted_features = []
        feature_details = {}

        if "drift_by_columns" in drift_metrics:
            for col_name, col_result in drift_metrics["drift_by_columns"].items():
                feature_details[col_name] = {
                    "drift_detected": col_result.get("drift_detected", False),
                    "drift_score": col_result.get("drift_score", 0.0),
                    "stattest_name": col_result.get("stattest_name", ""),
                }
                if col_result.get("drift_detected", False):
                    drifted_features.append(col_name)

        drift_share = drift_metrics.get("share_of_drifted_columns", 0.0)
        is_drifted = drift_share > self._drift_threshold

        if is_drifted:
            self._drift_detected_count += 1
            logger.warning(
                f"[DRIFT ALERT] Data Drift 감지! "
                f"드리프트 비율: {drift_share:.2%}, "
                f"드리프트 피처: {drifted_features}, "
                f"누적 감지 횟수: {self._drift_detected_count}"
            )

        return {
            "is_drifted": is_drifted,
            "drift_score": drift_share,
            "drifted_features": drifted_features,
            "total_features": len(self._feature_columns),
            "total_predictions": self._total_predictions,
            "drift_detected_count": self._drift_detected_count,
            "details": feature_details,
        }

    def get_status(self) -> dict:
        """현재 Drift 감지기 상태 조회"""
        return {
            "buffer_size": len(self._buffer),
            "window_size": self._window_size,
            "total_predictions": self._total_predictions,
            "drift_detected_count": self._drift_detected_count,
            "drift_threshold": self._drift_threshold,
            "monitored_features": self._feature_columns,
        }
