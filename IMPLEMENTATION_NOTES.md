# Multi-provider live tech job upgrade

## Replace these project files

- `backend/services/live_jobs.py`
- `backend/routes/jobs.py`
- `backend/static/jobs.js`
- `backend/static/alignment.js`
- `backend/static/alignment.css`
- `backend/templates/workspace.html` is already compatible with the current alignment layer; keep your existing file if it contains the same script/style includes.
- `backend/tests/test_live_jobs.py`
- `docs/LIVE_JOBS.md`

## What changed

The live job layer now supports Greenhouse, Ashby and Lever public posting feeds. The frontend keeps the scope explicitly tech-only and supports role, location, technology, work-mode, experience and employer filters.

`provider_id` is no longer assumed to be numeric, so Ashby/Lever UUID-style identifiers can be opened and compared.

The saved comparison snapshot records the provider type (`greenhouse`, `ashby`, or `lever`) but does not change the evidence policy or create a hiring score.

## Verification

Run:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s backend/tests -v
```

Then start the server:

```powershell
.\.venv\Scripts\python.exe .\backend\app.py
```

Open **Find Tech Jobs** and verify that:

1. multiple live sources appear;
2. Notion/Vercel/Linear/Ramp and Lever sources appear when their public feeds are reachable;
3. obvious nontechnical jobs do not appear in the search results;
4. location filtering works;
5. technology filtering works;
6. opening an Ashby or Lever role works;
7. comparison produces an immutable snapshot;
8. the Apply button opens the employer's current public job page.

Provider availability may vary. An unavailable source is shown as unavailable rather than serving stale data.
