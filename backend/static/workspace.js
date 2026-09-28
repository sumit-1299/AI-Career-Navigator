"use strict";

// The API owns scoring and candidate access. This file only presents its responses.
// Tokens, passwords and unsubmitted answers are never placed in browser storage.
const state = {
  token: "",
  user: null,
  authMode: "login",
  view: "overview",
  busy: false,
  skills: [],
  history: [],
  metadata: null,
  attempt: null,
  roadmap: null,
  evidence: [],
  evidenceEditor: null,
  evidenceDirty: false,
  showArchived: false,
  matchMetadata: null,
  matchHistory: [],
  comparison: null,
  matchDraft: null,
  matchDirty: false,
  index: 0,
  drafts: new Map(),
};
const root = document.querySelector("#root");
const notice = document.querySelector("#notice");
const submitDialog = document.querySelector("#submit-dialog");
const reauthDialog = document.querySelector("#reauth-dialog");
let noticeTimer;

const escapeHtml = (value) =>
  String(value ?? "").replace(
    /[&<>"']/g,
    (character) =>
      ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;",
      })[character],
  );
const percent = (value) =>
  value === null
    ? "Not assessed"
    : `${Number(value).toLocaleString(undefined, { maximumFractionDigits: 2 })}%`;
const dateLabel = (value) =>
  new Date(value).toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
const sqlClaims = () =>
  state.skills.filter(
    (skill) => skill.skill_name.trim().toLowerCase() === "sql",
  );
const brand = `<div class="brand"><span class="brand-mark" aria-hidden="true"><svg viewBox="0 0 32 32" fill="none"><path d="M7 24V8l18 16V8M7 8h7M18 24h7" stroke="currentColor" stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round"/></svg></span><span>Career Navigator<small>ASSESS. REFLECT. GROW.</small></span></div>`;

function showNotice(message, success = false) {
  clearTimeout(noticeTimer);
  notice.textContent = message;
  notice.className = `notice${success ? " success" : ""}`;
  notice.hidden = false;
  if (success)
    noticeTimer = setTimeout(() => {
      notice.hidden = true;
    }, 7000);
}

async function request(
  path,
  { method = "GET", body, auth = true, retry = true } = {},
) {
  const headers = { Accept: "application/json" };
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (auth) headers.Authorization = `Bearer ${state.token}`;
  let response;
  try {
    response = await fetch(path, {
      method,
      headers,
      cache: "no-store",
      credentials: "omit",
      body: body === undefined ? undefined : JSON.stringify(body),
      signal: AbortSignal.timeout(15000),
    });
  } catch {
    throw new Error(
      "The server could not be reached in time. Check that Flask is running. If a save was interrupted, check your saved records before trying again. Unsaved form text remains in this tab.",
    );
  }
  if (response.status === 401 && auth && retry) {
    await reauthenticate();
    return request(path, { method, body, auth, retry: false });
  }
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = new Error(
      data.message ||
        data.msg ||
        `Request failed (${response.status}). Please try again.`,
    );
    error.status = response.status;
    throw error;
  }
  return data;
}

function reauthenticate() {
  // Keep the pending action and draft in memory; only the same account can resume it.
  return new Promise((resolve, reject) => {
    const form = document.querySelector("#reauth-form");
    const password = document.querySelector("#reauth-password");
    const errorBox = document.querySelector("#reauth-error");
    document.querySelector("#reauth-email").value = state.user.email;
    password.value = "";
    errorBox.textContent = "";
    let authenticated = false;
    form.onsubmit = async (event) => {
      event.preventDefault();
      const button = form.querySelector('[type="submit"]');
      if (button.disabled) return;
      button.disabled = true;
      errorBox.textContent = "";
      try {
        const data = await request("/api/login", {
          method: "POST",
          auth: false,
          body: { email: state.user.email, password: password.value },
        });
        if (data.user.id !== state.user.id)
          throw new Error("Sign in to the account that started this attempt.");
        state.token = data.access_token;
        authenticated = true;
        reauthDialog.close();
      } catch (error) {
        errorBox.textContent = error.message;
      } finally {
        password.value = "";
        button.disabled = false;
      }
    };
    document.querySelector("#reauth-cancel").onclick = () =>
      reauthDialog.close();
    reauthDialog.addEventListener(
      "close",
      () => {
        form.onsubmit = null;
        password.value = "";
        if (authenticated) resolve();
        else
          reject(
            new Error(
              "Sign-in cancelled. Your unsaved work remains in this tab. Retry the action when you are ready to sign in.",
            ),
          );
      },
      { once: true },
    );
    reauthDialog.showModal();
    password.focus();
  });
}

async function withBusy(button, action) {
  if (state.busy) return;
  state.busy = true;
  notice.hidden = true;
  if (button) button.disabled = true;
  root.setAttribute("aria-busy", "true");
  try {
    await action();
  } catch (error) {
    showNotice(error.message);
  } finally {
    state.busy = false;
    root.removeAttribute("aria-busy");
    if (button?.isConnected) button.disabled = false;
  }
}

