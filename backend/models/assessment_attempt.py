"""A candidate's assigned questions and immutable submitted result."""

from datetime import datetime, timezone
from uuid import uuid4

from extensions import db
from services.sql_assessment import public_questions


def utc_now():
    return datetime.now(timezone.utc)


def iso_utc(value):
    if value is None:
        return None
    # SQLite test databases return naive timestamps; values are stored as UTC.
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


class AssessmentAttempt(db.Model):
    __tablename__ = "assessment_attempts"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    skill_key = db.Column(db.String(40), nullable=False)
    assessment_version = db.Column(db.String(80), nullable=False)
    question_snapshot = db.Column(db.JSON, nullable=False)
    self_reported_claims = db.Column(db.JSON, nullable=False)
    answers = db.Column(db.JSON, nullable=True)
    result = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utc_now)
    submitted_at = db.Column(db.DateTime(timezone=True), nullable=True)

    def to_dict(self, include_questions=True):
        payload = {
            "id": self.id, "skill_key": self.skill_key,
            "assessment_version": self.assessment_version,
            "assessment": self.question_snapshot["metadata"],
            "status": "submitted" if self.submitted_at else "in_progress",
            "created_at": iso_utc(self.created_at), "submitted_at": iso_utc(self.submitted_at),
            "self_reported_claims": self.self_reported_claims,
            "result": self.result,
        }
        if include_questions:
            payload["questions"] = public_questions(self.question_snapshot["questions"])
        return payload
