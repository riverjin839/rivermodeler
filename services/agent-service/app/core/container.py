"""
의존성 주입 컨테이너
헥사고날 아키텍처의 핵심: Port와 Adapter를 조립(wiring)하는 계층

                    ┌─────────────────────────┐
                    │      Container          │
                    │  (의존성 주입 / 조립)     │
                    └─────┬───────────────────┘
                          │
          ┌───────────────┼────────────────┐
          ▼               ▼                ▼
    ┌──────────┐   ┌──────────┐    ┌──────────────┐
    │ ChromaDB │   │  Neo4j   │    │   Ollama     │
    │ Adapter  │   │ Adapter  │    │   Adapter    │
    └──────────┘   └──────────┘    └──────────────┘
         │               │                │
    (VectorDBPort) (GraphDBPort)     (LLMPort)
         │               │                │
         └───────────────┴────────────────┘
                         │
                  OrchestratorService
"""

from app.adapters.outbound.vectordb.chroma_adapter import ChromaDBAdapter
from app.adapters.outbound.neo4j.graph_db_adapter import Neo4jGraphDBAdapter
from app.adapters.outbound.ollama.llm_adapter import OllamaLLMAdapter
from app.adapters.outbound.mlflow.ml_serving_adapter import MLServingAdapter
from app.domain.services.orchestrator import OrchestratorService

# --- 싱글톤 인스턴스 (애플리케이션 수명 주기 동안 유지) ---
_orchestrator: OrchestratorService | None = None


def get_orchestrator() -> OrchestratorService:
    """
    OrchestratorService 싱글톤 팩토리
    Port 인터페이스에 구체적 Adapter 구현체를 주입하여 조립
    """
    global _orchestrator

    if _orchestrator is None:
        # Outbound Adapter 인스턴스 생성
        vector_db = ChromaDBAdapter()
        graph_db = Neo4jGraphDBAdapter()
        llm = OllamaLLMAdapter()
        ml_serving = MLServingAdapter()

        # 도메인 서비스에 Port 구현체 주입 (의존성 역전)
        _orchestrator = OrchestratorService(
            vector_db=vector_db,
            graph_db=graph_db,
            ml_serving=ml_serving,
            llm=llm,
        )

    return _orchestrator
