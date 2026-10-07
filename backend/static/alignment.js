"use strict";

// The legacy matcher referenced this helper without defining it. Keep the
// comparison-mode toggle explicit so the Job Alignment actions are reliable.
function otherComparisonMode(action) {
  return action === "compare-semantic" ? "semantic" : "keyword";
}

/*
 * Enhanced Job Alignment presentation layer.
 *
 * The existing backend already returns explainable evidence records:
 * resume mentions, self-ratings, projects/certificates, diagnostics,
 * job importance, semantic suggestions and manual-review passages.
 *
 * This file turns those records into a visual, action-oriented alignment
 * dashboard without inventing a hiring probability or proficiency score.
 */

function alignmentPercent(numerator, denominator) {
  if (!denominator) return 0;
  return Math.round((numerator / denominator) * 100);
}

function alignmentImportance(row) {
  const sources = row.job_sources || [];
  if (sources.some((source) => source.importance === "required")) {
    return {
      key: "required",
      label: "Required",
      weight: 3,
    };
  }
  if (sources.some((source) => source.importance === "optional")) {
    return {
      key: "optional",
      label: "Preferred",
      weight: 1,
    };
  }
  return {
    key: "mentioned",
    label: "Mentioned",
    weight: 2,
  };
}

function alignmentAssessment(row) {
  return row.assessment?.result || null;
}

function alignmentStatus(row) {
  const assessment = alignmentAssessment(row);
  const importance = alignmentImportance(row);
  const hasResume = Boolean(row.resume_mentions?.length);
  const hasClaims = Boolean(row.candidate_claims?.length);
  const answered = Boolean(assessment?.answered_count);
  const incorrect = Number(assessment?.incorrect_count || 0);
  const unanswered = Number(assessment?.unanswered_count || 0);

  if (incorrect > 0) {
    return {
      key: "practice",
      label: "Practice recommended",
      detail: `${incorrect} diagnostic answer${incorrect === 1 ? "" : "s"} marked incorrect.`,
      tone: "attention",
      priority: 100 + importance.weight,
      action: "open-assessment",
    };
  }

  if (assessment && unanswered > 0) {
    return {
      key: "collect",
      label: "More evidence needed",
      detail: `${unanswered} question${unanswered === 1 ? "" : "s"} remain unassessed.`,
      tone: "warning",
      priority: 80 + importance.weight,
      action: "open-assessment",
    };
  }

  if (!assessment && (hasResume || hasClaims)) {
    return {
      key: "assess",
      label: "Assess next",
      detail: "A candidate record exists, but a diagnostic is not available yet.",
      tone: "brand",
      priority: 60 + importance.weight,
      action: "open-assessment",
    };
  }

  if (!hasResume && !hasClaims && !answered) {
    return {
      key: "support",
      label: "Collect evidence",
      detail: "No candidate record is attached to this named job skill.",
      tone: "warning",
      priority: 40 + importance.weight,
      action: "evidence",
    };
  }

  if (assessment && answered) {
    return {
      key: "observed",
      label: "Diagnostic evidence",
      detail: "This status reflects the saved diagnostic attempt only.",
      tone: "positive",
      priority: 0,
      action: "open-assessment",
    };
  }

  return {
    key: "recorded",
    label: "Recorded evidence",
    detail: "Supporting candidate evidence is present for this skill.",
    tone: "positive",
    priority: 0,
    action: "none",
  };
}

function alignmentEvidenceCounts(row) {
  const claims = row.candidate_claims || [];
  const assessment = alignmentAssessment(row);
  return {
    resume: row.resume_mentions?.length || 0,
    rating: claims.filter((claim) => claim.kind === "self_report").length,
    work: claims.filter((claim) => claim.kind !== "self_report").length,
    answered: Number(assessment?.answered_count || 0),
  };
}

function alignmentSkillAction(row, compact = false) {
  const status = alignmentStatus(row);
  const supported = state.assessmentCatalog.some(
    (item) => item.skill_key === row.skill_key,
  );

  if (status.action === "open-assessment" && row.assessment?.attempt_id) {
    return `<button class="text-button" data-action="open-attempt" data-id="${escapeHtml(row.assessment.attempt_id)}">Open result →</button>`;
  }

  if (status.action === "open-assessment" && supported) {
    return `<button class="text-button" data-action="start" data-skill="${escapeHtml(row.skill_key)}">Assess ${escapeHtml(row.label)} →</button>`;
  }

  if (status.action === "evidence" && !compact) {
    return `<button class="text-button" data-action="evidence">Add supporting evidence →</button>`;
  }

  return "";
}

