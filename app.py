from flask import Flask, render_template, redirect, url_for, request, session
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from werkzeug.utils import secure_filename
from wtforms import Form, FileField, SubmitField
from wtforms.validators import DataRequired

import os
import c2pa
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'longandrandomkey'

lookup = {
    'color_adjustments': 'Changes have been made to the tone, saturation or other areas.',
    'converted': 'The format of the media was changed.',
    'created': 'The asset was first created, usually the asset’s origin.',
    'cropped': 'Areas of the asset’s "editorial" content were cropped out.',
    'drawing': 'Changes using drawing tools including brushes or eraser.',
    'edited': 'Generalized actions that would be considered editorial transformations.',
    'filtered': 'Changes to appearance with applied filters, styles, etc.',
    'opened': 'An existing asset was opened and is being set as the parentOf ingredient.',
    'orientation': 'Changes to the direction and position of content.',
    'placed': 'Added/Placed a componentOf ingredient into the asset.',
    'published': 'Asset is released to a wider audience.',
    'redacted': 'One or more assertions or W3C verifiable credentials were redacted',
    'removed': 'A componentOf ingredient was removed.',
    'repackaged': 'A conversion of one packaging or container format to another. Content is repackaged without transcoding. This action is considered as a non-editorial transformation of the parentOf ingredient.',
    'resized': 'Changes to content dimensions and/or file size',
    'transcoded': 'A conversion of one encoding to another, including resolution scaling, bitrate adjustment and encoding format change. This action is considered as a non-editorial transformation of the parentOf ingredient.',
    'unknown': 'Something happened, but the claim_generator cannot specify what.'

}


class UploadForm(FlaskForm):
    upload = FileField('File', validators=[DataRequired(), FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Upload')


@app.route('/', methods=['GET', 'POST'])
def index():
    form = UploadForm()
    if form.validate_on_submit():
        name = secure_filename(form.upload.data.filename)
        session['file'] = os.path.join('static/uploads', name)
        form.upload.data.save(os.path.join('static/uploads', name))
        return redirect(url_for('report'))
    return render_template('Interface.html', form=form)


@app.route('/sign', methods=['GET', 'POST'])
def sign():
    return render_template('Sign.html')


"""
def report():
    return render_template('Report.html',
                           modifications=['c2pa.created', 'c2pa.drawing', 'c2pa.placed', 'c2pa.resized'],
                           errors = ['assertion.hashedURI.mismatch'],
                           ingredients = ['Image_3', 'Image_4', 'Image_5'],
                           ai = False)
"""


@app.route('/report', methods=['GET', 'POST'])
def report():
    name = session['file']
    json_store = json.loads(c2pa.read_file(name, 'Verify/Extract/temp'))
    print(json.dumps(json_store, indent=2))
    modifications = []
    ingredients = []
    errors = []
    signer = ''
    ai = False
    for manifest in json_store['manifests']:
        if manifest == json_store['active_manifest']:
            for action in json_store['manifests'][manifest]['assertions']:
                signer = json_store['manifests'][manifest]['signature_info']['issuer']
                if action['label'] == 'c2pa.actions':
                    for a in action['data']['actions']:
                        if a['action'] == 'c2pa.created' and ('digitalSourceType' in a.keys()):
                            ai = True
                        modifications.append(str(a['action']).replace('c2pa.', ''))

            for ingredient in json_store['manifests'][manifest]['ingredients']:
                ingredients.append(str(ingredient['title']))
            print('Ingredients:', ingredients)

    if 'validation_status' in json_store.keys():
        for validation in json_store['validation_status']:
            print(validation['code'], '-', validation['explanation'])
            errors.append(str(validation['code']))

    return render_template('Report.html', modifications=modifications, errors=errors, ingredients=ingredients, ai=ai,
                           path=name, signer=signer, lookup=lookup)


if __name__ == '__main__':
    app.run(debug=True)
