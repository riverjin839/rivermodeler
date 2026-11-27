/**
 * 클라이언트 사이드 fetch 헬퍼
 * 브라우저 → Next.js BFF API Route로 요청 (백엔드 URL 비노출)
 */

export async function fetchApi<T>(
  path: string,
  options?: RequestInit
): Promise<T> {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    throw new Error(`API error: ${res.status}`);
  }
  return res.json();
}

/** Agent 질의 */
export async function queryAgent(question: string, context?: string) {
  return fetchApi<{
    answer: string;
    tool_used: string;
    source_details: Record<string, unknown> | null;
  }>("/api/agent/query", {
    method: "POST",
    body: JSON.stringify({ question, context }),
  });
}

/** ML 예측 */
export async function predictML(features: Record<string, number>) {
  return fetchApi<{
    prediction: number;
    confidence: number;
    drift_alert: Record<string, unknown> | null;
  }>("/api/ml/predict", {
    method: "POST",
    body: JSON.stringify({ features }),
  });
}
