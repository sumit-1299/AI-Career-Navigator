"use strict";

// Live job state and request helpers are initialized by workspace.js.

function isLiveJobSource(job) {
  return ["greenhouse", "ashby", "lever"].includes(
    String(job?.source_type || job?.provider || "").toLowerCase(),
  );
}

window.isLiveJobSource = isLiveJobSource;

function clearJobsState() {
  state.jobsData = null;
  state.jobFilters = {
    q: "",
    location: "",
    board: "",
    work_mode: "",
    experience: "",
    tech: "",
    page: 1,
  };
  state.selectedJob = null;
  state.jobCompareDraft = null;
}

async function loadJobs(filters = state.jobFilters) {
  const params = new URLSearchParams();

  for (const key of [
    "q",
    "location",
    "board",
    "work_mode",
    "experience",
    "tech",
  ]) {
    if (filters[key]) params.set(key, filters[key]);
  }

  params.set("page", String(filters.page || 1));

  const query = params.toString();
  const data = await request(`/api/jobs${query ? `?${query}` : ""}`);

  state.jobFilters = { ...filters };
  state.jobsData = data;
}

function fetchDate(value) {
  return value ? escapeHtml(dateLabel(value)) : "Not available";
}

function jobTagsMarkup(tags = []) {
  if (!tags.length) return "";
  return `<div class="job-tech-tags" aria-label="Technology tags">${tags
    .slice(0, 6)
    .map((tag) => `<span>${escapeHtml(tag)}</span>`)
    .join("")}</div>`;
}

function boardMarkup(board) {
  const live = board.available && board.status === "live";

  return `
    <article class="panel job-board">
      <div class="button-row spread">
        <div>
          <span class="eyebrow">LIVE SOURCE</span>
          <h2>${escapeHtml(board.employer)}</h2>
        </div>
        <span class="badge ${live ? "green" : "amber"}">
          ${live ? "Live" : "Unavailable"}
        </span>
      </div>

      <p class="small muted">
        ${Number(board.tech_count || 0)} technology roles in scope
        · ${Number(board.listed_count || 0)} total provider listings
        <br>
        Retrieved: ${fetchDate(board.retrieved_at)}
      </p>

      ${
        board.last_error
          ? `<p class="error-text">${escapeHtml(board.last_error)}</p>`
          : ""
      }

      <div class="button-row">
        <button
          class="button secondary"
          data-action="refresh-board"
          data-board="${escapeHtml(board.board)}"
        >
          Refresh live source
        </button>
        <a
          class="text-button"
          href="${escapeHtml(board.source_url)}"
          target="_blank"
          rel="noopener noreferrer"
        >
          Employer board ↗
        </a>
      </div>
    </article>
  `;
}

function jobSearchFacetOptions(values, selected, placeholder) {
  return [
    `<option value="">${placeholder}</option>`,
    ...values.map(
      (value) =>
        `<option value="${escapeHtml(value)}" ${
          selected === value ? "selected" : ""
        }>${escapeHtml(value)}</option>`,
    ),
  ].join("");
}