function renderAuth(email = "") {
  const registering = state.authMode === "register";
  root.innerHTML = `<div class="auth-layout">
    <aside class="auth-story">${brand}<div><span class="eyebrow">Your next step starts with evidence</span><h1>Know where you are.<br>See what comes next.</h1><p class="intro">Explore your SQL knowledge, understand your results, and make your next practice session count.</p>
      <div class="story-steps"><div class="story-detail"><span class="step-number">01</span><div><strong>Bring your perspective</strong><p class="muted">Record how you currently rate your SQL skill.</p></div></div><div class="story-detail"><span class="step-number">02</span><div><strong>Put it into practice</strong><p class="muted">Answer six questions across three SQL topics.</p></div></div><div class="story-detail"><span class="step-number">03</span><div><strong>Explore the evidence</strong><p class="muted">Review feedback and areas that need more practice or assessment.</p></div></div></div>
    </div><p class="auth-footer">AI Career Navigator · Research prototype<br>Current module: SQL foundations diagnostic</p></aside>
    <main class="auth-main" id="main-content"><div class="auth-card"><span class="badge neutral">Candidate workspace</span><h2>${registering ? "Create your account" : "Welcome back"}</h2><p class="muted">${registering ? "Start your assessment journey." : "Sign in to your assessment workspace."}</p>
      <div class="tabs" aria-label="Account access"><button type="button" data-action="login-tab" class="${registering ? "" : "active"}" aria-pressed="${!registering}">Sign in</button><button type="button" data-action="register-tab" class="${registering ? "active" : ""}" aria-pressed="${registering}">Create account</button></div>
      <form id="auth-form">${registering ? '<label>Full name<input name="name" type="text" autocomplete="name" maxlength="120" required></label>' : ""}<label>Email<input name="email" type="email" autocomplete="username" value="${escapeHtml(email)}" required></label><label>Password<input name="password" type="password" autocomplete="${registering ? "new-password" : "current-password"}" ${registering ? 'minlength="8"' : ""} required></label>${registering ? '<p class="small muted">Use at least 8 characters.</p>' : ""}<button class="button primary" type="submit">${registering ? "Create account & continue" : "Sign in to workspace"} <span aria-hidden="true">→</span></button></form>
      <p class="auth-note">Draft assessment content awaiting human review. Results describe these questions; they are not a validated proficiency rating.</p></div></main></div>`;
}

function renderShell() {
  const onHistory = state.view === "history";
  const onEvidence = state.view === "evidence";
  const onMatches = state.view === "matches";
  root.innerHTML = `<div class="workspace"><aside class="sidebar">${brand}<nav aria-label="Main navigation"><button class="nav-button ${onHistory || onEvidence || onMatches ? "" : "active"}" data-action="overview" ${!onHistory && !onEvidence && !onMatches ? 'aria-current="page"' : ""}><span class="nav-symbol" aria-hidden="true">▦</span>Overview</button><button class="nav-button ${onHistory ? "active" : ""}" data-action="history" ${onHistory ? 'aria-current="page"' : ""}><span class="nav-symbol" aria-hidden="true">◷</span>My assessments</button><button class="nav-button ${onEvidence ? "active" : ""}" data-action="evidence" ${onEvidence ? 'aria-current="page"' : ""}><span class="nav-symbol" aria-hidden="true">◇</span>My evidence</button><button class="nav-button ${onMatches ? "active" : ""}" data-action="matches" ${onMatches ? 'aria-current="page"' : ""}><span class="nav-symbol" aria-hidden="true">⌕</span>Compare a job</button></nav><div class="sidebar-note"><span class="badge neutral">Research prototype</span><p>SQL foundations v1<br>Draft content awaiting human review.</p></div></aside><div><header class="topbar"><span class="breadcrumb">Workspace / ${onMatches ? "Job comparison" : onEvidence ? "My evidence" : onHistory ? "History" : state.view === "roadmap" ? "Learning roadmap" : "SQL foundations"}</span><div class="account"><span class="avatar" aria-hidden="true">${escapeHtml(state.user.name.slice(0, 1).toUpperCase())}</span><span class="account-name">${escapeHtml(state.user.name)}</span><button class="text-button" data-action="logout">Sign out</button></div></header><main id="main-content" class="content" tabindex="-1"></main></div></div>`;
  const main = document.querySelector("#main-content");
  if (state.view === "quiz") main.innerHTML = quizMarkup();
  else if (state.view === "results") main.innerHTML = resultsMarkup();
  else if (state.view === "roadmap") main.innerHTML = roadmapMarkup();
  else if (state.view === "evidence") main.innerHTML = evidenceMarkup();
  else if (state.view === "matches") main.innerHTML = matchesMarkup();
  else if (state.view === "history")
    main.innerHTML = `<div class="page-intro"><span class="eyebrow">Your evidence over time</span><h1>My assessments</h1><p class="muted">Revisit submitted results or continue an unfinished attempt.</p></div>${historyMarkup(state.history)}<p class="section-note">Showing up to 50 recent attempts. Repeating these same questions can reflect familiarity and is not independent evidence of skill improvement.</p>`;
  else main.innerHTML = overviewMarkup();
}

function evidenceMarkup() {
  if (state.evidenceEditor) return evidenceEditorMarkup();
  const active = state.evidence.filter((item) => !item.archived);
  const archived = state.evidence.length - active.length;
  const items = state.evidence.filter(
    (item) => item.archived === state.showArchived,
  );
  return `<div class="page-intro"><span class="eyebrow">Experience behind your skills</span><h1>My evidence</h1><p class="muted">Bring together projects you contributed to and certificates you earned. Explain what each item shows and which skills you used.</p></div>
    <section class="panel evidence-intro"><div><span class="badge neutral">Candidate-submitted · Unverified</span><h2>Your work, with context.</h2><p class="muted">A link gives someone a starting point for review. It does not verify ownership, certificate validity or skill proficiency.</p><div class="evidence-counts"><span><strong>${active.filter((item) => item.kind === "project").length}</strong> projects</span><span><strong>${active.filter((item) => item.kind === "certification").length}</strong> certifications</span></div></div><div class="evidence-add-actions"><button class="button primary" data-action="add-project">+ Add project</button><button class="button secondary" data-action="add-certification">+ Add certification</button></div></section>
    <div class="info-line"><span class="info-icon" aria-hidden="true">i</span><p>Skill tags are your claims. Your SQL assessment results and learning activity stay separate. These submissions do not change your score or roadmap.</p></div>
    <div class="section-label"><h2>${state.showArchived ? "Archived evidence" : "Submitted evidence"}</h2><button class="text-button" data-action="evidence-filter">${state.showArchived ? `Show active (${active.length})` : `Show archived (${archived})`}</button></div>
    ${items.length ? `<div class="evidence-grid">${items.map(evidenceCardMarkup).join("")}</div>` : `<div class="empty-state"><span class="empty-icon" aria-hidden="true">◇</span><div><strong>${state.showArchived ? "No archived evidence" : "Add your first piece of evidence"}</strong><p>${state.showArchived ? "Archived items can be restored whenever you need them." : "Start with a project where you can describe your own contribution."}</p></div></div>`}`;
}

