"use strict";

/*
 * Final-sprint fix for the live multi-provider job loader.
 *
 * The multi-source /api/jobs request can legitimately take longer than the
 * generic 15-second request timeout because several public provider feeds are
 * fetched concurrently. This wrapper keeps the existing jobs.js untouched and
 * only raises the job-list request timeout to 45 seconds.
 *
 * It also preserves every filter currently supported by the tech-job search.
 */

async function loadJobs(filters = state.jobFilters) {
  const params = new URLSearchParams();

  const safeFilters = filters || {};

  if (safeFilters.q) params.set("q", safeFilters.q);
  if (safeFilters.location) params.set("location", safeFilters.location);
  if (safeFilters.board) params.set("board", safeFilters.board);
  if (safeFilters.work_mode) params.set("work_mode", safeFilters.work_mode);
  if (safeFilters.experience) params.set("experience", safeFilters.experience);
  if (safeFilters.tech) params.set("tech", safeFilters.tech);
  params.set("page", String(safeFilters.page || 1));

  const query = params.toString();

  // Public multi-provider job feeds can be slower than ordinary API calls.
  // 45 seconds is still bounded, while preventing a false timeout notice when
  // the backend ultimately returns a valid response.
  const data = await request(
    `/api/jobs${query ? `?${query}` : ""}`,
    { timeout: 45000 },
  );

  state.jobFilters = {
    q: "",
    location: "",
    board: "",
    work_mode: "",
    experience: "",
    tech: "",
    page: 1,
    ...(safeFilters || {}),
  };
  state.jobsData = data;
}
