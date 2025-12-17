const recommendationForm = document.getElementById("recommendation-form");
const searchForm = document.getElementById("search-form");
const resultsContainer = document.getElementById("results-container");
const resultsTitle = document.getElementById("results-title");
const resultsCount = document.getElementById("results-count");

const setResults = (title, items, renderFn) => {
  resultsTitle.textContent = title;
  resultsCount.textContent = `${items.length} item${items.length === 1 ? "" : "s"}`;

  if (!items.length) {
    resultsContainer.innerHTML = `<p class="muted">No results. Try adjusting your filters.</p>`;
    return;
  }

  resultsContainer.innerHTML = items.map(renderFn).join("");
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

