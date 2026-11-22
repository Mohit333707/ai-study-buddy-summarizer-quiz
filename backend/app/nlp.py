"""AI Study Buddy — NLP engine.

Pure-stdlib, offline NLP: no model download, no API key, deterministic
results so tests (and students) can rely on them.

Pipeline
--------
1. Split the notes into sentences.
2. Score every sentence with TF-IDF (each sentence is treated as a
   document, the whole note as the corpus) — sentences that carry the
   most distinctive words win.
3. Extract key concepts the same way (top TF-IDF words + bigrams).
4. Turn the best sentences into quiz questions:
   - fill-in-the-blank: hide a key concept inside its sentence.
   - multiple-choice: hide a key concept, offer it plus three other
     key concepts as distractors.
"""

from __future__ import annotations

import math
import random
import re
from collections import Counter

# ---------------------------------------------------------------------------
# Tokenising
# ---------------------------------------------------------------------------

STOPWORDS = frozenset(
    """
    a an the and or but if then else when while of at by for with about
    against between into through during before after above below to from
    up down in out on off over under again further once here there all
    any both each few more most other some such no nor not only own same
    so than too very can will just should now is am are was were be been
    being have has had having do does did doing would could shall may
    might must i you he she it we they me him her us them my your his
    its our their this that these those as what which who whom how why
    where when also one two three first second etc eg ie per via etc
    """.split()
)

_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'])")
_WORD_RE = re.compile(r"[a-z][a-z\-']*")


def split_sentences(text: str) -> list[str]:
    """Split text into sentences, keeping the trailing punctuation."""
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    parts = _SENTENCE_RE.split(text)
    return [p.strip() for p in parts if p.strip()]


def tokenize(sentence: str) -> list[str]:
    """Lower-case word tokens, stopwords removed."""
    words = _WORD_RE.findall(sentence.lower())
    return [w.strip("-'") for w in words if w.strip("-'") and w not in STOPWORDS]


def _syllables(word: str) -> int:
    """Rough syllable count (vowel-group heuristic) for readability."""
    word = re.sub(r"[^a-z]", "", word.lower())
    if not word:
        return 0
    groups = len(re.findall(r"[aeiouy]+", word))
    if word.endswith("e"):
        groups -= 1
    return max(1, groups)


# ---------------------------------------------------------------------------
# TF-IDF
# ---------------------------------------------------------------------------

def _tfidf(sentences: list[str]) -> tuple[list[Counter], dict[str, float]]:
    """Return per-sentence term frequencies and the IDF table."""
    docs = [tokenize(s) for s in sentences]
    n = len(docs)
    doc_freq: Counter = Counter()
    for tokens in docs:
        for term in set(tokens):
            doc_freq[term] += 1
    idf = {term: math.log((n + 1) / (df + 1)) + 1.0 for term, df in doc_freq.items()}
    return [Counter(t) for t in docs], idf


def _sentence_scores(sentences: list[str]) -> list[float]:
    tf_list, idf = _tfidf(sentences)
    scores = []
    for tokens in tf_list:
        total = sum(tokens.values())
        if total == 0:
            scores.append(0.0)
            continue
        # Length-normalised so long sentences don't win by word count alone.
        score = sum((count / total) * idf[term] for term, count in tokens.items())
        scores.append(score / math.sqrt(total))
    return scores


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def summarize(text: str, num_sentences: int = 3) -> list[str]:
    """Extractive summary: the highest-scoring sentences, in original order."""
    sentences = split_sentences(text)
    if len(sentences) <= num_sentences:
        return sentences
    scores = _sentence_scores(sentences)
    ranked = sorted(range(len(sentences)), key=lambda i: (-scores[i], i))
    chosen = sorted(ranked[:num_sentences])
    return [sentences[i] for i in chosen]


