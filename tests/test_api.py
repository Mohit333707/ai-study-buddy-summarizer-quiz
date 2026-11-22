"""API tests for AI Study Buddy (run: pytest)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from backend.app.main import app  # noqa: E402

client = TestClient(app)

NOTES = (
    "Photosynthesis is the process by which green plants convert sunlight, water "
    "and carbon dioxide into glucose and oxygen. Chlorophyll, the green pigment in "
    "leaves, absorbs light energy, mostly in the blue and red parts of the spectrum. "
    "The light-dependent reactions take place in the thylakoid membranes of "
    "chloroplasts, where water is split and ATP and NADPH are produced. The Calvin "
    "cycle then uses ATP and NADPH to fix carbon dioxide into sugars in the stroma. "
    "Photosynthesis is essential for life on Earth because it produces nearly all "
    "the oxygen in the atmosphere and forms the base of almost every food chain. "
    "Factors such as light intensity, carbon dioxide concentration and temperature "
    "affect the rate of photosynthesis."
)


def test_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"
    assert res.json()["engine"] == "tf-idf-extractive-v1"


def test_analyze_returns_real_results():
    res = client.post("/api/analyze", json={"text": NOTES})
    assert res.status_code == 200
    data = res.json()
    # Summary: real sentences from the input, in original order.
    assert 1 <= len(data["summary"]) <= 3
    assert all(s in NOTES for s in data["summary"])
    assert data["summary"] == sorted(data["summary"], key=NOTES.index)
    # Keywords: real terms from the input.
    terms = [k["term"] for k in data["keywords"]]
    assert "photosynthesis" in terms
    assert all(0 < k["score"] <= 1 for k in data["keywords"])
    # Quiz: questions blank out a keyword, answers are real terms.
    assert len(data["quiz"]) >= 1
    for q in data["quiz"]:
        assert "_____" in q["question"]
        assert q["answer"] in NOTES.lower() or q["answer"].lower() in NOTES.lower()
        if q["type"] == "multiple_choice":
            assert q["answer"] in q["options"] and len(q["options"]) == 4
    # Stats agree with the input.
    assert data["stats"]["word_count"] == len(NOTES.split())
    assert data["stats"]["sentence_count"] == 6
    assert data["stats"]["reading_time_minutes"] > 0


def test_analyze_is_deterministic():
    a = client.post("/api/analyze", json={"text": NOTES}).json()
    b = client.post("/api/analyze", json={"text": NOTES}).json()
    assert a == b


def test_summarize_keywords_quiz_endpoints():
    payload = {"text": NOTES, "summary_sentences": 2, "num_keywords": 5,
               "num_questions": 2}
    assert len(client.post("/api/summarize", json=payload).json()["summary"]) == 2
    kws = client.post("/api/keywords", json=payload).json()["keywords"]
    assert 1 <= len(kws) <= 5  # dedup may drop words covered by a phrase
    assert len(client.post("/api/quiz", json=payload).json()["quiz"]) == 2


def test_short_text_rejected():
    res = client.post("/api/analyze", json={"text": "Too short."})
    assert res.status_code == 422


def test_frontend_served():
    res = client.get("/")
    assert res.status_code == 200
    assert "AI Study Buddy" in res.text
