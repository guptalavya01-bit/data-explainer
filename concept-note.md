# Data Explainer — Concept Note

## Project Title

**Data Explainer: AI-Powered Data Analysis and Explanation Tool**

---

## Problem Statement

Non-technical users, business analysts, and students frequently receive CSV or Excel datasets without any accompanying documentation. Understanding what a dataset contains — its structure, quality, statistical distributions, and hidden patterns — requires significant time and expertise in data analysis and programming.

There is a need for a tool that can **instantly translate raw data into plain-language insights**, making data literacy accessible to everyone regardless of their technical background.

---

## Target Users & Use Case

| User | Use Case |
|------|----------|
| **Business analysts** | Get quick dataset overviews before deep-diving into BI tools |
| **Students & researchers** | Understand unfamiliar datasets for coursework or projects |
| **Data engineers** | Quick profiling during data pipeline debugging |
| **Product managers** | Understand data exports without asking the data team |
| **Anyone** | Go from "I have a spreadsheet" to "I understand my data" in 60 seconds |

---

## LLM Model & API Used

- **Model:** Anthropic Claude (`claude-sonnet-4-20250514`)
- **API:** Anthropic Messages API with **streaming** enabled via `client.messages.stream()`
- **SDK:** `anthropic` Python SDK (v0.42+)
- **Why Claude:** Strong analytical reasoning, structured output quality, and native streaming support for real-time user experience

---

## Key Features

1. **Drag-and-drop file upload** — supports CSV and XLSX with client-side + server-side validation (type, size ≤ 10 MB, non-empty)
2. **Automated data profiling** — pandas-powered analysis producing shape, data types, missing-value percentages, summary statistics (mean/median/std/min/max), top-5 value counts for categorical columns, and a full numeric correlation matrix
3. **Streaming AI explanation** — Claude receives the structured profile (not raw data) and generates a comprehensive plain-language explanation, streamed token-by-token via Server-Sent Events
4. **Interactive data preview** — first 10 rows displayed in a responsive table with color-coded column type badges
5. **Follow-up Q&A chat** — multi-turn conversational interface where users ask questions about the same dataset, with full conversation context maintained across turns
6. **Production deployment** — Dockerized multi-stage build, deployable for free on Render.com

---

## Expected UX / Outcomes

1. User lands on a clean, dark-themed interface with a prominent upload zone
2. Drops a CSV/XLSX file → sees immediate validation feedback
3. Within 2–3 seconds: data preview table appears with column badges
4. Simultaneously: AI explanation streams in, rendering as markdown with headers, bullet points, and statistics
5. After explanation completes: follow-up chat appears with suggestion chips
6. User asks "What are the key trends?" → streamed answer referencing actual numbers from their data
7. Multi-turn conversation continues with full context

**End result:** A user with zero data analysis experience can understand any tabular dataset in under 60 seconds.

---

## Technology Stack Summary

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, Vite, Tailwind CSS 3 |
| Backend | Python 3.11, FastAPI, pandas, openpyxl |
| LLM | Anthropic Claude (streaming) |
| Container | Docker (multi-stage) |
| Deployment | Render.com (free tier) |
