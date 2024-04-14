from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from wtforms import FileField, SubmitField, StringField, RadioField
from wtforms.validators import DataRequired


class UploadForm(FlaskForm):
    upload = FileField('File', validators=[FileAllowed(['jpg', 'png'])])
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
    to_sign = FileField('File', validators=[FileAllowed(['jpg', 'png'])])

    #Ingredients
    metadata = RadioField('Metadata', choices=[(True, 'Yes'), (False, 'No')])

    #Thumbnail
    thumbnail = RadioField('Thumbnail', choices=[(True, 'Yes'), (False, 'No')])

    # Actions
    ai_image = RadioField('AI', choices=[(True, 'Yes')], validators=[DataRequired()])
    color_adjustments = RadioField('Colour Adjustments', choices=[(True, 'Yes')], validators=[DataRequired()])
    converted = RadioField('Format change', choices=[(True, 'Yes'), (False, 'No')], validators=[DataRequired()])
    cropped = RadioField('Cropped', choices=[(True, 'Yes'), (False, 'No')], validators=[DataRequired()])
    drawing = RadioField('Drawing', choices=[(True, 'Yes'), (False, 'No')], validators=[DataRequired()])
    edited = RadioField('Edited', choices=[(True, 'Yes'), (False, 'No')], validators=[DataRequired()])
    filtered = RadioField('Filtered', choices=[(True, 'Yes'), (False, 'No')], validators=[DataRequired()])
    opened = RadioField('colour adjustments', choices=[(True, 'Yes'), (False, 'No')], validators=[DataRequired()])
    orientation = RadioField('colour adjustments', choices=[(True, 'Yes'), (False, 'No')], validators=[DataRequired()])
    placed = RadioField('colour adjustments', choices=[(True, 'Yes'), (False, 'No')], validators=[DataRequired()])
    published = RadioField('colour adjustments', choices=[(True, 'Yes'), (False, 'No')], validators=[DataRequired()])
    removed = RadioField('colour adjustments', choices=[(True, 'Yes'), (False, 'No')], validators=[DataRequired()])
    resized = RadioField('colour adjustments', choices=[(True, 'Yes'), (False, 'No')], validators=[DataRequired()])
    transcoded = RadioField('colour adjustments', choices=[(True, 'Yes'), (False, 'No')], validators=[DataRequired()])
    submit = SubmitField()

