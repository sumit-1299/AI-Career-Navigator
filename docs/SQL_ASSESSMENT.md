# SQL assessment: first implementation

This milestone adds a draft assessment lifecycle to the existing Flask API.
It preserves self-reported skills separately from assessment evidence.

## Scope and interpretation

- Skill: SQL; version: `sql-foundations-v1`.
- Six original multiple-choice questions: two each on filtering, joins and aggregation.
- Question status: draft, pending human review before a research pilot.
- All candidates receive the same questions in this version. Job-targeted selection,
  practical tasks, alternate reassessment forms and the web UI are later milestones.
- A result describes performance on these items. It is not a validated proficiency
  level, a probability of competence, or a job-readiness score.
- Repeating the same public question set is practice. Changes in its scores alone
  cannot establish learning improvement; the research study needs separate items/tasks.

SQL semantics were checked against the PostgreSQL documentation:

- [Filtering, joins, GROUP BY and HAVING](https://www.postgresql.org/docs/18/queries-table-expressions.html)
- [NULL predicates](https://www.postgresql.org/docs/18/functions-comparison.html)
- [COUNT and other aggregates](https://www.postgresql.org/docs/18/functions-aggregate.html)

The concrete join and aggregate examples also run in the automated tests. This
checks their expected SQL results, not the educational validity of the question bank.

## Candidate flow

1. Authenticate using the existing registration/login endpoints.
2. Start an attempt. The server stores its version, full question snapshot and
   the candidate's existing SQL claims at that time. Claims are optional.
3. Receive questions and options without their answer keys.
4. Submit exactly one response per assigned question. `option_id: null` means skip.
5. The server grades the stored snapshot and persists the result once.
6. Retrieve the result and the candidate's recent attempt history.

The existing `skills.proficiency` value stays on its original self-report scale.
The assessment does not overwrite it or convert its accuracy to that scale.
For the initial snapshot, SQL claims are matched by case-insensitive, trimmed
skill name `SQL`. Taxonomy identifiers and semantic aliases are not integrated yet.

## API contract

All endpoints require an `Authorization: Bearer <access_token>` header.

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/assessments/sql` | Describe the draft assessment |
| POST | `/api/assessments/sql/attempts` | Start; body must be `{}` |
| GET | `/api/assessments/sql/attempts` | Most recent 50 attempts belonging to this candidate |
| GET | `/api/assessments/attempts/<id>` | Retrieve an owned attempt |
| POST | `/api/assessments/attempts/<id>/submit` | Submit the answers once |

Submission body:

```json
{
  "answers": [
    {"question_id": "sql-filter-1", "option_id": "b"},
    {"question_id": "sql-filter-2", "option_id": "c"},
    {"question_id": "sql-join-1", "option_id": "a"},
    {"question_id": "sql-join-2", "option_id": "b"},
    {"question_id": "sql-aggregate-1", "option_id": "b"},
    {"question_id": "sql-aggregate-2", "option_id": null}
  ]
}
```

This deliberately mixed example yields 3 correct, 2 incorrect and 1 unassessed
response: 60% accuracy among answered items and 83.33% question coverage. These
are example software-test values, not research results.

The result contains counts, coverage, accuracy among answered items, topic
summaries and post-submission feedback. All skipped gives zero coverage and
`null` accuracy, rather than labelling the candidate unskilled. Incorrect answers
set `practice_suggested`; skips set `additional_evidence_needed`.

Clients cannot set the score, owner or answer key. Unknown/duplicate question IDs,
invalid options, malformed bodies and extra score fields return 400. Other
candidates' attempt IDs return 404. Submitting a completed attempt returns 409.
A conditional database update protects completed attempts from overwrite.

## Database and startup

The new `assessment_attempts` table stores the owner, timestamps, bank/rubric
snapshot, claimed skills, answers and result. It is created by the application's
existing `db.create_all()` startup mechanism. Existing tables are not changed.
Schema migrations remain a separate project task.

Restart Flask after installing the changes:

```powershell
.\.venv\Scripts\python.exe .\backend\app.py
```

## Verify locally

From the repository root, run the tests in a separate terminal/process:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s backend/tests -v
```

Tests explicitly use an isolated SQLite in-memory database. They cover scoring,
skips, invalid input, answer-key visibility, ownership, persistence, version
snapshots, resubmission and preservation of the self-reported skill. These tests
do not substitute for verifying the new endpoints against local PostgreSQL.

With Flask running, try the interactive API demonstration:

```powershell
.\.venv\Scripts\python.exe .\backend\scripts\try_sql_assessment.py --demo
```

This creates a fresh **DEMO - SQL Assessment** candidate, an `@example.test` email,
a SQL claim of 7/10 and an attempt in the local database. It presents questions,
accepts option letters or skips, submits to the API, and checks saved history.
It keeps passwords and access tokens out of its output. Demo accounts/results
must be excluded from any research participant dataset. A new run creates new
demonstration records; it is not an alternate-form reassessment study.

## Next integration

Use the topic summaries as inputs to a reviewed roadmap catalogue. Add the
candidate UI, practical-task rubrics, project/certification evidence and
job-targeted question selection in separate, measurable steps.
