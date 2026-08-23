from extensions import db

class Skill(db.Model):
    __tablename__ = "skills"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    skill_name = db.Column(
        db.String(100),
        nullable=False
    )

    proficiency = db.Column(
        db.Integer,
        nullable=False
    )

    def __repr__(self):
        return f"<Skill {self.skill_name}>"