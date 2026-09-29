# SQL, Python and REST API foundations

Implemented 29 September 2026. This extends the existing application; it does not
replace the original SQL bank, saved attempts or comparison snapshots.

## Candidate flow

1. Choose SQL, Python or REST APIs on Overview and optionally record a self-rating.
2. Start or resume a six-question diagnostic. Submit answers or explicit skips.
3. Open the saved result and its learning roadmap. Incorrect answers suggest
   practice; skipped questions request more evidence, with optional resources.
4. Compare a pasted or cached live job. The latest submitted attempt for each
   supported skill appears beside claims, project tags and certificate tags.
5. If a relevant skill is unassessed, choose **Assess [skill]** on its job card.
6. After submission, return to the original comparison and choose **Compare with
   latest evidence**. Review and submit the new comparison. The old one stays
   unchanged. For live jobs this opens the current cached posting for review.

An unfinished attempt is resumed when available. Draft answers stay in the tab;
reloading still clears unsubmitted answers. Assessment history covers all skills.

## Scope and versions

| Skill | Bank | Topics | Resource catalogue |
| --- | --- | --- | --- |
| SQL | `sql-foundations-v1` (unchanged) | Filtering, joins, aggregation | `sql-resources-2026-09-26-v1` |
| Python | `python-foundations-v1` | Functions, collections, exceptions | `python-resources-2026-09-29-v1` |
| REST APIs | `rest-http-foundations-v1` | HTTP methods, status codes, representations | `rest-http-resources-2026-09-29-v1` |

Each bank has two items per topic. REST questions sample HTTP knowledge; they do
not measure complete REST architectural design or practical API implementation.
All content is AI-assisted, original draft project content pending human review.
No claim of psychometric validation, security against cheating or practical coding
proficiency is made. Fixed questions with feedback are practice diagnostics;
repeat scores are not independent evidence of learning gains.

Scoring remains `equal-weight-with-skips-v1`. Resource selection remains the
explicit `topic-evidence-rules-v1` policy. Answer keys stay server-side until
submission, and submitted attempts retain the exact assigned question snapshot.
No new database columns, migration or Python dependency is required.

## API and compatibility

- `GET /api/assessments/catalog`: supported banks, labels, topics and aliases;
  no answers or explanations.
- `GET /api/assessments/<skill_key>`: one bank's description.
- `GET|POST /api/assessments/<skill_key>/attempts`: skill-scoped history/start.
- `GET /api/assessments/attempts`: latest 50 attempts across skills.
- Existing attempt read/submit and roadmap routes are unchanged and owner-scoped.
- Existing `/sql` and `/sql/attempts` URLs continue to work.
- SQL snapshot content and SQL roadmap payload semantics are preserved.
- New candidate snapshots contain `assessments` keyed by skill and the legacy
  `sql_assessment` field for compatibility. `snapshot_version` is
  `candidate-evidence-v2`; results record `candidate_evidence_version` as
  `latest-per-skill-v2`. Extraction rules/version are unchanged by this batch.

Matching uses the latest **submitted**, not best-scoring, attempt independently
for each skill. An all-skipped latest attempt remains unassessed. Other users'
records, unfinished attempts and unrelated skill claims cannot provide assessment
evidence for that skill. Projects and certifications remain unverified records.
No overall score is calculated by mixing these evidence types.

## Resource provenance

Links and topic relevance checked on 29 September 2026. These are curated links,
not a live course feed or endorsements of learning effectiveness. Course costs,
certification conditions and future availability are not guaranteed.

- [CS50 Python: functions](https://cs50.harvard.edu/python/weeks/0/),
  [loops and collections](https://cs50.harvard.edu/python/weeks/2/),
  [exceptions](https://cs50.harvard.edu/python/weeks/3/).
- [Python 3.13 control flow](https://docs.python.org/3.13/tutorial/controlflow.html),
  [data structures](https://docs.python.org/3.13/tutorial/datastructures.html),
  [exceptions](https://docs.python.org/3.13/tutorial/errors.html).
- [MDN guided client-server lesson](https://developer.mozilla.org/en-US/docs/Learn_web_development/Extensions/Server-side/First_steps/Client-Server_overview),
  [HTTP methods](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Methods),
  [status codes](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status),
  [HTTP overview](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Overview).
- [CS50 Web: API lesson section](https://cs50.harvard.edu/web/notes/5/#apis):
  supplementary API/JSON material; JavaScript familiarity helps. It is not a full
  REST design course and does not replace method/status references.
- HTTP answer-key reference: [RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html),
  especially methods, representation metadata and status definitions.

Practice tasks are original, ungraded exercises. Python/HTTP starters render as
text; SQL's existing `starter_sql` remains supported. No candidate code is executed.
Marking a task complete only records self-reported activity and never changes a
score or verifies improvement.

## Verification and Windows smoke check

Automated checks cover skill-scoped claims, cross-bank answer rejection, owner
isolation, per-skill latest evidence, snapshot immutability and roadmap semantics.
Existing SQL and live-job regression checks must continue to pass.

From the repository root:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s backend/tests -v
```

After restarting Flask, hard-refresh `/app` (Ctrl+F5). Use a test account:

1. Compare `Python, SQL and REST APIs are required for this backend role.` with
   keyword mode. If the test account has no attempts, all three cards offer an
   assessment action.
2. Assess Python, submit at least one wrong answer and leave another topic
   unanswered. Confirm the two needs have different labels in its roadmap.
3. Open a CS50/Python resource link. Mark a practice task complete; its assessment
   score must remain unchanged.
4. Return to the saved comparison, then compare with latest evidence. The new
   comparison includes the Python result while the original stays unchanged.
5. Select REST APIs on Overview; check its heading and HTTP resources. Existing
   SQL history and roadmaps must still open.

These are functional checks using test data, not research results or participant
outcomes. Keep test accounts and example attempts separate from research data.
