/**
 * BFF Proxy: 서빙 모델 정보 조회
 * Browser → GET /api/ml/model-info → ml-serving-service:8081/model-info
 */
import { ML_SERVING_URL } from "@/lib/constants";

export async function GET() {
  try {
    const res = await fetch(`${ML_SERVING_URL}/model-info`, {
      next: { revalidate: 30 },
    });
    const data = await res.json();
    return Response.json(data);
  } catch {
    return Response.json(
      { status: "unavailable", message: "ML Serving 서비스 연결 실패" },
      { status: 503 }
    );
  }
}
