import os
from pathlib import Path

from dotenv import load_dotenv


# Load backend/.env explicitly, regardless of the directory from which
# the application is started.
BACKEND_DIR = Path(__file__).resolve().parent
load_dotenv(BACKEND_DIR / ".env")

# Also allow a repository-root .env when one exists.
load_dotenv()


class Config:
    ENV = os.getenv("FLASK_ENV", "production")
    DEBUG = os.getenv("FLASK_DEBUG", "False").lower() in ("true", "1", "yes")

    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JWT_SECRET_KEY = os.getenv(
        "JWT_SECRET_KEY",
        "default-dev-jwt-secret-replace-in-production"
    )

    # CORS configuration
    CORS_ORIGINS = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "*").split(",")
        if origin.strip()
    ]

    # Password reset configuration
    APP_BASE_URL = os.getenv("APP_BASE_URL", "http://127.0.0.1:5000")
    RESET_TOKEN_MINUTES = int(os.getenv("RESET_TOKEN_MINUTES", "30"))
    RESET_SHOW_DEBUG_LINK = (
        os.getenv("RESET_SHOW_DEBUG_LINK", "false")
        .lower() in ("true", "1", "yes")
    )

    # SMTP configuration
    MAIL_HOST = os.getenv("MAIL_HOST", "")
    MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
    MAIL_FROM = os.getenv("MAIL_FROM", "")
    MAIL_USE_TLS = (
        os.getenv("MAIL_USE_TLS", "true")
        .lower() in ("true", "1", "yes", "on")
    )


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "TEST_DATABASE_URL",
        "sqlite:///:memory:"
    )