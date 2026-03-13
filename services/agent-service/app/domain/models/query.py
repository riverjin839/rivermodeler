"""
도메인 모델 - 사용자 질의 및 응답
비즈니스 로직의 핵심 엔티티. 외부 인프라에 비종속적인 순수 도메인 객체
"""

from pydantic import BaseModel
from enum import Enum
from typing import Optional


class ToolType(str, Enum):
    """Agent가 라우팅할 수 있는 Tool 유형"""
    VECTOR_RAG = "vector_rag"      # ChromaDB 기반 일반 RAG
    GRAPH_RAG = "graph_rag"        # Neo4j 기반 GraphRAG / Ontology 질의
    ML_PREDICTION = "ml_prediction" # 전통 ML 모델 예측


class UserQuery(BaseModel):
    """사용자 입력 질의"""
    question: str
    context: Optional[str] = None


class AgentResponse(BaseModel):
    """Agent 최종 응답"""
    answer: str
    tool_used: ToolType
    source_details: Optional[dict] = None


class ToolResult(BaseModel):
    """개별 Tool 실행 결과 (도메인 내부 전달용)"""
    tool_type: ToolType
    content: str
    metadata: Optional[dict] = None
