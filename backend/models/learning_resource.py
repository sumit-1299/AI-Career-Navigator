"""
LearningResource Model for AI Career Navigator.

Connects canonical skills to curated learning resources such as
courses, documentation, tutorials, certifications, and projects.
"""

from datetime import datetime
from extensions import db


class LearningResource(db.Model):
    __tablename__ = "learning_resources"

    id = db.Column(db.Integer, primary_key=True)

    canonical_skill_id = db.Column(
        db.Integer,
        db.ForeignKey("canonical_skills.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    title = db.Column(
        db.String(250),
        nullable=False
    )

    resource_type = db.Column(
        db.String(50),
        nullable=False
    )  # e.g., Course, Tutorial, Documentation, Certification, Project, Practice Platform, Book

    provider = db.Column(
        db.String(100),
        nullable=False
    )  # e.g., AWS, Coursera, FreeCodeCamp, Cisco, Official Docs

    url = db.Column(
        db.Text,
        nullable=False
    )

    difficulty_level = db.Column(
        db.String(50),
        nullable=False,
        default="Beginner"
    )  # Beginner, Intermediate, Advanced

    estimated_duration = db.Column(
        db.String(50),
        nullable=True
    )  # e.g., "10 hours", "4 weeks", "Self-paced"

    description = db.Column(
        db.Text,
        nullable=True
    )

    certification_available = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )

    status = db.Column(
        db.String(50),
        default="Active",
        nullable=False
    )  # Active, Draft, Archived

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    canonical_skill = db.relationship(
        "CanonicalSkill",
        back_populates="learning_resources"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "canonical_skill_id": self.canonical_skill_id,
            "title": self.title,
            "resource_type": self.resource_type,
            "provider": self.provider,
            "url": self.url,
            "difficulty_level": self.difficulty_level,
            "estimated_duration": self.estimated_duration,
            "description": self.description,
            "certification_available": self.certification_available,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<LearningResource {self.title} ({self.resource_type})>"