function evidenceSourceMarkup(value) {
  try {
    const url = new URL(value);
    if (url.protocol !== "https:" || url.username || url.password)
      throw new Error();
    return `<a class="evidence-source" href="${escapeHtml(url.href)}" target="_blank" rel="noopener noreferrer">Open submitted source <span aria-hidden="true">↗</span><small>${escapeHtml(url.hostname)}</small></a>`;
  } catch {
    return '<span class="muted">Source link unavailable</span>';
  }
}

function evidenceCardMarkup(item) {
  const project = item.kind === "project";
  return `<article class="panel evidence-card" data-evidence-id="${escapeHtml(item.id)}"><div class="button-row spread"><span class="eyebrow">${project ? "Project" : "Certification"}</span><span class="badge neutral">${item.archived ? "Archived · " : ""}Unverified</span></div><h3>${escapeHtml(item.title)}</h3>${project ? '<p class="small muted">Individual contribution recorded</p>' : `<p class="small muted">${escapeHtml(item.issuer)} · Issued ${escapeHtml(item.issued_on)}</p>`}<div class="topic-chips" aria-label="Claimed skills">${item.skills.map((skill) => `<span>${escapeHtml(skill)}</span>`).join("")}</div><details class="evidence-details"><summary>View submitted details</summary><h4>${project ? "Project description" : "What the certificate covers"}</h4><p>${escapeHtml(item.description)}</p>${project ? `<h4>Your contribution</h4><p>${escapeHtml(item.contribution)}</p>` : ""}</details>${evidenceSourceMarkup(item.source_url)}<div class="evidence-card-footer"><span class="small muted">Updated ${escapeHtml(dateLabel(item.updated_at))}</span><div class="button-row">${item.archived ? "" : `<button class="text-button" data-action="edit-evidence" data-id="${escapeHtml(item.id)}">Edit</button>`}<button class="text-button" data-action="archive-evidence" data-id="${escapeHtml(item.id)}">${item.archived ? "Restore" : "Archive"}</button></div></div></article>`;
}

function evidenceEditorMarkup() {
  const item = state.evidenceEditor;
  const project = item.kind === "project";
  const heading = `${item.id ? "Edit" : "Add"} ${project ? "project" : "certification"}`;
  return `<div class="page-intro"><span class="eyebrow">My evidence</span><h1>${heading}</h1><p class="muted">Record your experience clearly so it can be reviewed alongside your assessment results.</p></div><div class="evidence-editor-layout"><section class="panel"><form id="evidence-form"><div class="evidence-form-grid"><label>Title<input name="title" maxlength="160" value="${escapeHtml(item.title)}" placeholder="${project ? "Example: Library management database" : "Example: Introduction to Databases with SQL"}" required></label><label>Claimed skills<input name="skills" maxlength="418" value="${escapeHtml((item.skills || []).join(", "))}" placeholder="SQL, Python, REST APIs" aria-describedby="skills-hint" required><span class="field-hint" id="skills-hint">Separate 1–10 skills with commas; up to 40 characters each.</span></label></div>
      <label>${project ? "Project description" : "What the certificate covers"}<textarea name="description" rows="4" maxlength="2000" required placeholder="${project ? "What does the project do, and what was the outcome?" : "What did you study or practise? Describe any assessment that was required."}">${escapeHtml(item.description)}</textarea></label>
      ${project ? `<label>Your individual contribution<textarea name="contribution" rows="4" maxlength="2000" required placeholder="Describe the parts you designed, wrote or tested yourself. For team work, distinguish your contribution from the team's.">${escapeHtml(item.contribution)}</textarea></label>` : `<div class="evidence-form-grid"><label>Issuing organisation<input name="issuer" maxlength="160" value="${escapeHtml(item.issuer)}" required></label><label>Issue date<input name="issued_on" type="date" value="${escapeHtml(item.issued_on)}" required></label></div>`}
      <label>${project ? "Repository or project link" : "Certificate or credential link"}<input name="source_url" type="url" maxlength="2048" value="${escapeHtml(item.source_url)}" placeholder="https://" aria-describedby="source-hint" required><span class="field-hint" id="source-hint">Use an HTTPS page that a reviewer can access. Links are saved as submitted; the app does not open or verify them.</span></label>
      <div class="button-row evidence-form-actions"><button class="button primary" type="submit">${item.id ? "Save changes" : "Save evidence"}</button><button class="button secondary" type="button" data-action="cancel-evidence">Cancel</button></div></form></section><aside class="panel evidence-guide"><span class="badge neutral">Submitted · Unverified</span><h2>${project ? "Make your role clear" : "Add useful context"}</h2><p>${project ? "A team repository alone does not show who did what. Describe your own work and, where possible, link to relevant commits, documentation or a demo." : "Use the issuer's credential page when available. Record the organisation and issue date as shown on your certificate."}</p><p>Only tag skills this item relates to. A skill tag records your claim; it is not an assessed rating.</p><p class="section-note">You can edit or archive saved evidence later. Unsaved form text is kept only while this tab stays open.</p></aside></div>`;
}

async function loadEvidence() {
  state.evidence = (await request("/api/evidence")).evidence;
}

async function saveEvidence(values) {
  const item = state.evidenceEditor;
  const body = {
    kind: item.kind,
    title: values.get("title").trim(),
    description: values.get("description").trim(),
    source_url: values.get("source_url").trim(),
    skills: values
      .get("skills")
      .split(",")
      .map((value) => value.trim()),
  };
  if (item.kind === "project")
    body.contribution = values.get("contribution").trim();
  else {
    body.issuer = values.get("issuer").trim();
    body.issued_on = values.get("issued_on");
  }
  if (item.id) body.version = item.version;
  else body.submission_id = item.submission_id;
  const data = await request(
    item.id ? `/api/evidence/${item.id}` : "/api/evidence",
    {
      method: item.id ? "PUT" : "POST",
      body,
    },
  );
  state.evidence = [
    data.evidence,
    ...state.evidence.filter((entry) => entry.id !== data.evidence.id),
  ];
  state.evidenceEditor = null;
  state.evidenceDirty = false;
  state.showArchived = false;
  renderShell();
  focusContent();
  showNotice(
    "Evidence saved as an unverified submission. Your assessment result is unchanged.",
    true,
  );
}

