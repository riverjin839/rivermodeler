/**
 * BFF Proxy: ML 모델 추론
 * Browser → POST /api/ml/predict → ml-serving-service:8081/predict
 */
import { ML_SERVING_URL } from "@/lib/constants";

export async function POST(request: Request) {
  const body = await request.json();
  const res = await fetch(`${ML_SERVING_URL}/predict`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json();
  return Response.json(data, { status: res.status });
}
