from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
import hashlib
import os
import secrets
import smtplib

from flask import Blueprint, current_app, request
from flask_jwt_extended import create_access_token
from werkzeug.security import generate_password_hash, check_password_hash

from extensions import db
from models.user import User
from models.password_reset_token import PasswordResetToken


auth_bp = Blueprint("auth", __name__, url_prefix="/api")


def _utc_now():
    return datetime.now(timezone.utc)


def _normalize_email(value):
    return (value or "").strip().lower()


def _hash_reset_token(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _reset_expiry_minutes():
    try:
        return max(5, int(os.getenv("RESET_TOKEN_MINUTES", "30")))
    except ValueError:
        return 30


def _base_url():
    configured = os.getenv("APP_BASE_URL", "").strip().rstrip("/")
    if configured:
        return configured
    return request.host_url.rstrip("/")


def _build_reset_url(raw_token):
    return f"{_base_url()}/app?reset_token={raw_token}"


def _mail_is_configured():
    return bool(
        os.getenv("MAIL_HOST", "").strip()
        and os.getenv("MAIL_FROM", "").strip()
    )


def _send_reset_email(user, reset_url):
    host = os.getenv("MAIL_HOST", "").strip()
    sender = os.getenv("MAIL_FROM", "").strip()
    username = os.getenv("MAIL_USERNAME", "").strip()
    password = os.getenv("MAIL_PASSWORD", "")

    try:
        port = int(os.getenv("MAIL_PORT", "587"))
    except ValueError:
        port = 587

    use_tls = os.getenv("MAIL_USE_TLS", "true").strip().lower() in {
        "1", "true", "yes", "on"
    }

    message = EmailMessage()
    message["Subject"] = "Reset your AI Career Navigator password"
    message["From"] = sender
    message["To"] = user.email
    message.set_content(
        "Hello,\n\n"
        "We received a request to reset your AI Career Navigator password.\n\n"
        f"Use this link to choose a new password:\n{reset_url}\n\n"
        f"This link expires in {_reset_expiry_minutes()} minutes and can only be used once.\n\n"
        "If you did not request this, you can ignore this email.\n"
    )

    with smtplib.SMTP(host, port, timeout=15) as smtp:
        smtp.ehlo()
        if use_tls:
            smtp.starttls()
            smtp.ehlo()
        if username:
            smtp.login(username, password)
        smtp.send_message(message)


def _debug_link_allowed():
    value = os.getenv("RESET_SHOW_DEBUG_LINK", "false").strip().lower()
    return current_app.debug or current_app.testing or value in {
        "1", "true", "yes", "on"
    }


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}

    name = (data.get("name") or "").strip()
    email = _normalize_email(data.get("email"))
    password = data.get("password") or ""

    if not name or not email or not password:
        return {
            "status": "error",
            "message": "Name, email and password are required"
        }, 400

    if len(password) < 8:
        return {
            "status": "error",
            "message": "Password must be at least 8 characters"
        }, 400

    existing_user = User.query.filter_by(email=email).first()

    if existing_user:
        return {
            "status": "error",
            "message": "Email already registered"
        }, 409

    user = User(
        name=name,
        email=email,
        password_hash=generate_password_hash(password)
    )

    db.session.add(user)
    db.session.commit()

    return {
        "status": "success",
        "message": "User registered successfully",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email
        }
    }, 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}

    email = _normalize_email(data.get("email"))
    password = data.get("password") or ""

    if not email or not password:
        return {
            "status": "error",
            "message": "Email and password are required"
        }, 400

    user = User.query.filter_by(email=email).first()

    if not user or not check_password_hash(user.password_hash, password):
        return {
            "status": "error",
            "message": "Invalid email or password"
        }, 401

    access_token = create_access_token(identity=str(user.id))

    return {
        "status": "success",
        "message": "Login successful",
        "access_token": access_token,
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email
        }
    }, 200


@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    data = request.get_json(silent=True) or {}
    email = _normalize_email(data.get("email"))

    generic_response = {
        "status": "success",
        "message": "If an account exists for that email, a password reset link has been prepared."
    }

    if not email:
        return {
            "status": "error",
            "message": "Email is required"
        }, 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return generic_response, 200

    now = _utc_now()
    PasswordResetToken.query.filter(
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.used_at.is_(None),
    ).update({PasswordResetToken.used_at: now}, synchronize_session=False)

    raw_token = secrets.token_urlsafe(48)
    record = PasswordResetToken(
        user_id=user.id,
        token_hash=_hash_reset_token(raw_token),
        expires_at=now + timedelta(minutes=_reset_expiry_minutes()),
    )
    db.session.add(record)
    db.session.commit()

    reset_url = _build_reset_url(raw_token)

    if _mail_is_configured():
        try:
            _send_reset_email(user, reset_url)
        except Exception:
            current_app.logger.exception("Password reset email delivery failed")
    elif _debug_link_allowed():
        generic_response["debug_reset_url"] = reset_url

    return generic_response, 200


@auth_bp.route("/reset-password", methods=["POST"])
def reset_password():
    data = request.get_json(silent=True) or {}
    raw_token = (data.get("token") or "").strip()
    password = data.get("password") or ""

    if not raw_token or not password:
        return {
            "status": "error",
            "message": "Reset token and password are required"
        }, 400

    if len(password) < 8:
        return {
            "status": "error",
            "message": "Password must be at least 8 characters"
        }, 400

    now = _utc_now()
    token_record = PasswordResetToken.query.filter_by(
        token_hash=_hash_reset_token(raw_token)
    ).first()

    expires_at = token_record.expires_at if token_record is not None else None
    if expires_at is not None and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if (
        token_record is None
        or token_record.used_at is not None
        or expires_at <= now
    ):
        return {
            "status": "error",
            "message": "This reset link is invalid or has expired"
        }, 400

    user = User.query.get(token_record.user_id)
    if user is None:
        return {
            "status": "error",
            "message": "This reset link is invalid or has expired"
        }, 400

    user.password_hash = generate_password_hash(password)
    token_record.used_at = now

    PasswordResetToken.query.filter(
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.id != token_record.id,
        PasswordResetToken.used_at.is_(None),
    ).update({PasswordResetToken.used_at: now}, synchronize_session=False)

    db.session.commit()

    return {
        "status": "success",
        "message": "Password updated successfully. You can now sign in."
    }, 200
