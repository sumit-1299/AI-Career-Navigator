from datetime import datetime
from extensions import db


class SkillAlias(db.Model):
    __tablename__ = "skill_aliases"

    id = db.Column(db.Integer, primary_key=True)

    canonical_skill_id = db.Column(
        db.Integer,
        db.ForeignKey("canonical_skills.id", ondelete="CASCADE"),
        nullable=False
    )

    alias_name = db.Column(
        db.String(200),
        nullable=False
    )

    normalized_alias = db.Column(
        db.String(200),
        nullable=False,
        index=True
    )

    source_id = db.Column(
        db.Integer,
        db.ForeignKey("data_sources.id", ondelete="SET NULL"),
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    canonical_skill = db.relationship(
        "CanonicalSkill",
        back_populates="aliases"
    )

    data_source = db.relationship(
        "DataSource",
        back_populates="aliases"
    )

    __table_args__ = (
        db.UniqueConstraint(
            "canonical_skill_id",
            "normalized_alias",
            name="uq_canonical_skill_normalized_alias"
        ),
    )

    @property
    def alias(self):
        return self.alias_name

    @alias.setter
    def alias(self, value):
        self.alias_name = value

    @property
    def skill_id(self):
        return self.canonical_skill_id

    @skill_id.setter
    def skill_id(self, value):
        self.canonical_skill_id = value

    def __repr__(self):
        return f"<SkillAlias {self.alias_name} -> Skill {self.canonical_skill_id}>"
