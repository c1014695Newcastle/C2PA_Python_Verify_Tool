import flask
from flask import session, render_template, Blueprint, redirect, url_for
import folium
import c2pa
import json
from datetime import datetime

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
    folium.Marker(location=[lat, lng]).add_to(map)
    return map._repr_html_()

@report_blueprint.route('/compare', methods=['GET','POST'])
def compare(original, path):
    return redirect(url_for('report'), original=original, compare_path=path)

@report_blueprint.route('/report', methods=['GET', 'POST'])
def report():
    name = session['file']
    try:
        json_store = json.loads(c2pa.read_file(name, 'verify/extract/extract'))
        print(json.dumps(json_store, indent=2))
    except c2pa.c2pa.Error.ManifestNotFound:
        return render_template('report.html', not_found=True, path=name)

    modifications = []
    signer_info = {}
    ingredients = {}
    errors = []
    metadata = {}
    ai = False
    m = None

    for manifest in json_store['manifests']:
        if manifest == json_store['active_manifest']:
            signer_info['issuer'] = json_store['manifests'][manifest]['signature_info']['issuer']
            signer_info['date'] = datetime.fromisoformat(json_store['manifests'][manifest]['signature_info']['time']).strftime('%d %B, %Y')

            for action in json_store['manifests'][manifest]['assertions']:
                if action['label'] == 'stds.exif' or action['label'] == 'c2pa.metadata':
                    keys = action['data'].keys()
                    if 'EXIF:GPSLatitude' in keys:
                        metadata['latitude'] = float(action['data']['EXIF:GPSLatitude'])
                    if 'EXIF:GPSLongitude' in keys:
                        metadata['longitude'] = float(action['data']['EXIF:GPSLongitude'])
                    if 'EXIF:Make' in keys and 'Exif:Model':
                        metadata['device'] = action['data']['EXIF:Make'] + " " + action['data']['EXIF:Model']
                        ai = False

                if action['label'] == 'c2pa.actions':
                    for a in action['data']['actions']:
                        if a['action'] == 'c2pa.created' and ('digitalSourceType' in a.keys()):
                            if a['digitalSourceType'] == 'http://cv.iptc.org/newscodes/digitalsourcetype/trainedAlgorithmicMedia':
                                ai = True
                        action_string = str(a['action']).replace('c2pa.', '')
                        action_string = action_string.replace('_', ' ')
                        modifications.append(action_string)

            for ingredient in json_store['manifests'][manifest]['ingredients']:
                if ingredient['relationship'] == 'inputTo':
                    ai = True
                ingredient_path = 'static/extract/'+ingredient['thumbnail']['identifier']
                ingredients[str(ingredient['title'])] = {
                    'path': ingredient_path,
                    'use' : ingredient['relationship']}

    if 'validation_status' in json_store.keys():
        for validation in json_store['validation_status']:
            errors.append(str(validation['code']))

    if 'latitude' in metadata.keys() and 'longitude' in metadata.keys():
        m = make_map(metadata['latitude'], metadata['longitude'])

    return render_template('report.html', not_found=False, modifications=modifications, errors=errors, ingredients=ingredients, ai=ai, metadata=metadata,
                           path=name, signer=signer_info, lookup=lookup, map=m)


