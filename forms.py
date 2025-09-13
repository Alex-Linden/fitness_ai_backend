from wsgiref.validate import validator
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, IntegerField, BooleanField, FileField, DateField
from wtforms.validators import DataRequired, InputRequired, Email, Length, Optional


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