function jobsMarkup() {
  if (state.selectedJob) return jobDetailMarkup();

  const data = state.jobsData;
  const filter = state.jobFilters;

  if (!data) {
    return `
      <div class="empty-state">
        <div>
          <strong>Loading technology jobs…</strong>
          <p>Fetching current public employer postings.</p>
        </div>
      </div>
    `;
  }

  const pages = Math.max(1, Math.ceil(data.total / data.page_size));
  const filters = data.filters || {};

  return `
    <div class="page-intro">
      <span class="eyebrow">FIND YOUR NEXT TECH ROLE</span>
      <h1>Tech job search</h1>
      <p class="muted">
        Search current technology-focused vacancies by role, location,
        work mode, experience level and technology. Search relevance helps
        find roles; it is not candidate suitability or a hiring prediction.
      </p>
    </div>

    <section class="job-search-journey">
      <div><span>01</span><strong>Search</strong><small>Find relevant technical roles</small></div>
      <div><span>02</span><strong>Align</strong><small>Compare the role with your evidence</small></div>
      <div><span>03</span><strong>Prepare</strong><small>Close the most useful evidence gaps</small></div>
      <div><span>04</span><strong>Apply</strong><small>Apply on the employer site</small></div>
    </section>

    <div class="job-boards">
      ${(data.boards || []).map(boardMarkup).join("")}
    </div>

    <section class="panel job-search job-search-enhanced">
      <div class="section-label">
        <div>
          <span class="eyebrow">SEARCH & FILTER</span>
          <h2>Find a technical opportunity</h2>
        </div>
        <span class="badge neutral">Tech roles only</span>
      </div>

      <form id="job-filter-form">
        <label>
          Role or technology
          <input
            name="q"
            maxlength="100"
            value="${escapeHtml(filter.q)}"
            placeholder="Python backend, data engineer, React…"
          >
        </label>

        <label>
          Location
          <input
            name="location"
            list="job-location-options"
            maxlength="100"
            value="${escapeHtml(filter.location)}"
            placeholder="Pune, Bengaluru, Remote…"
          >
          <datalist id="job-location-options">
            ${(filters.locations || [])
              .map((location) => `<option value="${escapeHtml(location)}"></option>`)
              .join("")}
          </datalist>
        </label>

        <label>
          Technology
          <select name="tech">
            ${jobSearchFacetOptions(
              filters.technologies || [],
              filter.tech,
              "Any technology",
            )}
          </select>
        </label>

        <label>
          Work mode
          <select name="work_mode">
            ${jobSearchFacetOptions(
              filters.work_modes || [],
              filter.work_mode,
              "Any work mode",
            )}
          </select>
        </label>

        <label>
          Experience
          <select name="experience">
            ${jobSearchFacetOptions(
              filters.experience_levels || [],
              filter.experience,
              "Any experience level",
            )}
          </select>
        </label>

        <label>
          Employer
          <select name="board">
            <option value="">All live tech sources</option>
            ${(data.boards || [])
              .map(
                (board) =>
                  `<option value="${escapeHtml(board.board)}" ${
                    filter.board === board.board ? "selected" : ""
                  }>${escapeHtml(board.employer)}</option>`,
              )
              .join("")}
          </select>
        </label>

        <div class="job-search-actions">
          <button class="button primary" type="submit">
            Search tech jobs
          </button>
          <button class="text-button" type="submit" name="clear" value="1">
            Clear filters
          </button>
        </div>
      </form>
    </section>

    <div class="section-label">
      <div>
        <span class="eyebrow">SEARCH RESULTS</span>
        <h2>${Number(data.total).toLocaleString()} matching tech roles</h2>
      </div>
      <span class="small muted">
        ${data.search_scope_note || "Technology-focused vacancies only."}
      </span>
    </div>

    ${
      data.jobs.length
        ? `
          <div class="job-list">
            ${data.jobs
              .map(
                (job) => `
                  <article class="panel job-card job-card-enhanced">
                    <div class="job-card-main">
                      <div class="button-row spread job-card-heading">
                        <span class="eyebrow">${escapeHtml(job.employer)}</span>
                        <span class="badge neutral">${escapeHtml(job.experience_level || "Tech role")}</span>
                      </div>

                      <h3>${escapeHtml(job.title)}</h3>

                      <div class="job-card-meta">
                        <span>⌖ ${escapeHtml(job.location || "Location not supplied")}</span>
                        <span>◌ ${escapeHtml(job.work_mode || "Work mode not specified")}</span>
                      </div>

                      ${jobTagsMarkup(job.tech_tags)}

                      <p class="small muted">
                        Live retrieval: ${fetchDate(job.retrieved_at)}
                      </p>
                    </div>

                    <button
                      class="button secondary job-view-button"
                      data-action="open-job"
                      data-board="${escapeHtml(job.board)}"
                      data-provider-id="${escapeHtml(job.provider_id)}"
                    >
                      View role & align →
                    </button>
                  </article>
                `,
              )
              .join("")}
          </div>
        `
        : `
          <div class="empty-state">
            <div>
              <strong>No technology roles match these filters</strong>
              <p>
                Try a broader technology, location or experience filter.
                The search intentionally excludes obvious nontechnical job families.
              </p>
            </div>
          </div>
        `
    }

    <div class="button-row jobs-pagination">
      <button
        class="button secondary"
        data-action="jobs-page"
        data-page="${Math.max(1, data.page - 1)}"
        ${data.page <= 1 ? "disabled" : ""}
      >
        Previous page
      </button>
      <span class="small muted">Page ${data.page} of ${pages}</span>
      <button
        class="button secondary"
        data-action="jobs-page"
        data-page="${data.page + 1}"
        ${data.page >= pages ? "disabled" : ""}
      >
        Next page
      </button>
    </div>
  `;
}

