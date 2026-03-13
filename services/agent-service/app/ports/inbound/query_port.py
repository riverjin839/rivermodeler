"""
Inbound Port - 질의 처리 인터페이스
외부 요청(REST, gRPC 등)이 도메인 서비스를 호출하기 위한 추상 계약
"""

from abc import ABC, abstractmethod
from app.domain.models.query import UserQuery, AgentResponse


class QueryPort(ABC):
    """
    Inbound Port: 사용자 질의 처리
    Inbound Adapter(FastAPI 등)가 이 Port를 통해 도메인 로직에 접근
    """

    @abstractmethod
    async def handle_query(self, query: UserQuery) -> AgentResponse:
        """사용자 질의를 처리하고 Agent 응답 반환"""
        ...
