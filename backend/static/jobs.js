"use strict";

// Shared state and request helpers are initialized by workspace.js before use.
function clearJobsState() {
  state.jobsData = null;
  state.jobFilters = { q: "", location: "", board: "", page: 1 };
  state.selectedJob = null;
  state.jobCompareDraft = null;
}

async function loadJobs(filters = state.jobFilters) {
  const data = await request(`/api/jobs?${new URLSearchParams(filters)}`);
  state.jobFilters = { ...filters };
  state.jobsData = data;
}

function fetchDate(value) {
  return value ? escapeHtml(dateLabel(value)) : "Not fetched yet";
}

function boardMarkup(board) {
  return `<article class="panel job-board"><div class="button-row spread"><h2>${escapeHtml(board.employer)}</h2><span class="badge ${board.last_error || board.stale ? "amber" : "neutral"}">${board.last_error ? "Refresh failed" : !board.last_success_at ? "Ready to fetch" : board.stale ? "Cache over 24h old" : "Cached listings"}</span></div><p class="small muted">Last successful fetch: ${fetchDate(board.last_success_at)}<br>${board.listed_count} listed vacancies${board.prospect_count ? ` · ${board.prospect_count} general-interest posts excluded` : ""}</p>${board.last_error ? `<p class="error-text">${escapeHtml(board.last_error)}</p><p class="small muted">Last attempt: ${fetchDate(board.last_attempt_at)}</p>` : ""}<div class="button-row"><button class="button secondary" data-action="refresh-board" data-board="${escapeHtml(board.board)}">Refresh ${escapeHtml(board.employer)}</button><a class="text-button" href="${escapeHtml(board.source_url)}" target="_blank" rel="noopener noreferrer">Employer board ↗</a></div>${!board.can_refresh ? `<p class="section-note">Next provider refresh available after ${fetchDate(board.next_refresh_at)}.</p>` : ""}</article>`;
}

function jobsMarkup() {
  if (state.selectedJob) return jobDetailMarkup();
  const data = state.jobsData;
  const filter = state.jobFilters;
  const pages = Math.max(1, Math.ceil(data.total / data.page_size));
  return `<div class="page-intro"><span class="eyebrow">Explore roles in the market</span><h1>Live jobs</h1><p class="muted">Browse public postings from selected employers. Open a role to compare its requirements with your skills, evidence and assessment records.</p></div>
    <div class="job-boards">${data.boards.map(boardMarkup).join("")}</div>
    <div class="info-line"><span class="info-icon" aria-hidden="true">i</span><p>This is a small employer sample. Listings reflect the last successful fetch. Check the employer page for availability, experience requirements and location eligibility; remote does not always mean worldwide.</p></div>
    <section class="panel job-search"><form id="job-filter-form"><label>Keyword in title or description<input name="q" maxlength="100" value="${escapeHtml(filter.q)}" placeholder="Python, SQL, backend…"></label><label>Location contains<input name="location" maxlength="100" value="${escapeHtml(filter.location)}" placeholder="Bengaluru, APAC, Worldwide…"></label><label>Employer<select name="board"><option value="">All selected employers</option>${data.boards.map((board) => `<option value="${escapeHtml(board.board)}" ${filter.board === board.board ? "selected" : ""}>${escapeHtml(board.employer)}</option>`).join("")}</select></label><button class="button primary" type="submit">Search cached jobs</button></form></section>
    <div class="section-label"><h2>${data.total} matching listings</h2><span class="small muted">Alphabetical · Not ranked by suitability</span></div>
    ${data.jobs.length ? `<div class="job-list">${data.jobs.map((job) => `<article class="panel job-card"><div><span class="eyebrow">${escapeHtml(job.employer)}</span><h3>${escapeHtml(job.title)}</h3><p class="muted">${escapeHtml(job.location || "Location not supplied")}</p><p class="small muted">Last seen: ${fetchDate(job.last_seen_at)}${job.stale ? " · Cache over 24h old" : ""}</p></div><button class="button secondary" data-action="open-job" data-id="${escapeHtml(job.id)}">View & compare</button></article>`).join("")}</div>` : `<div class="empty-state"><div><strong>${data.boards.some((board) => board.last_success_at) ? "No listings match these filters" : "Fetch an employer board to get started"}</strong><p>${data.boards.some((board) => board.last_success_at) ? "Try a broader keyword or location. New listings appear after a successful refresh." : "Use a Refresh button above. Your cached results will remain available if the provider is temporarily unreachable."}</p><button class="text-button" data-action="matches">Compare a pasted description →</button></div></div>`}
    <div class="button-row jobs-pagination"><button class="button secondary" data-action="jobs-page" data-page="${Math.max(1, data.page - 1)}" ${data.page <= 1 ? "disabled" : ""}>Previous page</button><span class="small muted">Page ${data.page} of ${pages}</span><button class="button secondary" data-action="jobs-page" data-page="${data.page + 1}" ${data.page >= pages ? "disabled" : ""}>Next page</button></div>`;
}

