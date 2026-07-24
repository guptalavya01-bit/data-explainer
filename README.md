# Data Explainer — AI-Powered Data Analysis

Upload a CSV or Excel file and get a **streaming, AI-generated explanation** of your data — trends, distributions, anomalies, correlations — plus a follow-up Q&A chat about the same dataset.

Built for the IBM SkillsBuild × Bharat Cares **"Vibe Coding" GenAI + Cloud Computing** internship.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| **Drag & drop upload** | CSV / XLSX, max 10 MB, validated client + server side |
| **Pandas profiling** | Shape, dtypes, missing %, summary stats, top-5 values, correlation matrix |
| **Streaming AI analysis** | Claude explains your data token-by-token via SSE — no fake typewriter |
| **Follow-up Q&A** | Multi-turn chat about the same dataset with full conversation context |
| **Dark glassmorphism UI** | Premium dark theme with gradients, animations, Inter font |
| **One-command deploy** | `render.yaml` included for free Render.com hosting |

---

## 🛠 Tech Stack

- **Frontend:** React 18 + Vite + Tailwind CSS 3
- **Backend:** Python 3.11, FastAPI, pandas, openpyxl
- **LLM Engine:** Local LLM via Ollama / vLLM (Llama 3.1, Qwen 2.5 - **No API Key needed**), AWS Bedrock, or Anthropic Claude
- **Containerization:** Docker multi-stage build
- **Deployment:** AWS (App Runner / EC2 GPU — see [AWS Deployment Guide](file:///c:/Users/LAVYA/OneDrive/Desktop/IBM%20oroject/data-explainer/AWS_DEPLOYMENT.md)) or Render / Vercel

---



## 🚀 Quick Start

### Prerequisites

- **Node.js** ≥ 18 and **npm**
- **Python** ≥ 3.10
- An [Anthropic API key](https://console.anthropic.com) (new accounts get free credit)

### 1. Clone & configure

```bash
git clone <your-repo-url>
cd data-explainer
cp .env.example .env
# Edit .env and paste your ANTHROPIC_API_KEY
```

### 2. Run backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### 3. Run frontend (separate terminal)

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** — the Vite dev server proxies `/api` requests to the backend.

---

## 🐳 Docker (production build)

```bash
cp .env.example .env   # add your API key
docker compose up --build
```

Open **http://localhost:8000**.

---

## ☁️ Deploy to Render (Free)

1. Push this repo to GitHub
2. Go to [render.com](https://render.com) → **New** → **Blueprint**
3. Connect your GitHub repo — Render detects `render.yaml` automatically
4. Add your `ANTHROPIC_API_KEY` as a secret environment variable
5. Click **Deploy** — you'll get a free `*.onrender.com` URL

> **Note:** The free tier spins down after 15 min of inactivity. First request after spin-down takes ~30 s.

---

## 📁 Project Structure

```
data-explainer/
├── frontend/                  # Vite + React app
│   └── src/
│       ├── components/
│       │   ├── Upload.jsx     # Drag-drop file upload
│       │   ├── DataPreview.jsx# First-10-rows table + type badges
│       │   ├── ExplainPanel.jsx# Streaming AI explanation
│       │   └── FollowUpChat.jsx# Multi-turn Q&A chat
│       ├── App.jsx            # Main orchestrator + SSE parser
│       └── index.css          # Tailwind + glassmorphism styles
├── backend/
│   ├── main.py                # FastAPI routes
│   ├── core/config.py         # pydantic-settings env loading
│   └── services/
│       ├── data_profiler.py   # pandas profiling logic
│       ├── llm_service.py     # Claude streaming client
│       └── storage_service.py # File storage (local / COS)
├── Dockerfile                 # Multi-stage production build
├── docker-compose.yml         # Local dev with Docker
├── render.yaml                # Render.com free deploy blueprint
└── .env.example               # Template — never commit .env
```

---

## 🔐 Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | ✅ | Your Anthropic API key |
| `MAX_FILE_SIZE_MB` | No | Max upload size, default `10` |
| `ALLOWED_ORIGINS` | No | CORS origins, default `localhost` |
| `COS_ENDPOINT` | No | IBM COS endpoint (optional) |
| `COS_API_KEY_ID` | No | IBM COS API key (optional) |
| `COS_INSTANCE_CRN` | No | IBM COS instance CRN (optional) |
| `COS_BUCKET_NAME` | No | IBM COS bucket name (optional) |

---

## 📜 License

MIT — built as an educational project for IBM SkillsBuild.
