/**
 * 서비스 헬스 상태 배지
 * 초록: 정상, 빨강: 비정상, 회색: 확인 중
 */
export default function HealthBadge({
  status,
}: {
  status: "healthy" | "unhealthy" | "loading";
}) {
  const config = {
    healthy: { bg: "bg-green-100", text: "text-green-700", dot: "bg-green-500", label: "정상" },
    unhealthy: { bg: "bg-red-100", text: "text-red-700", dot: "bg-red-500", label: "비정상" },
    loading: { bg: "bg-gray-100", text: "text-gray-500", dot: "bg-gray-400", label: "확인 중" },
  }[status];

  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${config.bg} ${config.text}`}>
      <span className={`w-2 h-2 rounded-full ${config.dot}`} />
      {config.label}
    </span>
  );
}
