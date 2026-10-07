"""Owner-scoped resume editing, extraction preview and optimistic updates."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.exc import StaleDataError
from werkzeug.exceptions import RequestEntityTooLarge

from extensions import db
from models.assessment_attempt import utc_now
from models.candidate_resume import CandidateResume
from routes.assessments import current_user_id, error
from services.resume_evidence import analyze_resume
from services.resume_parser import MAX_FILE, MAX_TEXT
from services.skill_catalog import SKILLS

resume_bp = Blueprint("resume", __name__, url_prefix="/api/resume")


@resume_bp.before_request
@jwt_required()
def account_required():
    request.max_content_length = MAX_FILE + 65536
    if current_user_id() is None:
        return error("The candidate account is unavailable. Log in again.", 401)


@resume_bp.after_request
def private_response(response):
    response.headers["Cache-Control"] = "no-store"
    return response


@resume_bp.errorhandler(RequestEntityTooLarge)
def too_large(_):
    return error("Choose a resume file up to 2 MB.", 413)


def payload(record):
    return {"status": "success", "version": record.version if record else 0,
            "resume": record.to_dict() if record and record.text else None,
            "analysis": analyze_resume(record.text if record else ""),
            "catalogue": [{"key": s["key"], "label": s["label"]} for s in SKILLS]}


@resume_bp.route("", methods=["GET", "PUT", "DELETE"])
def resume():
    user_id = current_user_id()
    record = db.session.get(CandidateResume, user_id)
    if request.method == "GET":
        return payload(record)
    body = request.get_json(silent=True)
    fields = {"version"} if request.method == "DELETE" else {"version", "text", "source_name"}
    if not isinstance(body, dict) or set(body) != fields or type(body.get("version")) is not int:
        return error("Send the current version and the expected resume fields.", 400)
    if body["version"] != (record.version if record else 0):
        return error("Your resume changed in another request. Reload the saved resume before editing again.", 409)
    text, name = "", ""
    if request.method == "PUT":
        text, name = body["text"], body["source_name"]
        if not isinstance(text, str) or not 40 <= len(text.strip()) <= MAX_TEXT or "\x00" in text:
            return error("Enter 40–30,000 characters of resume text.", 400)
        if not isinstance(name, str) or not 1 <= len(name.strip()) <= 160 or any(ord(c) < 32 for c in name):
            return error("Provide a short resume name, up to 160 characters.", 400)
        text = text.strip()
        name = name.replace("\\", "/").rsplit("/", 1)[-1].strip()
        if not name:
            return error("Provide a resume name.", 400)
    if record is None:
        if request.method == "DELETE":
            return payload(None)
        record = CandidateResume(user_id=user_id)
        db.session.add(record)
    record.text, record.source_name = text, name
    record.content_hash = hashlib.sha256(text.encode()).hexdigest()
    record.updated_at = utc_now()
    try:
        db.session.commit()
    except (StaleDataError, SQLAlchemyError):
        db.session.rollback()
        return error("The resume could not be saved. Reload the saved version before retrying.", 409)
    return payload(record)


@resume_bp.post("/extract")
def extract():
    if set(request.files) != {"file"} or request.form or len(request.files.getlist("file")) != 1:
        return error("Upload one file in the file field.", 400)
    uploaded = request.files["file"]
    name = (uploaded.filename or "resume").replace("\\", "/").rsplit("/", 1)[-1]
    suffix = Path(name).suffix.lower()
    if suffix not in {".pdf", ".docx", ".txt"}:
        return error("Choose PDF, DOCX or TXT, or paste your resume text.", 400)
    data = uploaded.stream.read(MAX_FILE + 1)
    if not data or len(data) > MAX_FILE:
        return error("Choose a nonempty resume file up to 2 MB.", 400)
    try:
        child = subprocess.run([sys.executable, "-I", str(Path(__file__).resolve().parents[1] / "services" / "resume_parser.py"), suffix],
                               input=data, capture_output=True, timeout=10, check=True)
        result = json.loads(child.stdout)
    except (subprocess.SubprocessError, ValueError, OSError):
        return error("This file could not be read within the limit. Paste the resume text instead.", 400)
    if "error" in result:
        return error(result["error"], 400)
    return {"status": "success", "text": result["text"], "source_name": name[:160],
            "saved": False, "message": "Text extracted. Review it and choose Save resume. The original file is not stored."}
