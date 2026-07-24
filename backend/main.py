"""
FastAPI application — routes + startup.

Routes:
  POST /api/upload       – multipart file → profile + preview JSON
  GET  /api/explain/{id} – SSE stream of AI explanation tokens
  POST /api/ask          – SSE stream of follow-up answer tokens
  GET  /api/health       – healthcheck for deployment platforms
"""

from __future__ import annotations

import asyncio
import json
import os
import uuid

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from core.config import settings
from services.data_profiler import DataProfiler
from services.llm_service import LLMService
from services.storage_service import StorageService

# ── app setup ────────────────────────────────────────────────
app = FastAPI(
    title="Data Explainer API",
    description="AI-powered data analysis and explanation",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── services ─────────────────────────────────────────────────
storage = StorageService()
profiler = DataProfiler()
llm = LLMService()

# In-memory conversation history keyed by file_id
conversations: dict[str, list[dict]] = {}

# ── constants ────────────────────────────────────────────────
MAX_FILE_SIZE = settings.max_file_size_mb * 1024 * 1024
ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls"}

SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
}


# ── request models ───────────────────────────────────────────
class AskRequest(BaseModel):
    file_id: str
    question: str


# ── routes ───────────────────────────────────────────────────


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """Accept a CSV/XLSX upload, profile it with pandas, return metadata."""

    # validate extension
    filename = file.filename or "upload"
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {ext}. Allowed: CSV, XLSX, XLS.",
        )

    # read + validate size
    contents = await file.read()
    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="File is empty.")
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large ({len(contents) / 1024 / 1024:.1f} MB). "
            f"Maximum: {settings.max_file_size_mb} MB.",
        )

    # profile with pandas (CPU-bound → run in thread)
    try:
        profile, preview = await asyncio.to_thread(
            profiler.profile, contents, filename
        )
    except Exception as exc:
        raise HTTPException(
            status_code=400, detail=f"Could not parse file: {exc}"
        )

    # store
    file_id = str(uuid.uuid4())
    storage.save(file_id, contents, filename, profile, preview)
    conversations[file_id] = []

    return {
        "file_id": file_id,
        "filename": filename,
        "preview": preview,
        "profile": profile,
    }


@app.get("/api/explain/{file_id}")
async def explain(file_id: str):
    """Stream an AI-generated explanation of the dataset as SSE."""

    data = storage.get(file_id)
    if not data:
        raise HTTPException(status_code=404, detail="File not found.")

    profile = data["profile"]

    async def event_stream():
        full_response = ""
        try:
            async for token in llm.stream_explanation(profile):
                full_response += token
                yield f"data: {json.dumps({'token': token})}\n\n"
            yield f"data: {json.dumps({'done': True})}\n\n"

            # Store initial exchange in conversation history
            conversations[file_id] = [
                {"role": "user", "content": "Please analyze this dataset."},
                {"role": "assistant", "content": full_response},
            ]
        except Exception as exc:
            yield f"data: {json.dumps({'error': str(exc)})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers=SSE_HEADERS,
    )


@app.post("/api/ask")
async def ask(request: AskRequest):
    """Stream a follow-up answer about the same dataset as SSE."""

    data = storage.get(request.file_id)
    if not data:
        raise HTTPException(status_code=404, detail="File not found.")

    profile = data["profile"]
    history = conversations.get(request.file_id, [])

    # Append user question
    history.append({"role": "user", "content": request.question})

    async def event_stream():
        full_response = ""
        try:
            async for token in llm.stream_answer(
                profile, history, request.question
            ):
                full_response += token
                yield f"data: {json.dumps({'token': token})}\n\n"
            yield f"data: {json.dumps({'done': True})}\n\n"

            # Store assistant response in history
            history.append({"role": "assistant", "content": full_response})
        except Exception as exc:
            yield f"data: {json.dumps({'error': str(exc)})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers=SSE_HEADERS,
    )


# ── serve frontend static build (production) ────────────────
_static = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(_static):
    app.mount("/", StaticFiles(directory=_static, html=True), name="static")
