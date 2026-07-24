import { useState, useRef, useEffect, useCallback } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

const SUGGESTIONS = [
  "What are the key trends?",
  "Are there any outliers?",
  "Summarize the correlations",
  "What should I clean first?",
];

export default function FollowUpChat({ fileId }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const endRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  /* ── send question ─────────────────────────────────────── */
  const send = useCallback(
    async (text) => {
      const question = (text ?? input).trim();
      if (!question || isStreaming) return;

      setInput("");
      setMessages((m) => [...m, { role: "user", content: question }]);
      setIsStreaming(true);

      // add empty assistant placeholder
      setMessages((m) => [...m, { role: "assistant", content: "" }]);

      try {
        const res = await fetch("/api/ask", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ file_id: fileId, question }),
        });

        if (!res.ok) {
          const body = await res.json().catch(() => ({}));
          throw new Error(body.detail || "Failed to get answer");
        }

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        // eslint-disable-next-line no-constant-condition
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const parts = buffer.split("\n\n");
          buffer = parts.pop() || "";

          for (const part of parts) {
            for (const line of part.split("\n")) {
              const trimmed = line.trim();
              if (!trimmed.startsWith("data: ")) continue;
              try {
                const data = JSON.parse(trimmed.slice(6));
                if (data.done) {
                  setIsStreaming(false);
                  return;
                }
                if (data.error) throw new Error(data.error);
                if (data.token !== undefined) {
                  setMessages((prev) => {
                    const copy = [...prev];
                    const last = copy[copy.length - 1];
                    if (last?.role === "assistant") {
                      copy[copy.length - 1] = {
                        ...last,
                        content: last.content + data.token,
                      };
                    }
                    return copy;
                  });
                }
              } catch (e) {
                if (e.message && !e.message.includes("JSON")) throw e;
              }
            }
          }
        }
        setIsStreaming(false);
      } catch (err) {
        setMessages((prev) => {
          const copy = [...prev];
          const last = copy[copy.length - 1];
          if (last?.role === "assistant") {
            copy[copy.length - 1] = {
              ...last,
              content: `⚠️ ${err.message}`,
              isError: true,
            };
          }
          return copy;
        });
        setIsStreaming(false);
      }
    },
    [input, isStreaming, fileId]
  );

  const onKey = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  return (
    <div className="glass-card p-5 sm:p-6 animate-slide-up">
      {/* ── header ─────────────────────────────────────────── */}
      <div className="flex items-center gap-2.5 mb-4">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
          <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
          </svg>
        </div>
        <h3 className="text-lg font-semibold text-white">
          Ask About Your Data
        </h3>
      </div>

      {/* ── messages ───────────────────────────────────────── */}
      {messages.length > 0 && (
        <div className="space-y-3 mb-4 max-h-[28rem] overflow-y-auto pr-1">
          {messages.map((msg, i) => (
            <div
              key={i}
              className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[85%] rounded-2xl px-4 py-3 ${
                  msg.role === "user"
                    ? "bg-indigo-600/30 border border-indigo-500/20 text-white"
                    : msg.isError
                      ? "bg-rose-500/10 border border-rose-500/20 text-rose-300"
                      : "bg-white/[0.03] border border-white/[0.06] text-slate-300"
                }`}
              >
                {msg.role === "assistant" ? (
                  <div
                    className={`
                      prose prose-invert prose-sm max-w-none
                      prose-p:text-slate-300 prose-p:leading-relaxed prose-p:my-1.5
                      prose-strong:text-white prose-li:text-slate-300
                      prose-code:text-indigo-300 prose-code:bg-indigo-500/10 prose-code:px-1 prose-code:rounded prose-code:text-xs
                      ${isStreaming && i === messages.length - 1 ? "streaming-cursor" : ""}
                    `}
                  >
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {msg.content || "Thinking…"}
                    </ReactMarkdown>
                  </div>
                ) : (
                  <p className="text-sm leading-relaxed">{msg.content}</p>
                )}
              </div>
            </div>
          ))}
          <div ref={endRef} />
        </div>
      )}

      {/* ── suggestion chips ───────────────────────────────── */}
      {messages.length === 0 && (
        <div className="flex flex-wrap gap-2 mb-4">
          {SUGGESTIONS.map((q) => (
            <button
              key={q}
              onClick={() => send(q)}
              className="text-xs px-3 py-1.5 rounded-full bg-white/[0.05] border border-white/[0.08]
                         text-slate-400 hover:text-white hover:bg-white/[0.1] transition-all duration-200"
            >
              {q}
            </button>
          ))}
        </div>
      )}

      {/* ── input ──────────────────────────────────────────── */}
      <div className="flex gap-3">
        <input
          ref={inputRef}
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={onKey}
          placeholder="Ask a follow-up question…"
          className="input-field flex-1"
          disabled={isStreaming}
        />
        <button
          onClick={() => send()}
          disabled={!input.trim() || isStreaming}
          className="btn-primary !px-4"
          aria-label="Send question"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
          </svg>
        </button>
      </div>
    </div>
  );
}