function overviewMarkup() {
  const claims = sqlClaims();
  const pending = state.history.find(
    (attempt) => attempt.status === "in_progress",
  );
  return `<div class="page-intro"><span class="eyebrow">Your learning workspace</span><h1>Build a clearer picture of your skills.</h1><p class="muted">Start with SQL. Add your own perspective, take the diagnostic, and explore the evidence behind your next steps.</p></div><div class="overview-grid"><section class="panel assessment-card"><div class="button-row spread"><span class="badge">Available assessment</span><span class="small muted">Foundations · v1</span></div><h2>SQL foundations</h2><p class="muted">A short diagnostic covering how you filter, connect, and summarise data.</p><div class="topic-chips"><span>Filtering</span><span>Joins</span><span>Aggregation</span></div><div class="assessment-meta"><div><strong>${escapeHtml(state.metadata.question_count)}</strong><span>Questions</span></div><div><strong>3</strong><span>Topics</span></div><div><strong>Untimed</strong><span>Go at your pace</span></div></div><button class="button primary" data-action="${pending ? "open-attempt" : "start"}" ${pending ? `data-id="${escapeHtml(pending.id)}"` : ""}>${pending ? "Continue assessment" : "Start SQL assessment"} <span aria-hidden="true">→</span></button><p class="section-note">You may skip a question. It will remain unassessed.</p></section>
    <section class="panel claim-panel"><span class="eyebrow">Your perspective</span><h2>Self-reported SQL skill</h2>${claims.length ? (claims.length === 1 ? `<div class="claim-value">${escapeHtml(claims[0].proficiency)}<small> / 10</small></div>` : `<ul class="claim-list">${claims.map((claim) => `<li>${escapeHtml(claim.skill_name)}: ${escapeHtml(claim.proficiency)}/10</li>`).join("")}</ul>`) + '<p class="muted">This is your own rating. Assessment evidence is recorded separately.</p>' : '<p class="muted">Optional: how would you rate your current SQL skill?</p><form id="claim-form"><label>Rating from 1 to 10<input type="number" name="proficiency" min="1" max="10" step="1" placeholder="1–10" required></label><button class="button secondary" type="submit">Save my rating</button></form><p class="section-note">This is a self-report, not a verified score.</p>'}</section></div>
    <div class="info-line"><span class="info-icon" aria-hidden="true">i</span><p>The question bank is a draft awaiting human review. Your result describes performance on this small set of questions, not overall SQL proficiency or job readiness.</p></div><section class="history-section"><div class="section-label"><h2>Recent assessments</h2><button class="text-button" data-action="history">View history <span aria-hidden="true">→</span></button></div>${historyMarkup(state.history.slice(0, 3))}</section>`;
}

function historyMarkup(attempts) {
  if (!attempts.length)
    return '<div class="empty-state"><span class="empty-icon" aria-hidden="true">◷</span><div><strong>Your assessment history starts here</strong><p>Start a diagnostic to create your first attempt.</p></div></div>';
  return `<div class="history-list">${attempts
    .map((attempt) => {
      const done = attempt.status === "submitted";
      return `<article class="history-row"><div><h3>SQL foundations <span class="badge ${done ? "green" : "neutral"}">${done ? "Submitted" : "In progress"}</span></h3><p>${escapeHtml(dateLabel(attempt.submitted_at || attempt.created_at))}</p></div><div class="history-right">${done ? `<div class="history-score">${escapeHtml(percent(attempt.result.accuracy_on_answered_percent))}<small>${attempt.result.answered_count}/${attempt.result.question_count} answered</small></div>` : '<span class="small muted">Not submitted</span>'}<button class="button secondary" data-action="open-attempt" data-id="${escapeHtml(attempt.id)}">${done ? "View result" : "Continue"}</button></div></article>`;
    })
    .join("")}</div>`;
}

function answersFor(attempt) {
  if (!state.drafts.has(attempt.id)) state.drafts.set(attempt.id, {});
  return state.drafts.get(attempt.id);
}

function quizMarkup() {
  const attempt = state.attempt;
  const questions = attempt.questions;
  const question = questions[state.index];
  const answers = answersFor(attempt);
  const count = questions.filter((item) => answers[item.id]).length;
  return `<div class="page-intro"><span class="eyebrow">SQL foundations diagnostic</span><h1>One question. One piece of evidence.</h1><p class="muted">Choose the best answer, or leave a question unassessed. You can revisit any question before submitting.</p></div><div class="quiz-grid"><section class="panel question-panel"><div class="question-top"><span class="badge">${escapeHtml(question.topic)}</span><span class="question-count">Question ${state.index + 1} of ${questions.length}</span></div><fieldset><legend id="question-prompt">${escapeHtml(question.prompt)}</legend>${Object.entries(
    question.options,
  )
    .map(
      ([key, value]) =>
        `<label class="option"><input type="radio" name="answer" value="${escapeHtml(key)}" ${answers[question.id] === key ? "checked" : ""}><span class="option-letter">${escapeHtml(key)}.</span><span>${escapeHtml(value)}</span></label>`,
    )
    .join(
      "",
    )}</fieldset><div class="question-footer"><button class="button secondary" data-action="previous" ${state.index === 0 ? "disabled" : ""}>← Previous</button><button class="text-button" data-action="skip">${answers[question.id] ? "Clear & skip" : "Skip question"}</button><button class="button primary" data-action="${state.index === questions.length - 1 ? "review-submit" : "next"}">${state.index === questions.length - 1 ? "Review & submit" : "Next question →"}</button></div></section><aside class="panel quiz-summary"><h2>Your progress</h2><div class="progress-label"><span id="answered-label">${count} of ${questions.length} answered</span></div><progress id="answer-progress" aria-labelledby="answered-label" value="${count}" max="${questions.length}"></progress><div class="question-map" aria-label="Jump to a question">${questions.map((item, index) => `<button data-action="jump" data-index="${index}" class="${index === state.index ? "current" : ""} ${answers[item.id] ? "answered" : ""}" aria-label="Question ${index + 1}, ${answers[item.id] ? "answered" : "unanswered"}" ${index === state.index ? 'aria-current="step"' : ""}>${index + 1}</button>`).join("")}</div><button class="button secondary" data-action="review-submit">Review & submit</button><p class="quiz-note">Answers stay in this tab until submitted. Reloading or signing out clears unsubmitted answers.</p></aside></div>`;
}

