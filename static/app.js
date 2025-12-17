const recommendationForm = document.getElementById("recommendation-form");
const searchForm = document.getElementById("search-form");
const nlpForm = document.getElementById("nlp-form");
const explainButton = document.getElementById("explain_button");
const resultsContainer = document.getElementById("results-container");
const resultsTitle = document.getElementById("results-title");
const resultsCount = document.getElementById("results-count");
const explanationContainer = document.getElementById("explanation-container");

const setResults = (title, items, renderFn) => {
  resultsTitle.textContent = title;
  resultsCount.textContent = `${items.length} item${items.length === 1 ? "" : "s"}`;

  if (!items.length) {
    resultsContainer.innerHTML = `<p class="muted">No results. Try adjusting your filters.</p>`;
    return;
  }

  resultsContainer.innerHTML = items.map(renderFn).join("");
};

const renderTable = (items) => {
  if (!items.length) {
    return `<p class="muted">No results. Try adjusting your query or URL.</p>`;
  }
  const rows = items
    .map(
      (r) => `
      <tr>
        <td>${r.name || ""}</td>
        <td>${
          r.url
            ? `<a href="${r.url}" target="_blank" rel="noopener">View</a>`
            : "N/A"
        }</td>
        <td>${r.similarity != null ? (r.similarity * 100).toFixed(1) + "%" : "—"}</td>
      </tr>
    `
    )
    .join("");

  return `
    <table class="results-table">
      <thead>
        <tr>
          <th>Assessment</th>
          <th>URL</th>
          <th>Match</th>
        </tr>
      </thead>
      <tbody>
        ${rows}
      </tbody>
    </table>
  `;
};

const renderRecommendation = (rec) => {
  const competencies = rec.competencies?.slice(0, 4).join(", ") || "N/A";
  const useCases = rec.use_cases?.join(", ") || "N/A";
  const score = rec.match_score != null ? `${rec.match_score}%` : "—";
  return `
    <div class="result-card">
      <h4>${rec.name} <span class="pill">${score}</span></h4>
      <div class="meta">
        <span class="badge">${rec.type}</span>
        <span class="badge">${rec.category}</span>
        <span class="badge">${rec.duration_minutes} min</span>
        <span class="badge">${rec.difficulty_level}</span>
      </div>
      <p class="muted">${rec.description || "No description"}</p>
      <p class="muted"><strong>Competencies:</strong> ${competencies}</p>
      <p class="muted"><strong>Use cases:</strong> ${useCases}</p>
    </div>
  `;
};

const renderAssessment = (a) => {
  const competencies = a.competencies?.slice(0, 4).join(", ") || "N/A";
  const useCases = a.use_cases?.join(", ") || "N/A";
  return `
    <div class="result-card">
      <h4>${a.name} <span class="pill">${a.id}</span></h4>
      <div class="meta">
        <span class="badge">${a.type}</span>
        <span class="badge">${a.category}</span>
        <span class="badge">${a.duration_minutes} min</span>
        <span class="badge">${a.difficulty_level}</span>
      </div>
      <p class="muted">${a.description || "No description"}</p>
      <p class="muted"><strong>Competencies:</strong> ${competencies}</p>
      <p class="muted"><strong>Use cases:</strong> ${useCases}</p>
    </div>
  `;
};

const toList = (value) =>
  value
    ?.split(",")
    .map((v) => v.trim())
    .filter(Boolean) || undefined;

recommendationForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  const payload = {
    target_role: recommendationForm.target_role.value || undefined,
    competencies: toList(recommendationForm.competencies.value),
    use_case: recommendationForm.use_case.value || undefined,
    assessment_type: recommendationForm.assessment_type.value || undefined,
    max_duration_minutes: recommendationForm.max_duration_minutes.value
      ? Number(recommendationForm.max_duration_minutes.value)
      : undefined,
    difficulty_level: recommendationForm.difficulty_level.value || undefined,
    language: recommendationForm.language.value || undefined,
    exclude_ids: toList(recommendationForm.exclude_ids.value),
    top_n: recommendationForm.top_n.value ? Number(recommendationForm.top_n.value) : 5,
  };

  try {
    resultsContainer.innerHTML = `<p class="muted">Loading recommendations...</p>`;
    const res = await fetch("/recommendations", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Request failed");

    setResults("Recommendations", data.recommendations || [], renderRecommendation);
  } catch (err) {
    resultsContainer.innerHTML = `<p class="muted">Error: ${err.message}</p>`;
  }
});

nlpForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  const query = nlpForm.nlp_query.value || "";
  const jdUrl = nlpForm.jd_url.value || undefined;
  let topN = 10;
  if (nlpForm.nlp_top_n.value) {
    const parsed = Number(nlpForm.nlp_top_n.value);
    if (!Number.isNaN(parsed)) {
      topN = parsed;
    }
  }
  // Enforce 5–10 as per requirements
  if (topN < 5) topN = 5;
  if (topN > 10) topN = 10;

  const payload = {
    query,
    jd_url: jdUrl,
    top_n: topN,
  };

  try {
    resultsContainer.innerHTML = `<p class="muted">Loading text-based recommendations...</p>`;
    const res = await fetch("/text_recommendations", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Request failed");

    resultsTitle.textContent = "Text-based Recommendations";
    resultsCount.textContent = `${data.recommendations.length} item${
      data.recommendations.length === 1 ? "" : "s"
    }`;
    resultsContainer.innerHTML = renderTable(data.recommendations || []);
  } catch (err) {
    resultsContainer.innerHTML = `<p class="muted">Error: ${err.message}</p>`;
  }
});

if (explainButton) {
  explainButton.addEventListener("click", async () => {
    const query = nlpForm.nlp_query.value || "";
    const jdUrl = nlpForm.jd_url.value || undefined;
    let topN = 10;
    if (nlpForm.nlp_top_n.value) {
      const parsed = Number(nlpForm.nlp_top_n.value);
      if (!Number.isNaN(parsed)) {
        topN = parsed;
      }
    }
    if (topN < 5) topN = 5;
    if (topN > 10) topN = 10;

    const payload = {
      query,
      jd_url: jdUrl,
      top_n: topN,
    };

    try {
      explanationContainer.innerHTML = `<p class="muted">Generating explanation with Gemini...</p>`;
      const res = await fetch("/explanations", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Request failed");

      // Optionally refresh recommendations with what the server used
      if (data.recommendations) {
        resultsTitle.textContent = "Text-based Recommendations";
        resultsCount.textContent = `${data.recommendations.length} item${
          data.recommendations.length === 1 ? "" : "s"
        }`;
        resultsContainer.innerHTML = renderTable(data.recommendations);
      }

      const explanationText = data.explanation || "No explanation returned.";
      explanationContainer.innerHTML = `<h4>Gemini Explanation</h4><pre>${explanationText}</pre>`;
    } catch (err) {
      explanationContainer.innerHTML = `<p class="muted">Error: ${err.message}</p>`;
    }
  });
}

searchForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const term = searchForm.search_term.value.trim();
  if (!term) {
    resultsContainer.innerHTML = `<p class="muted">Enter a search term.</p>`;
    return;
  }

  try {
    resultsContainer.innerHTML = `<p class="muted">Searching...</p>`;
    const res = await fetch(`/assessments/search?q=${encodeURIComponent(term)}`);
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Request failed");

    setResults(`Search: "${term}"`, data.assessments || [], renderAssessment);
  } catch (err) {
    resultsContainer.innerHTML = `<p class="muted">Error: ${err.message}</p>`;
  }
});

// On load, fetch all assessments to populate initial view
window.addEventListener("DOMContentLoaded", async () => {
  try {
    const res = await fetch("/assessments");
    const data = await res.json();
    if (res.ok) {
      setResults("All assessments", data.assessments || [], renderAssessment);
    }
  } catch (err) {
    // ignore initial load errors
  }
});

