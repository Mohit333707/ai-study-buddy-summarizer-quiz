"""AI Study Buddy — FastAPI backend.

Endpoints
---------
GET  /api/health     — liveness check (engine + version)
POST /api/analyze    — summary + keywords + quiz + reading stats, in one call
POST /api/summarize  — extractive summary only
POST /api/keywords   — key concepts only
POST /api/quiz       — auto-generated quiz only
GET  /               — the frontend (static files under /frontend)
"""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from . import nlp
from .models import (
    AnalyzeRequest,
    AnalyzeResponse,
    KeywordsResponse,
    QuizResponse,
    SummaryResponse,
)

BASE_DIR = Path(__file__).resolve().parents[2]
FRONTEND_DIR = BASE_DIR / "frontend"

app = FastAPI(
    title="AI Study Buddy",
    description="Paste study notes → get a summary, key concepts and a quiz.",
    version="1.0.0",
)


@app.get("/api/health")
def health() -> dict:
    return {
        "status": "ok",
        "engine": "tf-idf-extractive-v1",
        "version": app.version,
    }


def _require_text(text: str) -> str:
    return text.strip()


@app.post("/api/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest) -> dict:
    return nlp.analyze(
        _require_text(req.text),
        num_sentences=req.summary_sentences,
        num_keywords=req.num_keywords,
        num_questions=req.num_questions,
    )


@app.post("/api/summarize", response_model=SummaryResponse)
def summarize(req: AnalyzeRequest) -> dict:
    return {"summary": nlp.summarize(_require_text(req.text), req.summary_sentences)}


@app.post("/api/keywords", response_model=KeywordsResponse)
def keywords(req: AnalyzeRequest) -> dict:
    return {"keywords": nlp.extract_keywords(_require_text(req.text), req.num_keywords)}


@app.post("/api/quiz", response_model=QuizResponse)
def quiz(req: AnalyzeRequest) -> dict:
    return {"quiz": nlp.generate_quiz(_require_text(req.text), req.num_questions)}


# --- Frontend (served statically, no build step) ---------------------------
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

    @app.get("/", include_in_schema=False)
    def index() -> FileResponse:
        return FileResponse(FRONTEND_DIR / "index.html")
