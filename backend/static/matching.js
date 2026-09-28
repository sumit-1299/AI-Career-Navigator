"use strict";

// Loaded before workspace.js. Functions run only after its shared state is initialized.
const MATCH_DEMO = {
  title: "Junior Python Backend Developer — example",
  description:
    "Requirements:\nDevelop backend applications in Python.\nWrite relational queries to combine tables and summarize records.\nBuild web endpoints that accept JSON requests and return responses over HTTP.\nUse Git to collaborate on source code.\nPreferred skills:\nDocker is a bonus.\nNo Java experience is required.",
};

function clearMatchDraft() {
  state.matchDraft = null;
  state.matchDirty = false;
}

function clearMatchState() {
  clearMatchDraft();
  state.matchMetadata = null;
  state.matchHistory = [];
  state.comparison = null;
}

async function loadMatches() {
  state.matchMetadata = await request("/api/job-matches/metadata");
  state.matchHistory = (await request("/api/job-matches")).comparisons;
}

function freshMatchDraft(overrides = {}) {
  return {
    submission_id: crypto.randomUUID(),
    title: "",
    description: "",
    source_url: "",
    mode: state.matchMetadata.semantic_model.available ? "semantic" : "keyword",
    ...overrides,
  };
}

function matchesMarkup() {
  if (state.comparison && !state.matchDraft) return comparisonMarkup();
  const draft = state.matchDraft || (state.matchDraft = freshMatchDraft());
  const ready = state.matchMetadata.semantic_model.available;
  return `<div class="page-intro"><span class="eyebrow">Connect your experience to a role</span><h1>Compare a job</h1><p class="muted">Paste a job description to explore its skill requirements alongside your saved claims, projects, certificates and SQL assessment.</p></div>
    <div class="match-editor-layout"><section class="panel"><form id="match-form"><label>Job title<input name="title" maxlength="160" value="${escapeHtml(draft.title)}" placeholder="Junior Python Backend Developer" required></label><label>Job description<textarea name="description" rows="10" minlength="20" maxlength="8000" aria-describedby="match-description-hint" placeholder="Paste the responsibilities and skill requirements here…" required>${escapeHtml(draft.description)}</textarea><span class="field-hint" id="match-description-hint">20–8,000 characters. Preserve headings such as Requirements and Preferred skills.</span></label><label>Source link (optional)<input name="source_url" type="url" maxlength="2048" value="${escapeHtml(draft.source_url)}" placeholder="https://company.example/careers/job"></label><label>Comparison method<select name="mode"><option value="semantic" ${draft.mode === "semantic" ? "selected" : ""} ${ready ? "" : "disabled"}>Keywords + semantic suggestions</option><option value="keyword" ${draft.mode === "keyword" ? "selected" : ""}>Keyword baseline</option></select></label>${ready ? '<p class="small muted">Semantic suggestions use a pretrained model running locally. Suggested links still need review.</p>' : '<p class="small muted">The semantic model is not ready on this server. Keyword comparison is available.</p>'}<div class="button-row evidence-form-actions"><button class="button primary" type="submit">Compare and save</button><button class="button secondary" type="button" data-action="demo-match">Use example description</button></div></form></section>
    <aside class="panel evidence-guide"><span class="badge neutral">Research prototype</span><h2>What this comparison shows</h2><p>Named skills and possible semantic links are displayed separately. A missing record means we need more evidence.</p><p>Each comparison saves the job text and profile records it used. Later profile edits do not rewrite a saved comparison.</p><h3>Current vocabulary</h3><div class="topic-chips">${state.matchMetadata.skills.map((skill) => `<span>${escapeHtml(skill.label)}</span>`).join("")}</div><p class="section-note">This is a pasted description, not a live vacancy check. The example description is fictional.</p></aside></div>${matchHistoryMarkup()}`;
}

function matchHistoryMarkup() {
  return `<section class="history-section"><div class="section-label"><h2>Saved comparisons</h2><span class="small muted">Latest 30</span></div>${state.matchHistory.length ? `<div class="history-list">${state.matchHistory.map((item) => `<article class="history-row"><div><h3>${escapeHtml(item.title)}</h3><p>${escapeHtml(dateLabel(item.created_at))} · ${item.mode === "semantic" ? "Keywords + semantic suggestions" : "Keyword baseline"}</p></div><button class="button secondary" data-action="open-match" data-id="${escapeHtml(item.id)}">Open comparison</button></article>`).join("")}</div>` : '<div class="empty-state"><span class="empty-icon" aria-hidden="true">◇</span><div><strong>Your first comparison starts here</strong><p>Saved results can be reopened without running the model again.</p></div></div>'}</section>`;
}

