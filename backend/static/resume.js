"use strict";

function uiIcon(name) {
  const paths = {
    home: '<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',
    resume: '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6M8 12h8M8 16h6"/>',
    jobs: '<rect x="3" y="7" width="18" height="14" rx="2"/><path d="M8 7V4h8v3M3 12l9 3 9-3M12 12v5"/>',
    matches: '<circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 5 5m-13-11 2 2 4-4"/>',
    evidence: '<path d="m12 2 9 5-9 5-9-5 9-5Zm-9 10 9 5 9-5M3 17l9 5 9-5"/>',
    history: '<path d="M3 12a9 9 0 1 0 3-6.7L3 8m0-5v5h5m4-1v5l3 2"/>',
    arrow: '<path d="M5 12h14m-5-5 5 5-5 5"/>',
  };
  return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${paths[name] || paths.home}</svg>`;
}

async function loadResume() {
  state.resumeData = await request("/api/resume");
}

function resetResumeDraft() {
  state.resumeDraft = {
    text: state.resumeData?.resume?.text || "",
    source_name: state.resumeData?.resume?.source_name || "My resume",
    version: state.resumeData?.version || 0,
  };
  state.resumeDirty = false;
  state.resumeFileStatus = "";
}

function dashboardLeadMarkup() {
  const done = state.history.filter((a) => a.status === "submitted").length;
  const evidence = state.evidence.filter((e) => !e.archived).length;
  const resume = state.resumeData?.resume;
  return `<section class="dashboard-hero"><div><span class="eyebrow">YOUR NEXT CAREER MOVE</span><h1>Turn your experience<br>into a clearer next step.</h1><p>Explore live opportunities. See how your resume and evidence connect to a role, then build the skills that need attention.</p><div class="button-row"><button class="button primary" data-action="jobs">Explore live jobs ${uiIcon("arrow")}</button><button class="button secondary" data-action="resume">${resume ? "Review my resume" : "Add my resume"}</button></div></div><div class="journey-card"><span class="eyebrow">YOUR WORKSPACE</span><h2>Hello, ${escapeHtml(state.user.name.split(" ")[0])}.</h2><p>One place for your next opportunity.</p><div class="journey-row"><span class="journey-dot ${resume ? "complete" : ""}">1</span><div><strong>Build your profile</strong><small>${resume ? "Resume saved · ready to compare" : "Add a resume and your skill claims"}</small></div></div><div class="journey-row"><span class="journey-dot">2</span><div><strong>Find a role</strong><small>Browse selected employer job boards</small></div></div><div class="journey-row"><span class="journey-dot ${done ? "complete" : ""}">3</span><div><strong>Support your skills</strong><small>${done ? `${done} submitted diagnostic${done === 1 ? "" : "s"}` : "Assess SQL, Python or HTTP foundations"}</small></div></div></div></section>
  <div class="dashboard-stats"><button data-action="resume" class="dashboard-stat">${uiIcon("resume")}<span><strong>${resume ? "Ready" : "Add resume"}</strong><small>Resume for comparisons</small></span></button><button data-action="jobs" class="dashboard-stat">${uiIcon("jobs")}<span><strong>${state.jobsData?.total ?? 0}</strong><small>Listings in the current cache</small></span></button><button data-action="evidence" class="dashboard-stat">${uiIcon("evidence")}<span><strong>${evidence}</strong><small>Projects and certificates</small></span></button><button data-action="history" class="dashboard-stat">${uiIcon("history")}<span><strong>${done}</strong><small>Submitted diagnostics</small></span></button></div>
  <div class="section-label"><div><span class="eyebrow">BUILD YOUR EVIDENCE</span><h2>A focused next step</h2></div><span class="small muted">Three foundation diagnostics</span></div>`;
}

function resumeMarkup() {
  if (!state.resumeDraft) resetResumeDraft();
  const draft = state.resumeDraft;
  const saved = state.resumeData.resume;
  const analysis = state.resumeData.analysis;
  return `<div class="page-intro"><span class="eyebrow">THE EXPERIENCE YOU BRING</span><h1>Resume & skills</h1><p class="muted">Add your resume, check the extracted text and save it for job comparisons. Your skills and assessment evidence stay visible alongside it.</p></div>
  <div class="resume-layout"><section class="panel"><div class="section-label"><h2>Your resume</h2><span id="resume-status" class="badge ${state.resumeDirty ? "amber" : saved ? "green" : "neutral"}">${state.resumeDirty ? "Unsaved changes" : saved ? `Saved · version ${saved.version}` : "No resume saved"}</span></div><form id="resume-form"><div class="resume-upload">${uiIcon("resume")}<div><label for="resume-file">Choose a resume file</label><p class="small muted">PDF, DOCX or TXT · Up to 2 MB · PDF up to 10 pages</p><input id="resume-file" type="file" accept=".pdf,.docx,.txt"><p id="resume-file-status" class="small" role="status">${escapeHtml(state.resumeFileStatus || "Or paste your resume text below.")}</p></div></div><label>Resume name<input name="source_name" maxlength="160" required value="${escapeHtml(draft.source_name)}"></label><label>Review and edit resume text<textarea name="text" rows="13" minlength="40" maxlength="30000" required placeholder="Paste your experience, projects, education and skills here…">${escapeHtml(draft.text)}</textarea></label><p class="field-hint">Check reading order, dates and skill names before saving. Scanned PDFs need text pasted from an OCR tool. DOCX headers, footers and graphics may be omitted.</p><div class="button-row"><button class="button primary" type="submit">Save resume</button><button class="button secondary" type="button" data-action="reload-resume">Use saved version</button>${saved ? '<button class="text-button" type="button" data-action="remove-resume">Remove saved resume</button>' : ""}</div><p class="section-note">Only the reviewed text is saved to your account. The original upload is not retained. Saved job comparisons keep the resume version they used, even after removal here.</p></form></section>
  <aside><section class="panel resume-insights"><span class="eyebrow">FROM YOUR SAVED RESUME</span><h2>Skill mentions</h2>${saved ? `<p class="small muted">${escapeHtml(saved.source_name)} · ${escapeHtml(dateLabel(saved.updated_at))}</p>` : '<p class="muted">Save a resume to see mentions in the supported skill catalogue.</p>'}<div class="topic-chips">${analysis.skills.map((s) => `<span>${escapeHtml(s.label)}</span>`).join("") || '<span>No supported mentions yet</span>'}</div><p class="small muted">These are literal mentions, not verified proficiency. Job comparisons also include your separate skill ratings, projects, certificates and diagnostics.</p>${analysis.manual_review.length ? `<details><summary>${analysis.manual_review.length} passages need review</summary>${analysis.manual_review.map((item) => `<blockquote class="match-quote">${escapeHtml(item.text)}<footer>${escapeHtml(item.reason)}</footer></blockquote>`).join("")}</details>` : ""}<button class="button secondary" data-action="jobs">Find a role to compare ${uiIcon("arrow")}</button></section><section class="panel resume-next"><h2>Make your work visible</h2><p class="small muted">Add a project and describe your own contribution. Link certificates to the skills they cover.</p><button class="text-button" data-action="evidence">Manage supporting evidence →</button></section></aside></div>
  <section class="panel profile-skills"><div class="section-label"><h2>Your self-reported skills</h2><span class="badge neutral">Your own ratings</span></div><form id="profile-skill-form"><label>Skill<input name="skill_name" list="profile-skill-options" maxlength="80" placeholder="Python, SQL, Docker…" required><datalist id="profile-skill-options">${state.resumeData.catalogue.map((s) => `<option value="${escapeHtml(s.label)}"></option>`).join("")}</datalist></label><label>Rating from 1 to 10<input type="number" name="proficiency" min="1" max="10" step="1" required placeholder="1–10"></label><button class="button secondary" type="submit">Add skill rating</button></form><div class="profile-skill-list">${state.skills.map((s) => `<div><span>${escapeHtml(s.skill_name)}</span><strong>${s.proficiency}/10</strong><button class="text-button" data-action="remove-skill" data-id="${s.id}" aria-label="Remove ${escapeHtml(s.skill_name)} rating">Remove</button></div>`).join("") || '<p class="small muted">No skill ratings recorded. Resume mentions are kept separate.</p>'}</div></section>`;
}

async function saveResume(values) {
  state.resumeDraft = { ...state.resumeDraft, text: values.get("text"), source_name: values.get("source_name") };
  state.resumeData = await request("/api/resume", { method: "PUT", body: state.resumeDraft });
  resetResumeDraft();
  renderShell();
  showNotice("Resume saved. New job comparisons will include this version.", true);
}

async function uploadResume(file) {
  if (!file) return;
  if (file.size > 2 * 1024 * 1024) throw new Error("Choose a resume file up to 2 MB.");
  const status = document.querySelector("#resume-file-status");
  status.textContent = `Reading ${file.name}…`;
  const body = new FormData(); body.append("file", file);
  try {
    const data = await request("/api/resume/extract", { method: "POST", body, timeout: 20000 });
    state.resumeDraft.text = data.text;
    state.resumeDraft.source_name = data.source_name;
    state.resumeDirty = true;
    state.resumeFileStatus = `${data.source_name} loaded successfully. Review the text below, then Save resume.`;
    renderShell();
  } catch (error) {
    status.textContent = "File could not be loaded. Your existing draft text is still below.";
    throw error;
  }
}

function resumeContextMarkup() {
  const resume = state.resumeData?.resume;
  return `<div class="resume-context">${uiIcon("resume")}<div><strong>${resume ? `Resume included: ${escapeHtml(resume.source_name)}` : "Add a resume for a fuller comparison"}</strong><p>${resume ? `Saved version ${resume.version} will be captured with this comparison.` : "You can compare your saved skills and evidence now, or add your resume first."}</p></div><button class="text-button" type="button" data-action="resume">${resume ? "Review resume" : "Add resume"} →</button></div>`;
}

function alignmentMarkup(saved) {
  const a = saved.result.alignment;
  if (!a) return ""; // Older saved results remain readable without recomputing them.
  return `<section class="panel alignment-panel"><div class="section-label"><div><span class="eyebrow">YOUR RECORDS AGAINST THIS ROLE</span><h2>Alignment at a glance</h2></div><span class="badge neutral">${a.named_skills} named skills in scope</span></div><p class="small muted">${escapeHtml(a.interpretation)}</p><div class="alignment-stats"><div><strong>${a.resume_included && a.named_skills ? `${a.with_resume_mentions}/${a.named_skills}` : "—"}</strong><span>Resume mentions</span></div><div><strong>${a.named_skills ? `${a.with_self_ratings}/${a.named_skills}` : "—"}</strong><span>Self-rated skills</span></div><div><strong>${a.named_skills ? `${a.with_project_or_certificate}/${a.named_skills}` : "—"}</strong><span>Project or certificate tags</span></div><div><strong>${a.named_skills ? `${a.with_answered_diagnostic}/${a.named_skills}` : "—"}</strong><span>Answered diagnostics</span></div></div><p class="small muted">${!a.resume_included ? "No resume was included in this saved comparison. " : `Resume: ${escapeHtml(saved.candidate_snapshot.resume.source_name)} · version ${saved.candidate_snapshot.resume.version}. `}${a.without_recorded_support.length ? `Collect evidence for: ${escapeHtml(a.without_recorded_support.join(", "))}.` : a.named_skills ? "Each named skill has at least one record. That record may still be an unverified claim." : "No named skills were mapped; coverage cannot be assessed."}</p><div class="alignment-scroll" tabindex="0" role="region" aria-label="Skill evidence alignment"><table class="alignment-table"><thead><tr><th scope="col">Job skill</th><th scope="col">Resume</th><th scope="col">Skill rating</th><th scope="col">Projects / certificates</th><th scope="col">Diagnostic evidence</th></tr></thead><tbody>${saved.result.skills.map((r) => `<tr><th scope="row">${escapeHtml(r.label)}<small>${r.mapping === "keyword" ? "Named mention" : "Suggested · review"}</small></th><td>${r.resume_mentions?.length ? '<span class="status-dot positive">Mentioned</span>' : a.resume_included ? "Not found" : "Not supplied"}</td><td>${r.candidate_claims.filter((c) => c.kind === "self_report").map((c) => `${c.rating}/10`).join(", ") || "Not recorded"}</td><td>${r.candidate_claims.filter((c) => c.kind !== "self_report").length || "None"}<small>Unverified records</small></td><td>${r.assessment ? `${r.assessment.result.answered_count}/${r.assessment.result.question_count} answered` : "Not assessed"}${r.assessment?.result.incorrect_count ? `<small>${r.assessment.result.incorrect_count} incorrect · review topics</small>` : ""}</td></tr>`).join("")}</tbody></table></div></section>`;
}
