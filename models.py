"""SQLAlchemy models for fitness_ai."""
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()
db = SQLAlchemy()


class User(UserMixin, db.Model):
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

    benchmarks = db.Column(db.JSON, nullable=True)

    def serialize(self):
        """Serialize to dictionary"""

        return {
            "id": self.id,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "birthday": self.birthday.isoformat() if self.birthday else None,
            "weight": self.weight,
            "gender": self.gender,
            "benchmarks": self.benchmarks,
        }

    @classmethod
    def signup(
        cls,
        email,
        password,
        first_name,
        last_name,
        birthday=None,
        weight=None,
        gender=None,
        benchmarks=None,
    ):
        """Sign up user.

        Hashes password and adds user to system.
        """
        hashed_pwd = bcrypt.generate_password_hash(password).decode("UTF-8")
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
        db.session.add(user)
        return user

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

        if user and bcrypt.check_password_hash(user.password, password):
            return user

        return False



class Activity(db.Model):
    """An individual activity for a user"""

    __tablename__ = "activities"

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True,
    )

    title = db.Column(
        db.String(20),
        nullable=False,
    )

    distance = db.Column(db.Float, nullable=False)

    duration = db.Column(db.Time, nullable=False)

    notes = db.Column(db.Text, nullable=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    time = db.Column(db.Time, nullable=False)

    complete = db.Column(db.Boolean, nullable=False)

    user = db.relationship('User', backref=db.backref('activities', lazy=True, cascade='all, delete-orphan'))

    # New FK to normalized category table
    category_id = db.Column(
        db.Integer,
        db.ForeignKey("activity_categories.id"),
        nullable=False,
        index=True,
    )
    category = db.relationship('ActivityCategory', backref=db.backref('activities', lazy=True))


class PasswordChangeLog(db.Model):
    """Audit log for password change attempts."""

    __tablename__ = "password_change_logs"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    ip = db.Column(db.String(45), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    success = db.Column(db.Boolean, nullable=False)

    user = db.relationship('User', backref=db.backref('password_change_logs', lazy=True, cascade='all, delete-orphan'))

    def serialize(self):
        """Serialize to dictionary for audit viewing."""

        return {
            "id": self.id,
            "user_id": self.user_id,
            "ip": self.ip,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "success": self.success,
        }


def connect_db(app):
    """Connect this database to provided Flask app.

    You should call this in your Flask app.
    """

    db.app = app
    db.init_app(app)


class ActivityCategory(db.Model):
    """Lookup for activity categories/types (e.g., Run, Bike)."""

    __tablename__ = "activity_categories"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False, unique=True, index=True)

    def serialize(self):
        return {"id": self.id, "name": self.name}
