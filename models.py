"""SQLAlchemy models for fitness_ai."""

from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
import os
from dotenv import load_dotenv
import jwt

load_dotenv()

secret_key = os.environ["SECRET_KEY"]
bcrypt = Bcrypt()
db = SQLAlchemy()


class User(db.Model):
    """User in the system."""

    __tablename__ = "users"

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True,
    )

    email = db.Column(
        db.Text,
        nullable=False,
        unique=True,
    )

    first_name = db.Column(
        db.Text,
        nullable=False,
    )

    last_name = db.Column(db.Text, nullable=False)

    password = db.Column(
        db.Text,
        nullable=False,
    )

    birthday = db.Column(db.Date, nullable=True)

    weight = db.Column(db.Integer, nullable=True)

    gender = db.Column(db.Text, nullable=True)

    benchmarks = db.Column(db.JSON, nullabel=True)

    def serialize(self):
        """Serialize to dictionary"""

        return {
            "id": self.id,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "birthday": self.birthday,
            "weight": self.weight,
            "gender": self.gender,
            "benchmarks": self.benchmarks,
        }
