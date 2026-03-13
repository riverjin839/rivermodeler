"""
Outbound Adapter - ML Serving
MLServingPort 구현체. ML 서빙 서비스의 REST API를 통해 추론 요청

통신: Agent Service → http://ml-serving-service:8081/predict
"""

import httpx
from app.ports.outbound.ml_serving_port import MLServingPort
from app.config import settings


class MLServingAdapter(MLServingPort):
    """
    ML Serving 어댑터
    전통적 ML 모델 추론 서비스와 HTTP 통신
    """

    def __init__(self):
        self._base_url = settings.ml_serving_url

    async def predict(self, question: str) -> str:
        """
        ML 모델 추론 요청
        POST http://ml-serving-service:8081/predict
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self._base_url}/predict",
                    json={"input_text": question},
                )
                response.raise_for_status()
                result = response.json()
                return f"ML 예측 결과: {result}"
        except Exception as e:
            return (
                f"[ML Mock] ML 서빙 서비스 미연결 상태. "
                f"입력: '{question[:80]}...', 오류: {str(e)}"
            )

    async def get_model_info(self) -> dict:
        """현재 서빙 중인 모델 정보 조회"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self._base_url}/model-info")
                response.raise_for_status()
                return response.json()
        except Exception:
            return {"status": "unavailable", "message": "ML 서빙 서비스 미연결"}
