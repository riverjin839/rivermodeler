/**
 * 재사용 메트릭 카드
 * 대시보드 및 ML 모니터링 페이지에서 주요 수치를 표시
 */
export default function MetricCard({
  title,
  value,
  subtitle,
  accent = "blue",
}: {
  title: string;
  value: string | number;
  subtitle?: string;
  accent?: "blue" | "green" | "orange" | "red";
}) {
  const accentColors = {
    blue: "border-blue-500",
    green: "border-green-500",
    orange: "border-orange-500",
    red: "border-red-500",
  };

  return (
    <div className={`bg-white rounded-lg shadow-sm border-l-4 ${accentColors[accent]} p-5`}>
      <p className="text-sm text-gray-500">{title}</p>
      <p className="text-2xl font-bold text-gray-900 mt-1">{value}</p>
      {subtitle && <p className="text-xs text-gray-400 mt-1">{subtitle}</p>}
    </div>
  );
}