function jobDetailMarkup() {
  const { job, board } = state.selectedJob;
  const semanticReady = state.matchMetadata?.semantic_model?.available === true;
  const mode =
    state.jobCompareDraft?.mode ||
    (semanticReady ? "semantic" : "keyword");

  return `
    <div class="page-intro">
      <button class="text-button" data-action="back-jobs">
        ← Back to tech job search
      </button>
      <p class="eyebrow">
        ${escapeHtml(job.employer)} · Live technology opportunity
      </p>
      <h1>${escapeHtml(job.title)}</h1>
      <p class="muted">
        ${escapeHtml(job.location || "Location not supplied")}
      </p>
      ${jobTagsMarkup(job.tech_tags)}
    </div>

    <section class="panel job-detail-meta job-detail-hero">
      <div class="job-detail-facts">
        <span><strong>Work mode</strong>${escapeHtml(job.work_mode || "Not specified")}</span>
        <span><strong>Experience</strong>${escapeHtml(job.experience_level || "Not specified")}</span>
        <span><strong>Source</strong>${escapeHtml(job.provider_label || "Live employer feed")}</span>
        <span><strong>Retrieved</strong>${fetchDate(job.retrieved_at)}</span>
      </div>

      <div class="button-row job-detail-actions">
        <a
          class="button primary"
          href="${escapeHtml(job.source_url)}"
          target="_blank"
          rel="noopener noreferrer"
        >
          View & apply on employer site ↗
        </a>
        <span class="badge green">Live posting</span>
      </div>

      <p class="small muted">
        Verify the employer's current availability, work-location eligibility,
        qualification requirements and application rules on the employer site.
        This app does not submit applications.
      </p>
    </section>

    <section class="panel job-compare">
      <div class="section-label">
        <div>
          <span class="eyebrow">NEXT STEP</span>
          <h2>Align this role with my evidence</h2>
        </div>
        <span class="badge neutral">Job → evidence → action</span>
      </div>

      <p class="muted">
        The comparison keeps your resume mentions, self-ratings,
        projects/certificates and diagnostic results separate. It identifies
        where evidence is strong, where practice may be useful and where we
        simply need more evidence.
      </p>

      <form id="job-compare-form">
        <label>
          Comparison method
          <select name="mode">
            <option value="semantic" ${mode === "semantic" ? "selected" : ""} ${semanticReady ? "" : "disabled"}>
              Keywords + semantic suggestions
            </option>
            <option value="keyword" ${mode === "keyword" ? "selected" : ""}>
              Keyword baseline
            </option>
          </select>
        </label>

        <button class="button primary" type="submit">
          Compare with my evidence
        </button>
      </form>

      ${
        semanticReady
          ? `<p class="small muted">Semantic suggestions use the local pinned MiniLM model. They are research signals and remain reviewable.</p>`
          : `<p class="small muted">Semantic mode is not ready on this server. Keyword baseline remains available.</p>`
      }
    </section>

    <section class="panel job-description">
      <div class="section-label">
        <h2>What the employer says</h2>
        <span class="small muted">Current live description</span>
      </div>
      <pre class="match-source-text">${escapeHtml(job.description)}</pre>
      <p class="section-note">
        Source: ${escapeHtml(job.employer)} via ${escapeHtml(job.provider_label || "live employer feed")} ·
        provider updated ${job.provider_updated_at ? fetchDate(job.provider_updated_at) : "not supplied"} ·
        content hash ${escapeHtml(job.content_hash || "not supplied")}
      </p>
    </section>
  `;
}

