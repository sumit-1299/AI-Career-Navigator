# Candidate project and certification evidence

This milestone adds a candidate-owned evidence profile to the existing browser
workspace. It builds on the SQL diagnostic and learning roadmap. It does not train
a model, verify credentials, or establish the research contribution by itself.

## Run on Windows

Stop Flask before applying the patch. From the repository root, on the completed
`prajwal/learning-roadmap` branch:

```powershell
git switch -c prajwal/candidate-evidence
git apply --ignore-space-change --check .\candidate_evidence_v1.patch
git apply --ignore-space-change .\candidate_evidence_v1.patch
Remove-Item -LiteralPath .\candidate_evidence_v1.patch
.\.venv\Scripts\python.exe -m unittest discover -s backend/tests -v
.\.venv\Scripts\python.exe .\backend\app.py
```

Expected: **42 tests, OK** (11 assessment, 14 roadmap, 17 evidence). These tests use
isolated SQLite and do not operate on the database configured in your private `.env`.
No new Python packages or frontend build are required. On restart, the existing
`db.create_all()` setup creates the new `candidate_evidence` table. No existing table
definition is changed. This is a new-table addition, not a general migration system.

Open http://127.0.0.1:5000/app and refresh with **Ctrl+F5**. Sign in and choose
**My evidence**. Existing accounts, assessments and roadmaps remain available.

## Candidate workflow

1. Choose **Add project**. Enter its title, description, individual contribution,
   related skill names and repository/project URL. For team projects, explain what
   you personally did. A repository URL alone does not establish authorship.
2. Choose **Add certification** for a certificate you actually earned. Enter its title,
   issuer, issue date, covered material, related skills and credential/source URL.
3. Saved cards display **Unverified**. Expand **View submitted details** to see the
   description and project contribution. Source links open in a separate tab.
4. **Edit** corrects a submission. Its ID and creation timestamp remain stable;
   its version and update timestamp change.
5. **Archive** moves an item out of the active list. **Show archived** and **Restore**
   bring it back. Archiving retains the record; it does not erase it.

For a demonstration, use a clearly named demo account. Sample certificates must be
labelled as demonstrations and excluded from any participant research dataset.

### What is and is not evidence of proficiency

| Record | Meaning in this version |
| --- | --- |
| Project link and individual contribution | Candidate-submitted account of work; not independently verified authorship or quality. |
| Certificate, issuer and issue date | Candidate-submitted credential details; not a verified credential or prestige score. |
| Skill tags | Candidate's claimed relationship between an item and a skill. |
| SQL diagnostic result | Performance on the fixed, draft six-question instrument, stored separately. |
| Roadmap completion | Self-reported learning activity, stored separately. |

There is no combined proficiency score and no automatic trust boost for a certificate
or GitHub URL. Evidence changes do not alter ratings, graded attempts, saved roadmaps,
or roadmap progress. Missing evidence is not treated as proof of low proficiency.
Skill tags allow free text with case-insensitive deduplication; they are not yet mapped
to an independently reviewed skill taxonomy.

## Validation and persistence

- The API derives the owner from the authenticated account. It never accepts a supplied
  owner, score, verification state or timestamp. Reads, updates and archives are scoped
  to that owner; another account receives 404 for an individual record.
- Titles and issuer names: 1–160 characters. Description and project contribution:
  1–2,000 characters. Skills: 1–10 entries, up to 40 characters each, normalized for
  surrounding/repeated whitespace and deduplicated without changing the first spelling.
- Credential issue dates must be real `YYYY-MM-DD` dates, no later than the UTC date.
- URLs: at most 2,048 characters, HTTPS, domain name, no embedded username/password,
  whitespace, backslashes or custom port. IP literals and common local/reserved suffixes
  are rejected. This is syntax validation only: there is no DNS lookup, URL fetch,
  accessibility check, ownership check or issuer verification. A domain can still resolve
  privately, point to an unsafe site, require sign-in, redirect, disappear or be misleading.
- Every creation has a browser-generated UUID submission key. An identical retry for
  the same candidate returns the saved item rather than creating a duplicate. Reusing
  that key for different content returns 409. Independently opening a new form creates
  a new key; this is not duplicate-content detection.
- Edits and archive changes require the version that was opened. The database applies
  a conditional update; a stale version receives 409 instead of overwriting a newer edit.
  Copy any unsaved text, reopen the current record, then apply the correction.
- The model retains the current details and a version counter, **not a full revision
  history**. Do not describe these records as immutable research snapshots or an audit log.
- Dynamic text is escaped before it is inserted into HTML. External links use
  `noopener noreferrer`. Evidence API responses use `Cache-Control: no-store`.

Unsaved form text stays in the current tab. Leaving the editor or signing out asks
before discarding changes; reload/close requests the browser's standard leave warning.
There is no autosave. Expired-session recovery retains the form and resumes the request
after signing in to the same account. Validation or conflict errors leave the input in
place. After an interrupted update, reopen the saved record to check whether it succeeded.

