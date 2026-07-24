import { useState, useCallback, useRef } from "react";

const ALLOWED_EXT = [".csv", ".xlsx", ".xls"];
const MAX_SIZE = 10 * 1024 * 1024; // 10 MB

export default function Upload({ onSuccess, onError }) {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [fileName, setFileName] = useState("");
  const inputRef = useRef(null);

  const validate = (file) => {
    const ext = "." + file.name.split(".").pop().toLowerCase();
    if (!ALLOWED_EXT.includes(ext))
      return `Unsupported file type (${ext}). Please upload a CSV or XLSX file.`;
    if (file.size > MAX_SIZE)
      return `File too large (${(file.size / 1024 / 1024).toFixed(1)} MB). Maximum is 10 MB.`;
    if (file.size === 0) return "File is empty.";
    return null;
  };

  const upload = useCallback(
    async (file) => {
      const err = validate(file);
      if (err) {
        onError(err);
        return;
      }

      setFileName(file.name);
      setIsUploading(true);
      onError(null);

      const fd = new FormData();
      fd.append("file", file);

      try {
        const res = await fetch("/api/upload", { method: "POST", body: fd });
        if (!res.ok) {
          const body = await res.json().catch(() => ({}));
          throw new Error(body.detail || `Upload failed (${res.status})`);
        }
        onSuccess(await res.json());
      } catch (e) {
        onError(e.message || "Upload failed — please try again.");
      } finally {
        setIsUploading(false);
      }
    },
    [onSuccess, onError]
  );

  /* ── drag / drop ────────────────────────────────────────── */
  const onDrop = useCallback(
    (e) => {
      e.preventDefault();
      setIsDragging(false);
      if (e.dataTransfer.files[0]) upload(e.dataTransfer.files[0]);
    },
    [upload]
  );
  const onDragOver = useCallback((e) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);
  const onDragLeave = useCallback((e) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);
  const onChange = useCallback(
    (e) => {
      if (e.target.files[0]) upload(e.target.files[0]);
    },
    [upload]
  );

  return (
    <div className="max-w-2xl mx-auto animate-slide-up">
      {/* ── hero ────────────────────────────────────────────── */}
      <div className="text-center mb-10">
        <h2 className="text-4xl sm:text-5xl font-extrabold mb-4 leading-tight">
          <span className="gradient-text">Understand Your Data</span>
          <br />
          <span className="text-white">in Seconds</span>
        </h2>
        <p className="text-slate-400 text-lg max-w-xl mx-auto leading-relaxed">
          Upload a CSV or Excel file and get an AI-powered analysis with trends,
          distributions, anomalies, and actionable insights.
        </p>
      </div>

      {/* ── drop zone ──────────────────────────────────────── */}
      <div
        role="button"
        tabIndex={0}
        onDrop={onDrop}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onClick={() => inputRef.current?.click()}
        onKeyDown={(e) => e.key === "Enter" && inputRef.current?.click()}
        className={`glass-card p-10 sm:p-16 cursor-pointer transition-all duration-500 group
          ${isDragging ? "border-indigo-500/50 bg-indigo-500/[0.08] scale-[1.02]" : "hover:border-white/[0.12] hover:bg-white/[0.05]"}
          ${isUploading ? "pointer-events-none opacity-80" : ""}
        `}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".csv,.xlsx,.xls"
          onChange={onChange}
          className="hidden"
          aria-label="Choose file to upload"
        />

        <div className="text-center">
          {isUploading ? (
            <>
              {/* spinner */}
              <div className="w-16 h-16 mx-auto mb-6 rounded-2xl bg-indigo-500/20 flex items-center justify-center">
                <svg className="w-8 h-8 text-indigo-400 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
              </div>
              <p className="text-white font-semibold text-lg mb-1">
                Analyzing {fileName}…
              </p>
              <p className="text-slate-400 text-sm">
                Profiling your data with pandas
              </p>
            </>
          ) : (
            <>
              {/* upload icon */}
              <div className="w-16 h-16 mx-auto mb-6 rounded-2xl bg-white/[0.05] group-hover:bg-indigo-500/20 flex items-center justify-center transition-all duration-500">
                <svg className="w-8 h-8 text-slate-400 group-hover:text-indigo-400 transition-colors duration-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
              </div>

              <p className="text-white font-semibold text-lg mb-1">
                {isDragging ? "Drop your file here" : "Drag & drop your file here"}
              </p>
              <p className="text-slate-400 text-sm mb-5">or click to browse</p>

              <div className="flex items-center justify-center gap-3 text-xs text-slate-500">
                <span className="px-2.5 py-1 rounded-lg bg-white/[0.05] border border-white/[0.06]">
                  CSV
                </span>
                <span className="px-2.5 py-1 rounded-lg bg-white/[0.05] border border-white/[0.06]">
                  XLSX
                </span>
                <span className="px-2.5 py-1 rounded-lg bg-white/[0.05] border border-white/[0.06]">
                  ≤ 10 MB
                </span>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