function claimMarkup(claim, related = false) {
  const kind =
    claim.kind === "self_report"
      ? `Self-rating ${claim.rating}/10`
      : `${claim.kind === "project" ? "Project" : "Certificate"} · Unverified`;
  return `<li><strong>${escapeHtml(claim.label)}</strong><span>${escapeHtml(kind)}${related ? ` · Related skill: ${escapeHtml(claim.skill_label)}` : ""}</span></li>`;
}

function comparisonSkillMarkup(row) {
  const assessment = row.assessment;
  return `<article class="panel match-skill"><div class="button-row spread"><h2>${escapeHtml(row.label)}</h2><span class="badge ${row.mapping === "keyword" ? "neutral" : "amber"}">${row.mapping === "keyword" ? "Named in description" : "Semantic suggestion · Review"}</span></div><div class="match-skill-columns"><section><h3>Job text</h3>${row.job_sources.map((source) => `<blockquote class="match-quote">${escapeHtml(source.text)}<footer>${source.importance === "required" ? "Required wording" : source.importance === "optional" ? "Optional / preferred wording" : "Mentioned in description"} · ${source.method === "keyword" ? "Keyword / alias" : `Semantic suggestion · cosine ${Number(source.similarity).toFixed(3)}`}</footer></blockquote>`).join("")}</section><section><h3>Your saved evidence</h3>${row.candidate_claims.length ? `<ul class="match-claims">${row.candidate_claims.map((claim) => claimMarkup(claim)).join("")}</ul>` : '<p class="small muted">No direct skill claim recorded for this concept.</p>'}${row.related_claims.length ? `<details class="evidence-details"><summary>Related claims (${row.related_claims.length})</summary><p class="small muted">Related technologies are not treated as equivalent skills.</p><ul class="match-claims">${row.related_claims.map((claim) => claimMarkup(claim, true)).join("")}</ul></details>` : ""}${assessment ? `<div class="match-assessment"><span class="badge neutral">SQL diagnostic snapshot</span><p>${escapeHtml(percent(assessment.result.accuracy_on_answered_percent))} accuracy · ${assessment.result.answered_count}/${assessment.result.question_count} answered</p><ul>${assessment.result.topics.map((topic) => `<li>${escapeHtml(topic.topic)}: ${topic.correct_count} correct, ${topic.incorrect_count} incorrect, ${topic.unanswered_count} unassessed</li>`).join("")}</ul><button class="text-button" data-action="open-attempt" data-id="${escapeHtml(assessment.attempt_id)}">Open SQL result & roadmap →</button></div>` : '<p class="small muted">No assessment result recorded for this skill.</p>'}</section></div><p class="match-guidance">${escapeHtml(row.guidance)}</p></article>`;
}