function alignmentSkillRows(saved) {
  const rows = saved.result.skills || [];

  return rows
    .map((row) => {
      const importance = alignmentImportance(row);
      const status = alignmentStatus(row);
      const counts = alignmentEvidenceCounts(row);
      const semantic = row.mapping === "semantic_suggestion";
      const score = semantic
        ? row.job_sources
            .filter((source) => source.method === "semantic_suggestion")
            .reduce(
              (best, source) => Math.max(best, Number(source.similarity || 0)),
              0,
            )
        : 0;

      return {
        row,
        importance,
        status,
        counts,
        semantic,
        semanticScore: score,
      };
    })
    .sort((a, b) => {
      if (b.status.priority !== a.status.priority) {
        return b.status.priority - a.status.priority;
      }
      if (b.importance.weight !== a.importance.weight) {
        return b.importance.weight - a.importance.weight;
      }
      return a.row.label.localeCompare(b.row.label);
    });
}

function alignmentCoverage(saved) {
  const alignment = saved.result.alignment || {};
  const rows = saved.result.skills || [];
  const named = Number(alignment.named_skills || rows.filter((row) => row.mapping === "keyword").length);
  const resume = Number(alignment.with_resume_mentions || 0);
  const ratings = Number(alignment.with_self_ratings || 0);
  const work = Number(alignment.with_project_or_certificate || 0);
  const diagnostics = Number(alignment.with_answered_diagnostic || 0);
  const anySupport = rows.filter((row) => {
    const assessment = alignmentAssessment(row);
    return Boolean(
      row.resume_mentions?.length ||
      row.candidate_claims?.length ||
      assessment?.answered_count,
    );
  }).length;

  return {
    named,
    resume,
    ratings,
    work,
    diagnostics,
    anySupport,
    resumePercent: alignmentPercent(resume, named),
    evidencePercent: alignmentPercent(anySupport, named),
    diagnosticsPercent: alignmentPercent(diagnostics, named),
  };
}

function alignmentRoleHeader(saved, coverage) {
  const job = saved.job || {};
  const live = window.isLiveJobSource ? window.isLiveJobSource(job) : job.source_type === "greenhouse";
  const sourceLabel = live
    ? `${escapeHtml(job.employer || "Employer")} · Live ${escapeHtml(job.provider_label || "employer")} posting`
    : "Candidate-pasted job description";

  return `
    <section class="alignment-role-header panel">
      <div class="alignment-role-main">
        <div class="alignment-breadcrumb-row">
          <span class="badge ${live ? "green" : "neutral"}">
            ${live ? "Live posting snapshot" : "Pasted role"}
          </span>
          <span class="small muted">${sourceLabel}</span>
        </div>

        <h2>${escapeHtml(saved.title)}</h2>

        <p class="muted">
          ${escapeHtml(job.location || "Use the employer source to confirm location and eligibility.")}
        </p>

        <div class="button-row alignment-role-actions">
          ${
            live && job.source_url
              ? `<a class="button secondary" href="${escapeHtml(job.source_url)}" target="_blank" rel="noopener noreferrer">View & apply on employer site ↗</a>`
              : ""
          }
          <button class="button secondary" data-action="repeat-comparison">Refresh with latest evidence →</button>
        </div>
      </div>

      <div class="alignment-role-meta">
        <span class="eyebrow">Saved comparison</span>
        <strong>${escapeHtml(dateLabel(saved.created_at))}</strong>
        <small>
          ${saved.mode === "semantic" ? "Keywords + semantic suggestions" : "Keyword baseline"}
        </small>
      </div>
    </section>

    <section class="alignment-research-strip">
      <div class="alignment-strip-step"><span>01</span><strong>Extract</strong><small>Job requirements & candidate records</small></div>
      <div class="alignment-strip-arrow">→</div>
      <div class="alignment-strip-step"><span>02</span><strong>Map</strong><small>Canonical skill concepts</small></div>
      <div class="alignment-strip-arrow">→</div>
      <div class="alignment-strip-step"><span>03</span><strong>Understand</strong><small>Keyword + optional SBERT semantics</small></div>
      <div class="alignment-strip-arrow">→</div>
      <div class="alignment-strip-step"><span>04</span><strong>Explain</strong><small>Evidence, priority & next action</small></div>
    </section>
  `;
}