function jobDetailMarkup() {
  const { job, board } = state.selectedJob;
  const ready = state.matchMetadata.semantic_model.available;
  const mode = state.jobCompareDraft.mode;
  return `<div class="page-intro"><button class="text-button" data-action="back-jobs">← Back to live jobs</button><p class="eyebrow">${escapeHtml(job.employer)} · Greenhouse job board</p><h1>${escapeHtml(job.title)}</h1><p class="muted">${escapeHtml(job.location || "Location not supplied")}</p></div>
    <section class="panel job-detail-meta"><div class="button-row spread"><span class="badge ${!job.listed || job.stale ? "amber" : "neutral"}">${!job.listed ? "No longer listed on this board" : job.stale ? "Cached posting · Over 24h old" : "Listed at last fetch"}</span><a class="button secondary" href="${escapeHtml(job.source_url)}" target="_blank" rel="noopener noreferrer">Open employer posting ↗</a></div><p class="small muted">Last seen: ${fetchDate(job.last_seen_at)}<br>Last board check: ${fetchDate(job.last_checked_at)}<br>Provider updated: ${job.provider_updated_at ? fetchDate(job.provider_updated_at) : "Not supplied"} (not the publication date)</p>${board.last_error ? `<p class="error-text">Latest refresh failed. The text below is the saved posting from the last successful fetch.</p>` : ""}<p class="small muted">Availability and work-location eligibility must be checked on the employer page. This app does not submit an application.</p></section>
    <section class="panel job-compare"><h2>Compare with my evidence</h2><p class="muted">Save this posting’s full text with your current skill claims, active projects, certificates and latest diagnostics for each supported skill. Unverified evidence stays labelled as a claim.</p><form id="job-compare-form"><label>Comparison method<select name="mode"><option value="semantic" ${mode === "semantic" ? "selected" : ""} ${ready ? "" : "disabled"}>Keywords + semantic suggestions</option><option value="keyword" ${mode === "keyword" ? "selected" : ""}>Keyword baseline</option></select></label><button class="button primary" type="submit" ${job.listed ? "" : "disabled"}>Compare with my evidence</button></form>${!ready ? '<p class="small muted">The semantic model is not ready on this server. Keyword comparison is available.</p>' : ""}${!job.listed ? '<p class="small muted">New comparisons are disabled for this removed posting. Earlier saved comparisons remain available.</p>' : ""}</section>
    <section class="panel job-description"><h2>Job description</h2><pre class="match-source-text">${escapeHtml(job.description)}</pre><p class="section-note">Source: ${escapeHtml(job.employer)} via Greenhouse. Formatting has been converted to plain text. Posting version ${job.version}.</p></section>`;
}

async function submitJobFilters(values) {
  await loadJobs({
    q: values.get("q").trim(),
    location: values.get("location").trim(),
    board: values.get("board"),
    page: 1,
  });
  renderShell();
  focusContent();
}

function otherComparisonMode(action) {
  return action === "compare-keyword" ? "keyword" : "semantic";
}

async function openLiveJob(id, mode) {
  const selected = await request(`/api/jobs/${id}`);
  await loadMatches();
  state.selectedJob = selected;
  state.jobCompareDraft = {
    submission_id: crypto.randomUUID(),
    job_version: selected.job.version,
    mode:
      mode ||
      (state.matchMetadata.semantic_model.available ? "semantic" : "keyword"),
  };
  clearMatchDraft();
  state.view = "jobs";
  renderShell();
  focusContent();
}

async function submitLiveComparison(values) {
  const mode = values.get("mode");
  // Preserve the retry key for an interrupted response; changed input gets a new key.
  if (state.jobCompareDraft.mode !== mode)
    state.jobCompareDraft.submission_id = crypto.randomUUID();
  state.jobCompareDraft.mode = mode;
  const button = document.querySelector('#job-compare-form [type="submit"]');
  button.textContent = "Comparing…";
  try {
    const data = await request(
      `/api/jobs/${state.selectedJob.job.id}/compare`,
      {
        method: "POST",
        body: { ...state.jobCompareDraft },
        timeout: 45000,
      },
    );
    state.comparison = data.comparison;
    state.matchHistory = [
      data.comparison,
      ...state.matchHistory.filter((item) => item.id !== data.comparison.id),
    ].slice(0, 30);
    clearMatchDraft();
    state.jobCompareDraft = null;
    state.selectedJob = null;
    state.view = "matches";
    renderShell();
    focusContent();
    showNotice(
      "Comparison saved with the posting version and your evidence snapshot.",
      true,
    );
  } finally {
    if (button.isConnected) button.textContent = "Compare with my evidence";
  }
}

async function handleJobsAction(action, button) {
  if (action === "open-job") {
    await openLiveJob(button.dataset.id);
    return;
  }
  let refresh;
  if (action === "refresh-board") {
    const label = button.textContent;
    button.textContent = "Fetching postings…";
    try {
      refresh = await request(
        `/api/jobs/boards/${button.dataset.board}/refresh`,
        { method: "POST", body: {}, timeout: 45000 },
      );
    } finally {
      if (button.isConnected) button.textContent = label;
    }
  }
  const page =
    action === "jobs-page"
      ? Number(button.dataset.page)
      : action === "refresh-board"
        ? 1
        : state.jobFilters.page;
  await loadJobs({ ...state.jobFilters, page });
  state.selectedJob = null;
  state.jobCompareDraft = null;
  state.evidenceEditor = null;
  state.evidenceDirty = false;
  clearMatchDraft();
  state.view = "jobs";
  renderShell();
  focusContent();
  if (refresh)
    showNotice(
      refresh.outcome === "failed"
        ? refresh.board.last_error
        : refresh.outcome === "cooldown"
          ? "Using the cache. Each board can be fetched once every five minutes; see its next refresh time."
          : `${refresh.board.employer}: ${refresh.board.listed_count} listed vacancies fetched.`,
      refresh.outcome !== "failed",
    );
}

function comparisonSourceLabel(job) {
  if (job.source_type !== "greenhouse")
    return "Source: candidate-pasted text. Vacancy availability has not been checked.";
  return `Source: ${escapeHtml(job.employer)} via Greenhouse · ${escapeHtml(job.location)}. Posting version ${job.posting_version}. Last seen ${fetchDate(job.last_seen_at)}${job.stale_at_comparison ? " (cache over 24h old when compared)" : ""}. This saved snapshot is not a new availability check.`;
}
