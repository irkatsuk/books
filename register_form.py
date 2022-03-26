from wtforms import PasswordField, SubmitField, StringField
from wtforms.validators import DataRequired
from flask_wtf import FlaskForm


class RegisterForm(FlaskForm):
    login = StringField('Login/email', validators=[DataRequired()])
    passw = PasswordField('Password', validators=[DataRequired()])
    repeat_passw = PasswordField('Repeat password', validators=[DataRequired()])
    surname = StringField('Surname', validators=[DataRequired()])
    name = StringField('Name', validators=[DataRequired()])
    access = SubmitField('Submit')