import os
from flask import Flask, request, jsonify
from flask_debugtoolbar import DebugToolbarExtension

from flask_login import LoginManager, UserMixin, login_user, logout_user,\
    current_user

from forms import UserAddForm, UserEditForm, LoginForm
from models import db, connect_db, User, bcrypt
from sqlalchemy.exc import IntegrityError

from auth import create_access_token, decode_access_token
from flask_cors import CORS
from werkzeug.exceptions import HTTPException


app = Flask(__name__)
# Get DB_URI from environ variable (useful for production/testing) or,
# if not set there, use development local db.
app.config['SQLALCHEMY_DATABASE_URI'] = (
    os.environ['DATABASE_URL'].replace("postgres://", "postgresql://"))
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = True
app.config['SECRET_KEY'] = os.environ['SECRET_KEY']
# From blog/tutorial TODO: register app with OAuth2Client and update secret keys
app.config['OAUTH2_PROVIDERS'] = {
    # Google OAuth 2.0 documentation:
    # https://developers.google.com/identity/protocols/oauth2/web-server#httprest
    'google': {
        'client_id': os.environ.get('GOOGLE_CLIENT_ID'),
        'client_secret': os.environ.get('GOOGLE_CLIENT_SECRET'),
        'authorize_url': 'https://accounts.google.com/o/oauth2/auth',
        'token_url': 'https://accounts.google.com/o/oauth2/token',
        'userinfo': {
            'url': 'https://www.googleapis.com/oauth2/v3/userinfo',
            'email': lambda json: json['email'],
        },
        'scopes': ['https://www.googleapis.com/auth/userinfo.email'],
    },

    # GitHub OAuth 2.0 documentation:
    # https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/authorizing-oauth-apps
    'github': {
        'client_id': os.environ.get('GITHUB_CLIENT_ID'),
        'client_secret': os.environ.get('GITHUB_CLIENT_SECRET'),
        'authorize_url': 'https://github.com/login/oauth/authorize',
        'token_url': 'https://github.com/login/oauth/access_token',
        'userinfo': {
            'url': 'https://api.github.com/user/emails',
            'email': lambda json: json[0]['email'],
        },
        'scopes': ['user:email'],
    },
    # TODO: validate that this is the right info for strava
    # Strava OAuth 2.0 documentation:
    # https://developers.strava.com/docs/authentication/
    'strava': {
        'client_id': os.environ.get('STRAVA_CLIENT_ID'),
        'client_secret': os.environ.get('STRAVA_CLIENT_SECRET'),
        'authorize_url': 'https://www.strava.com/oauth/authorize',
        'token_url': 'https://www.strava.com/oauth/token',
        'userinfo': {
            'url': 'https://www.strava.com/api/v3/athlete',
            'email': lambda json: json['email'],
        },
        'scopes': ['view_private'],
    },
}
toolbar = DebugToolbarExtension(app)
login_manager = LoginManager()


connect_db(app)
bcrypt.init_app(app)
CORS(
    app,
    resources={r"/*": {"origins": ["http://localhost:3000", "http://127.0.0.1:3000"]}},
    expose_headers=["Content-Type", "Authorization"],
    supports_credentials=False,
)


@app.get('/hello')
def say_hello():
    """Return simple "Hello" Greeting."""
    html = "<html><body><h1>Hello</h1></body></html>"
    return html




############################################################
# User signup/login/logout



@app.route('/signup', methods=["POST"])
def signup():
    """Handle user signup.

    Create new user and add to DB. Redirect to home page.

    If form not valid, present form.

    If the there already is a user with that username: flash message
    and re-present form.
    """

    received = request.get_json(silent=True) or {}
    form = UserAddForm(csrf_enabled=False, data=received)

    if not form.validate_on_submit():
        return jsonify(errors=form.errors), 400

    email = received.get("email")
    password = received.get("password")
    first_name = received.get("first_name")
    last_name = received.get("last_name")
    birthday = received.get("birthday")
    weight = received.get("weight")
    gender = received.get("gender")
    benchmarks = received.get("benchmarks")

    # Accept benchmarks as JSON or string
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


@app.route('/login', methods=["POST"])
def login():
    """Handle user login and redirect to homepage on success."""

    received = request.get_json(silent=True) or {}
    form = LoginForm(csrf_enabled=False, data=received)

    if not form.validate_on_submit():
        return jsonify(errors=form.errors), 400

    email = received.get("email")
    password = received.get("password")

    user = User.authenticate(email, password)

    if not user:
        return jsonify(message='Invalid email or password'), 401

    token = create_access_token(email)
    return jsonify(user=user.serialize(), token=token)


@app.route('/logout', methods=["POST"])
def logout():
    """Stateless JWT: client drops token; nothing to do server-side."""
    return jsonify(message="logged out")

############################################################
# General User routes - TODO: this was vibe coded don't trust


@app.get('/me')
def me():
    """Return the current user's profile using JWT from Authorization header."""
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return jsonify(message='Missing or invalid Authorization header'), 401

    token = auth_header.split(' ', 1)[1].strip()
    payload = decode_access_token(token)
    if payload is None or 'email' not in payload:
        return jsonify(message='Invalid or expired token'), 401

    user = User.query.filter_by(email=payload['email']).one_or_none()
    if not user:
        return jsonify(message='User not found'), 404

    return jsonify(user=user.serialize())


@app.route('/user/edit', methods=["GET", "POST"])
def edit_user():
    """Handle user editing profile.

    redirect to profile page on success."""


############################################################
# Error Handlers


def _json_error(status_code: int, message: str, **extra):
    payload = {"error": {"code": status_code, "message": message}}
    if extra:
        payload["error"].update(extra)
    return jsonify(payload), status_code


@app.errorhandler(400)
def bad_request(err):
    msg = err.description if isinstance(err, HTTPException) else "Bad Request"
    return _json_error(400, msg)


@app.errorhandler(401)
def unauthorized(err):
    msg = err.description if isinstance(err, HTTPException) else "Unauthorized"
    return _json_error(401, msg)


@app.errorhandler(403)
def forbidden(err):
    msg = err.description if isinstance(err, HTTPException) else "Forbidden"
    return _json_error(403, msg)


@app.errorhandler(404)
def not_found(err):
    msg = err.description if isinstance(err, HTTPException) else "Not Found"
    return _json_error(404, msg)


@app.errorhandler(405)
def method_not_allowed(err):
    msg = err.description if isinstance(err, HTTPException) else "Method Not Allowed"
    return _json_error(405, msg)


@app.errorhandler(422)
def unprocessable_entity(err):
    msg = err.description if isinstance(err, HTTPException) else "Unprocessable Entity"
    return _json_error(422, msg)


@app.errorhandler(Exception)
def internal_error(err):
    # Convert any HTTPException not explicitly handled above to JSON
    if isinstance(err, HTTPException):
        return _json_error(err.code or 500, err.description or err.name)

    # Log unexpected exceptions and return generic JSON error
    app.logger.exception("Unhandled exception")
    return _json_error(500, "Internal Server Error")
