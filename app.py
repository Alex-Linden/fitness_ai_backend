import os
from dotenv import load_dotenv, find_dotenv
from pathlib import Path
from flask import Flask, jsonify
from flask_debugtoolbar import DebugToolbarExtension
from flask_login import LoginManager
from flask_cors import CORS
from flask_migrate import Migrate
from sqlalchemy import text

from .models import db, connect_db, bcrypt


# Load env from backend/.env first (works regardless of CWD),
# then also load a repo-level .env if present.
_backend_dir = Path(__file__).resolve().parent
load_dotenv(_backend_dir / ".env")
load_dotenv(find_dotenv())
app = Flask(__name__)

# Database configuration
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

# Secrets
secret_key = os.getenv('SECRET_KEY')
if not secret_key:
    raise RuntimeError(
        "SECRET_KEY is not set. Create a .env from .env.example and set SECRET_KEY"
    )
app.config['SECRET_KEY'] = secret_key

# Optional OAuth provider config passthrough
app.config['OAUTH2_PROVIDERS'] = {
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

# Extensions
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
Migrate(app, db)


# Root routes
@app.get('/hello')
def say_hello():
    html = "<html><body><h1>Hello</h1></body></html>"
    return html


@app.get('/health')
def health():
    try:
        db.session.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False
    status_code = 200 if db_ok else 503
    return jsonify(status="ok" if db_ok else "degraded", db="ok" if db_ok else "unavailable"), status_code


# Register blueprints
from .routes.auth_routes import bp as auth_bp
from .routes.users import bp as users_bp
from .routes.activities import bp as activities_bp
from .routes.categories import bp as categories_bp

app.register_blueprint(auth_bp)
app.register_blueprint(users_bp)
app.register_blueprint(activities_bp)
app.register_blueprint(categories_bp)


# Error handlers and CLI
from .errors import register_error_handlers
from .cli import register_cli

register_error_handlers(app)
register_cli(app)