function alignmentCoverageCard(coverage) {
  const named = coverage.named;
  const ring = coverage.resumePercent;

  return `
    <section class="alignment-overview-grid">
      <article class="panel alignment-score-card">
        <div class="alignment-score-ring" style="--coverage:${ring}%;" aria-label="${ring}% resume mention coverage">
          <div>
            <strong>${ring}%</strong>
            <span>resume mention coverage</span>
          </div>
        </div>

        <div class="alignment-score-copy">
          <span class="eyebrow">JOB ↔ RESUME</span>
          <h2>What the role asks for</h2>
          <p>
            ${
              named
                ? `Your saved resume explicitly mentions ${coverage.resume} of ${named} named skill concepts in the supported catalogue.`
                : "No named skill concepts were extracted into the supported catalogue, so resume coverage cannot be assessed." 
            }
          </p>
          <p class="small muted">
            This is <strong>coverage</strong>, not a hiring probability or job-fit score. A missing mention does not prove a missing skill.
          </p>
        </div>
      </article>

      <article class="panel alignment-source-card">
        <div class="section-label">
          <div>
            <span class="eyebrow">EVIDENCE COVERAGE</span>
            <h2>Four ways to support a skill</h2>
          </div>
          <span class="badge neutral">Sources can overlap</span>
        </div>

        ${alignmentBar("Resume mentions", coverage.resume, named, "resume")}
        ${alignmentBar("Self-ratings", coverage.ratings, named, "rating")}
        ${alignmentBar("Projects / certificates", coverage.work, named, "work")}
        ${alignmentBar("Answered diagnostics", coverage.diagnostics, named, "diagnostic")}

        <div class="alignment-total-note">
          <strong>${coverage.anySupport}/${named || 0}</strong>
          <span>named skills with at least one supporting record</span>
        </div>
      </article>
    </section>
  `;
}

function alignmentBar(label, value, total, kind) {
  const width = alignmentPercent(value, total);
  return `
    <div class="alignment-bar-row">
      <div class="alignment-bar-label">
        <span>${escapeHtml(label)}</span>
        <strong>${value}/${total || 0}</strong>
      </div>
      <div class="alignment-bar-track" role="progressbar" aria-valuemin="0" aria-valuemax="${total || 1}" aria-valuenow="${value}" aria-label="${escapeHtml(label)}">
        <span class="alignment-bar-fill alignment-${kind}" style="width:${width}%"></span>
      </div>
    </div>
  `;
}

function alignmentPriorityMarkup(saved) {
  const items = alignmentSkillRows(saved)
    .filter((item) => item.status.priority > 0)
    .slice(0, 4);

  if (!items.length) {
    return `
      <section class="panel alignment-priority-panel alignment-clear-panel">
        <div class="section-label">
          <div>
            <span class="eyebrow">NEXT ACTION</span>
            <h2>No urgent evidence action surfaced</h2>
          </div>
          <span class="badge green">Clear for now</span>
        </div>
        <p class="muted">
          Your saved comparison does not show an incorrect diagnostic or an obvious missing evidence record among the named concepts. That is not a claim of overall job readiness.
        </p>
      </section>
    `;
  }

  return `
    <section class="panel alignment-priority-panel">
      <div class="section-label">
        <div>
          <span class="eyebrow">WHAT SHOULD I DO NEXT?</span>
          <h2>Priority focus</h2>
        </div>
        <span class="badge neutral">Evidence-first guidance</span>
      </div>

      <div class="priority-grid">
        ${items
          .map((item, index) => {
            const { row, status, importance, semanticScore } = item;
            return `
              <article class="priority-card priority-${escapeHtml(status.tone)}">
                <div class="priority-number">${index + 1}</div>
                <div class="priority-content">
                  <div class="button-row spread">
                    <h3>${escapeHtml(row.label)}</h3>
                    <span class="badge ${importance.key === "required" ? "amber" : "neutral"}">${importance.label}</span>
                  </div>
                  <strong>${escapeHtml(status.label)}</strong>
                  <p>${escapeHtml(status.detail)}</p>
                  ${semanticScore ? `<small>SBERT job-concept signal: ${semanticScore.toFixed(3)} · review, not a proficiency score</small>` : ""}
                  ${alignmentSkillAction(row, true)}
                </div>
              </article>
            `;
          })
          .join("")}
      </div>
    </section>
  `;
}

