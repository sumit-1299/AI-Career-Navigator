# Evidence-linked SQL learning roadmaps

This milestone adds a saved learning plan to each submitted SQL assessment. The plan
contains relevant course links, original practice tasks, an explanation for each step,
and reversible, self-reported activity tracking.

It is an explainable rule-based baseline. It is not a trained recommender, a validated
skill model, or proof of a new research contribution. Later experiments can compare
this baseline with the proposed evidence-aware, job-targeted approach.

## Run and use

Start PostgreSQL and run the existing Flask application from the repository root:

```powershell
.\.venv\Scripts\python.exe .\backend\app.py
```

Open http://127.0.0.1:5000/app, sign in, and open a submitted result from **My assessments**.
Choose **View learning roadmap** below the result summary. If the button is missing
after installing the patch and restarting Flask, refresh the page with Ctrl+F5.

The application creates the new `learning_roadmaps` table through the project's
existing `db.create_all()` startup mechanism. Existing tables and results are not
rewritten. No additional Python or frontend packages are required. Existing users
can generate plans from their already-submitted assessments.

Within a roadmap:

1. Read **Why this step** and its assessment counts.
2. Open a course lesson or reference in a new browser tab.
3. Expand **Show practice data (SQL)** and attempt the task in your SQL editor.
4. Expand **Self-check after trying** to compare the expected result.
5. Optionally mark the practice complete. This records your own activity report.
6. Use **Mark as not done** to reverse that mark.
7. Return to the result or sign in again later and reopen the same saved roadmap.

The practice starters use CTEs (`WITH ... VALUES ...`) with fictional data. They do
not create tables. Add a SELECT query before running a starter. The application does
not execute submitted SQL, collect solution files, or automatically grade these tasks.

## Recommendation policy

| Topic evidence | Roadmap behaviour |
| --- | --- |
| At least one incorrect answer | Suggest relevant practice and resources. Mention any unanswered questions separately. |
| Unanswered question(s), no incorrect answers | Request more evidence. Suggest trying a practical task first; resources are optional support. |
| All assigned questions answered correctly | Omit remedial steps for that topic. |
| Every topic answered correctly | Save an empty targeted plan and explain the need for broader practical evidence. |
| Topic without a catalogue mapping | List it explicitly as unmapped rather than silently treating it as covered. |

The fixed ordering is filtering, joins, then aggregation, omitting topics without a
flagged need. This is a curriculum ordering assumption, not a learned ranking or
an experimentally validated optimum. The candidate's self-rating is not converted
to a score or used to invent a skill deficit.

## Resource catalogue

These public pages were checked for availability and topic relevance on **26 September
2026**. A checked link does not establish course quality, completion, or learning impact.

