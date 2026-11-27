/**
 * Drift 비율 바 차트 (순수 CSS)
 * Drift 감지 비율을 시각적으로 표시
 */
export default function DriftChart({
  detected,
  total,
  threshold,
}: {
  detected: number;
  total: number;
  threshold: number;
}) {
  const ratio = total > 0 ? detected / total : 0;
  const percent = Math.round(ratio * 100);
  const isOver = ratio > threshold;

  return (
    <div className="bg-white rounded-lg shadow-sm p-5">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-medium text-gray-700">Drift 감지 비율</h3>
        <span className={`text-sm font-bold ${isOver ? "text-red-600" : "text-green-600"}`}>
          {percent}%
        </span>
      </div>
      {/* 바 차트 */}
      <div className="w-full bg-gray-200 rounded-full h-4 relative overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ${
            isOver ? "bg-red-500" : "bg-green-500"
          }`}
          style={{ width: `${Math.min(percent, 100)}%` }}
        />
        {/* 임계치 마커 */}
        <div
          className="absolute top-0 bottom-0 w-0.5 bg-gray-600"
          style={{ left: `${threshold * 100}%` }}
          title={`임계치: ${threshold * 100}%`}
        />
      </div>
      <div className="flex justify-between mt-1">
        <span className="text-xs text-gray-400">0%</span>
        <span className="text-xs text-gray-400">
          임계치 {threshold * 100}%
        </span>
        <span className="text-xs text-gray-400">100%</span>
      </div>
    </div>
  );
}
