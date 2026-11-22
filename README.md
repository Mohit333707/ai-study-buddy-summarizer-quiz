# 📚 AI Study Buddy — Notes to Summary & Quiz

Paste your study notes or textbook text, and get back **a summary, the key concepts, and a quiz to test yourself** — so revision actually sticks.

Built with **FastAPI + pure-Python NLP**, with a clean single-page frontend (plain HTML/CSS/JS — no build step).

---

## ✨ Features

- **Smart summary** — extractive summarisation picks the most important sentences from your notes, in their original order.
- **Key concepts** — TF-IDF ranks the words and phrases that matter most, with a relevance score for each.
- **Auto quiz** — fill-in-the-blank and multiple-choice questions generated from your own notes. Distractors come from the notes themselves, so wrong options are plausible. Answers are checked in the browser with a score.
- **Reading stats** — word/sentence count, estimated reading time, and a Flesch readability score with an Easy / Medium / Hard label.
- **Deterministic** — the same notes always give the same summary, keywords and quiz, so results are reproducible.
- **Sample notes** — one click loads a photosynthesis example so you can try it instantly.

## 🧠 How the AI works

No model download, no API key — everything runs locally, offline, in pure Python (standard library only).

| Step | Method |
|---|---|
| Sentence scoring | TF-IDF — each sentence is a document, the whole note is the corpus; sentences carrying the most distinctive words score highest (length-normalised) |
| Key concepts | Top TF-IDF words + two-word phrases that beat their parts |
| Quiz | The best sentences have a key concept blanked out; MCQs offer that concept plus three other concepts from the notes as distractors (seeded shuffle, so the quiz is stable) |
| Readability | Flesch Reading Ease from a vowel-group syllable estimate |

**Honest note:** this is extractive summarisation (it selects your sentences, it does not write new ones) — it never invents facts that weren't in your notes.

## 🛠️ Tech stack

- **Backend:** Python 3.10+, FastAPI, Pydantic, Uvicorn
- **Frontend:** plain HTML, CSS, JavaScript — no framework, no build step
- **Tests:** pytest + FastAPI TestClient

## 📁 Project structure

```
ai-study-buddy-summarizer-quiz/
├── backend/
│   └── app/
│       ├── __init__.py
│       ├── main.py        # FastAPI app: routes + static frontend
│       ├── nlp.py         # TF-IDF engine: summary, keywords, quiz, stats
│       └── models.py      # Pydantic request/response schemas
├── frontend/
│   ├── index.html         # The study-buddy page
│   ├── styles.css
│   └── app.js
├── tests/
│   ├── test_api.py        # Real API tests (health, analyse, errors, frontend)
│   └── test_nlp.py        # Unit tests for the NLP engine
├── examples/
│   └── sample-notes.txt   # Photosynthesis notes to try
├── requirements.txt
├── .gitignore
├── LICENSE
└── README.md
```

## 🚀 Setup

```bash
# 1. Clone and enter the project
git clone https://github.com/Mohit333707/ai-study-buddy-summarizer-quiz.git
cd ai-study-buddy-summarizer-quiz

# 2. Create a virtual environment and install dependencies
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 3. Run the tests
pytest

# 4. Start the server
uvicorn backend.app.main:app --reload
```

Then open **http://127.0.0.1:8000** in your browser, paste some notes, and hit **✨ Analyse my notes**.

## 🔌 API

| Method | Endpoint | What it returns |
|---|---|---|
| `GET` | `/api/health` | `{"status": "ok", "engine": "tf-idf-extractive-v1", ...}` |
| `POST` | `/api/analyze` | summary + keywords + quiz + reading stats (one call) |
| `POST` | `/api/summarize` | summary only |
| `POST` | `/api/keywords` | key concepts only |
| `POST` | `/api/quiz` | quiz questions only |

Request body for all `POST` endpoints:

```json
{
  "text": "Your study notes here (50–50,000 characters)…",
  "summary_sentences": 3,
  "num_keywords": 10,
  "num_questions": 5
}
```

Example:

```bash
curl -X POST http://127.0.0.1:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "Photosynthesis is the process by which green plants convert sunlight, water and carbon dioxide into glucose and oxygen. Chlorophyll absorbs light energy. The Calvin cycle fixes carbon dioxide into sugars."}'
```

## 🧪 Example output

For the photosynthesis notes in `examples/sample-notes.txt`:

- **Summary:** the sentences about what photosynthesis is, the light-dependent reactions, and why it matters for life on Earth.
- **Top keywords:** `photosynthesis`, `carbon dioxide`, `light`, `chlorophyll`, `calvin cycle`…
- **Quiz:** *“_____ is the process by which green plants convert sunlight, water and carbon dioxide into glucose and oxygen.”* → photosynthesis.

## 📄 License

MIT — see [LICENSE](LICENSE).
