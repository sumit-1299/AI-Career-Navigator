"""An immutable job input, candidate snapshot and comparison result."""

from uuid import uuid4
from extensions import db
from models.assessment_attempt import iso_utc, utc_now


class JobComparison(db.Model):
    __tablename__ = "job_comparisons"
    __table_args__ = (db.UniqueConstraint("user_id", "submission_id", name="uq_job_comparison_submission"),)
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    submission_id = db.Column(db.String(36), nullable=False)
    job = db.Column(db.JSON, nullable=False)
    candidate_snapshot = db.Column(db.JSON, nullable=False)
    result = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utc_now)

    def to_dict(self, full=True):
        result = {"id": self.id, "title": self.job["title"], "created_at": iso_utc(self.created_at),
                  "mode": self.result["mode"], "summary": self.result["summary"]}
        if full:
            result.update(job=self.job, candidate_snapshot=self.candidate_snapshot, result=self.result)
        return result
