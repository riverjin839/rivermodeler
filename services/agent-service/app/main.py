"""
Agent Service - FastAPI 엔트리포인트
헥사고날 아키텍처: Inbound Adapter (FastAPI) → Port → Domain Service → Port → Outbound Adapter
"""

from fastapi import FastAPI
from app.adapters.inbound.api.routes import router as api_router

app = FastAPI(
    title="AI Platform Agent Service",
    description="CRISP-DM 기반 AI 오케스트레이션 서비스 (LangGraph + Hexagonal Architecture)",
    version="0.1.0",
)

# --- Inbound Adapter: REST API 라우터 등록 ---
app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    """K8s liveness/readiness probe 용 헬스체크"""
    return {"status": "healthy", "service": "agent-service"}