function alignmentMatrixMarkup(saved) {
  const items = alignmentSkillRows(saved);

  if (!items.length) {
    return `
      <section class="panel alignment-matrix-panel">
        <div class="empty-state">
          <div>
            <strong>No supported skill concepts were mapped yet.</strong>
            <p>Try the semantic comparison mode or add a more focused job description.</p>
          </div>
        </div>
      </section>
    `;
  }

  return `
    <section class="panel alignment-matrix-panel">
      <div class="section-label">
        <div>
          <span class="eyebrow">JOB REQUIREMENT → YOUR RECORD</span>
          <h2>Evidence map</h2>
        </div>
        <span class="small muted">Open a row to inspect the details below.</span>
      </div>

      <div class="alignment-map" role="table" aria-label="Job requirement and candidate evidence map">
        <div class="alignment-map-head" role="row">
          <span role="columnheader">Skill</span>
          <span role="columnheader">Importance</span>
          <span role="columnheader">Resume</span>
          <span role="columnheader">Your records</span>
          <span role="columnheader">Diagnostic</span>
          <span role="columnheader">Next</span>
        </div>

        ${items
          .map(({ row, importance, status, counts, semanticScore }) => {
            const diagnostic = alignmentAssessment(row);
            return `
              <div class="alignment-map-row" role="row">
                <div class="alignment-skill-cell" role="cell">
                  <strong>${escapeHtml(row.label)}</strong>
                  <small>
                    ${
                      row.mapping === "keyword"
                        ? "Named in job text"
                        : "Semantic suggestion · review"
                    }
                  </small>
                </div>

                <div role="cell">
                  <span class="importance-pill importance-${importance.key}">${importance.label}</span>
                </div>

                <div class="signal-cell" role="cell">
                  <span class="signal-dot ${counts.resume ? "on" : "off"}"></span>
                  <span>${counts.resume ? `${counts.resume} mention${counts.resume === 1 ? "" : "s"}` : "Not found"}</span>
                </div>

                <div class="signal-cell" role="cell">
                  <span class="signal-dot ${counts.rating || counts.work ? "on" : "off"}"></span>
                  <span>${counts.rating + counts.work || 0} record${counts.rating + counts.work === 1 ? "" : "s"}</span>
                </div>

                <div class="signal-cell" role="cell">
                  <span class="signal-dot ${counts.answered ? "on" : "off"}"></span>
                  <span>${diagnostic ? `${counts.answered}/${diagnostic.question_count} answered` : "Not assessed"}</span>
                </div>

                <div class="alignment-next-cell" role="cell">
                  <span class="status-pill status-${escapeHtml(status.tone)}">${escapeHtml(status.label)}</span>
                  ${semanticScore ? `<small>SBERT ${semanticScore.toFixed(2)}</small>` : ""}
                  ${alignmentSkillAction(row, true)}
                </div>
              </div>
            `;
          })
          .join("")}
      </div>

      <div class="alignment-legend">
        <span><i class="signal-dot on"></i> Record exists</span>
        <span><i class="signal-dot off"></i> No record</span>
        <span><i class="importance-pill importance-required">Required</i></span>
        <span><i class="importance-pill importance-optional">Preferred</i></span>
      </div>
    </section>
  `;
}

function alignmentSemanticMarkup(saved) {
  const result = saved.result;
  const semanticRows = (result.skills || []).filter(
    (row) => row.mapping === "semantic_suggestion",
  );
  const manual = result.manual_review || [];

  if (!semanticRows.length && !manual.length) return "";

  return `
    <section class="alignment-semantic-grid">
      <article class="panel semantic-card">
        <span class="eyebrow">SEMANTIC LAYER</span>
        <h2>Meaning, not just exact words</h2>
        <p>
          The semantic mode uses the local MiniLM pipeline to suggest concept links that keyword matching may not catch. Suggestions remain reviewable rather than becoming automatic candidate claims.
        </p>
        <div class="semantic-stat-row">
          <div><strong>${semanticRows.length}</strong><span>semantic concept suggestions</span></div>
          <div><strong>${manual.length}</strong><span>passages requiring manual review</span></div>
        </div>
        <p class="small muted">
          Semantic similarity is a research signal. It is not a confidence probability, proficiency score or hiring prediction.
        </p>
      </article>

      <article class="panel semantic-examples">
        <div class="section-label"><h2>Examples to inspect</h2><span class="small muted">Highest signal first</span></div>
        ${
          semanticRows.length
            ? semanticRows.slice(0, 3).map((row) => {
                const source = row.job_sources
                  .filter((item) => item.method === "semantic_suggestion")
                  .sort((a, b) => Number(b.similarity || 0) - Number(a.similarity || 0))[0];
                return `<div class="semantic-example"><strong>${escapeHtml(row.label)}</strong><span>cosine ${Number(source?.similarity || 0).toFixed(3)}</span><p>${escapeHtml(source?.text || "Suggested from job context.")}</p></div>`;
              }).join("")
            : '<p class="muted">No semantic-only suggestions were produced.</p>'
        }
      </article>
    </section>

    ${
      manual.length
        ? `<details class="panel match-review alignment-manual-review"><summary>Manual-review passages (${manual.length})</summary><p class="small muted">These passages were deliberately withheld from automatic requirement mapping because context or negation needs a human decision.</p>${manual.map((item) => `<blockquote class="match-quote">${escapeHtml(item.text)}<footer>${escapeHtml(item.reason || "Review this passage before treating it as a requirement.")}</footer></blockquote>`).join("")}</details>`
        : ""
    }
  `;
}

