# Live job load timeout fix

Replace these files:

- `backend/static/jobs-timeout-fix.js` with `AI_Career_Navigator_Job_Load_Fix.js`
- `backend/templates/workspace.html` with `AI_Career_Navigator_Job_Load_Fix_workspace.html`

The fix leaves the existing multi-provider `jobs.js` untouched and raises only the live job list request timeout from the generic 15 seconds to 45 seconds.

This addresses the visible "server could not be reached in time" notice while `/api/jobs` continues working and eventually returns HTTP 200.

After replacement:

1. Stop Flask: `Ctrl + C`
2. Start it again:
   `\.venv\Scripts\python.exe .\backend\app.py`
3. Hard refresh Chrome: `Ctrl + Shift + R`
