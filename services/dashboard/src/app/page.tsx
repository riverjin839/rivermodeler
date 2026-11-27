import HealthBadge from "@/components/health-badge";
import MetricCard from "@/components/metric-card";
import { AGENT_SERVICE_URL, ML_SERVING_URL, TOOL_CONFIG } from "@/lib/constants";

/**
 * 대시보드 페이지 (/) - Server Component
 * 시스템 전체 상태 한눈에 보기
 */

async function fetchHealth(url: string): Promise<"healthy" | "unhealthy"> {
  try {
    const res = await fetch(`${url}/health`, { next: { revalidate: 30 } });
    if (res.ok) return "healthy";
    return "unhealthy";
  } catch {
    return "unhealthy";
  }
}

async function fetchJson<T>(url: string, fallback: T): Promise<T> {
  try {
    const res = await fetch(url, { next: { revalidate: 30 } });
    if (res.ok) return res.json();
    return fallback;
  } catch {
    return fallback;
  }
}

export default async function DashboardPage() {
  const [agentHealth, mlHealth, driftStatus, modelInfo, tools] = await Promise.all([
    fetchHealth(AGENT_SERVICE_URL),
    fetchHealth(ML_SERVING_URL),
    fetchJson<Record<string, unknown>>(`${ML_SERVING_URL}/drift/status`, {}),
    fetchJson<Record<string, unknown>>(`${ML_SERVING_URL}/model-info`, {}),
    fetchJson<{ tools: Array<{ name: string; description: string }> }>(
      `${AGENT_SERVICE_URL}/api/v1/tools`,
      { tools: [] }
    ),
  ]);

  return (
    <div className="space-y-8">
      {/* 헤더 */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">대시보드</h1>
        <p className="text-sm text-gray-500 mt-1">AI Platform 시스템 개요</p>
      </div>

      {/* 서비스 헬스 상태 */}
      <section>
        <h2 className="text-lg font-semibold text-gray-800 mb-4">서비스 상태</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-white rounded-lg shadow-sm p-5 flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-700">Agent Service</p>
              <p className="text-xs text-gray-400 mt-1">FastAPI + LangGraph 오케스트레이터</p>
            </div>
            <HealthBadge status={agentHealth} />
          </div>
          <div className="bg-white rounded-lg shadow-sm p-5 flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-700">ML Serving</p>
              <p className="text-xs text-gray-400 mt-1">ML 추론 + Evidently Drift 감지</p>
            </div>
            <HealthBadge status={mlHealth} />
          </div>
        </div>
      </section>

      {/* 주요 메트릭 */}
      <section>
        <h2 className="text-lg font-semibold text-gray-800 mb-4">ML 메트릭</h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <MetricCard
            title="총 예측 수"
            value={Number(driftStatus.total_predictions ?? 0)}
            accent="blue"
          />
          <MetricCard
            title="Drift 감지 횟수"
            value={Number(driftStatus.drift_detected_count ?? 0)}
            accent={Number(driftStatus.drift_detected_count ?? 0) > 0 ? "red" : "green"}
          />
          <MetricCard
            title="버퍼 크기"
            value={`${driftStatus.buffer_size ?? 0} / ${driftStatus.window_size ?? 50}`}
            subtitle="현재 / 윈도우 크기"
            accent="orange"
          />
          <MetricCard
            title="모델"
            value={String(modelInfo.model_name ?? "N/A")}
            subtitle={`v${modelInfo.model_version ?? "-"} (${modelInfo.framework ?? "-"})`}
            accent="blue"
          />
        </div>
      </section>

      {/* 사용 가능 Tools */}
      <section>
        <h2 className="text-lg font-semibold text-gray-800 mb-4">Agent Tools</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {tools.tools.map((tool) => {
            const config = TOOL_CONFIG[tool.name];
            return (
              <div key={tool.name} className="bg-white rounded-lg shadow-sm p-5">
                <div className="flex items-center gap-2 mb-2">
                  {config && (
                    <span className={`text-xs text-white px-2 py-0.5 rounded-full ${config.color}`}>
                      {config.label}
                    </span>
                  )}
                </div>
                <p className="text-sm text-gray-600">{tool.description}</p>
              </div>
            );
          })}
          {tools.tools.length === 0 && (
            <p className="text-sm text-gray-400 col-span-3">
              Agent Service에 연결할 수 없어 Tool 목록을 불러올 수 없습니다.
            </p>
          )}
        </div>
      </section>
    </div>
  );
}
