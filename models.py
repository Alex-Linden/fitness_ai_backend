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

    @classmethod
    def signup(cls, email, password, first_name, last_name, birthday, weight, gender, benchmarks):
        """Sign up user.

        Hashes password and adds user to system.
        """
        print('password', password)
        hashed_pwd = bcrypt.generate_password_hash(password).decode('UTF-8')
        print('hashed', hashed_pwd)
        user = User(
            email=email,
            password=hashed_pwd,
            first_name=first_name,
            last_name=last_name,
            birthday=birthday,
            weight=weight,
            gender=gender,
            benchmarks=benchmarks,
        )
        token = jwt.encode({'username': username }, secret_key)

        db.session.add(user)
        return [user, token]

    @classmethod
    def authenticate(cls, email, password):
        """Find user with `email` and `password`.

        This is a class method (call it on the class, not an individual user.)
        It searches for a user whose password hash matches this password
        and, if it finds such a user, returns that user object.

        If this can't find matching user (or if password is wrong), returns
        False.
        """

        user = cls.query.filter_by(email=email).one_or_none()

        if user:
            is_auth = bcrypt.check_password_hash(user.password, password)
            if is_auth:
                token = jwt.encode({'email': email }, secret_key)
                return [user, token]

        return False

    @classmethod
    def create_token(cls, email):
        """Create token for user"""
        print('create_token')
        print('secret key', secret_key)
        token = jwt({'email': email }, secret_key)
        return token