async function submitJobFilters(values) {
  if (values.get("clear") === "1") {
    await loadJobs({
      q: "",
      location: "",
      board: "",
      work_mode: "",
      experience: "",
      tech: "",
      page: 1,
    });
    state.selectedJob = null;
    state.jobCompareDraft = null;
    state.view = "jobs";
    renderShell();
    focusContent();
    return;
  }

  await loadJobs({
    q: values.get("q").trim(),
    location: values.get("location").trim(),
    board: values.get("board"),
    work_mode: values.get("work_mode"),
    experience: values.get("experience"),
    tech: values.get("tech"),
    page: 1,
  });

  state.selectedJob = null;
  state.jobCompareDraft = null;
  state.view = "jobs";
  renderShell();
  focusContent();
}

async function openLiveJob(board, providerId, mode) {
  const selected = await request(
    `/api/jobs/${encodeURIComponent(board)}/${encodeURIComponent(providerId)}`,
  );

  await loadMatches();

  state.selectedJob = selected;
  state.jobCompareDraft = {
    submission_id: crypto.randomUUID(),
    mode:
      mode ||
      (state.matchMetadata?.semantic_model?.available ? "semantic" : "keyword"),
  };

  clearMatchDraft();
  state.view = "jobs";
  renderShell();
  focusContent();
}

async function submitLiveComparison(values) {
  const mode = values.get("mode");

  if (!state.jobCompareDraft) {
    state.jobCompareDraft = {
      submission_id: crypto.randomUUID(),
      mode,
    };
  }

  if (state.jobCompareDraft.mode !== mode) {
    state.jobCompareDraft.submission_id = crypto.randomUUID();
  }

  state.jobCompareDraft.mode = mode;

  const button = document.querySelector('#job-compare-form [type="submit"]');
  if (button) button.textContent = "Comparing…";

  try {
    const job = state.selectedJob.job;
    const data = await request(
      `/api/jobs/${encodeURIComponent(job.board)}/${encodeURIComponent(job.provider_id)}/compare`,
      {
        method: "POST",
        body: {
          submission_id: state.jobCompareDraft.submission_id,
          mode: state.jobCompareDraft.mode,
        },
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
      "Live tech role saved as an immutable comparison snapshot.",
      true,
    );
  } finally {
    if (button?.isConnected) button.textContent = "Compare with my evidence";
  }
}

async function handleJobsAction(action, button) {
  if (action === "jobs") {
    state.selectedJob = null;
    state.jobCompareDraft = null;
    state.view = "jobs";
    await loadJobs(state.jobFilters);
    renderShell();
    focusContent();
    return;
  }

  if (action === "open-job") {
    await openLiveJob(button.dataset.board, button.dataset.providerId);
    return;
  }

  if (action === "back-jobs") {
    state.selectedJob = null;
    state.jobCompareDraft = null;
    state.view = "jobs";
    if (!state.jobsData) await loadJobs(state.jobFilters);
    renderShell();
    focusContent();
    return;
  }


  if (action === "refresh-board") {
    const label = button.textContent;
    button.textContent = "Fetching live postings…";
    try {
      await loadJobs({ ...state.jobFilters, board: "", page: 1 });
    } finally {
      if (button.isConnected) button.textContent = label;
    }
    state.selectedJob = null;
    state.jobCompareDraft = null;
    state.view = "jobs";
    renderShell();
    focusContent();
    showNotice("Live technology postings refreshed.", true);
    return;
  }

  if (action === "jobs-page") {
    const page = Number(button.dataset.page);
    await loadJobs({ ...state.jobFilters, page });
    state.selectedJob = null;
    state.jobCompareDraft = null;
    state.view = "jobs";
    renderShell();
    focusContent();
  }
}

function comparisonSourceLabel(job) {
  if (!isLiveJobSource(job)) {
    return "Source: candidate-pasted text. Vacancy availability has not been checked.";
  }

  const employer = job.employer ? escapeHtml(job.employer) : "Employer";
  const provider = job.provider_label ? escapeHtml(job.provider_label) : "live employer feed";
  const location = job.location ? escapeHtml(job.location) : "Location not supplied";
  const captured = job.source_captured_at
    ? fetchDate(job.source_captured_at)
    : "capture time unavailable";

  return `Source: ${employer} via ${provider} · ${location}. Live posting snapshot captured ${captured}. The saved comparison remains unchanged for research reproducibility.`;
}
