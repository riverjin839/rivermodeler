"use client";

import { useState, useEffect, useCallback } from "react";
import MetricCard from "@/components/metric-card";
import DriftChart from "@/components/drift-chart";
import { fetchApi, predictML } from "@/lib/api";

/**
 * ML 모니터링 페이지 (/ml) - Client Component
 * 상단: Drift 모니터링 (10초 자동 갱신)
 * 하단: Prediction 테스터 폼
 */

interface DriftStatus {
  buffer_size: number;
  window_size: number;
  total_predictions: number;
  drift_detected_count: number;
  drift_threshold: number;
  monitored_features: string[];
}

interface ModelInfo {
  model_name: string;
  model_version: string;
  framework: string;
  features: string[];
  status: string;
}

interface PredictResult {
  prediction: number;
  confidence: number;
  drift_alert: Record<string, unknown> | null;
}

export default function MLPage() {
  const [drift, setDrift] = useState<DriftStatus | null>(null);
  const [model, setModel] = useState<ModelInfo | null>(null);
  const [features, setFeatures] = useState({
    feature_1: 0,
    feature_2: 0,
    feature_3: 0,
    feature_4: 0,
  });
  const [result, setResult] = useState<PredictResult | null>(null);
  const [predicting, setPredicting] = useState(false);

  const loadDrift = useCallback(async () => {
    try {
      const data = await fetchApi<DriftStatus>("/api/ml/drift");
      setDrift(data);
    } catch {
      /* 서비스 미연결 */
    }
  }, []);

  // 초기 로드 + 10초 폴링
  useEffect(() => {
    loadDrift();
    fetchApi<ModelInfo>("/api/ml/model-info").then(setModel).catch(() => {});
    const interval = setInterval(loadDrift, 10_000);
    return () => clearInterval(interval);
  }, [loadDrift]);

  async function handlePredict(e: React.FormEvent) {
    e.preventDefault();
    setPredicting(true);
    try {
      const res = await predictML(features);
      setResult(res);
      // 예측 후 drift 상태 갱신
      await loadDrift();
    } catch {
      setResult(null);
    } finally {
      setPredicting(false);
    }
  }

  return (
    <div className="space-y-8">
      {/* 헤더 */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">ML 모니터링</h1>
        <p className="text-sm text-gray-500 mt-1">
          모델 Drift 감지 현황 및 추론 테스트
        </p>
      </div>

      {/* ====== Drift 모니터링 섹션 ====== */}
      <section>
        <div className="flex items-center gap-2 mb-4">
          <h2 className="text-lg font-semibold text-gray-800">Drift 모니터링</h2>
          <span className="text-xs text-gray-400">(10초 자동 갱신)</span>
        </div>

        {drift ? (
          <>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
              <MetricCard
                title="총 예측 수"
                value={drift.total_predictions}
                accent="blue"
              />
              <MetricCard
                title="Drift 감지"
                value={drift.drift_detected_count}
                accent={drift.drift_detected_count > 0 ? "red" : "green"}
              />
              <MetricCard
                title="버퍼"
                value={`${drift.buffer_size} / ${drift.window_size}`}
                subtitle="현재 수집 / 윈도우 크기"
                accent="orange"
              />
              <MetricCard
                title="임계치"
                value={`${drift.drift_threshold * 100}%`}
                accent="blue"
              />
            </div>

            {/* Drift 바 차트 */}
            <DriftChart
              detected={drift.drift_detected_count}
              total={Math.max(drift.total_predictions, 1)}
              threshold={drift.drift_threshold}
            />

            {/* 모니터링 피처 태그 */}
            <div className="mt-4 flex items-center gap-2 flex-wrap">
              <span className="text-sm text-gray-500">모니터링 피처:</span>
              {drift.monitored_features.map((f) => (
                <span
                  key={f}
                  className="px-2 py-1 text-xs bg-gray-200 text-gray-600 rounded-md"
                >
                  {f}
                </span>
              ))}
            </div>
          </>
        ) : (
          <div className="bg-white rounded-lg shadow-sm p-8 text-center text-gray-400">
            ML Serving 서비스에 연결 중...
          </div>
        )}
      </section>

      {/* ====== 모델 정보 섹션 ====== */}
      {model && (
        <section>
          <h2 className="text-lg font-semibold text-gray-800 mb-4">서빙 모델 정보</h2>
          <div className="bg-white rounded-lg shadow-sm p-5">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <p className="text-gray-400">모델명</p>
                <p className="font-medium">{model.model_name}</p>
              </div>
              <div>
                <p className="text-gray-400">버전</p>
                <p className="font-medium">{model.model_version}</p>
              </div>
              <div>
                <p className="text-gray-400">프레임워크</p>
                <p className="font-medium">{model.framework}</p>
              </div>
              <div>
                <p className="text-gray-400">상태</p>
                <p className="font-medium text-green-600">{model.status}</p>
              </div>
            </div>
          </div>
        </section>
      )}

      {/* ====== Prediction 테스터 섹션 ====== */}
      <section>
        <h2 className="text-lg font-semibold text-gray-800 mb-4">추론 테스트</h2>
        <div className="bg-white rounded-lg shadow-sm p-5">
          <form onSubmit={handlePredict} className="space-y-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {Object.entries(features).map(([key, value]) => (
                <div key={key}>
                  <label className="block text-sm text-gray-500 mb-1">{key}</label>
                  <input
                    type="number"
                    step="0.01"
                    value={value}
                    onChange={(e) =>
                      setFeatures((prev) => ({
                        ...prev,
                        [key]: parseFloat(e.target.value) || 0,
                      }))
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              ))}
            </div>
            <button
              type="submit"
              disabled={predicting}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:bg-gray-300 transition-colors"
            >
              {predicting ? "추론 중..." : "추론 실행"}
            </button>
          </form>

          {/* 결과 표시 */}
          {result && (
            <div className="mt-6 border-t pt-4 space-y-3">
              <div className="flex gap-8">
                <div>
                  <p className="text-sm text-gray-400">예측값</p>
                  <p className="text-xl font-bold">{result.prediction.toFixed(4)}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-400">신뢰도</p>
                  <div className="flex items-center gap-2">
                    <div className="w-32 bg-gray-200 rounded-full h-3">
                      <div
                        className="bg-blue-500 h-3 rounded-full transition-all"
                        style={{ width: `${result.confidence * 100}%` }}
                      />
                    </div>
                    <span className="text-sm font-medium">
                      {(result.confidence * 100).toFixed(1)}%
                    </span>
                  </div>
                </div>
              </div>

              {/* Drift Alert */}
              {result.drift_alert && (
                <div
                  className={`p-4 rounded-lg border ${
                    result.drift_alert.is_drifted
                      ? "bg-red-50 border-red-200"
                      : "bg-green-50 border-green-200"
                  }`}
                >
                  <p className="text-sm font-medium mb-1">
                    {result.drift_alert.is_drifted
                      ? "Drift 감지됨"
                      : "Drift 미감지"}
                  </p>
                  <p className="text-xs text-gray-500">
                    Drift Score: {String(result.drift_alert.drift_score)} |
                    드리프트 피처: {JSON.stringify(result.drift_alert.drifted_features)}
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