function comparisonMarkup() {
  const saved = state.comparison;
  const result = saved.result;
  const summary = result.summary;
  const otherMode = saved.mode === "semantic" ? "keyword" : "semantic";
  const canCompare =
    otherMode === "keyword" || state.matchMetadata.semantic_model.available;
  return `<div class="page-intro result-heading"><div><span class="eyebrow">Saved job comparison</span><h1>${escapeHtml(saved.title)}</h1><p class="muted">${escapeHtml(dateLabel(saved.created_at))} · ${saved.mode === "semantic" ? "Keywords + semantic suggestions" : "Keyword baseline"}</p></div><button class="button secondary" data-action="new-match">New comparison</button></div>
    <section class="panel match-summary"><div><strong>${summary.explicit_skill_mentions}</strong><span>Named skill concepts</span></div><div><strong>${summary.explicit_mentions_with_claims}</strong><span>Named concepts with your claims</span></div><div><strong>${summary.semantic_suggestions}</strong><span>Suggested concepts to review</span></div><div><strong>${summary.skills_with_assessment_records}</strong><span>Concepts with an assessment record</span></div></section>
    <div class="info-line"><span class="info-icon" aria-hidden="true">i</span><p>${escapeHtml(result.interpretation)}</p></div>
    <div class="section-label"><h2>Skills and supporting records</h2>${canCompare ? `<button class="text-button" data-action="compare-${otherMode}">Try ${otherMode === "keyword" ? "keyword baseline" : "semantic suggestions"}</button>` : ""}</div>
    ${result.skills.length ? `<div class="match-skill-list">${result.skills.map(comparisonSkillMarkup).join("")}</div>` : '<div class="empty-state"><div><strong>No skill mappings found in this vocabulary</strong><p>The job may require skills outside the current scope. This does not mean you are unsuitable.</p></div></div>'}
    ${result.manual_review.length ? `<section class="panel match-review"><h2>Read these passages manually</h2><p class="small muted">Negated or qualified statements were excluded from automatic requirement mapping.</p>${result.manual_review.map((item) => `<blockquote class="match-quote">${escapeHtml(item.text)}</blockquote>`).join("")}</section>` : ""}
    <details class="panel match-review"><summary>Unmapped text and profile tags</summary><p class="small muted">${escapeHtml(result.scope)}</p><h3>Job passages without a mapping</h3>${result.unassigned_fragments.length ? `<ul>${result.unassigned_fragments.map((text) => `<li>${escapeHtml(text)}</li>`).join("")}</ul>` : '<p class="small muted">No whole passage was left unmapped. Individual requirements can still be missed.</p>'}<h3>Profile tags outside the vocabulary</h3><p class="small muted">${escapeHtml(result.unmapped_candidate_tags.join(", ") || "None in this snapshot.")}</p></details>
    <details class="panel match-review"><summary>Source and comparison method</summary><p class="small muted">${comparisonSourceLabel(saved.job)}</p>${saved.job.source_url ? evidenceSourceMarkup(saved.job.source_url) : ""}<pre class="match-source-text">${escapeHtml(saved.job.description)}</pre><p class="small muted">Profile captured ${escapeHtml(dateLabel(saved.candidate_snapshot.captured_at))}. ${saved.candidate_snapshot.evidence.length} active evidence records were included. Saved snapshots retain their original details even if the profile is edited or an item is archived later.</p><p class="small muted">Policy: ${escapeHtml(result.policy_version)} · Vocabulary: ${escapeHtml(result.catalog_version)}</p>${result.model ? `<p class="small muted">Model: ${escapeHtml(result.model.id)}<br>Revision: ${escapeHtml(result.model.revision)}<br>Semantic suggestions use cosine ≥ ${result.suggestion_policy.minimum_cosine} and a best-versus-next margin ≥ ${result.suggestion_policy.minimum_margin}. These are uncalibrated prototype settings, not confidence probabilities.</p>` : '<p class="small muted">Keyword mode uses only the curated names and aliases. No embedding model was run.</p>'}</details>${matchHistoryMarkup()}`;
}

async function submitMatch(values) {
  const body = {
    submission_id: state.matchDraft.submission_id,
    title: values.get("title").trim(),
    description: values.get("description").trim(),
    source_url: values.get("source_url").trim(),
    mode: values.get("mode"),
  };
  state.matchDraft = { ...body };
  const button = document.querySelector('#match-form [type="submit"]');
  const label = button.textContent;
  button.textContent = "Comparing…";
  try {
    const data = await request("/api/job-matches", { method: "POST", body });
    state.comparison = data.comparison;
    state.matchHistory = [
      data.comparison,
      ...state.matchHistory.filter((item) => item.id !== data.comparison.id),
    ].slice(0, 30);
    clearMatchDraft();
    renderShell();
    focusContent();
    showNotice(
      "Comparison saved with the profile records used. Assessment scores are unchanged.",
      true,
    );
  } finally {
    if (button.isConnected) button.textContent = label;
  }
}

async function handleMatchAction(action, button) {
  if (action === "matches" || action === "new-match") {
    await loadMatches();
    state.evidenceEditor = null;
    state.evidenceDirty = false;
    clearMatchDraft();
    state.comparison = null;
    state.view = "matches";
  } else if (action === "open-match") {
    state.comparison = (
      await request(`/api/job-matches/${button.dataset.id}`)
    ).comparison;
    clearMatchDraft();
  } else if (action === "demo-match") {
    const form = document.querySelector("#match-form");
    if (
      state.matchDirty &&
      !window.confirm(
        "Replace this form with the fictional example description?",
      )
    )
      return;
    form.elements.title.value = MATCH_DEMO.title;
    form.elements.description.value = MATCH_DEMO.description;
    form.elements.source_url.value = "";
    state.matchDirty = true;
    return;
  } else if (state.comparison.job.source_type === "greenhouse") {
    await openLiveJob(
      state.comparison.job.live_job_id,
      otherComparisonMode(action),
    );
    showNotice(
      "Review the current cached posting before comparing. A new comparison uses your current profile records.",
      true,
    );
    return;
  } else {
    state.matchDraft = freshMatchDraft({
      ...state.comparison.job,
      mode: action === "compare-keyword" ? "keyword" : "semantic",
    });
    state.matchDirty = true;
  }
  renderShell();
  focusContent();
}
