"""Candidate submissions, kept separate from assessed performance."""

from uuid import uuid4

from extensions import db
from models.assessment_attempt import iso_utc, utc_now


class CandidateEvidence(db.Model):
    __tablename__ = "candidate_evidence"
    __table_args__ = (
        db.UniqueConstraint("user_id", "submission_id", name="uq_evidence_submission"),
    )

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    submission_id = db.Column(db.String(36), nullable=False)
    details = db.Column(db.JSON, nullable=False)
    version = db.Column(db.Integer, nullable=False, default=1)
    archived = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utc_now)

    def to_dict(self):
        return {
            **self.details, "id": self.id, "version": self.version,
            "archived": self.archived, "source": "candidate_submission",
            "verification_status": "unverified",
            "created_at": iso_utc(self.created_at),
            "updated_at": iso_utc(self.updated_at),
        }
