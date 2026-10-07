from extensions import db


class PasswordResetToken(db.Model):
    __tablename__ = "password_reset_tokens"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    token_hash = db.Column(
        db.String(64),
        unique=True,
        nullable=False,
        index=True,
    )

    expires_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    used_at = db.Column(
        db.DateTime(timezone=True),
        nullable=True,
    )