## API contract

All routes require a Bearer JWT. Successful responses contain `status: "success"`.

| Route | Behaviour |
| --- | --- |
| `GET /api/evidence` | All current candidate's records, including archived records, newest update first, under `evidence`. |
| `POST /api/evidence` | Creates a submission: 201; identical submission-key retry: 200. |
| `GET /api/evidence/<id>` | Returns the owned record under `evidence`; otherwise 404. |
| `PUT /api/evidence/<id>` | Replaces editable fields with version check; type cannot change. Archived items must be restored first. |
| `PATCH /api/evidence/<id>/archive` | Accepts exactly `version` and boolean `archived`; supports archive and restore. |

Project creation body (replace the example content and generate a fresh UUID v4):

```json
{
  "submission_id": "c45f6c70-8595-4c9a-93c3-4be3f1c1a92e",
  "kind": "project",
  "title": "Library management database",
  "description": "Team project for books, members and loans.",
  "contribution": "I designed the schema and tested the overdue-loan queries.",
  "source_url": "https://github.com/example/library-database",
  "skills": ["SQL", "Database design"]
}
```

Certification creation uses `kind: "certification"`, replaces `contribution` with
`issuer` and `issued_on`, and keeps all other creation fields. `PUT` uses the same
type-specific fields but replaces `submission_id` with the returned integer `version`.
Returned records additionally include ID, version, archived flag, source
`candidate_submission`, verification status `unverified`, and UTC timestamps.

The first version lists all records for one candidate. Pagination, quotas, deletion/
retention controls, authenticated reviewer roles, issuer verification and an immutable
review history are future work before wider deployment or participant data collection.
No files are uploaded, links crawled or content sent to an external model by this feature.

## Verification

Implementation checks on 27 September 2026:

- All 42 backend tests pass on isolated SQLite, including 17 evidence tests covering
  ownership, malformed payloads, field/URL/date validation, rejected client verification
  fields, retry behaviour, stale updates, archive/restore and unchanged assessment data.
- Automated Chromium checks cover form submission, editing, escaping HTML, preserving
  input after errors, retry after a deliberately lost creation response, same-account
  reauthentication after an injected 401, stale-edit conflicts and archive/restore.
- Desktop and 390-pixel mobile layouts were visually inspected. Browser checks also
  revisit assessment history, results and reversible roadmap activity.

The injected network/authentication failures exercise UI recovery; they do not measure
real-world network reliability or wait for natural token expiry. Automated checks use
Python 3.12 and SQLite in the development environment. Prajwal's Windows Python 3.13 /
PostgreSQL installation still needs the local smoke check below. These are software
checks, not experimental research results or a production security audit.

### Local smoke check

Save one real project, edit its contribution, archive it, restore it, then sign out and
sign back in. Confirm the saved details persist. If you have a real certificate, save
it through the other form; use a separate demo account for fictitious examples. Reopen
your prior assessment and roadmap and confirm their values have not changed.

## Commit after the local check

This milestone changes nine files:

```powershell
git add backend/app.py backend/models/candidate_evidence.py backend/routes/evidence.py backend/services/candidate_evidence.py
git add backend/static/workspace.css backend/static/workspace.js backend/tests/test_candidate_evidence.py
git add docs/ASSESSMENT_UI.md docs/CANDIDATE_EVIDENCE.md
git diff --cached --stat
git commit -m "Add candidate project and certification evidence profiles"
git push -u origin prajwal/candidate-evidence
git status
```

The downloaded patch itself is not part of the commit. The private `.env` stays ignored.

## How this contributes to the research workflow

The profile supplies structured candidate claims for a future evidence-aware assessment
policy. It does not demonstrate novelty simply by combining projects, certificates,
assessments and roadmaps. A defensible next question is whether targeting a fixed budget
of assessment questions toward relevant skills with missing or conflicting evidence
improves decisions against independently scored practical tasks.

Before running that experiment:

1. Agree with the expert on the skill taxonomy, practical-task rubric and the rules for
   reviewing candidate contributions and credentials. Review the draft question bank.
2. Freeze the exact candidate evidence used by each experimental decision, including
   record IDs, versions and contents. Current mutable profiles alone are insufficient.
3. Define comparison conditions: self-report/profile baseline, fixed assessment, and
   the proposed targeted assessment. Use the same question budget and separate held-out
   practical tasks to avoid rewarding repeated exposure to the same questions.
4. Specify primary metrics and splits before collecting results. Keep demo records out,
   collect participant consent and avoid using unverified claims as ground-truth labels.
5. Keep live job data timestamped and separate from the frozen evaluation set. A changing
   job feed should not silently change an experiment midway through evaluation.

Any claimed improvement, predictive accuracy or novel contribution must come from the
subsequent study and literature comparison. No such finding is claimed by this milestone.
