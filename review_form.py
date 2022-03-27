from wtforms import SubmitField, TextAreaField
from wtforms.validators import DataRequired
from flask_wtf import FlaskForm


class ReviewForm(FlaskForm):
    description = TextAreaField('Description', validators=[DataRequired()])
    submit = SubmitField('Submit')