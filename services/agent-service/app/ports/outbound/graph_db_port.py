"""
Outbound Port - Graph DB 인터페이스
Neo4j 등 그래프 DB 구현에 비종속적인 추상 계약
"""

from abc import ABC, abstractmethod


class GraphDBPort(ABC):
    """
    Outbound Port: Knowledge Graph / Ontology 질의
    구체적 Graph DB 구현(Neo4j, Neptune 등)은 Adapter에서 담당
    """

    @abstractmethod
    async def query_knowledge_graph(self, question: str) -> str:
        """자연어 질문 기반 Knowledge Graph 탐색"""
        ...

    @abstractmethod
    async def add_entity(self, entity_type: str, properties: dict) -> None:
        """엔티티(노드) 추가"""
        ...

    @abstractmethod
    async def add_relationship(self, from_id: str, to_id: str, rel_type: str) -> None:
        """관계(엣지) 추가"""
        ...
