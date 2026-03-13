"""
Outbound Adapter - ChromaDB Vector DB
VectorDBPort 구현체. ChromaDB REST API로 벡터 유사도 검색

통신: Agent Service → http://chromadb-service:8000
"""

import chromadb
from app.ports.outbound.vector_db_port import VectorDBPort
from app.config import settings


class ChromaDBAdapter(VectorDBPort):
    """
    ChromaDB 기반 Vector DB 어댑터
    문서 임베딩 저장 및 유사도 검색 수행
    """

    def __init__(self):
        try:
            # ChromaDB HTTP 클라이언트 (K8s Service 통신)
            self._client = chromadb.HttpClient(
                host=settings.chromadb_host.replace("http://", "").split(":")[0],
                port=int(settings.chromadb_host.split(":")[-1]),
            )
            self._collection = self._client.get_or_create_collection(
                name="ai_platform_docs",
                metadata={"description": "AI Platform RAG용 문서 컬렉션"},
            )
        except Exception:
            # MVP fallback: 연결 실패 시 None으로 초기화
            self._client = None
            self._collection = None

    async def similarity_search(self, query: str, top_k: int = 3) -> str:
        """
        벡터 유사도 기반 문서 검색
        ChromaDB가 자체 임베딩 모델로 쿼리를 벡터화하여 검색
        """
        if self._collection is None:
            return "[VectorRAG Mock] ChromaDB 미연결 상태. 샘플 응답을 반환합니다."

        try:
            results = self._collection.query(
                query_texts=[query],
                n_results=top_k,
            )
            if results["documents"] and results["documents"][0]:
                docs = "\n---\n".join(results["documents"][0])
                return f"Vector DB 검색 결과 (상위 {top_k}건):\n{docs}"
            return "Vector DB에서 관련 문서를 찾지 못했습니다."
        except Exception as e:
            return f"[VectorRAG Mock] ChromaDB 검색 실패: {str(e)}"

    async def add_documents(self, documents: list[str], metadatas: list[dict] | None = None) -> None:
        """문서를 벡터화하여 ChromaDB에 저장"""
        if self._collection is None:
            return

        ids = [f"doc_{i}" for i in range(len(documents))]
        self._collection.add(
            documents=documents,
            ids=ids,
            metadatas=metadatas,
        )
