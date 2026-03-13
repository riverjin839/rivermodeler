"""
Inbound Adapter - FastAPI REST API 라우터
외부 HTTP 요청을 받아 도메인 서비스로 전달하는 어댑터 계층

통신 흐름:
  Client → Ingress → [이 라우터] → OrchestratorService → Outbound Adapters
"""

from fastapi import APIRouter, HTTPException
from app.domain.models.query import UserQuery, AgentResponse, ToolType
from app.core.container import get_orchestrator

router = APIRouter()


@router.post("/query", response_model=AgentResponse)
async def process_query(query: UserQuery):
    """
    사용자 질의 처리 엔드포인트

    LangGraph 오케스트레이터가 질문을 분석하여 적절한 Tool로 라우팅:
    - Vector RAG (ChromaDB): 일반 문서 검색 기반 답변
    - Graph RAG (Neo4j): Knowledge Graph / Ontology 기반 답변
    - ML Prediction: 전통 ML 모델 예측 결과 기반 답변
    """
    try:
        orchestrator = get_orchestrator()
        result = await orchestrator.process_query(
            question=query.question,
            context=query.context or "",
        )
        return AgentResponse(
            answer=result["answer"],
            tool_used=ToolType(result["tool_used"]),
            source_details={"method": "langgraph_orchestration"},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent 처리 중 오류: {str(e)}")


@router.get("/tools")
async def list_tools():
    """사용 가능한 Tool 목록 조회"""
    return {
        "tools": [
            {
                "name": ToolType.VECTOR_RAG.value,
                "description": "ChromaDB 기반 벡터 유사도 검색 (일반 RAG)",
                "endpoint": "chromadb-service:8000",
            },
            {
                "name": ToolType.GRAPH_RAG.value,
                "description": "Neo4j 기반 Knowledge Graph 탐색 (GraphRAG)",
                "endpoint": "neo4j-service:7687",
            },
            {
                "name": ToolType.ML_PREDICTION.value,
                "description": "전통 ML 모델 추론 (MLflow 서빙)",
                "endpoint": "ml-serving-service:8081",
            },
        ]
    }
