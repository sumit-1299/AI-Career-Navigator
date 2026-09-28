"use strict";
const KEY_LABELS = {
  python: "Python",
  sql: "SQL",
  rest_api: "REST APIs",
  django: "Django",
  flask: "Flask",
  postgresql: "PostgreSQL",
  git: "Git",
  docker: "Docker",
  javascript: "JavaScript",
  java: "Java",
};
const KEYS = Object.keys(KEY_LABELS);
const VALUES = ["present", "absent", "uncertain"];
let packet = null,
  dataset = null,
  cases = [],
  index = 0,
  annotations = Object.create(null),
  dirty = false,
  loadedPacketName = "",
  loadedReviewName = "";
const $ = (id) => document.getElementById(id);
function notice(text) {
  $("notice").textContent = text;
  $("notice").hidden = false;
}
function canonical(value) {
  if (Array.isArray(value)) return value.map(canonical);
  if (value && typeof value === "object")
    return Object.fromEntries(
      Object.keys(value)
        .sort()
        .map((key) => [key, canonical(value[key])]),
    );
  return value;
}
async function hash(value) {
  const bytes = new TextEncoder().encode(JSON.stringify(canonical(value)));
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  return Array.from(new Uint8Array(digest), (byte) =>
    byte.toString(16).padStart(2, "0"),
  ).join("");
}
async function readFile(file) {
  if (!file) throw new Error("Choose a JSON file.");
  if (file.size > 20 * 1024 * 1024) throw new Error("File exceeds 20 MiB.");
  const text = await file.text();
  try {
    return JSON.parse(text.replace(/^\uFEFF/, ""));
  } catch {
    throw new Error(
      "This file is not valid JSON. Download the JSON attachment itself, not the answer sheet or a saved web page.",
    );
  }
}
function adjudicating() {
  return packet?.schema_version === "career-skill-adjudication-packet-v1";
}
function conflictFor(id) {
  return adjudicating()
    ? packet.disagreements.find((row) => row.case_id === id)
    : null;
}
function blankLabels() {
  return Object.fromEntries(KEYS.map((key) => [key, ""]));
}
function getAnnotation(id) {
  if (!annotations[id])
    annotations[id] = {
      case_id: id,
      labels: blankLabels(),
      notes: "",
      reviewed: false,
    };
  return annotations[id];
}
function reviewValid(row) {
  return (
    row.reviewed === true &&
    KEYS.every((key) => VALUES.includes(row.labels[key])) &&
    (!KEYS.some((key) => ["present", "uncertain"].includes(row.labels[key])) ||
      row.notes.trim())
  );
}
async function loadPacket(file) {
  const loaded = await readFile(file);
  const data =
    loaded.schema_version === "career-skill-adjudication-packet-v1"
      ? loaded.dataset
      : loaded;
  if (data?.schema_version !== "career-skill-dataset-v1")
    throw new Error(
      "Choose a frozen dataset or adjudication packet, not a model report.",
    );
  const { fingerprint, ...rest } = data;
  if ((await hash(rest)) !== fingerprint)
    throw new Error(
      "Dataset fingerprint mismatch. Use the unchanged exported packet.",
    );
  if (
    data.catalog_version !== "backend-skills-2026-09-27-v1" ||
    data.annotation_policy !== "job-relevant-skills-v1" ||
    JSON.stringify(data.skills) !==
      JSON.stringify(KEYS.map((key) => ({ key, label: KEY_LABELS[key] })))
  )
    throw new Error(
      "Packet vocabulary or policy differs from this review page.",
    );
  if (
    !Array.isArray(data.cases) ||
    data.cases.length < 2 ||
    data.cases.length > 200
  )
    throw new Error("Invalid case list.");
  const ids = new Set();
  for (const row of data.cases) {
    if (
      typeof row.id !== "string" ||
      !/^[-a-zA-Z0-9_]+$/.test(row.id) ||
      ids.has(row.id) ||
      typeof row.description !== "string" ||
      typeof row.title !== "string" ||
      !row.source
    )
      throw new Error("Invalid or duplicate case.");
    ids.add(row.id);
  }
  let selected = data.cases;
  if (loaded.schema_version === "career-skill-adjudication-packet-v1") {
    if (
      !Array.isArray(loaded.disagreements) ||
      !loaded.disagreements.length ||
      !Array.isArray(loaded.parent_review_hashes) ||
      loaded.parent_review_hashes.length !== 2 ||
      !Array.isArray(loaded.reviewer_ids)
    )
      throw new Error("Invalid adjudication packet.");
    const disputed = new Set();
    for (const row of loaded.disagreements) {
      if (
        !ids.has(row.case_id) ||
        disputed.has(row.case_id) ||
        !Array.isArray(row.skills) ||
        !row.skills.length ||
        !row.skills.every((key) => KEYS.includes(key)) ||
        !row.review_a?.labels ||
        !row.review_b?.labels
      )
        throw new Error("Invalid adjudication case.");
      disputed.add(row.case_id);
    }
    selected = data.cases.filter((row) => disputed.has(row.id));
  }
  if (
    dirty &&
    !confirm(
      "Replace this unsaved review? Download a draft first if you need it.",
    )
  )
    return false;
  packet = loaded;
  dataset = data;
  cases = selected;
  index = 0;
  annotations = Object.create(null);
  dirty = false;
  loadedReviewName = "";
  $("resume-file").value = "";
  $("resume-status").textContent =
    "Dataset loaded. Choose the saved review JSON for this original dataset.";
  $("attestation").checked = false;
  $("review-workspace").hidden = false;
  for (const row of cases) {
    const item = getAnnotation(row.id),
      conflict = conflictFor(row.id);
    if (conflict)
      for (const key of KEYS)
        if (!conflict.skills.includes(key))
          item.labels[key] = conflict.review_a.labels[key];
  }
  $("case-select").replaceChildren(
    ...cases.map((row, i) => new Option(`${i + 1}. ${row.title}`, String(i))),
  );
  $("packet-label").textContent =
    `${adjudicating() ? "Adjudication" : "Independent review"} · ${cases.length} cases${dataset.kind === "synthetic_smoke" ? " · SYNTHETIC PRACTICE ONLY" : ""}`;
  $("notice").hidden = true;
  renderCase();
  return true;
}
function renderCase() {
  const row = cases[index],
    item = getAnnotation(row.id),
    conflict = conflictFor(row.id);
  $("case-select").value = String(index);
  $("case-title").textContent = row.title;
  $("source-label").textContent =
    row.source.employer || "Synthetic practice example";
  $("case-meta").textContent =
    `Case ${index + 1} of ${cases.length} · ${row.id}${row.source.location ? ` · ${row.source.location}` : ""}`;
  $("source-details").textContent = row.source.last_seen_at
    ? `Frozen source last seen: ${row.source.last_seen_at}. Posting version ${row.source.version}.`
    : "AI-authored synthetic practice text. Not an independently reviewed research example.";
  $("source-link").hidden = true;
  $("source-link").removeAttribute("href");
  try {
    const url = new URL(row.source.source_url);
    if (url.protocol === "https:" && !url.username && !url.password) {
      $("source-link").href = url.href;
      $("source-link").hidden = false;
    }
  } catch {}
  $("case-text").textContent = row.description;
  $("case-notes").value = item.notes;
  $("skill-labels").replaceChildren();
  for (const key of KEYS) {
    const container = document.createElement("div");
    container.className = "skill-row";
    const label = document.createElement("label");
    label.textContent = KEY_LABELS[key];
    label.htmlFor = `label-${key}`;
    const select = document.createElement("select");
    select.id = `label-${key}`;
    select.dataset.skill = key;
    select.append(
      new Option("Choose label…", ""),
      ...VALUES.map(
        (value) => new Option(value[0].toUpperCase() + value.slice(1), value),
      ),
    );
    select.value = item.labels[key];
    select.disabled = !!conflict && !conflict.skills.includes(key);
    container.append(label, select);
    if (conflict) {
      const help = document.createElement("small");
      help.textContent = `${packet.reviewer_ids[0]}: ${conflict.review_a.labels[key]} · ${packet.reviewer_ids[1]}: ${conflict.review_b.labels[key]}${select.disabled ? " · Agreed, locked" : " · Resolve this label"}`;
      container.append(help);
    }
    $("skill-labels").append(container);
  }
  $("adjudication-note").hidden = !conflict;
  if (conflict)
    $("adjudication-note").textContent =
      `Resolve only disputed labels. ${packet.reviewer_ids[0]} notes: ${conflict.review_a.notes} | ${packet.reviewer_ids[1]} notes: ${conflict.review_b.notes}`;
  $("previous").disabled = index === 0;
  $("next").disabled = index === cases.length - 1;
  updateProgress();
}
function updateProgress() {
  const complete = cases.filter((row) =>
    reviewValid(getAnnotation(row.id)),
  ).length;
  const filled = cases.reduce(
    (total, row) =>
      total +
      KEYS.filter((key) => VALUES.includes(getAnnotation(row.id).labels[key]))
        .length,
    0,
  );
  $("progress").textContent =
    `${filled} of ${cases.length * KEYS.length} labels filled. ${complete} of ${cases.length} cases confirmed. ${dirty ? "Changes since last download." : ""}`;
  $("case-status").textContent = reviewValid(getAnnotation(cases[index].id))
    ? "Case confirmed. Editing a label or note will reopen it."
    : "Read the full text, label all skills, add notes where needed, then confirm.";
}
function changeCurrent() {
  getAnnotation(cases[index].id).reviewed = false;
  dirty = true;
  updateProgress();
}
$("packet-file").addEventListener("change", async (event) => {
  const input = event.currentTarget;
  const file = input.files[0];
  if (!file) return;
  input.disabled = true;
  $("resume-file").disabled = true;
  $("packet-status").textContent = `Loading ${file.name}…`;
  try {
    if (await loadPacket(file)) {
      loadedPacketName = file.name;
      $("packet-status").textContent =
        `Loaded ${file.name} — ${cases.length} cases. Your review appears below the annotation rules.`;
    } else {
      input.value = "";
      $("packet-status").textContent =
        `Selection cancelled. ${loadedPacketName} remains loaded with your unsaved review.`;
    }
  } catch (error) {
    // Clear failed selections so the same file can be chosen again after correction.
    input.value = "";
    $("packet-status").textContent =
      `Could not load ${file.name}: ${error.message}${loadedPacketName ? ` ${loadedPacketName} remains loaded.` : ""}`;
    notice(error.message);
  } finally {
    input.disabled = false;
    $("resume-file").disabled = false;
  }
});
$("skill-labels").addEventListener("change", (event) => {
  if (!event.target.dataset.skill) return;
  getAnnotation(cases[index].id).labels[event.target.dataset.skill] =
    event.target.value;
  changeCurrent();
});
$("case-notes").addEventListener("input", () => {
  getAnnotation(cases[index].id).notes = $("case-notes").value;
  changeCurrent();
});
for (const id of ["reviewer-id", "attestation"])
  $(id).addEventListener("change", () => {
    if (dataset) {
      dirty = true;
      updateProgress();
    }
  });
