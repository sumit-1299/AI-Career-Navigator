# Local backend setup on Windows

This guide runs the existing Flask backend with a local PostgreSQL database.
Run PowerShell commands from the root of the cloned AI-Career-Navigator repository.

## Verified development setup

On 26 September 2026, Prajwal verified the following on his Windows computer:

- Python 3.13.7 in the project's `.venv`.
- Dependencies installed from `backend/requirements.txt`; `pip check` passed.
- PostgreSQL 18 with application role `career_app` and database `ai_career_navigator`.
- `configure_local_db.py` successfully authenticated as the application role.
- Flask started at `http://127.0.0.1:5000`.
- The server returned HTTP 200 for `/` and `/db-test`.

These checks establish backend startup and database connectivity. Application
features need their own checks as development continues. The model, assessments,
roadmaps and candidate UI are separate implementation milestones.

## 1. Install prerequisites

Install Python, Git and PostgreSQL. Python 3.13.7 and PostgreSQL 18 were used in the
verified setup above; other combinations have not been verified by this guide.

Use the [official PostgreSQL Windows installer](https://www.postgresql.org/download/windows/).
Select PostgreSQL Server, pgAdmin 4 and Command Line Tools. Keep port `5432` if
available and store the installation password privately. That password belongs
to the PostgreSQL administrator account, `postgres`.

Check the installation:

```powershell
python --version
Get-Service -Name "*postgres*" -ErrorAction SilentlyContinue
```

The PostgreSQL service should be running. No output from the service command
means it found no matching Windows service; it does not detect every possible
installation method.

## 2. Install Python dependencies

Create the environment on a fresh checkout:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r .\backend\requirements.txt
.\.venv\Scripts\python.exe -m pip check
```

The final command should report `No broken requirements found.` These commands
use the environment's Python directly; activation is optional.

In VS Code, use **Python: Select Interpreter** and select
`.venv\Scripts\python.exe`.

## 3. Configure local secrets

For a fresh checkout, copy `backend/.env.example` to `backend/.env`. If `.env`
already exists, edit it rather than replacing its existing settings.

Generate two independent values locally:

```powershell
.\.venv\Scripts\python.exe -c "import secrets; print('APP_DB_PASSWORD=' + secrets.token_urlsafe(24)); print('JWT_SECRET_KEY=' + secrets.token_hex(32))"
```

In `backend/.env`, replace `PASTE_APP_DB_PASSWORD_HERE` with only the generated
application password, without the `APP_DB_PASSWORD=` label. Replace
`PASTE_JWT_SECRET_KEY_HERE` with the generated token-signing secret. Save the file.

The generated application password uses URL-safe characters. A different
password containing reserved URL characters would need URL encoding before
being placed in `DATABASE_URL`.

The existing `backend/config.py` reads `DATABASE_URL` and `JWT_SECRET_KEY`.
Keep the administrator password separate; the application connects as `career_app`.

Confirm that Git ignores the private configuration:

```powershell
git check-ignore backend/.env
```

Expected output: `backend/.env`. Commit the placeholder-only `.env.example`,
not the private `.env` or generated password output.

## 4. Configure the application account

```powershell
.\.venv\Scripts\python.exe .\backend\scripts\configure_local_db.py
```

At the prompt, enter the `postgres` administrator password chosen during
PostgreSQL installation. Input is hidden.

The helper:

- Reads the application password from `backend/.env` without displaying it.
- Restricts the target to a local server, role `career_app` and database
  `ai_career_navigator`.
- Creates the application role/database if missing, or updates the existing
  application role's password to match `.env`.
- Preserves existing database contents and the `.env` file.
- Refuses unexpected elevated role privileges or a database owned by another role.
- Tests a connection as `career_app` after configuration.

Expected result:

```text
SUCCESS: career_app connected to ai_career_navigator.
```

This is a local development administration helper. Rerunning it reapplies the
password currently specified in `.env`; use the existing settings consistently.

If the helper detects a conflicting `DATABASE_URL` in the current terminal,
follow its displayed PowerShell instruction before starting Flask. This removes
the conflicting value from that terminal process, allowing `.env` to supply it.

## 5. Start and check Flask

```powershell
.\.venv\Scripts\python.exe .\backend\app.py
```

Keep the terminal running. The current app creates its defined database tables
on startup using `db.create_all()`; this is not a schema migration workflow.

Open these URLs:

| URL | Expected result |
| --- | --- |
| `http://127.0.0.1:5000/` | HTTP 200 and `AI Career Navigator API is running!` |
| `http://127.0.0.1:5000/db-test` | HTTP 200, `status: success`, and `PostgreSQL connection successful!` |

The built-in Flask server is used here for local development. A browser request
for `/favicon.ico` may return 404 because an icon has not been provided; it does
not indicate a failure of the API checks above.

Stop the server with **Ctrl+C** when finished. Start it again using the same command.

## Troubleshooting

| Symptom | Next action |
| --- | --- |
| Password authentication failed for `career_app` | Save the intended password in `.env`, then run the helper to apply and verify it. |
| Helper fails at administrator connection/account setup | Confirm the PostgreSQL service is running and enter the installation password for `postgres`. |
| Helper reports a missing password or placeholder | Replace the placeholder in `backend/.env`, save, and rerun. |
| Helper succeeds but Flask uses different credentials | Check the helper's message about a terminal `DATABASE_URL` overriding `.env`. |
| Helper reports unexpected database ownership or role privileges | Review the existing local database configuration before changing privileges. |
| `psql` is not recognised as a command | This helper uses Python's installed PostgreSQL driver and does not require `psql` on PATH. |

For a diagnostic screenshot, show the helper's status or error code rather than
the `.env` contents or generated secret values.

## Contribution record

This setup milestone adds a repeatable local database helper, an environment
template and Windows setup instructions. The helper was prepared with Codex
assistance and run successfully by Prajwal against his local database.

Related files:

- `backend/scripts/configure_local_db.py`
- `backend/.env.example`
- `docs/LOCAL_SETUP.md`
