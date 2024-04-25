import base64

import flask
from flask import session, render_template, Blueprint, redirect, url_for, make_response, request
import folium
import c2pa
import json
from datetime import datetime
import pdfkit

lookup = {
    'color adjustments': 'Changes have been made to the tone, saturation or other areas.',
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

report_blueprint = Blueprint('report', __name__, template_folder='templates')


def make_map(lat, lng):
    map = folium.Map(location=(lat, lng), zoom_start=15, min_width=400, max_width=400, max_height=400)
    folium.Marker(location=[lat, lng], popup='This is the approximate location').add_to(map)
    return map._repr_html_()


@report_blueprint.route('/demo', methods=['GET', 'POST'])
def demo():
    session['file'] = 'static/test_image.jpg'
    return redirect(url_for('report.report'))


@report_blueprint.route('/download', methods=['GET', 'POST'])
def generate_report():
    with open(session['file'], 'rb') as f:
        image = f.read()
        b = base64.b64encode(bytearray(image)).decode('utf-8')
    ingredients = session['ingredients']
    for ingredient in ingredients:
        with open(ingredients[ingredient]['path'], 'rb') as f:
            image = f.read()
            ingredients[ingredient]['bytes'] = base64.b64encode(bytearray(image)).decode('utf-8')
    # Adapted from https://www.youtube.com/watch?v=C8jxInLM9nM
    rendered_pdf = render_template('report_download.html',
                                   filename=session['filename'],
                                   uploaded_image=b,
                                   date=datetime.now().strftime('%d %B, %Y'),
                                   ai=session['ai'],
                                   actions=session['actions'],
                                   signer=session['signer_info'],
                                   camera_info=session['metadata'],
                                   ingredients=ingredients,
                                   errors=session['errors'])
    options = {
        'page-size': 'A4',
        'margin-top': '1in',
        'margin-bottom': '1in',
        'margin-left': '1in',
        'margin-right': '1in',
        'footer-right': '[page]',
        'enable-local-file-access': None
    }
    config = pdfkit.configuration(wkhtmltopdf=r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe')
    pdf = pdfkit.from_string(rendered_pdf, False, configuration=config, options=options)
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=credentials_report.pdf'
    return response


@report_blueprint.route('/report', methods=['GET', 'POST'])
def report():
    try:
        json_store = json.loads(c2pa.read_file(session['file'], 'static/extract'))
        print(json.dumps(json_store, indent=2))
    except c2pa.c2pa.Error.ManifestNotFound:
        return render_template('report.html', not_found=True, path=session['file'])

    modifications = {}
    signer_info = {}
    ingredients = {}
    errors = {}
    metadata = {}
    ai = False
    m = None
    filename = ''
    session['actions'] = modifications
    session['signer_info'] = signer_info
    session['metadata'] = metadata
    session['ai'] = ai
    session['errors'] = errors
    session['ingredients'] = ingredients
    session['filename'] = filename

    if 'validation_status' in json_store.keys():
        for validation in json_store['validation_status']:
            errors[validation['code']] = validation['explanation']
        session['errors'] = errors
        return render_template('report.html', not_found=False, path=session['file'], errors=errors)

    active_manifest = json_store['manifests'][json_store['active_manifest']]
    session['filename'] = json_store['manifests'][json_store['active_manifest']]['title']
    signer_info['issuer'] = active_manifest['signature_info']['issuer']
    signer_info['date'] = datetime.fromisoformat(active_manifest['signature_info']['time']).strftime('%d %B, %Y')

    for assertion in active_manifest['assertions']:
        if 'stds.exif' in assertion['label']:
            exif_keys = assertion['data'].keys()
            if 'EXIF:GPSLatitude' in exif_keys:
                metadata['latitude'] = float(assertion['data']['EXIF:GPSLatitude'])
            if 'EXIF:GPSLongitude' in exif_keys:
                metadata['longitude'] = float(assertion['data']['EXIF:GPSLongitude'])
            if 'EXIF:DateTime' in exif_keys:
                metadata['date'] = datetime.strptime(assertion['data']['EXIF:DateTime'], '%Y:%m:%d %H:%M:%S').strftime('%d %B, %Y')
            if ('EXIF:Make' in exif_keys) and ('EXIF:Model' in exif_keys):
                metadata['device'] = assertion['data']['EXIF:Make'] + " " + assertion['data']['EXIF:Model']
                ai = False
            print(metadata)

        if 'c2pa.actions' in assertion['label']:
            for action in assertion['data']['actions']:
                if action['action'] == 'c2pa.created' and 'digitalSourceType' in action.keys():
                    if action['digitalSourceType'] == 'http://cv.iptc.org/newscodes/digitalsourcetype/trainedAlgorithmicMedia':
                        ai = True
                action_string = str(action['action']).replace('c2pa.', '').replace('_', ' ')
                modifications[action_string] = lookup[action_string]
            session['actions'] = modifications

    for ingredient in active_manifest['ingredients']:
        if ingredient['relationship'] == 'inputTo':
            ai = True
        ingredient_path = 'static/extract/' + ingredient['thumbnail']['identifier']
        ingredients[str(ingredient['title'])] = {
            'path': ingredient_path,
            'use': ingredient['relationship']
        }
    session['ingredients'] = ingredients

    session['metadata'] = metadata
    session['ai'] = ai
    session['signer_info'] = signer_info
    if ('latitude' in metadata.keys()) and ('longitude' in metadata.keys()):
        m = make_map(metadata['latitude'], metadata['longitude'])

    return render_template('report.html', not_found=False, modifications=modifications, errors=errors,
                           ingredients=ingredients, ai=ai, metadata=metadata,
                           path=session['file'], signer=signer_info, map=m)