function enhancedAlignmentMarkup(saved) {
  const coverage = alignmentCoverage(saved);

  return `
    ${alignmentRoleHeader(saved, coverage)}
    ${alignmentCoverageCard(coverage)}
    ${alignmentPriorityMarkup(saved)}
    ${practicalTasksMarkup(saved)}
    ${alignmentMatrixMarkup(saved)}
    ${alignmentSemanticMarkup(saved)}
  `;
}


const PRACTICAL_TASKS = [
  {
    id: "sql-sales-analysis",
    skill: "sql",
    title: "SQL sales-analysis challenge",
    level: "Beginner",
    time: "30–45 min",
    problem: "Use customers, orders and products tables to find the top customers, monthly revenue and customers with no orders.",
    deliverables: [
      "Write one query for top customers by revenue.",
      "Write one query for monthly sales totals.",
      "Write one query that returns customers with no orders.",
    ],
    selfCheck: "Can you explain your JOIN choices, GROUP BY logic and how NULL values are handled?",
  },
  {
    id: "python-api-health-checker",
    skill: "python",
    title: "Python API health checker",
    level: "Beginner–Intermediate",
    time: "30–60 min",
    problem: "Build a small Python utility that calls an HTTP endpoint, parses JSON, reports response time and handles failed requests.",
    deliverables: [
      "Call a configurable endpoint.",
      "Handle 2xx, 4xx and 5xx responses clearly.",
      "Parse JSON and print a compact health report.",
      "Keep network errors separate from application errors.",
    ],
    selfCheck: "Can another developer change the URL without editing your core logic?",
  },
  {
    id: "rest-order-api",
    skill: "rest_api",
    title: "REST Order API design task",
    level: "Beginner–Intermediate",
    time: "45–90 min",
    problem: "Design a small Order API with predictable resources, status codes, JSON responses and validation.",
    deliverables: [
      "POST /orders",
      "GET /orders/{id}",
      "PUT /orders/{id}",
      "DELETE /orders/{id}",
      "Document success and error status codes.",
    ],
    selfCheck: "Can you explain why each endpoint uses its method and status codes?",
  },
  {
    id: "git-collaboration",
    skill: "git",
    title: "Git collaboration simulation",
    level: "Beginner",
    time: "20–30 min",
    problem: "Create a feature branch, make two logical commits, rebase or merge a change, and document the final history.",
    deliverables: [
      "Create a feature branch.",
      "Use meaningful commit messages.",
      "Resolve one controlled conflict.",
      "Show the final branch history.",
    ],
    selfCheck: "Can you explain the difference between a working-tree change, a commit and a remote branch?",
  },
  {
    id: "dockerize-api",
    skill: "docker",
    title: "Containerize a Python service",
    level: "Intermediate",
    time: "45–75 min",
    problem: "Package a small Python API in Docker and document how another developer can run it locally.",
    deliverables: [
      "Write a Dockerfile.",
      "Expose the application port.",
      "Build and run the image.",
      "Document the exact commands used.",
    ],
    selfCheck: "Can the image run without relying on packages installed on the host machine?",
  },
  {
    id: "javascript-dashboard",
    skill: "javascript",
    title: "JavaScript API dashboard",
    level: "Beginner–Intermediate",
    time: "45–60 min",
    problem: "Build a small page that fetches JSON from an API and renders loading, success and error states.",
    deliverables: [
      "Fetch data asynchronously.",
      "Render a loading state.",
      "Render the successful result.",
      "Handle HTTP and network errors.",
    ],
    selfCheck: "Can the UI recover from a failed request without a page reload?",
  },
];

function taskProgress(id) {
  try {
    return localStorage.getItem(`career-task-${id}`) === "attempted";
  } catch {
    return false;
  }
}

function setTaskProgress(id, attempted) {
  try {
    if (attempted) localStorage.setItem(`career-task-${id}`, "attempted");
    else localStorage.removeItem(`career-task-${id}`);
  } catch {
    /* Browser storage may be unavailable; the task remains usable. */
  }
}

function practicalTaskForSkill(skillKey) {
  return PRACTICAL_TASKS.find((task) => task.skill === skillKey);
}

