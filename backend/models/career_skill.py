from extensions import db


class CareerSkill(db.Model):
    __tablename__ = "career_skills"

    id = db.Column(db.Integer, primary_key=True)

    career_id = db.Column(
        db.Integer,
        db.ForeignKey("careers.id"),
        nullable=False
    )

    canonical_skill_id = db.Column(
        db.Integer,
        db.ForeignKey("canonical_skills.id", ondelete="SET NULL"),
        nullable=True
    )

    skill_name = db.Column(
        db.String(100),
        nullable=False
    )

    required_level = db.Column(
        db.Integer,
        nullable=False
    )

    importance = db.Column(
        db.Integer,
        nullable=False,
        default=1
    )

    canonical_skill = db.relationship(
        "CanonicalSkill",
        back_populates="career_skills"
    )

    def __repr__(self):
        return f"<CareerSkill {self.skill_name}>"
