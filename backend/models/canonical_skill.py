from datetime import datetime
from extensions import db


class CanonicalSkill(db.Model):
    __tablename__ = "canonical_skills"

    id = db.Column(db.Integer, primary_key=True)

    canonical_name = db.Column(
        db.String(150),
        nullable=False,
        unique=True
    )

    normalized_name = db.Column(
        db.String(150),
        nullable=False,
        unique=True,
        index=True
    )

    skill_type = db.Column(
        db.String(100),
        nullable=True
    )

    description = db.Column(
        db.Text,
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    aliases = db.relationship(
        "SkillAlias",
        back_populates="canonical_skill",
        cascade="all, delete-orphan",
        lazy="select"
    )

    # Relationships to student skills and career skills (Phase 2)
    student_skills = db.relationship(
        "Skill",
        back_populates="canonical_skill",
        lazy="select"
    )

    career_skills = db.relationship(
        "CareerSkill",
        back_populates="canonical_skill",
        lazy="select"
    )

    learning_resources = db.relationship(
        "LearningResource",
        back_populates="canonical_skill",
        lazy="select"
    )

    @property
    def name(self):
        return self.canonical_name

    @name.setter
    def name(self, value):
        self.canonical_name = value

    def __repr__(self):
        return f"<CanonicalSkill {self.canonical_name}>"