function practicalTasksMarkup(saved) {
  const priority = alignmentSkillRows(saved)
    .filter((item) => item.status.priority > 0)
    .map((item) => practicalTaskForSkill(item.row.skill_key))
    .filter(Boolean);

  const fallback = PRACTICAL_TASKS.slice(0, 3);
  const tasks = [...new Map([...priority, ...fallback].map((task) => [task.id, task])).values()].slice(0, 4);

  return `
    <section class="panel practical-tasks-panel">
      <div class="section-label">
        <div>
          <span class="eyebrow">BUILD EVIDENCE THROUGH PRACTICE</span>
          <h2>Practical tasks for this role</h2>
        </div>
        <span class="badge neutral">Ungraded assignments</span>
      </div>

      <p class="muted">
        These are original, hands-on tasks linked to supported skills. They are not automatic proof of proficiency;
        they give you a concrete way to practise a weak area or create fresh evidence before re-aligning the job.
      </p>

      <div class="practical-task-grid">
        ${tasks
          .map(
            (task) => `
              <article class="practical-task-card ${taskProgress(task.id) ? "task-attempted" : ""}">
                <div class="button-row spread">
                  <span class="badge neutral">${escapeHtml(task.level)}</span>
                  <span class="small muted">${escapeHtml(task.time)}</span>
                </div>
                <h3>${escapeHtml(task.title)}</h3>
                <p>${escapeHtml(task.problem)}</p>
                <details>
                  <summary>Open assignment</summary>
                  <h4>Deliverables</h4>
                  <ul>
                    ${task.deliverables.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}
                  </ul>
                  <h4>Self-check</h4>
                  <p class="small muted">${escapeHtml(task.selfCheck)}</p>
                </details>
                <label class="task-check-row">
                  <input type="checkbox" data-task-toggle="${escapeHtml(task.id)}" ${taskProgress(task.id) ? "checked" : ""}>
                  <span>I attempted this task</span>
                </label>
                <small class="task-note">
                  Marking this is self-reported activity. It does not change an assessment score.
                </small>
              </article>
            `,
          )
          .join("")}
      </div>

      <p class="section-note">
        Recommended order: diagnose → practise → keep the work as evidence → run a new comparison.
      </p>
    </section>
  `;
}

function alignmentSavedHistoryMarkup() {
  if (!state.matchHistory?.length) {
    return `
      <section class="panel alignment-empty-history">
        <div class="empty-state">
          <span class="empty-icon" aria-hidden="true">◎</span>
          <div>
            <strong>Your alignment history will appear here.</strong>
            <p>Save a job comparison to build a repeatable evidence trail.</p>
          </div>
        </div>
      </section>
    `;
  }

  return `
    <section class="panel alignment-history-panel">
      <div class="section-label">
        <div>
          <span class="eyebrow">YOUR SAVED ROLE VIEWS</span>
          <h2>Recent job alignments</h2>
        </div>
        <span class="small muted">Latest 30 snapshots</span>
      </div>
      <div class="alignment-history-grid">
        ${state.matchHistory
          .slice(0, 6)
          .map((item) => {
            const summary = item.summary || {};
            return `
              <article class="alignment-history-card">
                <div class="button-row spread">
                  <span class="badge neutral">${item.mode === "semantic" ? "Semantic" : "Keyword"}</span>
                  <span class="small muted">${escapeHtml(dateLabel(item.created_at))}</span>
                </div>
                <h3>${escapeHtml(item.title)}</h3>
                <div class="alignment-history-stats">
                  <span><strong>${Number(summary.explicit_skill_mentions || 0)}</strong> named skills</span>
                  <span><strong>${Number(summary.explicit_mentions_with_claims || 0)}</strong> with claims</span>
                  <span><strong>${Number(summary.skills_with_assessment_records || 0)}</strong> assessed</span>
                </div>
                <button class="button secondary" data-action="open-match" data-id="${escapeHtml(item.id)}">Open alignment →</button>
              </article>
            `;
          })
          .join("")}
      </div>
    </section>
  `;
}

