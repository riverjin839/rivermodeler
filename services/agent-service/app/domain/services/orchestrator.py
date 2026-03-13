"""
도메인 서비스 - LangGraph 기반 오케스트레이션 로직
핵심 비즈니스 로직: 사용자 질문을 분석하여 적절한 Tool로 라우팅

LangGraph 상태 머신 흐름:
  [classify] → Vector RAG  → [synthesize] → 응답
            → Graph RAG   → [synthesize] → 응답
            → ML Predict  → [synthesize] → 응답
"""

from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END

from app.domain.models.query import ToolType, ToolResult
from app.ports.outbound.vector_db_port import VectorDBPort
from app.ports.outbound.graph_db_port import GraphDBPort
from app.ports.outbound.ml_serving_port import MLServingPort
from app.ports.outbound.llm_port import LLMPort


# --- LangGraph 상태 정의 ---
class AgentState(TypedDict):
    """LangGraph 노드 간 공유되는 상태"""
    question: str
    context: str
    selected_tool: str  # ToolType value
    tool_result: str
    final_answer: str


class OrchestratorService:
    """
    LangGraph 기반 Agent 오케스트레이터 (도메인 서비스)

    헥사고날 원칙: 이 서비스는 Port 인터페이스에만 의존.
    구체적 어댑터(Neo4j, ChromaDB 등) 구현에 비종속적.
    """

    def __init__(
        self,
        vector_db: VectorDBPort,
        graph_db: GraphDBPort,
        ml_serving: MLServingPort,
        llm: LLMPort,
    ):
        self._vector_db = vector_db
        self._graph_db = graph_db
        self._ml_serving = ml_serving
        self._llm = llm
        self._graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """LangGraph 상태 머신 그래프 구성"""

        graph = StateGraph(AgentState)

        # --- 노드 등록 ---
        graph.add_node("classify", self._classify_node)
        graph.add_node("vector_rag", self._vector_rag_node)
        graph.add_node("graph_rag", self._graph_rag_node)
        graph.add_node("ml_prediction", self._ml_prediction_node)
        graph.add_node("synthesize", self._synthesize_node)

        # --- 엣지 연결 ---
        graph.set_entry_point("classify")

        # 분류 결과에 따른 조건부 라우팅
        graph.add_conditional_edges(
            "classify",
            self._route_by_tool,
            {
                ToolType.VECTOR_RAG.value: "vector_rag",
                ToolType.GRAPH_RAG.value: "graph_rag",
                ToolType.ML_PREDICTION.value: "ml_prediction",
            },
        )

        # 각 Tool → 합성 노드 → 종료
        graph.add_edge("vector_rag", "synthesize")
        graph.add_edge("graph_rag", "synthesize")
        graph.add_edge("ml_prediction", "synthesize")
        graph.add_edge("synthesize", END)

        return graph.compile()

    # =====================================================================
    # LangGraph 노드 구현
    # =====================================================================

    async def _classify_node(self, state: AgentState) -> dict:
        """
        [노드 1] 질문 분류 - LLM을 사용하여 최적 Tool 결정
        키워드 기반 규칙 + LLM 판단 하이브리드 방식
        """
        question = state["question"].lower()

        # 간단한 규칙 기반 분류 (MVP 단계)
        # 프로덕션에서는 LLM의 function calling으로 대체
        if any(kw in question for kw in ["관계", "연결", "온톨로지", "그래프", "개체"]):
            selected = ToolType.GRAPH_RAG.value
        elif any(kw in question for kw in ["예측", "분류", "회귀", "모델 성능", "drift"]):
            selected = ToolType.ML_PREDICTION.value
        else:
            # 기본값: Vector RAG (일반 문서 검색)
            selected = ToolType.VECTOR_RAG.value

        return {"selected_tool": selected}

    def _route_by_tool(self, state: AgentState) -> str:
        """조건부 라우팅 함수: 분류된 Tool 타입 반환"""
        return state["selected_tool"]

    async def _vector_rag_node(self, state: AgentState) -> dict:
        """
        [노드 2a] Vector RAG - ChromaDB에서 유사 문서 검색 후 LLM으로 답변 생성
        통신: → ChromaDB (http://chromadb-service:8000)
        """
        results = await self._vector_db.similarity_search(
            query=state["question"],
            top_k=3,
        )
        return {"tool_result": results}

    async def _graph_rag_node(self, state: AgentState) -> dict:
        """
        [노드 2b] Graph RAG - Neo4j에서 관련 엔티티/관계 탐색
        통신: → Neo4j (bolt://neo4j-service:7687)
        """
        results = await self._graph_db.query_knowledge_graph(
            question=state["question"],
        )
        return {"tool_result": results}

    async def _ml_prediction_node(self, state: AgentState) -> dict:
        """
        [노드 2c] ML 예측 - 전통 ML 모델 추론 API 호출
        통신: → ML Serving (http://ml-serving-service:8081)
        """
        results = await self._ml_serving.predict(
            question=state["question"],
        )
        return {"tool_result": results}

    async def _synthesize_node(self, state: AgentState) -> dict:
        """
        [노드 3] 합성 - Tool 결과를 LLM으로 종합하여 최종 답변 생성
        통신: → Ollama (http://ollama-service:11434)
        """
        prompt = (
            f"사용자 질문: {state['question']}\n\n"
            f"검색/분석 결과:\n{state['tool_result']}\n\n"
            f"위 결과를 바탕으로 사용자에게 명확하고 도움이 되는 답변을 작성하세요."
        )
        answer = await self._llm.generate(prompt=prompt)
        return {"final_answer": answer}

    # =====================================================================
    # 공개 인터페이스
    # =====================================================================

    async def process_query(self, question: str, context: str = "") -> dict:
        """
        사용자 질의 처리 메인 메서드
        LangGraph 상태 머신을 실행하여 최종 답변 반환
        """
        initial_state: AgentState = {
            "question": question,
            "context": context,
            "selected_tool": "",
            "tool_result": "",
            "final_answer": "",
        }

        # LangGraph 실행
        result = await self._graph.ainvoke(initial_state)

        return {
            "answer": result["final_answer"],
            "tool_used": result["selected_tool"],
        }
