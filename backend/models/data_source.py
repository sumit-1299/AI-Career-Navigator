from datetime import datetime
from extensions import db


class DataSource(db.Model):
    __tablename__ = "data_sources"

    id = db.Column(db.Integer, primary_key=True)

    source_name = db.Column(
        db.String(150),
        nullable=False,
        unique=True
    )

    source_version = db.Column(
        db.String(50),
        nullable=True
    )

    source_type = db.Column(
        db.String(50),
        nullable=True
    )

    website = db.Column(
        db.Text,
        nullable=True
    )

    license = db.Column(
        db.Text,
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

    aliases = db.relationship(
        "SkillAlias",
        back_populates="data_source",
        lazy="select"
    )

    @property
    def name(self):
        return self.source_name

    @name.setter
    def name(self, value):
        self.source_name = value

    def __repr__(self):
        version_str = f" v{self.source_version}" if self.source_version else ""
        return f"<DataSource {self.source_name}{version_str}>"
