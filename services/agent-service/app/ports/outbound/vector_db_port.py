"""
Outbound Port - Vector DB 인터페이스
ChromaDB, Milvus 등 벡터 DB 구현에 비종속적인 추상 계약
"""

from abc import ABC, abstractmethod


class VectorDBPort(ABC):
    """
    Outbound Port: 벡터 유사도 검색
    구체적 Vector DB 구현(ChromaDB, Milvus 등)은 Adapter에서 담당
    """

    @abstractmethod
    async def similarity_search(self, query: str, top_k: int = 3) -> str:
        """벡터 유사도 기반 문서 검색"""
        ...

    @abstractmethod
    async def add_documents(self, documents: list[str], metadatas: list[dict] | None = None) -> None:
        """문서를 벡터화하여 저장"""
        ...