| Topic | Course lessons | PostgreSQL reference |
| --- | --- | --- |
| Filtering | [CS50 SQL: Querying](https://cs50.harvard.edu/sql/weeks/0/) | [Querying a table](https://www.postgresql.org/docs/18/tutorial-select.html) |
| Joins | [CS50 SQL: Relating](https://cs50.harvard.edu/sql/weeks/1/) | [Joins between tables](https://www.postgresql.org/docs/18/tutorial-join.html) |
| Aggregation | [Querying](https://cs50.harvard.edu/sql/weeks/0/) and [Relating](https://cs50.harvard.edu/sql/weeks/1/) | [Aggregate functions](https://www.postgresql.org/docs/18/tutorial-agg.html) |

The practice tasks are original project examples, not copied course assignments.
Their expected outputs are provided for learning and checked by automated SQL tests.
They need human review before use with research participants. They must not be used
as unseen evaluation tasks after candidates have been shown the answers.

## Saved snapshots and progress

Each assessment attempt has at most one saved roadmap. Reopening it returns the same
plan, even if future code changes the live catalogue. The snapshot includes:

- Source assessment/scoring versions and summary/topic counts.
- Recommendation policy `topic-evidence-rules-v1`.
- Resource catalogue `sql-resources-2026-09-26-v1`.
- Selected resources, checked dates, reasons, task text, and expected outputs.
- Creation time and the original assessment attempt ID.

Activity marks are stored separately from that snapshot. Each changed step records
a boolean completion state and UTC update time. Repeating an identical mark is
idempotent. Progress on one attempt is not copied to another attempt.

The progress bar means **practice activities marked complete**. It does not mean
verified proficiency, course completion, mastery, employability, or a learning gain.
Assessment scores and self-reported skill claims remain unchanged. No progress marks
or resource clicks are treated as training labels.

The API restricts each plan to the account that owns its source assessment. A unique
constraint prevents duplicate plans for the same attempt. PostgreSQL row locking is
used when updating progress to avoid overwriting other steps changed by another tab.
SQLite tests do not establish PostgreSQL concurrency behaviour.

## API contract

All routes require the existing JWT bearer token.

| Method and path | Behaviour |
| --- | --- |
| `GET /api/roadmaps/attempts/<attempt_id>` | Read an existing owned plan; return `roadmap: null` if it has not been created. No write. |
| `POST /api/roadmaps/attempts/<attempt_id>` | Body `{}`. Create a plan for a submitted owned attempt (`201`), or return its existing plan (`200`). |
| `PATCH /api/roadmaps/<roadmap_id>/progress` | Set a known step's self-reported completion state. |

Example PATCH body:

```json
{"step_id": "joins", "completed": true}
```

`completed` must be a JSON boolean. Additional fields, unknown steps, client scores
and owner IDs are rejected. Other candidates' attempts and plans return `404`.
Creating a plan for an unfinished assessment returns `409`.

## Verification

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s backend/tests -v
```

Expected at this milestone: **25 tests**, ending with **OK** (11 previous checks and
14 roadmap checks). Tests use isolated SQLite and do not alter the normal database.

The added checks cover authentication/ownership, skipped-versus-incorrect semantics,
the all-correct case, repeated creation, frozen catalogue snapshots, reversible and
idempotent progress, malformed input, score preservation, separate attempts, unmapped
topics, safe catalogue links, and the actual SQL outputs of the original practice tasks.

An automated Chromium flow against an isolated SQLite server also verified course-link
attributes, task display, saved progress after reload/sign-in, unchanged scores,
mixed/all-skipped/all-correct plans, and mobile layouts. The existing assessment flow
continued to pass. These are implementation checks, not research participant results.
Live link availability was checked separately; browser tests did not open external lessons.

### Check with your local PostgreSQL database

- Open your saved **20%** demonstration result with one filtering error, two join
  errors, and one aggregation error plus one skip. Expect three practice steps; the
  aggregation reason also mentions missing evidence.
- The controlled **60%** example (`B, C, A, B, B, skip`) should produce two steps:
  **joins: practice**, **aggregation: more evidence needed**. Filtering is omitted.
- With all questions skipped, expect three evidence-gathering steps and optional resources.
- With all correct (`B, C, D, A, B, C`), expect no targeted remedial steps.
- On a demo account, mark one practice task complete, reopen the plan and verify the
  mark persists. Undo it and check the assessment score is unchanged.

These scripted examples are demo records. Exclude them from any participant dataset.

## Code and commit

| File | Responsibility |
| --- | --- |
| `backend/services/learning_roadmap.py` | Curated resources, original tasks and versioned recommendation rules. |
| `backend/models/learning_roadmap.py` | Saved plan and separate activity data. |
| `backend/routes/roadmaps.py` | Owned reads/creation and progress updates. |
| `backend/app.py` | Registers the roadmap blueprint. |
| `backend/static/workspace.js` | Connects results to the roadmap and its saved activity controls. |
| `backend/static/workspace.css` | Responsive roadmap layout. |
| `backend/tests/test_learning_roadmaps.py` | Meaningful API, policy and SQL checks. |

Create `prajwal/learning-roadmap` from the completed `prajwal/assessment-ui` branch
before applying the patch. After local verification, commit the nine changed files:

```powershell
git add backend/app.py backend/models/learning_roadmap.py backend/routes/roadmaps.py backend/services/learning_roadmap.py backend/static/workspace.css backend/static/workspace.js backend/tests/test_learning_roadmaps.py docs/ASSESSMENT_UI.md docs/LEARNING_ROADMAP.md
git diff --cached --stat
git commit -m "Add evidence-linked SQL learning roadmaps and activity tracking"
git push -u origin prajwal/learning-roadmap
```

## What still needs research work

The next work is to capture project/certification evidence, introduce job-targeted
assessment selection under a question budget, and evaluate against this fixed baseline
using independently reviewed, held-out practical tasks. Model training requires
appropriate labelled data; this catalogue and activity log do not supply those labels.
Live job feeds also remain a separate ingestion task, with provenance and timestamps.

Document the fixed assumptions and actual pilot outcomes. Do not claim that a UI,
curated course links, or completion checkboxes alone establish novelty or effectiveness.
