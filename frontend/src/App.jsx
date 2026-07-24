import { useState, useCallback, useRef } from "react";
import Upload from "./components/Upload";
import DataPreview from "./components/DataPreview";
import ExplainPanel from "./components/ExplainPanel";
import FollowUpChat from "./components/FollowUpChat";

/* ── SSE helper — parses `data: {...}\n\n` events from a ReadableStream ── */
async function consumeSSE(response, { onToken, onDone, onError }) {
  const reader = response.body.getReader();
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
            onDone?.();
            return;
          }
          if (data.error) {
            onError?.(data.error);
            return;
          }
          if (data.token !== undefined) onToken(data.token);
        } catch {
          /* partial JSON — skip */
        }
      }
    }
  }
  onDone?.();
}

export default function App() {
  const [fileData, setFileData] = useState(null);
  const [explanation, setExplanation] = useState("");
  const [isExplaining, setIsExplaining] = useState(false);
  const [explanationDone, setExplanationDone] = useState(false);
  const [error, setError] = useState(null);
  const abortRef = useRef(null);

  /* ── stream explanation ────────────────────────────────── */
  const streamExplanation = useCallback(async (fileId) => {
    setIsExplaining(true);
    setExplanation("");

    try {
      const ctrl = new AbortController();
      abortRef.current = ctrl;

      const res = await fetch(`/api/explain/${fileId}`, {
        signal: ctrl.signal,
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Failed to start explanation");
      }

      await consumeSSE(res, {
        onToken: (t) => setExplanation((p) => p + t),
        onDone: () => {
          setIsExplaining(false);
          setExplanationDone(true);
        },
        onError: (msg) => {
          setError(msg);
          setIsExplaining(false);
        },
      });
    } catch (err) {
      if (err.name !== "AbortError") {
        setError(err.message || "Connection to AI service failed");
        setIsExplaining(false);
      }
    }
  }, []);

  /* ── handlers ──────────────────────────────────────────── */
  const handleUploadSuccess = useCallback(
    (data) => {
      setFileData(data);
      setError(null);
      setExplanationDone(false);
      streamExplanation(data.file_id);
    },
    [streamExplanation]
  );

  const handleReset = useCallback(() => {
    abortRef.current?.abort();
    setFileData(null);
    setExplanation("");
    setIsExplaining(false);
    setExplanationDone(false);
    setError(null);
  }, []);

  /* ── render ────────────────────────────────────────────── */
  return (
    <div className="min-h-screen flex flex-col">
      {/* ── header ─────────────────────────────────────────── */}
      <header className="sticky top-0 z-50 glass-card rounded-none border-0 border-b border-white/[0.06]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/30">
              <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <div>
              <h1 className="text-xl font-bold gradient-text">Data Explainer</h1>
              <p className="text-[11px] text-slate-500 hidden sm:block">
                AI-Powered Data Analysis
              </p>
            </div>
          </div>
          {fileData && (
            <button onClick={handleReset} className="btn-secondary text-sm">
              ← New File
            </button>
          )}
        </div>
      </header>

      {/* ── main ───────────────────────────────────────────── */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 py-8">
        {/* error toast */}
        {error && (
          <div className="mb-6 p-4 bg-rose-500/10 border border-rose-500/20 rounded-xl flex items-center justify-between animate-fade-in">
            <div className="flex items-center gap-3 min-w-0">
              <svg className="w-5 h-5 text-rose-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span className="text-rose-300 text-sm truncate">{error}</span>
            </div>
            <button
              onClick={() => setError(null)}
              className="text-rose-400 hover:text-rose-300 transition-colors ml-3 shrink-0"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        )}

        {!fileData ? (
          <Upload onSuccess={handleUploadSuccess} onError={setError} />
        ) : (
          <div className="space-y-6 animate-fade-in">
            <DataPreview data={fileData} />
            <ExplainPanel
              explanation={explanation}
              isStreaming={isExplaining}
            />
            {explanationDone && <FollowUpChat fileId={fileData.file_id} />}
          </div>
        )}
      </main>

      {/* ── footer ─────────────────────────────────────────── */}
      <footer className="py-6 text-center text-xs text-slate-600">
        Built with FastAPI, React &amp; Claude AI — IBM SkillsBuild Project
      </footer>
    </div>
  );
}
