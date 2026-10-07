r"""Configure this project's local PostgreSQL account from backend/.env.

From the repository root on Windows:
    .\.venv\Scripts\python.exe .\backend\scripts\configure_local_db.py

Only the local career_app role and ai_career_navigator database are targeted.
An existing role's password is updated; a missing role/database is created.
Existing database contents and the .env file are not modified.
"""

from contextlib import closing
from getpass import getpass
import os
from pathlib import Path
import sys

import psycopg2
from psycopg2 import sql
from psycopg2.extensions import encrypt_password
from dotenv import dotenv_values
from sqlalchemy.engine import make_url


APP_USER = "career_app"
APP_DATABASE = "ai_career_navigator"
ENV_FILE = Path(__file__).resolve().parents[1] / ".env"


def read_settings(env_file=ENV_FILE):
    """Read and validate configuration without printing its secret values."""
    if not env_file.is_file():
        raise ValueError("Create backend/.env before running this helper.")
    raw_url = dotenv_values(env_file).get("DATABASE_URL")
    if not raw_url:
        raise ValueError("DATABASE_URL is missing from backend/.env.")
    try:
        url = make_url(raw_url)
        port = url.port or 5432
    except Exception:
        raise ValueError("DATABASE_URL in backend/.env is not a valid URL.") from None

    if url.drivername not in ("postgresql", "postgresql+psycopg2"):
        raise ValueError("DATABASE_URL must use postgresql+psycopg2.")
    if url.host not in ("127.0.0.1", "localhost", "::1"):
        raise ValueError("This helper only supports a local PostgreSQL server.")
    if not 1 <= port <= 65535:
        raise ValueError("DATABASE_URL contains an invalid port.")
    if url.username != APP_USER or url.database != APP_DATABASE:
        raise ValueError(
            "Expected user career_app and database ai_career_navigator in DATABASE_URL."
        )
    if url.query:
        raise ValueError("Use the simple DATABASE_URL from the setup instructions.")
    placeholders = {
        "YOUR_APP_PASSWORD", "PASTE_APP_DB_PASSWORD_HERE", "YOUR_APP_DB_PASSWORD"
    }
    if not url.password or url.password in placeholders:
        raise ValueError("Replace the password placeholder in backend/.env.")
    if url.password.startswith("APP_DB_PASSWORD="):
        raise ValueError("Use only the password value, without APP_DB_PASSWORD=.")
    return url, raw_url


def configure_account(url, admin_password):
    """Use administrator access only for this local development setup."""
    with closing(psycopg2.connect(
        host=url.host, port=url.port or 5432, dbname="postgres",
        user="postgres", password=admin_password, connect_timeout=5,
    )) as admin:
        admin.autocommit = True  # CREATE DATABASE cannot run in a transaction.
        with admin.cursor() as cursor:
            cursor.execute(
                "SELECT rolsuper, rolcreatedb, rolcreaterole, rolreplication, "
                "rolbypassrls FROM pg_roles WHERE rolname = %s", (APP_USER,),
            )
            role = cursor.fetchone()
            if role is not None and any(role):
                raise ValueError("career_app has elevated privileges; review it manually.")

            cursor.execute(
                "SELECT pg_get_userbyid(datdba) FROM pg_database WHERE datname = %s",
                (APP_DATABASE,),
            )
            database = cursor.fetchone()
            if database is not None and database[0] != APP_USER:
                raise ValueError(
                    "The existing database is not owned by career_app. "
                    "No password was changed; review database ownership first."
                )

            # Pass a SCRAM verifier to SQL, rather than the plaintext password.
            verifier = encrypt_password(
                url.password, APP_USER, scope=admin, algorithm="scram-sha-256"
            )
            if role is None:
                cursor.execute(
                    sql.SQL("CREATE ROLE {} LOGIN PASSWORD %s").format(
                        sql.Identifier(APP_USER)
                    ), (verifier,),
                )
            else:
                cursor.execute(
                    sql.SQL("ALTER ROLE {} LOGIN PASSWORD %s").format(
                        sql.Identifier(APP_USER)
                    ), (verifier,),
                )

            if database is None:
                cursor.execute(
                    sql.SQL("CREATE DATABASE {} OWNER {}").format(
                        sql.Identifier(APP_DATABASE), sql.Identifier(APP_USER)
                    )
                )


def verify_login(url):
    with closing(psycopg2.connect(
        host=url.host, port=url.port or 5432, dbname=APP_DATABASE,
        user=APP_USER, password=url.password, connect_timeout=5,
    )) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT current_user, current_database()")
            if cursor.fetchone() != (APP_USER, APP_DATABASE):
                raise ValueError("The connection did not use the expected user/database.")


def main():
    stage = "configuration check"
    try:
        url, raw_url = read_settings()
        print("This will configure local career_app using backend/.env.")
        print("Enter the postgres password chosen during PostgreSQL installation.")
        admin_password = getpass("PostgreSQL administrator password (hidden): ")
        if not admin_password:
            raise ValueError("The administrator password was empty. Run the helper again.")
        stage = "administrator connection / account setup"
        configure_account(url, admin_password)
        del admin_password
        stage = "application login test"
        verify_login(url)
    except ValueError as error:
        print(f"STOPPED: {error}")
        return 1
    except psycopg2.Error as error:
        # Avoid tracebacks, SQL text and connection URLs in screenshot output.
        print(f"FAILED during {stage}.")
        print(f"Database error code: {error.pgcode or 'connection error'}")
        if isinstance(error, psycopg2.OperationalError):
            print("Check that PostgreSQL is running and the entered password is correct.")
        else:
            print("Share this stage and error code for the next troubleshooting step.")
        return 1
    except (EOFError, KeyboardInterrupt):
        print("\nCancelled.")
        return 1

    print("SUCCESS: career_app connected to ai_career_navigator.")
    if os.environ.get("DATABASE_URL") not in (None, raw_url):
        print("Your terminal DATABASE_URL differs from backend/.env.")
        print("Before starting Flask in this PowerShell terminal, run:")
        print("Remove-Item Env:DATABASE_URL")
    print(r"Start Flask: .\.venv\Scripts\python.exe .\backend\app.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