function updateProgress() {
  const answers = answersFor(state.attempt);
  const questions = state.attempt.questions;
  const count = questions.filter((question) => answers[question.id]).length;
  document.querySelector("#answered-label").textContent =
    `${count} of ${questions.length} answered`;
  document.querySelector("#answer-progress").value = count;
  document.querySelector('[data-action="skip"]').textContent = answers[
    questions[state.index].id
  ]
    ? "Clear & skip"
    : "Skip question";
  document.querySelectorAll('[data-action="jump"]').forEach((button, index) => {
    const answered = Boolean(answers[questions[index].id]);
    button.classList.toggle("answered", answered);
    button.setAttribute(
      "aria-label",
      `Question ${index + 1}, ${answered ? "answered" : "unanswered"}`,
    );
  });
}

function topicStatus(topic) {
  if (topic.answered_count === 0)
    return '<span class="badge neutral">Unassessed</span>';
  return `${topic.practice_suggested ? '<span class="badge amber">Practice suggested</span>' : '<span class="badge green">Answered correctly</span>'}${topic.additional_evidence_needed ? ' <span class="badge neutral">Some unassessed</span>' : ""}`;
}

function resultsMarkup() {
  const attempt = state.attempt;
  const result = attempt.result;
  const suggested = result.topics.filter(
    (topic) => topic.practice_suggested || topic.additional_evidence_needed,
  );
  return `<div class="page-intro result-heading"><div><span class="badge green">Result saved</span><h1>Your SQL assessment evidence</h1><p class="muted">${escapeHtml(dateLabel(attempt.submitted_at))} · SQL foundations</p></div><button class="button secondary" data-action="history">View history</button></div><div class="metrics"><div class="metric primary-metric"><span class="metric-label">Accuracy on answered questions</span><strong>${escapeHtml(percent(result.accuracy_on_answered_percent))}</strong><small>${result.correct_count} correct out of ${result.answered_count} answered</small></div><div class="metric"><span class="metric-label">Assessment coverage</span><strong>${escapeHtml(percent(result.coverage_percent))}</strong><small>${result.answered_count} of ${result.question_count} questions answered</small></div><div class="metric"><span class="metric-label">Incorrect answers</span><strong>${result.incorrect_count}</strong><small>Evidence to guide further practice</small></div><div class="metric"><span class="metric-label">Unassessed questions</span><strong>${result.unanswered_count}</strong><small>Skipped questions need more evidence</small></div></div>
    <div class="result-grid"><section class="panel"><div class="section-label"><h2>Evidence by topic</h2><span class="small muted">${result.topics.length} topics</span></div>${result.topics.map((topic) => `<div class="topic-row"><div class="topic-title"><h3>${escapeHtml(topic.topic)}</h3><div>${topicStatus(topic)}</div></div><p>${topic.correct_count} correct · ${topic.incorrect_count} incorrect · ${topic.unanswered_count} unassessed</p></div>`).join("")}</section><aside class="panel"><span class="eyebrow">Make your next step count</span><h2>Where to focus</h2>${suggested.length ? suggested.map((topic) => `<div class="next-action"><strong>${escapeHtml(topic.topic)}</strong><p>${topic.practice_suggested ? "Review the explanations and practise the concepts you missed." : "Answer fresh questions to collect evidence for this topic."}${topic.additional_evidence_needed && topic.practice_suggested ? " Some questions also remain unassessed." : ""}</p></div>`).join("") : '<p class="muted small">You answered this question set correctly. A fresh practical task would provide additional evidence.</p>'}<div class="snapshot"><strong>Self-report when this attempt started</strong><p class="muted">${attempt.self_reported_claims.length ? attempt.self_reported_claims.map((claim) => `${escapeHtml(claim.skill_name)}: ${escapeHtml(claim.proficiency)}/10`).join(" · ") : "No SQL self-rating recorded."}</p><p class="muted">Self-report and assessment results are separate evidence.</p></div></aside></div>
    <div class="info-line"><span class="info-icon" aria-hidden="true">i</span><p>${escapeHtml(attempt.assessment.interpretation)}</p></div>${roadmapEntryMarkup()}<section class="review-list"><div class="section-label"><h2>Review your answers</h2><span class="small muted">Open a question for feedback</span></div>${result.feedback
      .map((feedback, index) => {
        const question = attempt.questions.find(
          (item) => item.id === feedback.question_id,
        );
        const outcome = feedback.outcome;
        const label =
          outcome === "correct"
            ? "Correct"
            : outcome === "incorrect"
              ? "Incorrect"
              : "Unassessed";
        const chosen = feedback.selected_option_id;
        return `<details class="review-item"><summary>Question ${index + 1} · ${escapeHtml(question.topic)} <span class="badge ${outcome === "correct" ? "green" : outcome === "incorrect" ? "red" : "neutral"}">${label}</span></summary><div class="review-body"><p><strong>${escapeHtml(question.prompt)}</strong></p><p>Your answer: ${chosen === null ? "Skipped — unassessed" : `${escapeHtml(chosen.toUpperCase())}. ${escapeHtml(question.options[chosen])}`}</p><p>Correct answer: ${escapeHtml(feedback.correct_option_id.toUpperCase())}. ${escapeHtml(question.options[feedback.correct_option_id])}</p><p class="muted">${escapeHtml(feedback.explanation)}</p></div></details>`;
      })
      .join(
        "",
      )}</section><div class="result-footer">Attempt: <code>${escapeHtml(attempt.id)}</code><br>Question bank: ${escapeHtml(attempt.assessment_version)} · Scoring: ${escapeHtml(attempt.assessment.scoring_version)}<br>Draft bank awaiting human review. Repeated attempts on these questions are not an independent measure of learning improvement.</div>`;
}

