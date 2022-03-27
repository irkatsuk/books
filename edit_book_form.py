from wtforms import BooleanField, SubmitField, StringField, FileField
from wtforms.validators import DataRequired
from flask_wtf import FlaskForm


class EditBookForm(FlaskForm):
    name = StringField('Name Title', validators=[DataRequired()])
    author = StringField('Author Name', validators=[DataRequired()])
    description = StringField('Description', validators=[DataRequired()])
    isfin = BooleanField('Is book finished?')
    path_image_title = FileField('Path to title image')
    submit = SubmitField('Edit')
