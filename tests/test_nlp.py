"""Unit tests for the NLP engine (run: pytest)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.app import nlp  # noqa: E402

TEXT = (
    "The mitochondria is known as the powerhouse of the cell. "
    "Mitochondria generate most of the chemical energy needed to power the cell. "
    "This energy is stored in molecules called ATP. "
    "Cells with high energy demands, such as muscle cells, contain many mitochondria."
)


def test_split_sentences():
    assert len(nlp.split_sentences(TEXT)) == 4


def test_summarize_picks_real_sentences_in_order():
    summary = nlp.summarize(TEXT, 2)
    assert len(summary) == 2
    assert all(s in TEXT for s in summary)
    assert summary == sorted(summary, key=TEXT.index)


def test_keywords_include_core_term():
    terms = [k["term"] for k in nlp.extract_keywords(TEXT, 5)]
    assert "mitochondria" in terms


def test_quiz_answers_match_blanks():
    for q in nlp.generate_quiz(TEXT, 4):
        assert "_____" in q["question"]
        assert q["answer"]
        assert q["answer"].lower() not in q["question"].lower().replace("_____", "")


def test_quiz_deterministic():
    assert nlp.generate_quiz(TEXT, 4) == nlp.generate_quiz(TEXT, 4)


def test_reading_stats():
    stats = nlp.reading_stats(TEXT)
    assert stats["word_count"] == len(TEXT.split())
    assert stats["sentence_count"] == 4
    assert stats["difficulty"] in {"Easy", "Medium", "Hard"}


def test_empty_and_short_inputs():
    assert nlp.summarize("", 3) == []
    assert nlp.extract_keywords("", 5) == []
    assert nlp.generate_quiz("One sentence only.", 3) == []