$("remaining-absent").addEventListener("click", () => {
  const item = getAnnotation(cases[index].id);
  for (const key of KEYS) if (!item.labels[key]) item.labels[key] = "absent";
  changeCurrent();
  renderCase();
});
$("mark-reviewed").addEventListener("click", () => {
  const row = getAnnotation(cases[index].id);
  if (!KEYS.every((key) => VALUES.includes(row.labels[key]))) {
    notice("Label all ten skills first.");
    return;
  }
  if (
    KEYS.some((key) => ["present", "uncertain"].includes(row.labels[key])) &&
    !row.notes.trim()
  ) {
    notice(
      "Add supporting quotations for present skills and explain uncertain labels.",
    );
    return;
  }
  row.reviewed = true;
  dirty = true;
  $("notice").hidden = true;
  updateProgress();
});
function navigate(next) {
  index = next;
  $("notice").hidden = true;
  renderCase();
  $("case-title").scrollIntoView({ block: "start" });
}
$("previous").addEventListener("click", () => navigate(Math.max(0, index - 1)));
$("next").addEventListener("click", () =>
  navigate(Math.min(cases.length - 1, index + 1)),
);
$("case-select").addEventListener("change", (event) =>
  navigate(Number(event.target.value)),
);
function download(complete) {
  const reviewer = $("reviewer-id").value.trim();
  if (!/^[A-Za-z0-9_-]{2,40}$/.test(reviewer)) {
    notice(
      "Enter a reviewer ID such as R1 (2–40 letters, digits, underscores or hyphens).",
    );
    return;
  }
  if (adjudicating() && packet.reviewer_ids.includes(reviewer)) {
    notice("The adjudicator must use a third reviewer ID.");
    return;
  }
  if (
    complete &&
    (!$("attestation").checked ||
      !cases.every((row) => reviewValid(getAnnotation(row.id))))
  ) {
    notice(
      "Confirm every case and check the independent-review declaration before exporting a completed review. You can download a draft at any time.",
    );
    return;
  }
  const review = {
    schema_version: "career-skill-review-v1",
    dataset_id: dataset.dataset_id,
    dataset_fingerprint: dataset.fingerprint,
    kind: adjudicating() ? "adjudication" : "independent",
    reviewer_id: reviewer,
    without_model_predictions: $("attestation").checked,
    complete,
    exported_at: new Date().toISOString(),
    annotations: cases.map((row) => getAnnotation(row.id)),
  };
  if (adjudicating()) review.parent_review_hashes = packet.parent_review_hashes;
  const url = URL.createObjectURL(
    new Blob([JSON.stringify(review, null, 2)], { type: "application/json" }),
  );
  const a = document.createElement("a");
  a.href = url;
  a.download = `${complete ? "review" : "draft"}-${reviewer}-${dataset.dataset_id.slice(0, 8)}.json`;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
  dirty = false;
  updateProgress();
  notice(
    complete
      ? "Completed review downloaded. Keep the original file unchanged for evaluation."
      : "Draft downloaded. To resume, load the same packet and then this draft.",
  );
}
$("save-draft").addEventListener("click", () => download(false));
$("save-complete").addEventListener("click", () => download(true));
$("resume-file").addEventListener("change", async (event) => {
  const input = event.currentTarget;
  const file = input.files[0];
  if (!file) return;
  input.disabled = true;
  $("packet-file").disabled = true;
  $("resume-status").textContent = `Loading ${file.name}…`;
  try {
    if (!dataset)
      throw new Error(
        "Load the original dataset or adjudication packet first.",
      );
    const review = await readFile(file);
    if (review?.schema_version !== "career-skill-review-v1")
      throw new Error(
        "Choose a saved review JSON, such as pilot_v1_AI_DRAFT.json. The original pilot-v1.json belongs in the first picker.",
      );
    if (review.dataset_id !== dataset.dataset_id)
      throw new Error(
        "This draft is for a different exported dataset. Load the exact original pilot-v1.json used to create the draft; a new export will not match.",
      );
    if (review.dataset_fingerprint !== dataset.fingerprint)
      throw new Error(
        "This draft does not match the contents of the loaded dataset. Use its unchanged original dataset file.",
      );
    if (review.kind !== (adjudicating() ? "adjudication" : "independent"))
      throw new Error(
        "This review type does not match the loaded packet. Load the original dataset for an ordinary draft, or the adjudication packet for an adjudication draft.",
      );
    if (
      !Array.isArray(review.annotations) ||
      review.annotations.length !== cases.length
    )
      throw new Error("Review case count differs from this packet.");
    const restored = Object.create(null);
    for (const row of review.annotations) {
      if (
        !row ||
        !cases.some((item) => item.id === row.case_id) ||
        restored[row.case_id] ||
        !row.labels ||
        Object.keys(row.labels).length !== KEYS.length ||
        !KEYS.every((key) => ["", ...VALUES].includes(row.labels[key])) ||
        typeof row.notes !== "string" ||
        row.notes.length > 5000
      )
        throw new Error("Invalid review annotation.");
      const conflict = conflictFor(row.case_id);
      if (
        conflict &&
        KEYS.some(
          (key) =>
            !conflict.skills.includes(key) &&
            row.labels[key] !== conflict.review_a.labels[key],
        )
      )
        throw new Error("An agreed label was changed in this draft.");
      restored[row.case_id] = row;
    }
    if (
      adjudicating() &&
      JSON.stringify(review.parent_review_hashes) !==
        JSON.stringify(packet.parent_review_hashes)
    )
      throw new Error("Adjudication belongs to different original reviews.");
    if (dirty && !confirm("Replace unsaved labels with this saved review?")) {
      input.value = "";
      $("resume-status").textContent =
        "Selection cancelled. Your current labels and unsaved changes remain loaded.";
      return;
    }
    annotations = restored;
    $("reviewer-id").value =
      typeof review.reviewer_id === "string" ? review.reviewer_id : "";
    $("attestation").checked = review.without_model_predictions === true;
    dirty = false;
    index = 0;
    loadedReviewName = file.name;
    renderCase();
    const aiAssisted =
      review.annotation_origin === "ai_assisted" ||
      review.annotations.some((row) => row.annotation_origin === "ai_assisted");
    const guidance = aiAssisted
      ? "AI-assisted draft: keep the human-review declaration unchecked and use Download draft. Filled labels are separate from confirmed human reviews."
      : "Confirm unfinished cases before completing the review.";
    $("resume-status").textContent =
      `Loaded ${file.name} — ${cases.length} cases. ${$("progress").textContent} ${guidance}`;
    notice(`Saved review loaded. ${guidance}`);
  } catch (error) {
    input.value = "";
    $("resume-status").textContent =
      `Could not load ${file.name}: ${error.message}${loadedReviewName ? ` Your previously loaded review (${loadedReviewName}) and current labels remain in place.` : " Your current labels remain in place."}`;
    notice(error.message);
  } finally {
    input.disabled = false;
    $("packet-file").disabled = false;
  }
});
window.addEventListener("beforeunload", (event) => {
  if (dirty) {
    event.preventDefault();
    event.returnValue = "";
  }
});