function enhancedMatchesMarkup() {
  if (state.comparison && !state.matchDraft) return enhancedComparisonMarkup();

  const draft = state.matchDraft || (state.matchDraft = freshMatchDraft());
  const ready = state.matchMetadata.semantic_model.available;

  return `
    <div class="page-intro">
      <span class="eyebrow">UNDERSTAND A ROLE BEFORE YOU ACT</span>
      <h1>Job alignment</h1>
      <p class="muted">
        Connect a job's named requirements with your resume, skill ratings, projects, certificates and diagnostic evidence. Start from a live opportunity or paste a description.
      </p>
    </div>

    <section class="alignment-how-panel">
      <div class="alignment-how-item"><span>1</span><div><strong>Choose a role</strong><p>Use a live employer posting or paste a job description.</p></div></div>
      <div class="alignment-how-item"><span>2</span><div><strong>See your evidence</strong><p>Resume, ratings, projects and diagnostics stay separate.</p></div></div>
      <div class="alignment-how-item"><span>3</span><div><strong>Take the next step</strong><p>Practice an observed error or collect evidence where it is unknown.</p></div></div>
    </section>

    ${alignmentSavedHistoryMarkup()}

    ${resumeContextMarkup()}

    <div class="match-editor-layout">
      <section class="panel">
        <div class="section-label">
          <div>
            <span class="eyebrow">COMPARE A ROLE</span>
            <h2>Paste a job description</h2>
          </div>
          <span class="badge neutral">Research mode</span>
        </div>

        <form id="match-form">
          <label>
            Job title
            <input name="title" maxlength="160" value="${escapeHtml(draft.title)}" placeholder="Junior Python Backend Developer" required>
          </label>

          <label>
            Job description
            <textarea name="description" rows="10" minlength="20" maxlength="8000" aria-describedby="match-description-hint" placeholder="Paste responsibilities, requirements and preferred skills…" required>${escapeHtml(draft.description)}</textarea>
          </label>

          <span class="field-hint" id="match-description-hint">
            20–8,000 characters. Preserve headings such as Requirements, Responsibilities and Preferred skills.
          </span>

          <label>
            Source link (optional)
            <input name="source_url" type="url" maxlength="2048" value="${escapeHtml(draft.source_url)}" placeholder="https://company.example/careers/job">
          </label>

          <label>
            Comparison method
            <select name="mode">
              <option value="semantic" ${draft.mode === "semantic" ? "selected" : ""} ${ready ? "" : "disabled"}>Keywords + semantic suggestions</option>
              <option value="keyword" ${draft.mode === "keyword" ? "selected" : ""}>Keyword baseline</option>
            </select>
          </label>

          <div class="alignment-method-note">
            <strong>${ready ? "Semantic mode available" : "Keyword mode available"}</strong>
            <span>${ready ? "The local MiniLM model suggests meaning-based concept links; you still review the result." : "Prepare the local semantic model later to enable semantic suggestions."}</span>
          </div>

          <div class="button-row evidence-form-actions">
            <button class="button primary" type="submit">Compare and save</button>
            <button class="button secondary" type="button" data-action="demo-match">Use example description</button>
            <button class="button secondary" type="button" data-action="jobs">Choose a live job →</button>
          </div>
        </form>
      </section>

      <aside class="panel evidence-guide alignment-guide-panel">
        <span class="badge neutral">Research differentiator</span>
        <h2>NLP → concepts → semantics → evidence → action</h2>
        <p>
          The prototype first extracts supported concepts, then uses the semantic layer where enabled. The alignment view keeps the candidate's evidence types distinct instead of collapsing them into a hidden suitability score.
        </p>
        <div class="alignment-guide-list">
          <div><strong>Resume</strong><span>Literal experience mentions</span></div>
          <div><strong>Profile</strong><span>Self-reported ratings</span></div>
          <div><strong>Work</strong><span>Projects & certificates</span></div>
          <div><strong>Diagnostic</strong><span>Observed answers on a small item set</span></div>
        </div>
        <p class="section-note">The current prototype does not infer hiring probability, years of experience, location eligibility or overall proficiency.</p>
      </aside>
    </div>
  `;
}

