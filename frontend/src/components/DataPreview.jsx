export default function DataPreview({ data }) {
  const { filename, preview, profile } = data;
  const columns = profile.columns || [];

  const TYPE_COLORS = {
    int: "bg-blue-500/20 text-blue-300 border-blue-500/30",
    float: "bg-cyan-500/20 text-cyan-300 border-cyan-500/30",
    object: "bg-amber-500/20 text-amber-300 border-amber-500/30",
    bool: "bg-emerald-500/20 text-emerald-300 border-emerald-500/30",
    datetime: "bg-purple-500/20 text-purple-300 border-purple-500/30",
    category: "bg-pink-500/20 text-pink-300 border-pink-500/30",
  };

  const badgeColor = (dtype) => {
    for (const [key, val] of Object.entries(TYPE_COLORS)) {
      if (dtype.includes(key)) return val;
    }
    return "bg-slate-500/20 text-slate-300 border-slate-500/30";
  };

  return (
    <div className="glass-card p-5 sm:p-6 animate-slide-up">
      {/* ── header ─────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-5">
        <div>
          <h3 className="text-lg font-semibold text-white flex items-center gap-2">
            <svg className="w-5 h-5 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
            </svg>
            {filename}
          </h3>
          <p className="text-sm text-slate-400 mt-0.5">
            {profile.shape.rows.toLocaleString()} rows ×{" "}
            {profile.shape.columns} columns
          </p>
        </div>

        {/* column badges — scrollable on mobile */}
        <div className="flex flex-wrap gap-1.5 max-w-full overflow-x-auto pb-1">
          {columns.map((col) => (
            <span
              key={col.name}
              className={`inline-flex items-center gap-1 px-2 py-0.5 text-[10px] font-medium rounded-full border whitespace-nowrap ${badgeColor(col.dtype)}`}
            >
              {col.name}
              <span className="opacity-60">({col.dtype})</span>
            </span>
          ))}
        </div>
      </div>

      {/* ── table ──────────────────────────────────────────── */}
      <div className="overflow-x-auto rounded-xl border border-white/[0.06]">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-white/[0.04]">
              {preview.length > 0 &&
                Object.keys(preview[0]).map((key) => (
                  <th
                    key={key}
                    className="px-4 py-3 text-left text-[11px] font-semibold text-slate-300 uppercase tracking-wider whitespace-nowrap border-b border-white/[0.06]"
                  >
                    {key}
                  </th>
                ))}
            </tr>
          </thead>
          <tbody>
            {preview.map((row, i) => (
              <tr
                key={i}
                className="border-b border-white/[0.03] hover:bg-white/[0.02] transition-colors"
              >
                {Object.values(row).map((val, j) => (
                  <td
                    key={j}
                    className="px-4 py-2.5 text-slate-300 whitespace-nowrap font-mono text-xs"
                  >
                    {val === null || val === "" ? (
                      <span className="text-slate-600 italic">null</span>
                    ) : (
                      String(val)
                    )}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p className="text-[11px] text-slate-500 mt-2.5 text-right">
        Showing first {preview.length} of{" "}
        {profile.shape.rows.toLocaleString()} rows
      </p>
    </div>
  );
}