def extract_keywords(text: str, num_keywords: int = 10) -> list[dict]:
    """Top key concepts with a 0–1 relevance score.

    Returns single words and two-word phrases, ranked by TF-IDF weight.
    """
    sentences = split_sentences(text)
    if not sentences:
        return []
    tf_list, idf = _tfidf(sentences)
    totals: Counter = Counter()
    phrase_totals: Counter = Counter()
    for tokens, sentence in zip(tf_list, sentences):
        # Raw count across the whole note: a concept repeated through the
        # notes matters more than a word that appears once, however rare.
        for term, count in tokens.items():
            totals[term] += count * idf[term]
        # Bigrams from the raw (stopword-stripped) token stream.
        words = tokenize(sentence)
        for a, b in zip(words, words[1:]):
            phrase_totals[f"{a} {b}"] += (idf.get(a, 0) + idf.get(b, 0)) / 2

    merged: dict[str, float] = dict(totals)
    for phrase, score in phrase_totals.items():
        # A phrase only counts if it is repeated, or clearly beats its parts;
        # this keeps one-off word pairs from crowding out the real concepts.
        parts = phrase.split()
        phrase_count = sum(
            1 for s in sentences
            if re.search(rf"\b{re.escape(phrase)}\b", s, re.IGNORECASE)
        )
        if phrase_count >= 2 or score > max(merged.get(p, 0) for p in parts) * 2:
            merged[phrase] = score * phrase_count
    if not merged:
        return []
    top_score = max(merged.values())
    ranked = sorted(merged.items(), key=lambda kv: (-kv[1], kv[0]))[:num_keywords]
    # Drop a single word when a higher-ranked phrase already covers it
    # (e.g. keep "carbon dioxide", drop the bare "carbon" / "dioxide").
    phrases = {term for term, _ in ranked if " " in term}
    kept = [
        (term, score) for term, score in ranked
        if " " in term or not any(term in p.split() for p in phrases)
    ]
    return [
        {"term": term, "score": round(score / top_score, 3)}
        for term, score in kept
    ]


def _blank_out(sentence: str, term: str) -> str | None:
    """Replace the first whole-word occurrence of term with a blank."""
    pattern = re.compile(rf"\b{re.escape(term)}\b", re.IGNORECASE)
    if not pattern.search(sentence):
        return None
    return pattern.sub("_____", sentence, count=1)


def generate_quiz(text: str, num_questions: int = 5) -> list[dict]:
    """Build quiz questions from the notes.

    Alternates fill-in-the-blank and multiple-choice. Distractors come
    from the notes' own keywords, so every wrong option is plausible.
    Seeded per sentence, so the same notes always give the same quiz.
    """
    sentences = split_sentences(text)
    keywords = [k["term"] for k in extract_keywords(text, num_keywords=12)]
    if len(sentences) < 2 or not keywords:
        return []

    # Rank sentences by score; prefer ones containing a top keyword.
    scores = _sentence_scores(sentences)
    order = sorted(range(len(sentences)), key=lambda i: (-scores[i], i))

    questions: list[dict] = []
    used_terms: set[str] = set()
    for idx in order:
        if len(questions) >= num_questions:
            break
        sentence = sentences[idx]
        # Only blank a term that occurs exactly once in this sentence —
        # otherwise the answer stays visible elsewhere in the question.
        term = next(
            (kw for kw in keywords if kw not in used_terms
             and len(re.findall(rf"\b{re.escape(kw)}\b", sentence, re.IGNORECASE)) == 1),
            None,
        )
        if term is None:
            continue
        blanked = _blank_out(sentence, term)
        if blanked is None:
            continue
        used_terms.add(term)
        rng = random.Random(f"{sentence}|{term}")  # deterministic shuffle
        if len(questions) % 2 == 0:
            questions.append({
                "type": "fill_in_blank",
                "question": blanked,
                "answer": term,
            })
        else:
            distractors = [k for k in keywords if k != term][:3]
            while len(distractors) < 3:  # tiny notes: pad with generic terms
                distractors.append(f"none of the above ({len(distractors)})")
            options = distractors + [term]
            rng.shuffle(options)
            questions.append({
                "type": "multiple_choice",
                "question": blanked,
                "options": options,
                "answer": term,
            })
    return questions


def reading_stats(text: str) -> dict:
    """Word/sentence counts, reading time and a readability estimate."""
    sentences = split_sentences(text)
    words = re.findall(r"[A-Za-z][A-Za-z\-']*", text)
    n_words = len(words)
    n_sentences = max(1, len(sentences))
    n_syllables = sum(_syllables(w) for w in words) or 1
    # Flesch Reading Ease (0–100; higher = easier).
    flesch = 206.835 - 1.015 * (n_words / n_sentences) - 84.6 * (n_syllables / max(1, n_words))
    if flesch >= 70:
        level = "Easy"
    elif flesch >= 50:
        level = "Medium"
    else:
        level = "Hard"
    return {
        "word_count": n_words,
        "sentence_count": len(sentences),
        "reading_time_minutes": round(n_words / 200, 1),
        "avg_sentence_length_words": round(n_words / n_sentences, 1),
        "flesch_reading_ease": round(max(0.0, min(100.0, flesch)), 1),
        "difficulty": level,
    }


def analyze(text: str, num_sentences: int = 3, num_keywords: int = 10,
            num_questions: int = 5) -> dict:
    """Run the full pipeline and return everything the frontend needs."""
    return {
        "summary": summarize(text, num_sentences),
        "keywords": extract_keywords(text, num_keywords),
        "quiz": generate_quiz(text, num_questions),
        "stats": reading_stats(text),
    }
