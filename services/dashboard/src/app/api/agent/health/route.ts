/**
 * BFF Proxy: Agent Service 헬스체크
 * Browser → GET /api/agent/health → agent-service:8080/health
 */
import { AGENT_SERVICE_URL } from "@/lib/constants";

export async function GET() {
  try {
    const res = await fetch(`${AGENT_SERVICE_URL}/health`, {
      next: { revalidate: 10 },
    });
    const data = await res.json();
    return Response.json(data);
  } catch {
    return Response.json({ status: "unhealthy" }, { status: 503 });
  }
}
