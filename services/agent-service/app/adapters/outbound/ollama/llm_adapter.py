"""
Outbound Adapter - Ollama LLM 서빙
LLMPort 구현체. Ollama REST API를 통해 LG EXAONE 3.0 모델 호출

통신: Agent Service → http://ollama-service:11434/api/generate
"""

import httpx
from app.ports.outbound.llm_port import LLMPort
from app.config import settings


class OllamaLLMAdapter(LLMPort):
    """
    Ollama 기반 LLM 어댑터
    EXAONE 3.0 모델을 사용한 텍스트 생성
    """

    def __init__(self):
        self._base_url = settings.ollama_base_url
        self._model = settings.ollama_model

    async def generate(self, prompt: str, temperature: float = 0.7) -> str:
        """
        Ollama API를 통한 텍스트 생성
        POST http://ollama-service:11434/api/generate
        """
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self._base_url}/api/generate",
                    json={
                        "model": self._model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": temperature,
                        },
                    },
                )
                response.raise_for_status()
                return response.json().get("response", "")
        except Exception as e:
            # MVP fallback: Ollama 미연결 시 mock 응답
            return (
                f"[LLM Mock] Ollama({self._model}) 미연결 상태입니다. "
                f"프롬프트 수신 확인: '{prompt[:100]}...'"
            )
