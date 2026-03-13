"""
Outbound Adapter - Neo4j GraphDB
GraphDBPort 구현체. Neo4j Bolt 프로토콜로 Knowledge Graph 질의

통신: Agent Service → bolt://neo4j-service:7687
"""

from neo4j import AsyncGraphDatabase
from app.ports.outbound.graph_db_port import GraphDBPort
from app.config import settings


class Neo4jGraphDBAdapter(GraphDBPort):
    """
    Neo4j 기반 Graph DB 어댑터
    Ontology 및 Knowledge Graph 관련 CRUD 및 질의 수행
    """

    def __init__(self):
        self._driver = AsyncGraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )

    async def query_knowledge_graph(self, question: str) -> str:
        """
        자연어 질문을 Cypher 질의로 변환하여 Neo4j 검색
        MVP: 간단한 키워드 기반 노드 검색. 프로덕션에서는 LLM 기반 Text-to-Cypher 적용
        """
        try:
            async with self._driver.session() as session:
                # MVP: 질문에서 키워드를 추출하여 관련 노드와 관계 검색
                result = await session.run(
                    """
                    MATCH (n)-[r]->(m)
                    WHERE n.name CONTAINS $keyword OR m.name CONTAINS $keyword
                    RETURN n.name AS source, type(r) AS relationship, m.name AS target
                    LIMIT 10
                    """,
                    keyword=question.split()[0] if question.split() else "",
                )
                records = [
                    f"{r['source']} --[{r['relationship']}]--> {r['target']}"
                    async for r in result
                ]
                if records:
                    return "Knowledge Graph 검색 결과:\n" + "\n".join(records)
                return "Knowledge Graph에서 관련 정보를 찾지 못했습니다."
        except Exception as e:
            return f"[GraphRAG Mock] Neo4j 연결 실패 (MVP fallback): {str(e)}"

    async def add_entity(self, entity_type: str, properties: dict) -> None:
        """엔티티(노드) 생성"""
        async with self._driver.session() as session:
            props = ", ".join(f"{k}: ${k}" for k in properties.keys())
            await session.run(
                f"CREATE (n:{entity_type} {{{props}}})",
                **properties,
            )

    async def add_relationship(self, from_id: str, to_id: str, rel_type: str) -> None:
        """관계(엣지) 생성"""
        async with self._driver.session() as session:
            await session.run(
                f"""
                MATCH (a {{name: $from_id}}), (b {{name: $to_id}})
                CREATE (a)-[:{rel_type}]->(b)
                """,
                from_id=from_id,
                to_id=to_id,
            )

    async def close(self):
        await self._driver.close()
