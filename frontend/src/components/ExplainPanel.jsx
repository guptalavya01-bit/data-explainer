import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useEffect, useRef } from "react";

export default function ExplainPanel({ explanation, isStreaming }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    if (isStreaming) {
      bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
    }
  }, [explanation, isStreaming]);

  return (
    <div className="glass-card p-5 sm:p-6 animate-slide-up">
      {/* ── header ─────────────────────────────────────────── */}
      <div className="flex items-center gap-2.5 mb-5">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-purple-500/20">
          <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
        </div>
        <h3 className="text-lg font-semibold text-white">AI Analysis</h3>

        {isStreaming && (
          <span className="ml-auto flex items-center gap-2 text-xs text-indigo-400 font-medium">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-indigo-500" />
            </span>
            Analyzing…
          </span>
        )}
      </div>

      {/* ── body ───────────────────────────────────────────── */}
      {!explanation && isStreaming ? (
        /* skeleton */
        <div className="space-y-3 animate-pulse">
          {[90, 75, 60, 80].map((w, i) => (
            <div
              key={i}
              className="h-4 rounded bg-white/[0.05]"
              style={{ width: `${w}%` }}
            />
          ))}
        </div>
      ) : (
        <div
          className={`
            prose prose-invert prose-sm max-w-none
            prose-headings:text-white prose-headings:font-semibold prose-headings:mt-6 prose-headings:mb-3
            prose-p:text-slate-300 prose-p:leading-relaxed
            prose-strong:text-white
            prose-li:text-slate-300 prose-li:marker:text-indigo-400
            prose-code:text-indigo-300 prose-code:bg-indigo-500/10 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded prose-code:text-xs
            prose-a:text-indigo-400 prose-a:no-underline hover:prose-a:underline
            prose-table:border-collapse
            prose-th:bg-white/[0.05] prose-th:px-3 prose-th:py-2 prose-th:text-left prose-th:text-slate-300 prose-th:text-xs
            prose-td:px-3 prose-td:py-2 prose-td:border-t prose-td:border-white/[0.06] prose-td:text-xs
            ${isStreaming ? "streaming-cursor" : ""}
          `}
        >
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {explanation}
          </ReactMarkdown>
        </div>
      )}
      <div ref={bottomRef} />
    </div>
  );
}
