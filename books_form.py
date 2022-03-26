from wtforms import BooleanField, SubmitField, StringField, FileField
from wtforms.validators import DataRequired
from flask_wtf import FlaskForm


class BooksForm(FlaskForm):
    name = StringField('Book Title', validators=[DataRequired()])
    author = StringField('Author Name', validators=[DataRequired()])
    description = StringField('Description', validators=[DataRequired()])
    isfin = BooleanField('Is book finished?')
    path_image_title = FileField('Path to title image')
    submit = SubmitField('Submit')