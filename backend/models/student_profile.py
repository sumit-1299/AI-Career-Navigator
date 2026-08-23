from extensions import db


class StudentProfile(db.Model):
    __tablename__ = "student_profiles"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        unique=True
    )

    education = db.Column(
        db.String(100),
        nullable=False
    )

    specialization = db.Column(
        db.String(150)
    )

    graduation_year = db.Column(
        db.Integer
    )

    cgpa = db.Column(
        db.Float
    )

    user = db.relationship(
        "User",
        back_populates="profile"
    )