function roadmapEntryMarkup() {
  return `<section class="panel roadmap-entry"><div><span class="eyebrow">Your next step</span><h2>Turn your result into a learning plan.</h2><p class="muted">Open course lessons, try practical tasks, and track your learning activity. Each suggestion explains the evidence behind it.</p></div><button class="button primary" data-action="open-roadmap">View learning roadmap <span aria-hidden="true">→</span></button></section>`;
}

function resourceMarkup(resource) {
  let allowed = false;
  try {
    const url = new URL(resource.url);
    allowed =
      url.protocol === "https:" &&
      ["cs50.harvard.edu", "www.postgresql.org"].includes(url.hostname);
  } catch {
    /* Show the title without a link if a saved URL is invalid. */
  }
  return `<li class="roadmap-resource"><span class="resource-kind">${resource.kind === "course_lesson" ? "Course lesson" : "Reference"} · ${escapeHtml(resource.provider)}</span>${allowed ? `<a href="${escapeHtml(resource.url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(resource.title)} <span aria-hidden="true">↗</span><span class="visually-hidden"> (opens in a new tab)</span></a>` : `<strong>${escapeHtml(resource.title)} — link unavailable</strong>`}<p>${escapeHtml(resource.focus)}</p><span class="resource-date">Link checked ${escapeHtml(resource.checked_on)}</span></li>`;
}

function roadmapMarkup() {
  const roadmap = state.roadmap;
  const snapshot = roadmap.snapshot;
  const unmapped = snapshot.unmapped_topics.length > 0;
  return `<div class="page-intro result-heading"><div><span class="eyebrow">From evidence to action</span><h1>Your SQL learning roadmap</h1><p class="muted">Based on your assessment from ${escapeHtml(dateLabel(state.attempt.submitted_at))}. Follow the steps that fit the evidence from this attempt.</p></div><button class="button secondary" data-action="back-to-result">Back to result</button></div>
    <section class="panel roadmap-summary"><div><span class="badge">Saved learning plan</span><h2>${roadmap.step_count} ${roadmap.step_count === 1 ? "focused step" : "focused steps"}</h2><p class="muted">${roadmap.step_count ? "Work through the suggested order. Your progress is saved to this account." : "Your plan reflects this assessment only; broader SQL skills need additional evidence."}</p></div>${roadmap.step_count ? `<div class="roadmap-progress"><strong id="roadmap-progress-label">${roadmap.completed_count} of ${roadmap.step_count} practice activities marked complete</strong><progress id="roadmap-progress" value="${roadmap.completed_count}" max="${roadmap.step_count}" aria-labelledby="roadmap-progress-label"></progress><p class="muted">Self-reported activity. Your assessment score stays unchanged.</p></div>` : ""}</section>
    <div class="info-line"><span class="info-icon" aria-hidden="true">i</span><p>Wrong answers can suggest practice. Unanswered questions call for more evidence; resources for those topics are optional support.</p></div>
    ${unmapped ? `<div class="info-line"><p>Resource mapping is not yet available for: ${snapshot.unmapped_topics.map(escapeHtml).join(", ")}. These topics need separate review.</p></div>` : ""}
    <div class="roadmap-steps">${
      snapshot.steps.length
        ? snapshot.steps
            .map((step) => {
              const done =
                roadmap.self_reported_progress[step.id]?.completed === true;
              return `<article class="panel roadmap-step" data-step="${escapeHtml(step.id)}"><div class="roadmap-step-heading"><span class="roadmap-step-number">${step.position}</span><div><span class="eyebrow">${escapeHtml(step.topic)}</span><h2>${escapeHtml(step.title)}</h2></div><span class="badge ${step.kind === "practice" ? "amber" : "neutral"}">${step.kind === "practice" ? "Practice suggested" : "More evidence needed"}</span></div><p class="roadmap-reason"><strong>Why this step:</strong> ${escapeHtml(step.reason)}</p><p class="muted small">${escapeHtml(step.objective)}</p><div class="roadmap-columns"><section><h3>Learning resources</h3><p class="small muted">${escapeHtml(step.resource_guidance)}</p><ul class="roadmap-resource-list">${step.resources.map(resourceMarkup).join("")}</ul></section><section class="roadmap-practice"><span class="badge neutral">Original practice task</span><h3>${escapeHtml(step.task.title)}</h3><ol>${step.task.instructions.map((instruction) => `<li>${escapeHtml(instruction)}</li>`).join("")}</ol><details><summary>Show practice data (SQL)</summary><p class="small muted">Use this starter in your SQL editor and add your query. It uses temporary query data and does not create tables.</p><pre><code>${escapeHtml(step.task.starter_sql)}</code></pre></details><details><summary>Self-check after trying</summary><p>${escapeHtml(step.task.self_check)}</p><p class="muted small">Keep your query, output and explanation for review. This task is not automatically graded.</p></details></section></div><div class="roadmap-activity"><div><span class="badge ${done ? "green" : "neutral"} roadmap-activity-status">${done ? "Marked complete · self-reported" : "Not marked complete"}</span><p class="small muted">Mark this only after attempting the task. This records activity, not verified skill.</p></div><button class="button secondary roadmap-toggle" data-action="roadmap-progress" data-step="${escapeHtml(step.id)}" aria-label="Mark ${escapeHtml(step.topic)} practice ${done ? "as not done" : "complete"}">${done ? "Mark as not done" : "Mark practice complete"}</button></div></article>`;
            })
            .join("")
        : `<section class="panel"><h2>${unmapped ? "No mapped steps are available" : "No targeted practice suggested by this attempt"}</h2><p class="muted">${unmapped ? "Review the unmapped topics before drawing a conclusion." : "You answered the assessed topics correctly. A fresh practical evaluation would provide evidence beyond these multiple-choice questions."}</p></section>`
    }</div>
    <section class="panel roadmap-next"><span class="eyebrow">After practising</span><h2>Gather fresh evidence</h2><p class="muted">${escapeHtml(snapshot.next_evidence)}</p><p class="small muted">${escapeHtml(snapshot.progress_interpretation)}</p></section><details class="roadmap-method"><summary>How this roadmap was chosen</summary><p>Suggestions follow topic rules applied to this saved assessment. They are a baseline for the research project, not a trained recommendation model.</p><p>${escapeHtml(snapshot.ordering)} Tasks await human review. Link checks confirm resource availability and topic relevance, not learning effectiveness.</p><p class="small">Created ${escapeHtml(dateLabel(roadmap.created_at))}<br>Policy: ${escapeHtml(snapshot.policy_version)} · Catalogue: ${escapeHtml(snapshot.catalog_version)}<br>Assessment: ${escapeHtml(snapshot.source_assessment_version)}</p></details>`;
}

