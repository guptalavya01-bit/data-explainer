"""
Pandas-based data profiler.
Produces a structured profile dict and a preview (first 10 rows) from an
uploaded CSV / XLSX file.  The profile — not the raw data — is what gets
sent to the LLM.
"""

from __future__ import annotations

import io
import os

import numpy as np
import pandas as pd


def _to_python(v):
    """Convert numpy / pandas scalars to native Python types for JSON."""
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return None
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.floating,)):
        return float(v)
    if isinstance(v, (np.bool_,)):
        return bool(v)
    if isinstance(v, (np.ndarray,)):
        return v.tolist()
    if isinstance(v, (pd.Timestamp,)):
        return v.isoformat()
    return v


class DataProfiler:
    """Stateless profiler — call ``profile(file_bytes, filename)``."""

    @staticmethod
    def profile(file_bytes: bytes, filename: str) -> tuple[dict, list[dict]]:
        ext = os.path.splitext(filename)[1].lower()

        if ext == ".csv":
            df = pd.read_csv(io.BytesIO(file_bytes))
        elif ext in (".xlsx", ".xls"):
            df = pd.read_excel(io.BytesIO(file_bytes))
        else:
            raise ValueError(f"Unsupported file type: {ext}")

        if df.empty:
            raise ValueError("The file contains no data rows.")

        # ── column-level profiles ────────────────────────────
        columns: list[dict] = []
        for col in df.columns:
            info: dict = {
                "name": str(col),
                "dtype": str(df[col].dtype),
                "missing_pct": round(float(df[col].isnull().mean() * 100), 2),
                "unique_count": int(df[col].nunique()),
                "is_numeric": bool(pd.api.types.is_numeric_dtype(df[col])),
            }

            if info["is_numeric"]:
                desc = df[col].describe()
                info["stats"] = {
                    "mean": round(float(desc.get("mean", 0)), 4),
                    "median": round(float(df[col].median()), 4),
                    "std": round(float(desc.get("std", 0)), 4),
                    "min": _to_python(desc.get("min", 0)),
                    "max": _to_python(desc.get("max", 0)),
                }
            else:
                top5 = df[col].value_counts().head(5)
                info["top_values"] = [
                    {"value": str(v), "count": int(c)} for v, c in top5.items()
                ]

            columns.append(info)

        # ── correlation matrix (numeric only) ────────────────
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        correlations: dict = {}
        if len(numeric_cols) > 1:
            corr = df[numeric_cols].corr()
            correlations = {
                c1: {c2: round(float(corr.loc[c1, c2]), 4) for c2 in numeric_cols}
                for c1 in numeric_cols
            }

        profile_dict = {
            "shape": {"rows": int(df.shape[0]), "columns": int(df.shape[1])},
            "columns": columns,
            "correlations": correlations,
        }

        # ── first-10-rows preview ────────────────────────────
        preview_df = df.head(10)
        preview = [
            {str(k): _to_python(v) for k, v in row.items()}
            for row in preview_df.to_dict(orient="records")
        ]

        return profile_dict, preview
