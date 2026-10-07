# Live Tech Jobs 500 Error Fix

## Cause

The multi-provider live-job upgrade fetched sources through `ThreadPoolExecutor` and attempted to use Flask's `current_app.logger` from inside a worker thread. Flask's application context is request-local, so the worker raised:

`RuntimeError: Working outside of application context.`

## Fix

`routes/jobs.py` now captures `current_app.logger` in the request thread and passes that logger object into each worker. The worker never accesses `current_app` directly.

The same replacement also keeps the public multi-provider flow:
- Greenhouse
- Ashby
- Lever
- technology-only filtering
- location, work mode, experience and technology filters
- live posting retrieval
- immutable comparison snapshots

## Replace

- `backend/routes/jobs.py`
- `backend/services/live_jobs.py`
- `backend/tests/test_live_jobs.py`

Then run:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s backend/tests -v
```

Start the app:

```powershell
.\.venv\Scripts\python.exe .\backend\app.py
```

Then sign in and open **Find Tech Jobs**.
