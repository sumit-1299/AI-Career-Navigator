# Live jobs: selected Greenhouse employer boards

This milestone connects public job postings to the existing keyword and semantic
comparison flow. It uses the pretrained model already installed. Downloading new
vacancies does **not** train or fine-tune a model.

## Run and demonstrate

No additional Python packages, API keys or model downloads are required for this
milestone. Keep the existing private `backend/.env` settings. Restart Flask so
`db.create_all()` creates the new `live_jobs` and `job_board_syncs` tables. Existing
tables do not require a schema alteration.

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s backend/tests -v
.\.venv\Scripts\python.exe .\backend\app.py
```

Open http://127.0.0.1:5000/app and press Ctrl+F5 to load the updated scripts.

1. Sign in and open **Live jobs**.
2. Click **Refresh Canonical**, then **Refresh Razorpay**. Each refresh requests
   that employer's current public board and stores the successfully parsed list.
3. Search for `Python` and optionally filter the location with `APAC` or
   `Worldwide`. Search examines the title and description; location is a literal
   substring filter. For Razorpay, try `Bengaluru`. Results depend on the current
   postings. There may be no junior or Pune-based opening in this small sample.
4. Open **View & compare**. Read the requirements, location and fetch timestamps.
   Use **Open employer posting** to check availability and eligibility directly.
5. Choose **Keywords + semantic suggestions**, then **Compare with my evidence**.
   The server saves the full extracted posting text, provenance and current
   candidate records, then displays the existing evidence-aware comparison.
6. Expand **Source and comparison method** to inspect source details. Saved
   comparisons remain available under **Compare a job**, including after a job
   changes or disappears from a board.
7. **Try keyword baseline** reopens the current cached posting with keyword mode
   selected. Review and save it. This action uses the current candidate profile
   and posting version; it is not a controlled evaluation on frozen identical
   inputs. Use the future evaluation harness for that experiment.

Semantic matching still covers ten curated backend skill concepts. SQL is the
only available diagnostic. Project/certificate entries remain unverified claims.
There is no overall suitability ranking, proficiency score, or hiring probability.
Listings are alphabetical; keyword/location filters do not establish eligibility.

## Data sources and scope

Configured employer tokens are in `backend/services/live_jobs.py`:

| Employer | Greenhouse board token | Public board |
| --- | --- | --- |
| Canonical | `canonical` | https://job-boards.greenhouse.io/canonical |
| Razorpay | `razorpaysoftwareprivatelimited` | https://job-boards.greenhouse.io/razorpaysoftwareprivatelimited |

The connector requests:

`GET https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true`

Greenhouse documents public GET endpoints without authentication and full job
content with `content=true`: https://docs.greenhouse.io/job-board.html

The application uses only this read endpoint. It never fetches a candidate-supplied
URL, submits an application or sends candidate information to Greenhouse. Employer
links open externally. Public access is not a blanket redistribution/training
license; review source terms before publishing a collected dataset or using it
for training. Do not commit fetched job bodies or candidate records to Git.

This is a bounded employer sample, not a complete job market or an India-only feed.
Check the employer's location, seniority, work authorization and remote-work
conditions. The `updated_at` provider field is labelled **Provider updated**; it
is not represented as the publication date. No date is inferred when it is absent.
General-interest/prospect posts (`internal_job_id: null`) are counted separately
and excluded from vacancy browsing.

## Refresh and cache behavior

- Opening/searching the page reads the database cache; it does not contact the
  provider. Refresh is manual, once per board per five minutes across accounts.
  There is no background scheduler in this milestone.
- Each board has separate last-attempt, last-success and failure status. A failed
  refresh keeps existing rows and the original last-seen timestamps. A cooldown
  response also avoids a provider request.
- A successful response must include a job list, matching `meta.total`, unique
  identifiers and valid supported fields. The entire board is validated before
  changes are committed. A malformed or incomplete response leaves the cache
  intact, with a visible failure message.
- Only absence from a complete successful board response marks a posting
  **No longer listed on this board**. That does not prove the role was filled.
  New comparisons of removed postings are blocked; old comparisons remain.
- Cache entries older than 24 hours are explicitly labelled. They can still be
  compared as cached descriptions; this condition is frozen into the comparison.
- Unchanged postings retain their version and receive a new last-seen timestamp.
  Changed normalized content, provider update date, removal or reappearance
  increments the version. The cache stores the latest version; saved comparisons
  preserve the earlier versions they used. This is not a complete posting-history
  archive between comparison events.
- Refresh holds a per-process lock and a PostgreSQL row lock. The row is reloaded
  after acquiring that lock, so a waiting worker sees the latest cooldown state.
  Use PostgreSQL for deployment; SQLite is used only for isolated tests here.
- Downloads have an 8-second socket timeout, a 12-second elapsed check between
  reads, a 15 MiB response cap and no redirects. A stalled read can extend elapsed
  time to the socket timeout. The browser allows 45 seconds for refresh/comparison.

## Comparison integrity

The browser submits only a posting UUID, expected version, request UUID and mode.
The server resolves the job text and source, rejects changed/removed postings,
and stores the following with the candidate snapshot and result:

- Employer, board token, provider posting ID and source URL.
- Full normalized plain-text description and location.
- Posting version, SHA-256 content hash, provider update date, last-seen timestamp
  and source-capture timestamp.
- Whether the cache was over 24 hours old at comparison time.
- Model/catalogue/policy settings already recorded by the matcher.

HTML is entity-decoded and parsed into plain text; script/style content is dropped.
The UI escapes all provider strings and never inserts upstream HTML. Source links
must pass the existing HTTPS URL validator. Formatting removal can change how a
posting reads; the employer link remains available for checking the original.

Live comparisons allow 300 fragments and descriptions up to 60,000 characters;
manual pasted comparisons retain their 8,000-character / 60-fragment limits. Every
accepted fragment is retained. Oversized inputs are rejected explicitly, never
silently truncated. The encoder also rejects token overflow. If a posting exceeds
these limits, use a labelled excerpt in **Compare a job**; that excerpt is recorded
as candidate-pasted text rather than mislabelled as the full live posting.

A repeated request UUID with the same posting/version/mode returns the originally
saved comparison, even if the posting later changes or is removed. Changed request
input is rejected. Comparisons remain private to the candidate; public cache rows
are shared across accounts. This milestone adds no candidate-data export route.

## API

All routes require a valid candidate account and return `Cache-Control: no-store`.

| Route | Behavior |
| --- | --- |
| `GET /api/jobs?q=&location=&board=&page=1` | Listed cached jobs, 20 per page, totals and board statuses |
| `POST /api/jobs/boards/<board>/refresh` with `{}` | `refreshed`, `cooldown` or `failed` outcome |
| `GET /api/jobs/<uuid>` | Full cached text and board status, including removed records |
| `POST /api/jobs/<uuid>/compare` | Body: `submission_id`, `job_version`, `mode`; saves owned comparison |

A handled provider failure returns HTTP 200 with `outcome: failed` and the saved
board error so the UI can continue showing cached data. Unknown boards return 404;
concurrent same-process refreshes return 409; database save failures return 503.
Comparison creation returns 201, idempotent retry 200, stale version/removal 409,
and model unavailability 503. Missing model dependencies never silently switch a
requested semantic run to keyword mode.

## Verification and next research work

The automated suite covers authentication, source validation, entity extraction,
complete-response checks, failed-refresh retention, cache freshness, removal and
reappearance, version changes, filtering/pagination, ownership, immutable snapshots,
interrupted-response retries and long-description limits. Provider responses in
unit tests are offline fixtures; routine tests do not call employers.

Before this patch was delivered, both live endpoints were fetched successfully,
and the application was checked in a real desktop/mobile browser with the local
ONNX model. These checks establish operation in the development environment, not
Windows/PostgreSQL deployment performance or matching quality.

Next: create independently reviewed job-skill labels and candidate-job examples,
freeze evaluation inputs, compare keyword and semantic baselines, and measure the
added value of assessment/evidence context. Keep development and held-out examples
separate. Verify the research gap against existing work before claiming novelty.
The report/paper should distinguish implemented functionality, measured results and
future work; live ingestion alone is not a research contribution.
