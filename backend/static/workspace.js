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
      "The server could not be reached in time. Check that Flask is running. For an interrupted start or submission, check attempt history before trying again.",
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
              "Sign-in cancelled. Your answers remain in this tab. Retry the action when you are ready to sign in.",
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
  root.innerHTML = `<div class="workspace"><aside class="sidebar">${brand}<nav aria-label="Main navigation"><button class="nav-button ${onHistory ? "" : "active"}" data-action="overview" ${!onHistory ? 'aria-current="page"' : ""}><span class="nav-symbol" aria-hidden="true">▦</span>Overview</button><button class="nav-button ${onHistory ? "active" : ""}" data-action="history" ${onHistory ? 'aria-current="page"' : ""}><span class="nav-symbol" aria-hidden="true">◷</span>My assessments</button></nav><div class="sidebar-note"><span class="badge neutral">Research prototype</span><p>SQL foundations v1<br>Draft content awaiting human review.</p></div></aside><div><header class="topbar"><span class="breadcrumb">Workspace / ${onHistory ? "History" : "SQL foundations"}</span><div class="account"><span class="avatar" aria-hidden="true">${escapeHtml(state.user.name.slice(0, 1).toUpperCase())}</span><span class="account-name">${escapeHtml(state.user.name)}</span><button class="text-button" data-action="logout">Sign out</button></div></header><main id="main-content" class="content" tabindex="-1"></main></div></div>`;
  const main = document.querySelector("#main-content");
  if (state.view === "quiz") main.innerHTML = quizMarkup();
  else if (state.view === "results") main.innerHTML = resultsMarkup();
  else if (state.view === "history")
    main.innerHTML = `<div class="page-intro"><span class="eyebrow">Your evidence over time</span><h1>My assessments</h1><p class="muted">Revisit submitted results or continue an unfinished attempt.</p></div>${historyMarkup(state.history)}<p class="section-note">Showing up to 50 recent attempts. Repeating these same questions can reflect familiarity and is not independent evidence of skill improvement.</p>`;
  else main.innerHTML = overviewMarkup();
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
    <div class="info-line"><span class="info-icon" aria-hidden="true">i</span><p>${escapeHtml(attempt.assessment.interpretation)}</p></div><section class="review-list"><div class="section-label"><h2>Review your answers</h2><span class="small muted">Open a question for feedback</span></div>${result.feedback
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
  if (action === "login-tab" || action === "register-tab") {
    const email = document.querySelector('[name="email"]')?.value || "";
    state.authMode = action === "login-tab" ? "login" : "register";
    notice.hidden = true;
    renderAuth(email);
    return;
  }
  if (action === "logout") {
    if (
      hasUnsavedAnswers() &&
      !window.confirm(
        "Signing out will clear your unsubmitted answers. Sign out?",
      )
    )
      return;
    state.token = "";
    state.user = null;
    state.skills = [];
    state.history = [];
    state.metadata = null;
    state.attempt = null;
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
  void withBusy(button, async () => {
    if (action === "overview" || action === "history") {
      await loadWorkspace();
      state.view = action;
      renderShell();
      focusContent();
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
    }
  });
});

function hasUnsavedAnswers() {
  return [...state.drafts.values()].some(
    (answers) => Object.keys(answers).length > 0,
  );
}

window.addEventListener("beforeunload", (event) => {
  if (!hasUnsavedAnswers()) return;
  event.preventDefault();
  event.returnValue = "";
});

renderAuth();
