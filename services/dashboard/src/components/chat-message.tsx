import { TOOL_CONFIG } from "@/lib/constants";

/**
 * 채팅 메시지 말풍선
 * 유저 메시지: 우측 정렬 (파란 배경)
 * Agent 응답: 좌측 정렬 (흰 배경 + tool_used 배지)
 */
export default function ChatMessage({
  role,
  content,
  toolUsed,
}: {
  role: "user" | "agent";
  content: string;
  toolUsed?: string;
}) {
  if (role === "user") {
    return (
      <div className="flex justify-end">
        <div className="max-w-[70%] bg-blue-600 text-white rounded-2xl rounded-br-md px-4 py-3">
          <p className="text-sm whitespace-pre-wrap">{content}</p>
        </div>
      </div>
    );
  }

  const tool = toolUsed ? TOOL_CONFIG[toolUsed] : null;

  return (
    <div className="flex justify-start">
      <div className="max-w-[70%] bg-white border border-gray-200 rounded-2xl rounded-bl-md px-4 py-3 shadow-sm">
        {tool && (
          <span className={`inline-block text-xs text-white px-2 py-0.5 rounded-full mb-2 ${tool.color}`}>
            {tool.label}
          </span>
        )}
        <p className="text-sm text-gray-800 whitespace-pre-wrap">{content}</p>
      </div>
    </div>
  );
}
