from flask import Flask
from flask_debugtoolbar import DebugToolbarExtension

from forms import UserAddForm, UserEditForm, LoginForm
from models import db, connect_db, User


app = Flask(__name__)

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


