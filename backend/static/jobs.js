"use strict";

// Live job state and request helpers are initialized by workspace.js.

function clearJobsState() {
  state.jobsData = null;
  state.jobFilters = { q: "", location: "", board: "", page: 1 };
  state.selectedJob = null;
  state.jobCompareDraft = null;
}

async function loadJobs(filters = state.jobFilters) {
  const params = new URLSearchParams();

  if (filters.q) params.set("q", filters.q);
  if (filters.location) params.set("location", filters.location);
  if (filters.board) params.set("board", filters.board);
  params.set("page", String(filters.page || 1));

  const query = params.toString();
  const data = await request(`/api/jobs${query ? `?${query}` : ""}`);

  state.jobFilters = { ...filters };
  state.jobsData = data;
}

function fetchDate(value) {
  return value ? escapeHtml(dateLabel(value)) : "Not available";
}

function boardMarkup(board) {
  const live =
    board.available && board.status === "live";

  return `
    <article class="panel job-board">
      <div class="button-row spread">
        <h2>${escapeHtml(board.employer)}</h2>
        <span class="badge ${live ? "green" : "amber"}">
          ${live ? "Live source" : "Unavailable"}
        </span>
      </div>

      <p class="small muted">
        ${board.listed_count} listed vacancies
        ${
          board.prospect_count
            ? ` · ${board.prospect_count} general-interest posts excluded`
            : ""
        }
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
          Refresh ${escapeHtml(board.employer)}
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

function jobsMarkup() {
  if (state.selectedJob) return jobDetailMarkup();

  const data = state.jobsData;
  const filter = state.jobFilters;

  if (!data) {
    return `
      <div class="empty-state">
        <div>
          <strong>Loading live jobs…</strong>
          <p>Fetching the current employer postings.</p>
        </div>
      </div>
    `;
  }

  const pages = Math.max(
    1,
    Math.ceil(data.total / data.page_size),
  );

  return `
    <div class="page-intro">
      <span class="eyebrow">Explore roles in the market</span>
      <h1>Live jobs</h1>
      <p class="muted">
        Browse current public postings directly from selected employer
        Greenhouse boards. Open a role to compare its requirements with your
        skills, evidence and assessment records.
      </p>
    </div>

    <div class="job-boards">
      ${data.boards.map(boardMarkup).join("")}
    </div>

    <div class="info-line">
      <span class="info-icon" aria-hidden="true">i</span>
      <p>
        Listings are retrieved directly from the employer's live Greenhouse
        board. They are not ranked by suitability. Always verify availability,
        experience requirements and location eligibility on the employer page.
      </p>
    </div>

    <section class="panel job-search">
      <form id="job-filter-form">
        <label>
          Keyword in title or description
          <input
            name="q"
            maxlength="100"
            value="${escapeHtml(filter.q)}"
            placeholder="Python, SQL, backend…"
          >
        </label>

        <label>
          Location contains
          <input
            name="location"
            maxlength="100"
            value="${escapeHtml(filter.location)}"
            placeholder="Bengaluru, APAC, Worldwide…"
          >
        </label>

        <label>
          Employer
          <select name="board">
            <option value="">All selected employers</option>
            ${data.boards
              .map(
                (board) => `
                  <option
                    value="${escapeHtml(board.board)}"
                    ${
                      filter.board === board.board
                        ? "selected"
                        : ""
                    }
                  >
                    ${escapeHtml(board.employer)}
                  </option>
                `,
              )
              .join("")}
          </select>
        </label>

        <button class="button primary" type="submit">
          Search live jobs
        </button>
      </form>
    </section>

    <div class="section-label">
      <h2>${data.total} matching listings</h2>
      <span class="small muted">
        Alphabetical · Not ranked by suitability
      </span>
    </div>

    ${
      data.jobs.length
        ? `
          <div class="job-list">
            ${data.jobs
              .map(
                (job) => `
                  <article class="panel job-card">
                    <div>
                      <span class="eyebrow">
                        ${escapeHtml(job.employer)}
                      </span>

                      <h3>${escapeHtml(job.title)}</h3>

                      <p class="muted">
                        ${escapeHtml(
                          job.location || "Location not supplied",
                        )}
                      </p>

                      <p class="small muted">
                        Retrieved: ${fetchDate(job.retrieved_at)}
                      </p>
                    </div>

                    <button
                      class="button secondary"
                      data-action="open-job"
                      data-board="${escapeHtml(job.board)}"
                      data-provider-id="${escapeHtml(job.provider_id)}"
                    >
                      View & compare
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
              <strong>
                ${
                  data.boards.some((board) => board.available)
                    ? "No live listings match these filters"
                    : "Live employer boards are unavailable"
                }
              </strong>

              <p>
                ${
                  data.boards.some((board) => board.available)
                    ? "Try a broader keyword or location."
                    : "The employer provider could not be reached. Check the error above and try again."
                }
              </p>

              <button
                class="text-button"
                data-action="matches"
              >
                Compare a pasted description →
              </button>
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

      <span class="small muted">
        Page ${data.page} of ${pages}
      </span>

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

  const semanticReady =
    state.matchMetadata?.semantic_model?.available === true;

  const mode =
    state.jobCompareDraft?.mode ||
    (semanticReady ? "semantic" : "keyword");

  return `
    <div class="page-intro">
      <button class="text-button" data-action="back-jobs">
        ← Back to live jobs
      </button>

      <p class="eyebrow">
        ${escapeHtml(job.employer)} · Greenhouse job board
      </p>

      <h1>${escapeHtml(job.title)}</h1>

      <p class="muted">
        ${escapeHtml(job.location || "Location not supplied")}
      </p>
    </div>

    <section class="panel job-detail-meta">
      <div class="button-row spread">
        <span class="badge green">
          Live posting
        </span>

        <a
          class="button secondary"
          href="${escapeHtml(job.source_url)}"
          target="_blank"
          rel="noopener noreferrer"
        >
          Open employer posting ↗
        </a>
      </div>

      <p class="small muted">
        Retrieved: ${fetchDate(job.retrieved_at)}
        <br>
        Provider updated:
        ${
          job.provider_updated_at
            ? fetchDate(job.provider_updated_at)
            : "Not supplied"
        }
      </p>

      ${
        board.last_error
          ? `<p class="error-text">
              Latest live board request reported:
              ${escapeHtml(board.last_error)}
            </p>`
          : ""
      }

      <p class="small muted">
        Availability and work-location eligibility must be checked on the
        employer page. This app does not submit an application.
      </p>
    </section>

    <section class="panel job-compare">
      <h2>Compare with my evidence</h2>

      <p class="muted">
        Compare this live posting with your current skill claims, active
        projects, certificates and assessment records. Evidence types remain
        separate and are preserved in the saved comparison snapshot.
      </p>

      <form id="job-compare-form">
        <label>
          Comparison method

          <select name="mode">
            <option
              value="semantic"
              ${mode === "semantic" ? "selected" : ""}
              ${semanticReady ? "" : "disabled"}
            >
              Keywords + semantic suggestions
            </option>

            <option
              value="keyword"
              ${mode === "keyword" ? "selected" : ""}
            >
              Keyword baseline
            </option>
          </select>
        </label>

        <button
          class="button primary"
          type="submit"
        >
          Compare with my evidence
        </button>
      </form>

      ${
        !semanticReady
          ? `<p class="small muted">
              The semantic model is not ready on this server. Keyword
              comparison is available.
            </p>`
          : ""
      }
    </section>

    <section class="panel job-description">
      <h2>Job description</h2>

      <pre class="match-source-text">${escapeHtml(
        job.description,
      )}</pre>

      <p class="section-note">
        Source: ${escapeHtml(job.employer)} via Greenhouse.
        Retrieved ${fetchDate(job.retrieved_at)}.
        Content hash:
        <code>${escapeHtml(job.content_hash || "not supplied")}</code>
      </p>
    </section>
  `;
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

async function openLiveJob(board, providerId, mode) {
  const selected = await request(
    `/api/jobs/${encodeURIComponent(board)}/${encodeURIComponent(
      providerId,
    )}`,
  );

  await loadMatches();

  state.selectedJob = selected;

  state.jobCompareDraft = {
    submission_id: crypto.randomUUID(),
    mode:
      mode ||
      (state.matchMetadata?.semantic_model?.available
        ? "semantic"
        : "keyword"),
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

  const button = document.querySelector(
    '#job-compare-form [type="submit"]',
  );

  if (button) {
    button.textContent = "Comparing…";
  }

  try {
    const job = state.selectedJob.job;

    const data = await request(
      `/api/jobs/${encodeURIComponent(job.board)}/${encodeURIComponent(
        job.provider_id,
      )}/compare`,
      {
        method: "POST",
        body: {
          submission_id:
            state.jobCompareDraft.submission_id,
          mode: state.jobCompareDraft.mode,
        },
        timeout: 45000,
      },
    );

    state.comparison = data.comparison;

    state.matchHistory = [
      data.comparison,
      ...state.matchHistory.filter(
        (item) => item.id !== data.comparison.id,
      ),
    ].slice(0, 30);

    clearMatchDraft();
    state.jobCompareDraft = null;
    state.selectedJob = null;
    state.view = "matches";

    renderShell();
    focusContent();

    showNotice(
      "Comparison saved with the live posting and your evidence snapshot.",
      true,
    );
  } finally {
    if (button?.isConnected) {
      button.textContent = "Compare with my evidence";
    }
  }
}

async function handleJobsAction(action, button) {
  if (action === "open-job") {
    await openLiveJob(
      button.dataset.board,
      button.dataset.providerId,
    );
    return;
  }

  if (action === "back-jobs") {
    state.selectedJob = null;
    state.jobCompareDraft = null;
    state.view = "jobs";

    if (!state.jobsData) {
      await loadJobs(state.jobFilters);
    }

    renderShell();
    focusContent();
    return;
  }

  if (action === "refresh-board") {
    const label = button.textContent;

    button.textContent = "Fetching live postings…";

    try {
      await loadJobs({
        ...state.jobFilters,
        page: 1,
      });
    } finally {
      if (button.isConnected) {
        button.textContent = label;
      }
    }

    state.selectedJob = null;
    state.jobCompareDraft = null;
    state.view = "jobs";

    renderShell();
    focusContent();

    showNotice(
      "Live employer postings refreshed.",
      true,
    );

    return;
  }

  if (action === "jobs-page") {
    const page = Number(button.dataset.page);

    await loadJobs({
      ...state.jobFilters,
      page,
    });

    state.selectedJob = null;
    state.jobCompareDraft = null;
    state.view = "jobs";

    renderShell();
    focusContent();
  }
}

function comparisonSourceLabel(job) {
  if (job.source_type !== "greenhouse") {
    return "Source: candidate-pasted text. Vacancy availability has not been checked.";
  }

  const employer = job.employer
    ? escapeHtml(job.employer)
    : "Greenhouse";

  const location = job.location
    ? escapeHtml(job.location)
    : "Location not supplied";

  const captured = job.source_captured_at
    ? fetchDate(job.source_captured_at)
    : "capture time unavailable";

  return `Source: ${employer} via Greenhouse · ${location}. Live posting snapshot captured ${captured}. The saved comparison remains unchanged for research reproducibility.`;
}