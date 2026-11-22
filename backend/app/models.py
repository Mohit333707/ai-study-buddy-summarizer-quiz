"""Pydantic request/response schemas for the Study Buddy API."""

from __future__ import annotations

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    text: str = Field(..., min_length=50, max_length=50_000,
                      description="Study notes / textbook text to analyse.")
    summary_sentences: int = Field(3, ge=1, le=10)
    num_keywords: int = Field(10, ge=1, le=20)
    num_questions: int = Field(5, ge=0, le=10)


class Keyword(BaseModel):
    term: str
    score: float


class QuizQuestion(BaseModel):
    type: str
    question: str
    answer: str
    options: list[str] | None = None


class ReadingStats(BaseModel):
    word_count: int
    sentence_count: int
    reading_time_minutes: float
    avg_sentence_length_words: float
    flesch_reading_ease: float
    difficulty: str


class AnalyzeResponse(BaseModel):
    summary: list[str]
    keywords: list[Keyword]
    quiz: list[QuizQuestion]
    stats: ReadingStats


class SummaryResponse(BaseModel):
    summary: list[str]


class KeywordsResponse(BaseModel):
    keywords: list[Keyword]


class QuizResponse(BaseModel):
    quiz: list[QuizQuestion]
