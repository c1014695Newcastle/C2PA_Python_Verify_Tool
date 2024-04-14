import c2pa
from flask import render_template, Blueprint
from forms import UploadSignForm, FormSign
from PIL import Image

import requests
from werkzeug.utils import secure_filename
from flask import session, send_file

from c2pa_dissertation.action import Action
from c2pa_dissertation.metadata import read_exif_data

sign_blueprint = Blueprint('sign', __name__, template_folder='templates')

@sign_blueprint.route('/sign', methods=['GET'])
def sign():
    return render_template('sign.html', upload=0)


@sign_blueprint.route('/upload', methods=['GET', 'POST'])
def manifest_upload():
    form = UploadSignForm()
    if form.validate_on_submit():
        if form.to_sign.data is not None:
            img_filename = form.to_sign.data.filename
            form.to_sign.data.save('static/sign_uploads/{}'.format(img_filename))
        else:
            upload = Image.open(requests.get(form.url_to_sign.data, stream=True).raw)
            img_filename = secure_filename(upload.filename)
            path = 'static/uploads/{}'.format(img_filename)
            upload.save(path, format='JPEG')

        manifest_name = '{}.json'.format(img_filename.split('.')[0])
        form.manifest.data.save('static/sign_uploads/{}'.format(manifest_name))
        key = open('cryptography/key.pem', "rb").read()
        cert = open('cryptography/cert.pem', "rb").read()
        signer_info = c2pa.SignerInfo('es256', sign_cert=cert, private_key=key, ta_url="http://timestamp.digicert.com")

        image_name = 'static/sign_uploads/{}'.format(img_filename)
        signed_name = 'static/signed/{}'.format(img_filename)
        m = open('static/sign_uploads/{}'.format(manifest_name), "r").read()

        c2pa.sign_file(image_name, signed_name, m, signer_info, '')
        session['path'] = signed_name
        return render_template('signed.html', path=signed_name)

    return render_template('sign.html', upload=1, form=form)


@sign_blueprint.route('/form', methods=['GET', 'POST'])
def manifest_form():
    form = FormSign()
    if form.validate_on_submit():
        actions = []
        img_filename = form.to_sign.data.filename
        form.to_sign.data.save('static/sign_uploads/{}'.format(img_filename))
        if form.ai_image.data is True:
            actions.append(Action('c2pa.created', digital_source='http://cv.iptc.org/newscodes/digitalsourcetype/trainedAlgorithmicMedia').to_JSON())
        if form.metadata.data is True:
            with open('static/sign_uploads/{}'.format(img_filename), 'rb') as f:
                image_bytes = f.read()
            metadata = read_exif_data(image_bytes)
        if form.color_adjustments.data is True:
            actions.append(Action('c2pa.colour_adjustments').to_JSON())
        if form.converted.data is True:
            actions.append(Action('c2pa.converted').to_JSON())
        if form.cropped.data is True:
            actions.append(Action('c2pa.cropped').to_JSON())
        if form.drawing.data is True:
            actions.append(Action('c2pa.drawing').to_JSON())
        if form.edited.data is True:
            actions.append(Action('c2pa.edited').to_JSON())
        if form.filtered.data is True:
            actions.append(Action('c2pa.filtered').to_JSON())
        if form.opened.data is True:
            actions.append(Action('c2pa.opened').to_JSON())
        if form.orientation is True:
            actions.append(Action('c2pa.opened').to_JSON())
        if form.placed.data is True:
            actions.append(Action('c2pa.placed').to_JSON())
        if form.published.data is True:
            actions.append(Action('c2pa.published').to_JSON())
        if form.removed.data is True:
            actions.append(Action('c2pa.removed').to_JSON())
        if form.resized.data is True:
            actions.append(Action('c2pa.resized').to_JSON())
        if form.transcoded.data is True:
            actions.append(Action('c2pa.transcoded').to_JSON())
        print(actions)
    return render_template('sign.html', upload=2, form=form)


@sign_blueprint.route('/update', methods=['GET', 'POST'])
def update():
    return render_template('sign.html', upload=0)


@sign_blueprint.route('/download', methods=['GET', 'POST'])
def download():
    return send_file(session['path'], as_attachment=True)