function syncRoadmapProgress() {
  const roadmap = state.roadmap;
  document.querySelector("#roadmap-progress-label").textContent =
    `${roadmap.completed_count} of ${roadmap.step_count} practice activities marked complete`;
  document.querySelector("#roadmap-progress").value = roadmap.completed_count;
  document.querySelectorAll(".roadmap-step").forEach((element) => {
    const step = element.dataset.step;
    const done = roadmap.self_reported_progress[step]?.completed === true;
    const badge = element.querySelector(".roadmap-activity-status");
    badge.textContent = done
      ? "Marked complete · self-reported"
      : "Not marked complete";
    badge.className = `badge ${done ? "green" : "neutral"} roadmap-activity-status`;
    const button = element.querySelector(".roadmap-toggle");
    button.textContent = done ? "Mark as not done" : "Mark practice complete";
    button.setAttribute(
      "aria-label",
      `Mark ${step} practice ${done ? "as not done" : "complete"}`,
    );
  });
}

async function loadWorkspace() {
  // Sequential requests avoid several session-expiry dialogs opening together.
  const skills = await request("/api/skills");
  const metadata = await request("/api/assessments/sql");
  const history = await request("/api/assessments/sql/attempts");
  state.skills = skills.skills;
  state.metadata = metadata.assessment;
  state.history = history.attempts;
}

async function openAttempt(id) {
  const data = await request(
    `/api/assessments/attempts/${encodeURIComponent(id)}`,
  );
  state.attempt = data.attempt;
  state.roadmap = null;
  state.view = data.attempt.status === "submitted" ? "results" : "quiz";
  state.index = 0;
  if (state.view === "results") state.drafts.delete(id);
  renderShell();
  focusContent();
}

function focusContent() {
  document.querySelector("#main-content")?.focus({ preventScroll: true });
  window.scrollTo({ top: 0 });
}

function confirmSubmission() {
  const questions = state.attempt.questions;
  const answers = answersFor(state.attempt);
  const count = questions.filter((question) => answers[question.id]).length;
  document.querySelector("#submit-summary").textContent =
    `${count} of ${questions.length} answered. ${questions.length - count} will remain unassessed.`;
  // Clear the previous return value so Escape cannot repeat a prior submission.
  submitDialog.returnValue = "cancel";
  submitDialog.showModal();
}

submitDialog.addEventListener("close", () => {
  if (submitDialog.returnValue !== "submit") return;
  void withBusy(null, async () => {
    const attempt = state.attempt;
    const draft = answersFor(attempt);
    const answers = attempt.questions.map((question) => ({
      question_id: question.id,
      option_id: draft[question.id] || null,
    }));
    let data;
    try {
      data = await request(`/api/assessments/attempts/${attempt.id}/submit`, {
        method: "POST",
        body: { answers },
      });
    } catch (error) {
      if (error.status !== 409) throw error;
      // A previous submission may have succeeded even if its response was lost.
      data = await request(`/api/assessments/attempts/${attempt.id}`);
      if (data.attempt.status !== "submitted") throw error;
    }
    state.attempt = data.attempt;
    state.roadmap = null;
    state.drafts.delete(attempt.id);
    state.history = [
      data.attempt,
      ...state.history.filter((item) => item.id !== attempt.id),
    ];
    state.view = "results";
    renderShell();
    focusContent();
  });
});

root.addEventListener("submit", (event) => {
  event.preventDefault();
  const form = event.target;
  const button = form.querySelector('[type="submit"]');
  void withBusy(button, async () => {
    const values = new FormData(form);
    if (form.id === "auth-form") {
      const email = values.get("email").trim();
      const password = values.get("password");
      if (state.authMode === "register") {
        const name = values.get("name").trim();
        if (!name) throw new Error("Enter your name.");
        await request("/api/register", {
          method: "POST",
          auth: false,
          body: { name, email, password },
        });
        // If login later fails, the account already exists; offer sign-in next.
        state.authMode = "login";
        renderAuth(email);
      }
      const data = await request("/api/login", {
        method: "POST",
        auth: false,
        body: { email, password },
      });
      form.reset();
      state.token = data.access_token;
      state.user = data.user;
      state.view = "overview";
      await loadWorkspace();
      renderShell();
      focusContent();
    } else if (form.id === "match-form") {
      await submitMatch(new FormData(form));
    } else if (form.id === "evidence-form") {
      await saveEvidence(values);
    } else if (form.id === "claim-form") {
      const proficiency = Number(values.get("proficiency"));
      if (!Number.isInteger(proficiency) || proficiency < 1 || proficiency > 10)
        throw new Error("Choose a whole-number rating from 1 to 10.");
      const data = await request("/api/skills", {
        method: "POST",
        body: { skill_name: "SQL", proficiency },
      });
      state.skills.push(data.skill);
      renderShell();
      showNotice(
        "Self-reported SQL rating saved. New attempts will record this claim separately from their results.",
        true,
      );
    }
  });
});

root.addEventListener("input", (event) => {
  if (event.target.closest("#evidence-form")) state.evidenceDirty = true;
  if (event.target.closest("#match-form")) state.matchDirty = true;
});

