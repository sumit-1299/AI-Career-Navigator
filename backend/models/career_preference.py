from extensions import db


class CareerPreference(db.Model):
    __tablename__ = "career_preferences"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        unique=True
    )

    target_role = db.Column(
        db.String(100),
        nullable=False
    )

    preferred_domain = db.Column(
        db.String(100),
        nullable=False
    )

    experience_level = db.Column(
        db.String(50),
        nullable=False
    )

    def __repr__(self):
        return f"<CareerPreference {self.target_role}>"