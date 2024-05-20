from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from wtforms import FileField, SubmitField, StringField, RadioField, MultipleFileField
from wtforms.validators import DataRequired, Optional


class UploadForm(FlaskForm):
    upload = FileField('File', validators=[FileAllowed(['jpg', 'png', 'webp'])])
    url = StringField('URL')
    submit = SubmitField('Upload')

    def validate_on_submit(self, extra_validators=None):
        if super().validate(extra_validators):
            if not (self.upload.data or self.url.data):
                self.url.errors.append('Please upload either a link or an image')
                return False
            else:
                return True
        return False


class UploadSignForm(FlaskForm):
    to_sign = FileField('File', validators=[FileAllowed(['jpg', 'png'])])
    url_to_sign = StringField('URL')
    manifest = FileField('Manifest')
    submit = SubmitField('Upload')


class FormSign(FlaskForm):
    to_sign = FileField('File', validators=[DataRequired(), FileAllowed(['jpg', 'png', 'webp'])])

    # metadata
    metadata = RadioField('Metadata', choices=[(True, 'Yes'), (False, 'No')])

    # Actions
    ai_image = RadioField('AI', choices=[(True, 'Yes'), (False, 'No')], validators=[DataRequired()])
    opened_ingredient = FileField('Ingredients', validators=[Optional(), FileAllowed(['jpg', 'png', 'webp'])])
    placed_ingredients = MultipleFileField('Placed Ingredients',
                                           validators=[Optional(), FileAllowed(['jpg', 'png', 'webp'])])
    color_adjustments = RadioField('Colour Adjustments', choices=[(True, 'Yes'), (False, 'No')],
                                   validators=[DataRequired()])
    converted = RadioField('Format change', choices=[(True, 'Yes'), (False, 'No')], validators=[DataRequired()])
    cropped = RadioField('Cropped', choices=[(True, 'Yes'), (False, 'No')], validators=[DataRequired()])
    drawing = RadioField('Drawing', choices=[(True, 'Yes'), (False, 'No')], validators=[DataRequired()])
    edited = RadioField('Edited', choices=[(True, 'Yes'), (False, 'No')], validators=[DataRequired()])
    filtered = RadioField('Filtered', choices=[(True, 'Yes'), (False, 'No')], validators=[DataRequired()])

    orientation = RadioField('orientation', choices=[(True, 'Yes'), (False, 'No')], validators=[DataRequired()])

    published = RadioField('published', choices=[(True, 'Yes'), (False, 'No')], validators=[DataRequired()])
    removed = RadioField('removed', choices=[(True, 'Yes'), (False, 'No')], validators=[DataRequired()])
    resized = RadioField('resized', choices=[(True, 'Yes'), (False, 'No')], validators=[DataRequired()])
    transcoded = RadioField('transcoded', choices=[(True, 'Yes'), (False, 'No')], validators=[DataRequired()])
    submit = SubmitField()
