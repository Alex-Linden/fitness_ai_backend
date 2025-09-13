import os
from dotenv import load_dotenv, find_dotenv
from pathlib import Path
from flask import Flask, request, jsonify
from flask_debugtoolbar import DebugToolbarExtension

from flask_login import LoginManager, UserMixin, login_user, logout_user,\
    current_user

from .forms import UserAddForm, UserEditForm, LoginForm, PasswordChangeForm
from .models import db, connect_db, User, bcrypt, PasswordChangeLog
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from datetime import datetime, timedelta
from sqlalchemy import text

from .auth import create_access_token, decode_access_token
from flask_cors import CORS
from werkzeug.exceptions import HTTPException
from flask_migrate import Migrate


# Load env from backend/.env first (works regardless of CWD),
# then also load a repo-level .env if present.
_backend_dir = Path(__file__).resolve().parent
load_dotenv(_backend_dir / ".env")
load_dotenv(find_dotenv())
app = Flask(__name__)
# Get DB_URI from environ variable (useful for production/testing) or,
# if not set there, use development local db.
db_url = os.getenv('DATABASE_URL')
if not db_url:
    raise RuntimeError(
        "DATABASE_URL is not set. Create a .env from .env.example and set DATABASE_URL"
    )
if db_url.startswith('postgres://'):
    db_url = db_url.replace('postgres://', 'postgresql+psycopg://', 1)
elif db_url.startswith('postgresql://') and '+psycopg' not in db_url:
    db_url = db_url.replace('postgresql://', 'postgresql+psycopg://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = True
secret_key = os.getenv('SECRET_KEY')
if not secret_key:
    raise RuntimeError(
        "SECRET_KEY is not set. Create a .env from .env.example and set SECRET_KEY"
    )
app.config['SECRET_KEY'] = secret_key
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

migrate = Migrate(app, db)


@app.get('/hello')
def say_hello():
    """Return simple "Hello" Greeting."""
    html = "<html><body><h1>Hello</h1></body></html>"
    return html


@app.get('/health')
def health():
    """Basic health check including DB connectivity."""
    try:
        db.session.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False
    status_code = 200 if db_ok else 503
    return jsonify(status="ok" if db_ok else "degraded", db="ok" if db_ok else "unavailable"), status_code




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


@app.patch('/me')
def update_me():
    """Update the current user's profile using JWT auth.

    Accepts a JSON body with any subset of fields:
    - email, first_name, last_name, birthday (YYYY-MM-DD),
      weight (int), gender (str), benchmarks (JSON object or JSON string),
      password (min length enforced).
    Returns the updated user. If the email changes, a new token is returned.
    """
    # Auth: ensure caller is the user in token
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

    received = request.get_json(silent=True) or {}
    form = UserEditForm(csrf_enabled=False, data=received)
    if not form.validate_on_submit():
        return jsonify(errors=form.errors), 400

    # Track whether email changed to refresh JWT
    old_email = user.email

    # Update fields if provided
    if 'email' in received and received['email']:
        user.email = received['email']
    if 'first_name' in received and received['first_name']:
        user.first_name = received['first_name']
    if 'last_name' in received and received['last_name']:
        user.last_name = received['last_name']
    if 'birthday' in received and received['birthday']:
        # WTForms DateField already parsed; assign from form to ensure coercion
        user.birthday = form.birthday.data
    if 'weight' in received and received['weight'] is not None:
        user.weight = form.weight.data
    if 'gender' in received and received['gender']:
        user.gender = received['gender']
    if 'benchmarks' in received:
        benchmarks = received['benchmarks']
        if isinstance(benchmarks, str):
            try:
                import json as _json
                benchmarks = _json.loads(benchmarks)
            except Exception:
                benchmarks = None
        user.benchmarks = benchmarks
    if 'password' in received and received['password']:
        # Length validated by form; hash and set
        from .models import bcrypt as _bcrypt
        user.password = _bcrypt.generate_password_hash(received['password']).decode('UTF-8')

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify(message='Email already in use'), 409

    # Issue new token if email changed
    new_token = None
    if user.email != old_email:
        new_token = create_access_token(user.email)

    result = {"user": user.serialize()}
    if new_token:
        result["token"] = new_token
    return jsonify(result)


@app.patch('/me/password')
def change_password():
    """Change the current user's password.

    Requires JWT auth and validates the current password.
    Body: {"current_password": str, "new_password": str (min 6)}
    """
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

    received = request.get_json(silent=True) or {}
    form = PasswordChangeForm(csrf_enabled=False, data=received)
    if not form.validate_on_submit():
        return jsonify(errors=form.errors), 400

    current_password = received.get('current_password')
    new_password = received.get('new_password')

    # Rate limit failed attempts: 5 failures per 15 minutes
    window = datetime.utcnow() - timedelta(minutes=15)
    failed_count = db.session.query(func.count(PasswordChangeLog.id)).filter(
        PasswordChangeLog.user_id == user.id,
        PasswordChangeLog.success.is_(False),
        PasswordChangeLog.created_at >= window,
    ).scalar() or 0
    if failed_count >= 5:
        return jsonify(message='Too many failed attempts. Try again in 15 minutes'), 429

    # Verify current password
    if not bcrypt.check_password_hash(user.password, current_password):
        log = PasswordChangeLog(user_id=user.id, ip=request.remote_addr, success=False)
        db.session.add(log)
        db.session.commit()
        return jsonify(message='Current password is incorrect'), 401

    # Optional: prevent reusing the same password
    if bcrypt.check_password_hash(user.password, new_password):
        return jsonify(message='New password must be different from current password'), 400

    user.password = bcrypt.generate_password_hash(new_password).decode('UTF-8')
    log = PasswordChangeLog(user_id=user.id, ip=request.remote_addr, success=True)
    db.session.add(log)
    db.session.commit()

    return jsonify(message='Password updated successfully')


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


@app.errorhandler(429)
def too_many_requests(err):
    msg = err.description if isinstance(err, HTTPException) else "Too Many Requests"
    return _json_error(429, msg)


@app.errorhandler(Exception)
def internal_error(err):
    # Convert any HTTPException not explicitly handled above to JSON
    if isinstance(err, HTTPException):
        return _json_error(err.code or 500, err.description or err.name)

    # Log unexpected exceptions and return generic JSON error
    app.logger.exception("Unhandled exception")
    return _json_error(500, "Internal Server Error")
