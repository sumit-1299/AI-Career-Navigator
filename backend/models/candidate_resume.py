"""One editable resume per account; comparisons retain their own text snapshot."""
from extensions import db
from models.assessment_attempt import iso_utc, utc_now


class CandidateResume(db.Model):
    __tablename__ = "candidate_resumes"
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    text = db.Column(db.Text, nullable=False)
    source_name = db.Column(db.String(160), nullable=False)
    content_hash = db.Column(db.String(64), nullable=False)
    version = db.Column(db.Integer, nullable=False, default=1)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utc_now)
    __mapper_args__ = {"version_id_col": version}

    def to_dict(self):
        return {"text": self.text, "source_name": self.source_name,
                "content_hash": self.content_hash, "version": self.version,
                "updated_at": iso_utc(self.updated_at), "verification_status": "unverified"}