function enhancedComparisonMarkup() {
  const saved = state.comparison;
  const result = saved.result;
  const summary = result.summary || {};
  const otherMode = saved.mode === "semantic" ? "keyword" : "semantic";
  const canCompare =
    otherMode === "keyword" || state.matchMetadata.semantic_model.available;

  return `
    ${enhancedAlignmentMarkup(saved)}

    <section class="panel match-summary alignment-summary-strip">
      <div><strong>${Number(summary.explicit_skill_mentions || 0)}</strong><span>Named skill concepts</span></div>
      <div><strong>${Number(summary.explicit_mentions_with_claims || 0)}</strong><span>Named concepts with candidate claims</span></div>
      <div><strong>${Number(summary.semantic_suggestions || 0)}</strong><span>Semantic suggestions to review</span></div>
      <div><strong>${Number(summary.skills_with_assessment_records || 0)}</strong><span>Concepts with an assessment record</span></div>
    </section>

    <div class="info-line">
      <span class="info-icon" aria-hidden="true">i</span>
      <p>${escapeHtml(result.interpretation)}</p>
    </div>

    <section class="panel roadmap-entry">
      <div>
        <span class="eyebrow">KEEP THE SNAPSHOT REPRODUCIBLE</span>
        <h2>Updated your resume or evidence?</h2>
        <p class="muted">Create a new comparison using your latest records. This original saved snapshot stays unchanged.</p>
      </div>
      <button class="button secondary" data-action="repeat-comparison">Compare with latest evidence →</button>
    </section>

    <div class="section-label">
      <div>
        <span class="eyebrow">DETAILS</span>
        <h2>Skill-by-skill explanation</h2>
      </div>
      ${canCompare ? `<button class="text-button" data-action="compare-${otherMode}">Try ${otherMode === "keyword" ? "keyword baseline" : "semantic suggestions"} →</button>` : ""}
    </div>

    ${
      result.skills?.length
        ? `<div class="match-skill-list">${result.skills.map(comparisonSkillMarkup).join("")}</div>`
        : `<div class="empty-state"><div><strong>No supported skill concepts were mapped.</strong><p>Try a focused description or the semantic comparison mode. This does not mean the candidate is unsuitable.</p></div></div>`
    }

    <details class="panel match-review">
      <summary>Unmapped text and profile tags</summary>
      <p class="small muted">${escapeHtml(result.scope || "")} </p>
      <h3>Job passages without a mapping</h3>
      ${result.unassigned_fragments?.length ? `<ul>${result.unassigned_fragments.map((text) => `<li>${escapeHtml(text)}</li>`).join("")}</ul>` : '<p class="small muted">No whole passage was left unmapped.</p>'}
      <h3>Profile tags outside the supported catalogue</h3>
      <p class="small muted">${escapeHtml(result.unmapped_candidate_tags?.join(", ") || "None in this snapshot.")}</p>
    </details>

    <details class="panel match-review">
      <summary>Source, snapshot and method</summary>
      <p class="small muted">${comparisonSourceLabel(saved.job)}</p>
      ${saved.job.source_url ? evidenceSourceMarkup(saved.job.source_url) : ""}
      <pre class="match-source-text">${escapeHtml(saved.job.description)}</pre>
      <p class="small muted">Profile captured ${escapeHtml(dateLabel(saved.candidate_snapshot.captured_at))}. ${saved.candidate_snapshot.evidence.length} active evidence records were included. Saved snapshots retain their original details.</p>
      <p class="small muted">Policy: ${escapeHtml(result.policy_version || "not supplied")} · Vocabulary: ${escapeHtml(result.catalog_version || "not supplied")}${result.extraction_version ? ` · Extraction: ${escapeHtml(result.extraction_version)}` : ""}</p>
      ${result.model ? `<p class="small muted">Model: ${escapeHtml(result.model.id)}<br>Revision: ${escapeHtml(result.model.revision)}<br>Semantic suggestions use cosine ≥ ${result.suggestion_policy.minimum_cosine} and a best-versus-next margin ≥ ${result.suggestion_policy.minimum_margin}. These are uncalibrated prototype settings, not confidence probabilities.</p>` : '<p class="small muted">Keyword mode uses curated names and aliases with context review rules. No embedding model was run.</p>'}
    </details>

    ${alignmentSavedHistoryMarkup()}
  `;
}

/* Override the original match page with the enhanced version. */
const originalMatchesMarkup = matchesMarkup;
const originalComparisonMarkup = comparisonMarkup;

matchesMarkup = enhancedMatchesMarkup;
comparisonMarkup = enhancedComparisonMarkup;

/*
 * Important bug fix:
 * the earlier live-comparison reopen path passed live_job_id as the
 * Greenhouse board. A Greenhouse URL needs both board and provider_id.
 */
const originalHandleMatchAction = handleMatchAction;
handleMatchAction = async function (action, button) {
  const isLive = window.isLiveJobSource ? window.isLiveJobSource(state.comparison?.job) : state.comparison?.job?.source_type === "greenhouse";
  const liveAction = [
    "repeat-comparison",
    "compare-keyword",
    "compare-semantic",
  ].includes(action);

  if (isLive && liveAction) {
    const job = state.comparison.job;
    const requestedMode =
      action === "repeat-comparison"
        ? state.comparison.mode
        : otherComparisonMode(action);

    await openLiveJob(
      job.board,
      job.provider_id || job.live_job_id,
      requestedMode,
    );

    showNotice(
      "Opened the current live posting. Your saved comparison remains unchanged.",
      true,
    );
    return;
  }

  return originalHandleMatchAction(action, button);
};


if (typeof root !== "undefined") {
  root.addEventListener("change", (event) => {
    const checkbox = event.target.closest("[data-task-toggle]");
    if (!checkbox) return;
    setTaskProgress(checkbox.dataset.taskToggle, checkbox.checked);
    const card = checkbox.closest(".practical-task-card");
    card?.classList.toggle("task-attempted", checkbox.checked);
  }, true);
}
