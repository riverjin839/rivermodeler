"use client";

import { useState, useRef, useEffect } from "react";
import ChatMessage from "@/components/chat-message";
import { queryAgent } from "@/lib/api";

/**
 * AI 에이전트 채팅 페이지 (/chat) - Client Component
 * LangGraph 오케스트레이터에 질문을 보내고 답변을 받는 인터페이스
 */

interface Message {
  id: number;
  role: "user" | "agent";
  content: string;
  toolUsed?: string;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // 새 메시지 시 스크롤 하단 이동
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const question = input.trim();
    if (!question || loading) return;

    const userMsg: Message = {
      id: Date.now(),
      role: "user",
      content: question,
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const result = await queryAgent(question);
      const agentMsg: Message = {
        id: Date.now() + 1,
        role: "agent",
        content: result.answer,
        toolUsed: result.tool_used,
      };
      setMessages((prev) => [...prev, agentMsg]);
    } catch {
      const errorMsg: Message = {
        id: Date.now() + 1,
        role: "agent",
        content: "Agent Service에 연결할 수 없습니다. 서비스 상태를 확인해 주세요.",
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  }

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)]">
      {/* 헤더 */}
      <div className="mb-4">
        <h1 className="text-2xl font-bold text-gray-900">AI 에이전트</h1>
        <p className="text-sm text-gray-500 mt-1">
          질문을 입력하면 Vector RAG, Graph RAG, ML 예측 중 최적의 도구로 답변합니다
        </p>
      </div>

      {/* 메시지 영역 */}
      <div className="flex-1 overflow-y-auto rounded-lg bg-gray-100 p-4 space-y-4">
        {messages.length === 0 && (
          <div className="flex items-center justify-center h-full">
            <div className="text-center text-gray-400">
              <p className="text-lg mb-2">질문을 입력해 보세요</p>
              <div className="space-y-1 text-sm">
                <p>&quot;EXAONE 모델의 아키텍처를 설명해 줘&quot;</p>
                <p>&quot;고객과 제품 간의 관계를 분석해 줘&quot;</p>
                <p>&quot;이번 달 매출 예측을 해 줘&quot;</p>
              </div>
            </div>
          </div>
        )}
        {messages.map((msg) => (
          <ChatMessage
            key={msg.id}
            role={msg.role}
            content={msg.content}
            toolUsed={msg.toolUsed}
          />
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-white border border-gray-200 rounded-2xl rounded-bl-md px-4 py-3 shadow-sm">
              <div className="flex gap-1">
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:0.15s]" />
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:0.3s]" />
              </div>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* 입력 바 */}
      <form onSubmit={handleSubmit} className="mt-4 flex gap-2">
        <input
          ref={inputRef}
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="질문을 입력하세요..."
          disabled={loading}
          className="flex-1 px-4 py-3 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
        >
          전송
        </button>
      </form>
    </div>
  );
}
