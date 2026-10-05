"""
UserLearningProgress Model for AI Career Navigator.

Tracks a student's persistent progress through learning resources connected to canonical skills.
Prevents duplicate progress records and records completion milestones for skill proficiency progression.
"""

from datetime import datetime
from extensions import db


class UserLearningProgress(db.Model):
    __tablename__ = "user_learning_progress"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    learning_resource_id = db.Column(
        db.Integer,
        db.ForeignKey("learning_resources.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    canonical_skill_id = db.Column(
        db.Integer,
        db.ForeignKey("canonical_skills.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    status = db.Column(
        db.String(50),
        nullable=False,
        default="In Progress"
    )  # "In Progress", "Completed", "Not Started", "Abandoned"

    progress_percentage = db.Column(
        db.Float,
        nullable=False,
        default=0.0
    )

    notes = db.Column(
        db.Text,
        nullable=True
    )

    started_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=True
    )

    completed_at = db.Column(
        db.DateTime,
        nullable=True
    )

    last_updated = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Relationships
    user = db.relationship(
        "User",
        backref=db.backref("learning_progress", lazy="select", cascade="all, delete-orphan")
    )

    learning_resource = db.relationship(
        "LearningResource",
        backref=db.backref("user_progress", lazy="select", cascade="all, delete-orphan")
    )

    canonical_skill = db.relationship(
        "CanonicalSkill",
        backref=db.backref("learning_progress", lazy="select")
    )

    __table_args__ = (
        db.UniqueConstraint("user_id", "learning_resource_id", name="uq_user_learning_resource"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "learning_resource_id": self.learning_resource_id,
            "canonical_skill_id": self.canonical_skill_id,
            "status": self.status,
            "progress_percentage": round(self.progress_percentage, 1),
            "notes": self.notes,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
            "resource": {
                "title": self.learning_resource.title,
                "resource_type": self.learning_resource.resource_type,
                "provider": self.learning_resource.provider,
                "difficulty_level": self.learning_resource.difficulty_level,
                "url": self.learning_resource.url,
            } if self.learning_resource else None,
            "skill": {
                "canonical_name": self.canonical_skill.canonical_name,
                "skill_type": self.canonical_skill.skill_type,
            } if self.canonical_skill else None,
        }

    def __repr__(self):
        return f"<UserLearningProgress user={self.user_id} resource={self.learning_resource_id} status={self.status}>"
