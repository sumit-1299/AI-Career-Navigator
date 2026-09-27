# Candidate assessment UI — first milestone

This milestone connects the existing SQL diagnostic API to a browser workspace.
It provides a demonstration interface for the research project. It is not a trained
proficiency model, a validated instrument, or evidence of research novelty.

## Run on Windows

From the repository root, with PostgreSQL running and `backend/.env` configured:

```powershell
.\.venv\Scripts\python.exe .\backend\app.py
```

Open **http://127.0.0.1:5000/app**. Keep the Flask terminal running.
The API home page remains at http://127.0.0.1:5000/.
No new Python dependencies, Node installation, frontend build, or database migration
are needed for this UI milestone.

Use an existing account whose credentials you know, or choose **Create account**.
The earlier CLI demo generates a random password and does not print it; create a
separate browser demo account rather than trying to recover that password.
For demonstrations, use a visibly named account such as `Demo Candidate` with an
`example.test` email address. Demo records must not enter the participant dataset.

## What a candidate can do

1. Create an account and sign in.
2. Optionally record a self-reported SQL rating between 1 and 10 before starting.
3. Start the six-question SQL foundations diagnostic.
4. Answer, skip, revisit, and change answers before submitting.
5. Review the answered/skipped counts in a confirmation dialog before submission.
6. Read saved results, topic feedback, the original claim snapshot, and explanations.
7. Reopen submitted results or continue unfinished attempts through My assessments.

The Overview shows recent attempts; My assessments shows up to 50 recent attempts,
matching the existing API limit. An unfinished attempt appears as Continue assessment.
Once all attempts are submitted, Overview offers Start SQL assessment again.

## What each result means

| Display | Meaning |
| --- | --- |
| Accuracy on answered questions | Correct answers divided by answered questions. All skipped is shown as **Not assessed**, not 0% accuracy. |
| Assessment coverage | Answered questions divided by assigned questions. |
| Incorrect answers | Questions answered incorrectly; these can suggest practice. |
| Unassessed questions | Skipped questions; they do not establish a skill deficit. |
| Self-report snapshot | The SQL claim(s) recorded when that attempt started, separate from the assessment result. |
| Topic guidance | Practice suggestions and requests for more evidence derived from the server's topic flags. |

The UI displays the API's scores. It never sends a claimed score, another candidate's
ID, or an answer key to the submission endpoint. Grading, ownership checks, immutable
submission, and question snapshots remain in the existing backend.

## Session and draft behaviour

- The access token stays in JavaScript memory for the current page. Credentials and
  answers are not written to cookies, localStorage, or sessionStorage by this UI.
- Reloading requires signing in again. Submitted results are fetched from the database.
- Unsubmitted answer selections stay in the open tab, including when navigating to
  Overview or history. Reloading, closing the tab, or signing out clears those selections.
  The started attempt remains on the server and can be reopened, with questions unanswered.
- A standard page-leave warning is requested if there are selected unsubmitted answers.
  Browser policies control whether that warning is displayed; it is not autosave.
- An expired session opens a same-account sign-in dialog. After successful sign-in, the
  pending request resumes and in-tab answers remain available. Cancelling leaves the
  answers in the tab and shows a message explaining how to retry.
- An interrupted submission may already have reached the server. View attempt history
  to check. If a repeated submission receives the API's `409` response, the UI retrieves
  and displays the saved result instead of replacing it.
- The initial SQL claim form is offered only when the account has no SQL claims. Existing
  claims are displayed, including duplicates already present in the database. Editing,
  deduplication and a broader skill taxonomy are separate work.

## Local verification

Run the existing backend regression suite in a second terminal:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s backend/tests -v
```

Expected: all tests end with **OK**. The original assessment suite has 11 tests;
the learning roadmap milestone adds 14 more. These tests use isolated SQLite, not your
PostgreSQL database. They do not create or remove accounts in your normal database.

For a controlled browser demonstration, create a demo account, save SQL self-rating
**7**, and use these deliberately mixed answers:

| Question | Selection |
| --- | --- |
| 1 | B |
| 2 | C |
| 3 | A |
| 4 | B |
| 5 | B |
| 6 | Skip |

Expected: **60%** accuracy, **83.33%** coverage, **2** incorrect and **1** unassessed.
There are 3 correct answers among the 5 answered questions. Joins suggests practice;
aggregation includes an unassessed question. The snapshot remains SQL **7/10**.
Open a feedback item, go to history, reopen the result, then sign out and sign in again
to verify persistence against your PostgreSQL installation.

Also useful for demonstrations: an all-skipped attempt should show **Not assessed**
accuracy, **0%** coverage, **0** incorrect and **6** unassessed. Do not present either
controlled example as a measured participant outcome.

### Implementation verification, 26 September 2026

The backend regression suite passed. An automated Chromium browser check against an
isolated SQLite test server covered registration, sign-in, saving the optional claim,
question navigation, mixed scoring, feedback, history, reload/sign-in persistence,
all-skipped results, account separation, escaped candidate names and mobile overflow.
The sign-in recovery check injected one expired-token HTTP response to exercise the UI
and used the real login endpoint to resume; it did not wait for a real token to expire.
These are software checks, not a participant study or PostgreSQL browser validation.

## Code map

| File | Responsibility |
| --- | --- |
| `backend/app.py` | Serves `/app` and its document security headers. Existing API routes remain available. |
| `backend/templates/workspace.html` | Page shell and accessible submit/sign-in dialogs. |
| `backend/static/workspace.css` | Desktop/mobile layout, keyboard focus, questions and result cards. |
| `backend/static/workspace.js` | Account forms, authenticated API requests, in-tab drafts, navigation and result rendering. |

All static assets are served from this Flask application. No CDN scripts or external
fonts are fetched. Dynamic text is escaped before insertion into HTML. The document
uses a Content Security Policy restricting scripts, styles and API calls to its own
origin. These safeguards do not constitute a production security audit.

The UI uses `/api/register`, `/api/login`, `/api/skills`, and the existing
`/api/assessments` endpoints documented in `SQL_ASSESSMENT.md`.

## Commit this milestone after the local check

Create branch `prajwal/assessment-ui` from your completed `prajwal/sql-assessment`
branch before applying the UI patch. After verifying the browser flow:

```powershell
git add backend/app.py backend/templates/workspace.html backend/static/workspace.css backend/static/workspace.js docs/ASSESSMENT_UI.md
git diff --cached --stat
git commit -m "Add candidate assessment workspace and results UI"
git push -u origin prajwal/assessment-ui
```

The change contains five files. Do not commit the downloaded patch itself or the private
`.env` file. Commit only completed work you have checked and can explain.

## Next project milestones

- The curated course catalogue, practical roadmap and self-reported activity tracking
  are now implemented; see `LEARNING_ROADMAP.md` for use and validation.
- Capture project and certification evidence with clear provenance and limitations.
- Extend beyond the fixed SQL baseline to job-targeted assessment selection and fresh
  practical evaluation tasks. Compare against fixed-assessment and self-report baselines.
- Add live job ingestion with source/timestamps, separated from frozen evaluation data.
- Run a consented pilot and report actual measurements. Do not infer validity, fairness,
  model accuracy, or learning gains from this demonstration UI.

References for the implementation approach:

- Flask templates: https://flask.palletsprojects.com/en/stable/tutorial/templates/
- Flask static assets: https://flask.palletsprojects.com/en/stable/tutorial/static/
- HTML dialogs: https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/dialog