root.addEventListener("change", (event) => {
  if (state.view !== "quiz" || event.target.name !== "answer") return;
  answersFor(state.attempt)[state.attempt.questions[state.index].id] =
    event.target.value;
  updateProgress();
});

root.addEventListener("click", (event) => {
  const button = event.target.closest("button[data-action]");
  if (!button || button.disabled || state.busy) return;
  const action = button.dataset.action;
  if (
    state.evidenceDirty &&
    ["overview", "history", "evidence", "cancel-evidence", "matches"].includes(
      action,
    )
  ) {
    if (!window.confirm("Discard your unsaved evidence changes?")) return;
  }
  if (
    state.matchDirty &&
    [
      "overview",
      "history",
      "evidence",
      "matches",
      "open-match",
      "new-match",
    ].includes(action)
  ) {
    if (!window.confirm("Discard this unsaved job comparison?")) return;
  }
  if (action === "login-tab" || action === "register-tab") {
    const email = document.querySelector('[name="email"]')?.value || "";
    state.authMode = action === "login-tab" ? "login" : "register";
    notice.hidden = true;
    renderAuth(email);
    return;
  }
  if (action === "logout") {
    if (
      (hasUnsavedAnswers() || state.evidenceDirty || state.matchDirty) &&
      !window.confirm(
        "Signing out will clear your unsaved work in this tab. Sign out?",
      )
    )
      return;
    state.token = "";
    state.user = null;
    state.skills = [];
    state.history = [];
    state.metadata = null;
    state.attempt = null;
    state.roadmap = null;
    state.evidence = [];
    state.evidenceEditor = null;
    state.evidenceDirty = false;
    state.showArchived = false;
    clearMatchState();
    state.drafts.clear();
    state.view = "overview";
    state.authMode = "login";
    notice.hidden = true;
    renderAuth();
    return;
  }
  if (["previous", "next", "jump", "skip"].includes(action)) {
    if (action === "previous") state.index = Math.max(0, state.index - 1);
    if (action === "next")
      state.index = Math.min(
        state.attempt.questions.length - 1,
        state.index + 1,
      );
    if (action === "jump") state.index = Number(button.dataset.index);
    if (action === "skip") {
      delete answersFor(state.attempt)[state.attempt.questions[state.index].id];
      state.index = Math.min(
        state.attempt.questions.length - 1,
        state.index + 1,
      );
    }
    renderShell();
    focusContent();
    return;
  }
  if (action === "review-submit") {
    confirmSubmission();
    return;
  }
  if (action === "back-to-result") {
    state.view = "results";
    renderShell();
    focusContent();
    return;
  }
  void withBusy(button, async () => {
    if (action === "overview" || action === "history") {
      await loadWorkspace();
      clearMatchDraft();
      state.evidenceEditor = null;
      state.evidenceDirty = false;
      state.view = action;
      renderShell();
      focusContent();
    } else if (action === "evidence" || action === "cancel-evidence") {
      await loadEvidence();
      clearMatchDraft();
      state.evidenceEditor = null;
      state.evidenceDirty = false;
      state.view = "evidence";
      renderShell();
      focusContent();
    } else if (
      [
        "matches",
        "new-match",
        "open-match",
        "demo-match",
        "compare-keyword",
        "compare-semantic",
      ].includes(action)
    ) {
      await handleMatchAction(action, button);
    } else if (action === "add-project" || action === "add-certification") {
      state.evidenceEditor = {
        kind: action === "add-project" ? "project" : "certification",
        submission_id: crypto.randomUUID(),
      };
      state.evidenceDirty = false;
      renderShell();
      document.querySelector('#evidence-form [name="title"]').focus();
    } else if (action === "edit-evidence") {
      state.evidenceEditor = (
        await request(`/api/evidence/${button.dataset.id}`)
      ).evidence;
      state.evidenceDirty = false;
      renderShell();
      focusContent();
    } else if (action === "evidence-filter") {
      await loadEvidence();
      state.showArchived = !state.showArchived;
      renderShell();
      focusContent();
    } else if (action === "archive-evidence") {
      const item = state.evidence.find(
        (entry) => entry.id === button.dataset.id,
      );
      const data = await request(`/api/evidence/${item.id}/archive`, {
        method: "PATCH",
        body: { version: item.version, archived: !item.archived },
      });
      state.evidence = state.evidence.map((entry) =>
        entry.id === item.id ? data.evidence : entry,
      );
      renderShell();
      focusContent();
      showNotice(
        data.evidence.archived
          ? "Evidence archived. You can restore it from Show archived."
          : "Evidence restored. Find it under Show active.",
        true,
      );
    } else if (action === "start") {
      const data = await request("/api/assessments/sql/attempts", {
        method: "POST",
        body: {},
      });
      state.history.unshift(data.attempt);
      state.attempt = data.attempt;
      state.index = 0;
      state.view = "quiz";
      renderShell();
      focusContent();
    } else if (action === "open-attempt") {
      await openAttempt(button.dataset.id);
    } else if (action === "open-roadmap") {
      const data = await request(`/api/roadmaps/attempts/${state.attempt.id}`, {
        method: "POST",
        body: {},
      });
      state.roadmap = data.roadmap;
      state.view = "roadmap";
      renderShell();
      focusContent();
    } else if (action === "roadmap-progress") {
      const step_id = button.dataset.step;
      const completed =
        state.roadmap.self_reported_progress[step_id]?.completed !== true;
      const data = await request(`/api/roadmaps/${state.roadmap.id}/progress`, {
        method: "PATCH",
        body: { step_id, completed },
      });
      state.roadmap = data.roadmap;
      syncRoadmapProgress();
      showNotice(
        "Learning activity saved. Your assessment result is unchanged.",
        true,
      );
    }
  });
});

function hasUnsavedAnswers() {
  return [...state.drafts.values()].some(
    (answers) => Object.keys(answers).length > 0,
  );
}

window.addEventListener("beforeunload", (event) => {
  if (!hasUnsavedAnswers() && !state.evidenceDirty && !state.matchDirty) return;
  event.preventDefault();
  event.returnValue = "";
});

renderAuth();
