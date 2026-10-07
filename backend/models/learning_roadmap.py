"""A stable recommendation snapshot and separate, self-reported activity log."""

from uuid import uuid4

from extensions import db
from models.assessment_attempt import iso_utc, utc_now


class LearningRoadmap(db.Model):
    __tablename__ = "learning_roadmaps"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    attempt_id = db.Column(
        db.String(36), db.ForeignKey("assessment_attempts.id", ondelete="CASCADE"),
        nullable=False, unique=True,
    )
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    snapshot = db.Column(db.JSON, nullable=False)
    progress = db.Column(db.JSON, nullable=False, default=dict)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utc_now)

    def to_dict(self):
        completed = sum(
            self.progress.get(step["id"], {}).get("completed") is True
            for step in self.snapshot["steps"]
        )
        return {
            "id": self.id, "attempt_id": self.attempt_id,
            "created_at": iso_utc(self.created_at), "snapshot": self.snapshot,
            "self_reported_progress": self.progress,
            "completed_count": completed, "step_count": len(self.snapshot["steps"]),
        }
