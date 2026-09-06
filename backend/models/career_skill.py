from extensions import db


class CareerSkill(db.Model):
    __tablename__ = "career_skills"

    id = db.Column(db.Integer, primary_key=True)

    career_id = db.Column(
        db.Integer,
        db.ForeignKey("careers.id"),
        nullable=False
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

    def __repr__(self):
        return f"<CareerSkill {self.skill_name}>"