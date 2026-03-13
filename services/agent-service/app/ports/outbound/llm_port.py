"""
Outbound Port - LLM 인터페이스
Ollama, OpenAI 등 LLM 서빙 구현에 비종속적인 추상 계약
"""

from abc import ABC, abstractmethod


class LLMPort(ABC):
    """
    Outbound Port: LLM 텍스트 생성
    구체적 LLM 서빙 구현(Ollama, vLLM 등)은 Adapter에서 담당
    """

    @abstractmethod
    async def generate(self, prompt: str, temperature: float = 0.7) -> str:
        """프롬프트 기반 텍스트 생성"""
        ...
