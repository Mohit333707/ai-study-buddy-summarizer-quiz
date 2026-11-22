const $ = (id) => document.getElementById(id);

async function checkHealth() {
  try {
    const res = await fetch("/api/health");
    const data = await res.json();
    $("status").textContent = `Backend online ✓ — engine: ${data.engine}`;
  } catch {
    $("status").textContent = "Backend offline — start it with: uvicorn backend.app.main:app --reload";
  }
}

const SAMPLE = `Photosynthesis is the process by which green plants convert sunlight, water and carbon dioxide into glucose and oxygen. Chlorophyll, the green pigment in leaves, absorbs light energy, mostly in the blue and red parts of the spectrum. The light-dependent reactions take place in the thylakoid membranes of chloroplasts, where water is split and ATP and NADPH are produced. The Calvin cycle then uses ATP and NADPH to fix carbon dioxide into sugars in the stroma. Photosynthesis is essential for life on Earth because it produces nearly all the oxygen in the atmosphere and forms the base of almost every food chain. Factors such as light intensity, carbon dioxide concentration and temperature affect the rate of photosynthesis.`;

let currentQuiz = [];

$("sampleBtn").addEventListener("click", () => { $("notes").value = SAMPLE; });

$("analyzeBtn").addEventListener("click", async () => {
  const error = $("error");
  error.hidden = true;
  const text = $("notes").value.trim();
  if (text.length < 50) {
    error.textContent = "Please paste at least a few sentences (50+ characters) of notes.";
    error.hidden = false;
    return;
  }
  const btn = $("analyzeBtn");
  btn.disabled = true; btn.textContent = "Analysing…";
  try {
    const res = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        text,
        summary_sentences: Number($("numSentences").value),
        num_keywords: Number($("numKeywords").value),
        num_questions: Number($("numQuestions").value),
      }),
    });
    if (!res.ok) throw new Error(`Server returned ${res.status}`);
    render(await res.json());
  } catch (e) {
    error.textContent = `Could not analyse: ${e.message}. Is the backend running?`;
    error.hidden = false;
  } finally {
    btn.disabled = false; btn.textContent = "✨ Analyse my notes";
  }
});

function render(data) {
  $("results").hidden = false;
  $("score").textContent = "";
  const s = data.stats;
  $("stats").innerHTML = [
    [s.word_count, "words"], [s.sentence_count, "sentences"],
    [`${s.reading_time_minutes} min`, "reading time"],
    [s.flesch_reading_ease, `readability (${s.difficulty})`],
  ].map(([v, l]) => `<div class="stat"><b>${v}</b><span>${l}</span></div>`).join("");
  $("summary").innerHTML = data.summary.map((x) => `<li>${escapeHtml(x)}</li>`).join("");
  $("keywords").innerHTML = data.keywords
    .map((k) => `<span class="chip">${escapeHtml(k.term)} <small>${k.score}</small></span>`).join("");

  currentQuiz = data.quiz;
  $("quiz").innerHTML = data.quiz.map((q, i) => {
    if (q.type === "multiple_choice") {
      const opts = q.options.map((o) =>
        `<label><input type="radio" name="q${i}" value="${escapeHtml(o)}"> ${escapeHtml(o)}</label>`).join("");
      return `<li>${escapeHtml(q.question)}<div>${opts}</div><p class="feedback" id="fb${i}"></p></li>`;
    }
    return `<li>${escapeHtml(q.question)}<br>
      <input type="text" id="ans${i}" placeholder="Missing word…" autocomplete="off">
      <p class="feedback" id="fb${i}"></p></li>`;
  }).join("") || "<li>No quiz could be built — add more varied sentences.</li>";
  $("results").scrollIntoView({ behavior: "smooth" });
}

$("checkBtn").addEventListener("click", () => {
  let correct = 0;
  currentQuiz.forEach((q, i) => {
    let given = "";
    if (q.type === "multiple_choice") {
      const sel = document.querySelector(`input[name="q${i}"]:checked`);
      given = sel ? sel.value : "";
    } else {
      given = ($(`ans${i}`) || { value: "" }).value.trim();
    }
    const ok = given.toLowerCase() === q.answer.toLowerCase();
    if (ok) correct++;
    $(`fb${i}`).innerHTML = ok
      ? `<span class="correct">✓ Correct!</span>`
      : `<span class="wrong">✗ The answer is “${escapeHtml(q.answer)}”.</span>`;
  });
  $("score").textContent = `— ${correct}/${currentQuiz.length} correct`;
});

$("revealBtn").addEventListener("click", () => {
  currentQuiz.forEach((q, i) => {
    $(`fb${i}`).innerHTML = `<span class="correct">Answer: ${escapeHtml(q.answer)}</span>`;
  });
});

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

checkHealth();
