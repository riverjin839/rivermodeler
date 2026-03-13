/**
 * BFF Proxy: Agent 질의
 * Browser → POST /api/agent/query → agent-service:8080/api/v1/query
 */
import { AGENT_SERVICE_URL } from "@/lib/constants";

export async function POST(request: Request) {
  const body = await request.json();
  const res = await fetch(`${AGENT_SERVICE_URL}/api/v1/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json();
  return Response.json(data, { status: res.status });
}
