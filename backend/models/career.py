from extensions import db


class Career(db.Model):
    __tablename__ = "careers"

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(
        db.String(100),
        nullable=False,
        unique=True
    )

    domain = db.Column(
        db.String(100),
        nullable=False
    )

    description = db.Column(
        db.Text,
        nullable=True
    )

    skills = db.relationship(
        "CareerSkill",
        backref="career",
        lazy="select",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Career {self.title}>"
