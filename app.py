import os
import jwt
from flask import Flask, request, session, jsonify
from flask_debugtoolbar import DebugToolbarExtension

from forms import UserAddForm, UserEditForm, LoginForm
from models import db, connect_db, User


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

connect_db(app)


@app.get('/hello')
def say_hello():
    """Return simple "Hello" Greeting."""
    html = "<html><body><h1>Hello</h1></body></html>"
    return html




############################################################
# User signup/login/logout



@app.route('/signup', methods=["GET", "POST"])
def signup():
    print('signup route')
    """Handle user signup.

    Create new user and add to DB. Redirect to home page.

    If form not valid, present form.

    If the there already is a user with that username: flash message
    and re-present form.
    """

    # if CURR_USER_KEY in session:
    #     del session[CURR_USER_KEY]
    received = request.json
    print('received', received)
    form = UserAddForm(csrf_enabled=False, data=received)
    print('form=', form)
    print("username", received["username"])
    print('password', received["password"])

    if form.validate_on_submit():
        username = received["username"]
        password = received["password"]
        email = received["email"]
        first_name = received["first_name"]
        last_name = received["last_name"]
        bio = received["bio"]
        is_host = False
        print("username", username)

        try:
            user = User.signup(
                username=username,
                password=password,
                email=email,
                first_name=first_name,
                last_name=last_name,
                bio=bio,
                is_host=is_host,
                # image_url=form.image_url.data or User.image_url.default.arg,
            )
            db.session.commit()

            serialized = user[0].serialize()

            return jsonify(user=serialized, token=user[1])

        except ClientError as e:
            #TODO: default image
            return jsonify(e)

    return jsonify(errors=form.errors)


@app.route('/login', methods=["GET", "POST"])
def login():
    """Handle user login and redirect to homepage on success."""

    received = request.json
    form = LoginForm(csrf_enabled=False, data=received)

    if form.validate_on_submit():
        username = received["username"]
        password = received["password"]

        user = User.authenticate(
            username,
            password)

        if user[0]:
            serialized = user[0].serialize()

            return jsonify(user=serialized, token=user[1])
        else:
            return jsonify({"msg": 'failed to login username or password is invalid'})


    return jsonify(errors=form.errors)


@app.route('/logout', methods=["GET", "POST"])
def logout():
    """Handle user logout and redirect to homepage on success."""

    if "token" in session:
        del session["token"]
        return jsonify(msg="logged out")
    else:
        return jsonify(msg="not logged in")