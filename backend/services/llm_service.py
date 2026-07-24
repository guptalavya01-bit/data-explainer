"""
Multi-provider LLM streaming client.

Supports:
1. Google Gemini API (via GEMINI_API_KEY - Free Tier available)
2. Anthropic Claude (via ANTHROPIC_API_KEY)
3. OpenAI (via OPENAI_API_KEY)
4. Local LLM / Ollama / vLLM (NO API key needed for local execution)
5. AWS Bedrock (Serverless Llama 3 via AWS IAM credentials)
"""

from __future__ import annotations

import json
from typing import AsyncGenerator

from core.config import settings


class LLMService:
    """Wraps Gemini, Anthropic, OpenAI, Local LLMs (Ollama/vLLM), and AWS Bedrock."""

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
        # Determine provider based on available API keys or explicit LLM_PROVIDER setting
        if settings.gemini_api_key:
            self.provider = "gemini"
        elif settings.anthropic_api_key:
            self.provider = "anthropic"
        elif settings.openai_api_key:
            self.provider = "openai"
        else:
            self.provider = settings.llm_provider.lower()

        # Initialize clients
        self.openai_client = None
        self.anthropic_client = None
        self.bedrock_client = None

        if self.provider == "gemini":
            import openai
            self.openai_client = openai.AsyncOpenAI(
                base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
                api_key=settings.gemini_api_key,
            )
            self.model_name = "gemini-1.5-flash"

        elif self.provider == "openai":
            import openai
            self.openai_client = openai.AsyncOpenAI(
                api_key=settings.openai_api_key,
            )
            self.model_name = "gpt-4o-mini"

        elif self.provider in ("ollama", "local"):
            import openai
            self.openai_client = openai.AsyncOpenAI(
                base_url=settings.local_llm_base_url,
                api_key="ollama",
            )
            self.model_name = settings.local_llm_model

        elif self.provider == "anthropic":
            if settings.anthropic_api_key:
                import anthropic
                self.anthropic_client = anthropic.AsyncAnthropic(
                    api_key=settings.anthropic_api_key
                )

        elif self.provider == "bedrock":
            import boto3
            self.bedrock_client = boto3.client(
                service_name="bedrock-runtime",
                region_name=settings.aws_region
            )

    async def stream_explanation(
        self, profile: dict
    ) -> AsyncGenerator[str, None]:
        """Yield explanation tokens for the given data profile."""
        user_prompt = self._build_profile_prompt(profile)

        if self.provider in ("ollama", "local", "openai", "gemini"):
            async for token in self._stream_openai_compatible(
                system_prompt=self.SYSTEM_EXPLAIN,
                user_prompt=user_prompt
            ):
                yield token

        elif self.provider == "bedrock":
            async for token in self._stream_aws_bedrock(
                system_prompt=self.SYSTEM_EXPLAIN,
                messages=[{"role": "user", "content": user_prompt}]
            ):
                yield token

        elif self.provider == "anthropic":
            async for token in self._stream_anthropic(
                system_prompt=self.SYSTEM_EXPLAIN,
                messages=[{"role": "user", "content": user_prompt}]
            ):
                yield token

        else:
            yield f"⚠️ Unknown LLM_PROVIDER: `{self.provider}`. Supported: `gemini`, `ollama`, `bedrock`, `anthropic`, `openai`."

    async def stream_answer(
        self,
        profile: dict,
        history: list[dict],
        question: str,
    ) -> AsyncGenerator[str, None]:
        """Yield answer tokens for a follow-up question about the same dataset."""
        system_prompt = (
            "You are an expert data analyst. You have already analyzed a dataset. "
            "Answer the user's follow-up questions using the dataset profile below.\n\n"
            f"{self._build_profile_prompt(profile)}\n\n"
            "Be specific, reference actual numbers, and use markdown formatting."
        )

        messages = [{"role": msg["role"], "content": msg["content"]} for msg in history]

        if self.provider in ("ollama", "local", "openai", "gemini"):
            async for token in self._stream_openai_compatible(
                system_prompt=system_prompt,
                messages=messages
            ):
                yield token

        elif self.provider == "bedrock":
            async for token in self._stream_aws_bedrock(
                system_prompt=system_prompt,
                messages=messages
            ):
                yield token

        elif self.provider == "anthropic":
            async for token in self._stream_anthropic(
                system_prompt=system_prompt,
                messages=messages
            ):
                yield token

    # ── Private Provider Implementations ──────────────────────

    async def _stream_openai_compatible(
        self,
        system_prompt: str,
        user_prompt: str | None = None,
        messages: list[dict] | None = None,
    ) -> AsyncGenerator[str, None]:
        if not self.openai_client:
            yield "⚠️ LLM client not initialized. Check your environment variables."
            return

        formatted_messages = [{"role": "system", "content": system_prompt}]
        if messages:
            formatted_messages.extend(messages)
        elif user_prompt:
            formatted_messages.append({"role": "user", "content": user_prompt})

        try:
            stream = await self.openai_client.chat.completions.create(
                model=self.model_name,
                messages=formatted_messages,
                stream=True,
            )
            async for chunk in stream:
                if chunk.choices and len(chunk.choices) > 0 and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as exc:
            if self.provider in ("ollama", "local"):
                yield (
                    f"\n\n⚠️ **Local LLM Connection Error:** Could not connect to local server at `{settings.local_llm_base_url}`.\n"
                    f"Ensure Ollama or vLLM is running locally (`ollama run {settings.local_llm_model}`).\n"
                    f"For cloud deployment (e.g. Render/Vercel), add `GEMINI_API_KEY` or `ANTHROPIC_API_KEY` to Environment Variables.\n\n"
                    f"Details: `{exc}`"
                )
            else:
                yield f"\n\n⚠️ **AI Service Error ({self.provider}):** `{exc}`"

    async def _stream_aws_bedrock(
        self,
        system_prompt: str,
        messages: list[dict],
    ) -> AsyncGenerator[str, None]:
        if not self.bedrock_client:
            yield "⚠️ AWS Bedrock client not initialized."
            return

        import asyncio

        prompt_str = f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n{system_prompt}<|eot_id|>"
        for m in messages:
            role = m["role"]
            content = m["content"]
            prompt_str += f"<|start_header_id|>{role}<|end_header_id|>\n{content}<|eot_id|>"
        prompt_str += "<|start_header_id|>assistant<|end_header_id|>\n"

        body = json.dumps({
            "prompt": prompt_str,
            "max_gen_len": 4096,
            "temperature": 0.5,
        })

        try:
            response = await asyncio.to_thread(
                self.bedrock_client.invoke_model_with_response_stream,
                modelId=settings.aws_bedrock_model_id,
                body=body
            )

            for event in response.get("body"):
                chunk = json.loads(event["chunk"]["bytes"])
                if "generation" in chunk:
                    yield chunk["generation"]
        except Exception as exc:
            yield (
                f"\n\n⚠️ **AWS Bedrock Error:** `{exc}`\n"
                "Ensure your AWS credentials / IAM Role has `bedrock:InvokeModelWithResponseStream` permissions."
            )

    async def _stream_anthropic(
        self,
        system_prompt: str,
        messages: list[dict],
    ) -> AsyncGenerator[str, None]:
        if not self.anthropic_client:
            yield (
                "⚠️ **API Key Not Configured**\n\n"
                "Set `ANTHROPIC_API_KEY` or `GEMINI_API_KEY` in Environment Variables."
            )
            return

        async with self.anthropic_client.messages.stream(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4096,
            system=system_prompt,
            messages=messages,
        ) as stream:
            async for text in stream.text_stream:
                yield text

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
