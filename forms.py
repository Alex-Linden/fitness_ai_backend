from wsgiref.validate import validator
from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    TextAreaField,
    IntegerField,
    BooleanField,
    FileField,
    DateField,
    TimeField,
    FloatField,
)
from wtforms.validators import DataRequired, InputRequired, Email, Length, Optional, NumberRange


# class MessageForm(FlaskForm):
#     """Form for adding/editing messages."""

#     text = TextAreaField('text', validators=[DataRequired()])


class UserAddForm(FlaskForm):
    """Form for adding users."""

    class Meta:
        csrf = False

    email = StringField('E-mail', validators=[DataRequired(), Email()])
    first_name = StringField('First Name',validators=[DataRequired()])
    last_name = StringField('Last Name',validators=[DataRequired()])
    password = PasswordField('Password', validators=[Length(min=6)])
    birthday = DateField('Birthday', validators=[Optional()])
    weight = IntegerField('Weight', validators=[Optional()])
    gender = StringField('Gender', validators=[Optional()])
    benchmarks = StringField('Benchmarks', validators=[Optional()])


class UserEditForm(FlaskForm):
    """Form for adding users."""

    class Meta:
        csrf = False

    email = StringField('E-mail', validators=[Optional(), Email()])
    first_name = StringField('First Name', validators=[Optional()])
    last_name = StringField('Last Name', validators=[Optional()])
    birthday = DateField('Birthday', validators=[Optional()])
    weight = IntegerField('Weight', validators=[Optional()])
    gender = StringField('Gender', validators=[Optional()])
    benchmarks = StringField('Benchmarks', validators=[Optional()])
    password = PasswordField('Password', validators=[Length(min=6)])


class LoginForm(FlaskForm):
    """Login form."""

    class Meta:
        csrf = False

    email = StringField('E-mail', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[Length(min=6)])


class PasswordChangeForm(FlaskForm):
    """Form for changing a user's password."""

    class Meta:
        csrf = False

    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[Length(min=6)])


class DeleteAccountForm(FlaskForm):
    """Form for deleting a user's account."""

    class Meta:
        csrf = False

    current_password = PasswordField('Current Password', validators=[DataRequired()])
    confirm_email = StringField('Confirm Email', validators=[DataRequired(), Email()])


class ActivityForm(FlaskForm):
    """Form for logging an activity."""

    class Meta:
        csrf = False

    title = StringField('Title', validators=[DataRequired(), Length(max=20)])
    # Allow either category_id or category name to be supplied; enforce in route
    category_id = IntegerField('Category ID', validators=[Optional()])
    category = StringField('Category', validators=[Optional(), Length(max=50)])
    distance = FloatField('Distance', validators=[InputRequired(), NumberRange(min=0)])
    # Expect HH:MM:SS for both
    duration = TimeField('Duration', format='%H:%M:%S', validators=[DataRequired()])
    time = TimeField('Time', format='%H:%M:%S', validators=[DataRequired()])
    notes = TextAreaField('Notes', validators=[Optional()])
    complete = BooleanField('Complete', validators=[Optional()])
