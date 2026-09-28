"""Shared public postings; personal comparisons remain owned by their candidate."""

from uuid import uuid4
from extensions import db
from models.assessment_attempt import iso_utc, utc_now


class JobBoardSync(db.Model):
    __tablename__ = "job_board_syncs"
    board = db.Column(db.String(100), primary_key=True)
    last_attempt_at = db.Column(db.DateTime(timezone=True))
    last_success_at = db.Column(db.DateTime(timezone=True))
    last_error = db.Column(db.String(300))
    listed_count = db.Column(db.Integer, nullable=False, default=0)
    prospect_count = db.Column(db.Integer, nullable=False, default=0)


class LiveJob(db.Model):
    __tablename__ = "live_jobs"
    __table_args__ = (db.UniqueConstraint("board", "provider_id", name="uq_live_job_source"),)
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    board = db.Column(db.String(100), nullable=False, index=True)
    provider_id = db.Column(db.String(40), nullable=False)
    title = db.Column(db.String(500), nullable=False)
    location = db.Column(db.String(1000), nullable=False)
    description = db.Column(db.Text, nullable=False)
    source_url = db.Column(db.String(2048), nullable=False)
    provider_updated_at = db.Column(db.String(60))
    content_hash = db.Column(db.String(64), nullable=False)
    version = db.Column(db.Integer, nullable=False, default=1)
    listed = db.Column(db.Boolean, nullable=False, default=True, index=True)
    first_seen_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utc_now)
    last_seen_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utc_now)
    last_checked_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utc_now)

    def to_dict(self, full=False):
        from services.live_jobs import BOARDS, is_stale
        data = {"id": self.id, "provider": "greenhouse", "board": self.board,
                "employer": BOARDS[self.board], "provider_id": self.provider_id,
                "title": self.title, "location": self.location, "source_url": self.source_url,
                "provider_updated_at": self.provider_updated_at, "version": self.version,
                "listed": self.listed, "first_seen_at": iso_utc(self.first_seen_at),
                "last_seen_at": iso_utc(self.last_seen_at), "last_checked_at": iso_utc(self.last_checked_at),
                "stale": is_stale(self.last_seen_at)}
        if full:
            data.update(description=self.description, content_hash=self.content_hash)
        return data
