/**
 * 백엔드 서비스 URL (서버 사이드 전용 - BFF API Route에서만 사용)
 * K8s 환경에서는 Pod env로 주입, 로컬 개발 시 .env.local에서 오버라이드
 */
export const AGENT_SERVICE_URL =
  process.env.AGENT_SERVICE_URL || "http://agent-service:8080";

export const ML_SERVING_URL =
  process.env.ML_SERVING_URL || "http://ml-serving-service:8081";

/**
 * Tool 타입별 UI 설정
 */
export const TOOL_CONFIG: Record<string, { label: string; color: string }> = {
  vector_rag: { label: "Vector RAG", color: "bg-blue-500" },
  graph_rag: { label: "Graph RAG", color: "bg-green-500" },
  ml_prediction: { label: "ML 예측", color: "bg-orange-500" },
};
