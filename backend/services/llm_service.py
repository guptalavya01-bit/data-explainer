"""
Claude streaming client.

Uses ``anthropic.AsyncAnthropic`` with ``client.messages.stream()`` so that
tokens are yielded **as they arrive** — no buffering the full response first.
"""

from __future__ import annotations

from typing import AsyncGenerator

import anthropic

from core.config import settings


class LLMService:
    """Wraps the Anthropic Messages API for streaming explanations and Q&A."""

    SYSTEM_EXPLAIN = (
        "You are an expert data analyst. Analyze the provided dataset profile "
        "and give a comprehensive, plain-language explanation.\n\n"
        "Structure your response with these sections:\n\n"
        "## 📊 Overview\n"
        "What this dataset appears to be about, based on column names and data types.\n\n"
        "## 📐 Structure & Quality\n"
        "Number of records, columns, data types, and any data quality issues "
        "(missing values, etc.).\n\n"
        "## 📈 Key Statistics\n"
        "Important distributions, central tendencies, and ranges for numeric columns. "
        "Notable patterns in categorical columns.\n\n"
        "## 🔗 Correlations & Relationships\n"
        "Significant correlations between numeric variables and what they might indicate.\n\n"
        "## ⚠️ Anomalies & Concerns\n"
        "Any unusual patterns, potential outliers, or data quality issues worth investigating.\n\n"
        "## 💡 Recommendations\n"
        "Suggestions for further analysis or data cleaning.\n\n"
        "Be specific — cite actual numbers from the profile. Use markdown formatting."
    )

    def __init__(self) -> None:
        if settings.anthropic_api_key:
            self.client = anthropic.AsyncAnthropic(
                api_key=settings.anthropic_api_key
            )
        else:
            self.client = None
        self.model = "claude-sonnet-4-20250514"

    # ── public generators ────────────────────────────────────

    async def stream_explanation(
        self, profile: dict
    ) -> AsyncGenerator[str, None]:
        """Yield explanation tokens from Claude for the given data profile."""
        if not self.client:
            yield (
                "⚠️ **API Key Not Configured**\n\n"
                "Set the `ANTHROPIC_API_KEY` environment variable to enable "
                "AI analysis.\n\n"
                "Sign up at [console.anthropic.com](https://console.anthropic.com) "
                "— new accounts receive free credit."
            )
            return

        user_prompt = self._build_profile_prompt(profile)

        async with self.client.messages.stream(
            model=self.model,
            max_tokens=4096,
            system=self.SYSTEM_EXPLAIN,
            messages=[{"role": "user", "content": user_prompt}],
        ) as stream:
            async for text in stream.text_stream:
                yield text

    async def stream_answer(
        self,
        profile: dict,
        history: list[dict],
        question: str,
    ) -> AsyncGenerator[str, None]:
        """Yield answer tokens for a follow-up question about the same dataset."""
        if not self.client:
            yield "⚠️ API key not configured."
            return

        system = (
            "You are an expert data analyst. You have already analyzed a dataset. "
            "Answer the user's follow-up questions using the dataset profile below.\n\n"
            f"{self._build_profile_prompt(profile)}\n\n"
            "Be specific, reference actual numbers, and use markdown formatting."
        )

        # Build messages list — must start with a user turn for Claude
        messages: list[dict] = []
        for msg in history:
            messages.append({"role": msg["role"], "content": msg["content"]})

        async with self.client.messages.stream(
            model=self.model,
            max_tokens=4096,
            system=system,
            messages=messages,
        ) as stream:
            async for text in stream.text_stream:
                yield text

    # ── prompt builders ──────────────────────────────────────

    @staticmethod
    def _build_profile_prompt(profile: dict) -> str:
        lines: list[str] = []
        shape = profile["shape"]
        lines.append(
            f"**Dataset Shape:** {shape['rows']:,} rows × {shape['columns']} columns\n"
        )

        lines.append("**Columns:**\n")
        for col in profile["columns"]:
            line = (
                f"- **{col['name']}** (type: `{col['dtype']}`, "
                f"{col['missing_pct']}% missing, "
                f"{col['unique_count']} unique values)"
            )
            if col.get("is_numeric") and "stats" in col:
                s = col["stats"]
                line += (
                    f"\n  - Mean: {s['mean']}, Median: {s['median']}, "
                    f"Std: {s['std']}, Min: {s['min']}, Max: {s['max']}"
                )
            elif "top_values" in col:
                top = ", ".join(
                    f"{v['value']} ({v['count']})" for v in col["top_values"][:5]
                )
                line += f"\n  - Top values: {top}"
            lines.append(line)

        if profile.get("correlations"):
            lines.append("\n**Correlations (numeric columns):**")
            seen: set[tuple[str, str]] = set()
            for c1, corrs in profile["correlations"].items():
                for c2, val in corrs.items():
                    if c1 != c2 and (c2, c1) not in seen:
                        seen.add((c1, c2))
                        if abs(val) > 0.3:
                            lines.append(f"- {c1} ↔ {c2}: {val}")

        return "\n".join(lines)
