"""
Outbound Port - ML 서빙 인터페이스
ML 추론 서비스 구현에 비종속적인 추상 계약
"""

from abc import ABC, abstractmethod


class MLServingPort(ABC):
    """
    Outbound Port: 전통적 ML 모델 추론
    MLflow, TensorFlow Serving 등 구현은 Adapter에서 담당
    """

    @abstractmethod
    async def predict(self, question: str) -> str:
        """ML 모델 추론 요청"""
        ...

    @abstractmethod
    async def get_model_info(self) -> dict:
        """현재 서빙 중인 모델 정보 조회"""
        ...
