/**
 * BFF Proxy: 사용 가능한 Tool 목록 조회
 * Browser → GET /api/agent/tools → agent-service:8080/api/v1/tools
 */
import { AGENT_SERVICE_URL } from "@/lib/constants";

export async function GET() {
  const res = await fetch(`${AGENT_SERVICE_URL}/api/v1/tools`, {
    next: { revalidate: 60 },
  });
  const data = await res.json();
  return Response.json(data, { status: res.status });
}
