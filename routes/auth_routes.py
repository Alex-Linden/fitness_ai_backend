from flask import Blueprint, jsonify, g
from sqlalchemy.exc import IntegrityError

from ..forms import UserAddForm, LoginForm
from ..models import db, User
from ..auth import create_access_token
from ..auth import json_form_required


bp = Blueprint('auth_routes', __name__)


@bp.route('/signup', methods=["POST"])
@json_form_required(UserAddForm)
def signup():
    received = g.json
    form = g.form

    email = received.get("email")
    password = received.get("password")
    first_name = received.get("first_name")
    last_name = received.get("last_name")
    birthday = received.get("birthday")
    weight = received.get("weight")
    gender = received.get("gender")
    benchmarks = received.get("benchmarks")

    if isinstance(benchmarks, str):
        try:
            import json as _json
            benchmarks = _json.loads(benchmarks)
        except Exception:
            benchmarks = None

    try:
        user = User.signup(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            birthday=birthday,
            weight=weight,
            gender=gender,
            benchmarks=benchmarks,
        )
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify(message="Email already registered"), 409

    token = create_access_token(email)
    return jsonify(user=user.serialize(), token=token), 201


@bp.route('/login', methods=["POST"])
@json_form_required(LoginForm)
def login():
    received = g.json
    form = g.form

    email = received.get("email")
    password = received.get("password")

    user = User.authenticate(email, password)

    if not user:
        return jsonify(message='Invalid email or password'), 401

    token = create_access_token(email)
    return jsonify(user=user.serialize(), token=token)


@bp.route('/logout', methods=["POST"])
def logout():
    return jsonify(message="logged out")

