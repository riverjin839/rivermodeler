/**
 * BFF Proxy: Drift 감지기 상태 조회
 * Browser → GET /api/ml/drift → ml-serving-service:8081/drift/status
 */
import { ML_SERVING_URL } from "@/lib/constants";

export async function GET() {
  try {
    const res = await fetch(`${ML_SERVING_URL}/drift/status`, {
      cache: "no-store",
    });
    const data = await res.json();
    return Response.json(data);
  } catch {
    return Response.json(
      { error: "ML Serving 서비스 연결 실패" },
      { status: 503 }
    );
  }
}
