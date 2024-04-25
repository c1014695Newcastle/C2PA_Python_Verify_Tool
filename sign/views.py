import json
from app import app
import c2pa
from flask import render_template, Blueprint, request
from forms import UploadSignForm, FormSign
from PIL import Image
from PIL.TiffImagePlugin import IFDRational as irational
from PIL.ExifTags import TAGS
import io, os
import requests
from werkzeug.utils import secure_filename
from flask import session, send_file

sign_blueprint = Blueprint('sign', __name__, template_folder='templates')

supported_exif_tags = [
    'EXIF:ApertureValue', 'EXIF:BrightnessValue', 'EXIF:CFAPattern', 'EXIF:ColorSpace', 'EXIF:CompressedBitsPerPixel',
    'EXIF:Contrast', 'EXIF:CustomRendered', 'EXIF:DateTimeDigitized', 'EXIF:DateTimeOriginal',
    'EXIF:DeviceSettingDescription', 'EXIF:DigitalZoomRatio', 'EXIF:EXIFVersion', 'EXIF:ExposureBiasValue',
    'EXIF:ExposureIndex', 'EXIF:ExposureMode', 'EXIF:ExposureProgram', 'EXIF:ExposureTime', 'EXIF:FileSource',
    'EXIF:Flash', 'EXIF:FlashEnergy', 'EXIF:FlashpixVersion', 'EXIF:FNumber', 'EXIF:FocalLength',
    'EXIF:FocalLengthIn35mmFilm', 'EXIF:FocalPlaneResolutionUnit', 'EXIF:FocalPlaneXResolution',
    'EXIF:FocalPlaneYResolution', 'EXIF:GainControl', 'EXIF:ImageUniqueID', 'EXIF:ISOSpeedRatings', 'EXIF:LightSource',
    'EXIF:MaxApertureValue', 'EXIF:MeteringMode', 'EXIF:OECF', 'EXIF:PixelXDimension', 'EXIF:PixelYDimension',
    'EXIF:RelatedSoundFile', 'EXIF:Saturation', 'EXIF:SceneCaptureType', 'EXIF:SceneType', 'EXIF:SensingMethod',
    'EXIF:Sharpness', 'EXIF:ShutterSpeedValue', 'EXIF:SpatialFrequencyResponse', 'EXIF:SpectralSensitivity',
    'EXIF:SubjectArea', 'EXIF:SubjectDistance', 'EXIF:SubjectDistanceRange', 'EXIF:SubjectLocation',
    'EXIF:WhiteBalance', 'EXIF:GPSAltitude', 'EXIF:GPSAltitudeRef', 'EXIF:GPSDestBearing', 'EXIF:GPSDestBearingRef',
    'EXIF:GPSDestDistance', 'EXIF:GPSDestDistanceRef', 'EXIF:GPSDestLatitude', 'EXIF:GPSDestLongitude',
    'EXIF:GPSDifferential', 'EXIF:GPSDOP', 'EXIF:GPSImgDirection', 'EXIF:GPSImgDirectionRef', 'EXIF:GPSLatitude',
    'EXIF:GPSLongitude', 'EXIF:GPSMapDatum', 'EXIF:GPSMeasureMode', 'EXIF:GPSProcessingMethod', 'EXIF:GPSSatellites',
    'EXIF:GPSSpeed', 'EXIF:GPSSpeedRef', 'EXIF:GPSStatus', 'EXIF:GPSTimeStamp', 'EXIF:GPSTrack', 'EXIF:GPSTrackRef',
    'EXIF:GPSVersionID'
]


def make_thumbnail(image_bytes, size=(100, 100)):
    thumbnail = Image.open(io.BytesIO(image_bytes))
    return thumbnail.thumbnail(size).tobytes()


def read_exif_data(image_bytes):
    exif = Image.open(io.BytesIO(image_bytes)).getexif()
    metadata = {
        '@context': {
            'EXIF': 'http://ns.adobe.com/exif/1.0/'
        }
    }
    for tag_ID in exif:
        tag_name = TAGS.get(tag_ID, tag_ID)
        label = 'EXIF:{}'.format(tag_name.split('.')[-1])
        if label not in supported_exif_tags:
            pass
        data = exif.get(tag_ID)
        if isinstance(data, bytes):
            data = data.decode()
        if type(data) is not irational:
            metadata[label] = data
        else:
            metadata[label] = float(data)
    return metadata


def make_ingredient(ingredient, relationship):
    return {
        'title': ingredient.filename,
        'format': ingredient.content_type,
        'instance_id': 'test',
        'relationship': relationship,
    }


@sign_blueprint.route('/sign', methods=['GET'])
def sign():
    return render_template('sign.html', upload=0)


@sign_blueprint.route('/upload', methods=['GET', 'POST'])
def manifest_upload():
    form = UploadSignForm()
    if form.validate_on_submit():
        if form.to_sign.data is not None:
            img_filename = form.to_sign.data.filename
            form.to_sign.data.save(app.config['VERIFY_UPLOAD_FOLDER'] + img_filename)
        else:
            upload = Image.open(requests.get(form.url_to_sign.data, stream=True).raw)
            img_filename = secure_filename(upload.filename)
            path = app.config['VERIFY_UPLOAD_FOLDER'].format(img_filename)
            upload.save(path, format='JPEG')

        manifest_name = '{}.json'.format(img_filename.split('.')[0])
        form.manifest.data.save(app.config['TO_SIGN_FOLDER'] + manifest_name)
        key = open('cryptography/key.pem', "rb").read()
        cert = open('cryptography/cert.pem', "rb").read()
        signer_info = c2pa.SignerInfo('es256', sign_cert=cert, private_key=key, ta_url="http://timestamp.digicert.com")

        image_name = app.config['TO_SIGN_FOLDER'] + img_filename
        signed_name = app.config['TO_SIGN_FOLDER'] + img_filename
        m = open(app.config['TO_SIGN_FOLDER'] + manifest_name, "r").read()

        c2pa.sign_file(image_name, signed_name, m, signer_info, '')
        session['path'] = signed_name
        return render_template('signed.html', path=signed_name)

    return render_template('sign.html', upload=1, form=form)


@sign_blueprint.route('/form', methods=['GET', 'POST'])
def manifest_form():
    form = FormSign()
    if form.validate_on_submit():
        manifest = {
            'claim_generator': 'c1014695 dissertation',
            'ingredients': [],
            'assertions': []
        }
        actions = []
        img_filename = form.to_sign.data.filename
        form.to_sign.data.save(app.config['TO_SIGN_FOLDER'] + img_filename)
        directory_path = app.config['INGREDIENT_UPLOAD_FOLDER']
        print('DIRECTORY PATH ' + directory_path)
        if form.ai_image.data == 'True':
            actions.append({
                'action': 'c2pa.created',
                'digitalSourceType': 'http://cv.iptc.org/newscodes/digitalsourcetype/trainedAlgorithmicMedia'
            })
        if form.metadata.data == 'True':
            with open(app.config['TO_SIGN_FOLDER'] + img_filename, 'rb') as f:
                image_bytes = f.read()
            metadata = read_exif_data(image_bytes)
            manifest['assertions'].append({
                'label': 'stds.exif',
                'data': metadata
            })

        print('THIS IS THE DATA:', form.placed_ingredients.data)
        # Adapted from https://www.reddit.com/r/flask/comments/10297ge/how_to_determine_if_file_upload_is_empty/
        if all((file.filename != '') for file in form.placed_ingredients.data):
            for ingredient in form.placed_ingredients.data:
                filename = secure_filename(ingredient.filename)
                path = os.path.join(app.config['INGREDIENT_UPLOAD_FOLDER'], filename)
                ingredient.save(path)
                placed_ingredient_dict = json.loads(c2pa.read_ingredient_file(path, directory_path))
                manifest['ingredients'].append(placed_ingredient_dict)
                actions.append({
                    'action': 'c2pa.placed',
                    'instance_id': placed_ingredient_dict['instance_id']
                })

        if form.opened_ingredient.data:
            path = app.config['INGREDIENT_UPLOAD_FOLDER'] + form.opened_ingredient.data.filename
            form.opened_ingredient.data.save(path)
            opened_ingredient_dict = json.loads(c2pa.read_ingredient_file(path, directory_path))
            opened_ingredient_dict['relationship'] = 'parentOf'
            manifest['ingredients'].append(opened_ingredient_dict)
            actions.append({
                'action': 'c2pa.opened',
                'instance_id': opened_ingredient_dict['instance_id']
            })

        if form.color_adjustments.data == 'True':
            actions.append({'action': 'c2pa.colour_adjustments'})
        if form.converted.data == 'True':
            actions.append({'action': 'c2pa.converted'})
        if form.cropped.data == 'True':
            actions.append({'action': 'c2pa.cropped'})
        if form.drawing.data == 'True':
            actions.append({'action': 'c2pa.drawing'})
        if form.edited.data == 'True':
            actions.append({'action': 'c2pa.edited'})
        if form.filtered.data == 'True':
            actions.append({'action': 'c2pa.filtered'})
        if form.orientation == 'True':
            actions.append({'action': 'c2pa.opened'})
        if form.published.data == 'True':
            actions.append({'action': 'c2pa.published'})
        if form.removed.data == 'True':
            actions.append({'action': 'c2pa.removed'})
        if form.resized.data == 'True':
            actions.append({'action': 'c2pa.resized'})
        if form.transcoded.data == 'True':
            actions.append({'action': 'c2pa.transcoded'})

        if actions is not None:
            manifest['assertions'].append({
                'label': 'c2pa.actions',
                'data': {'actions': actions}
            })
        image_name = app.config['TO_SIGN_FOLDER'] + img_filename
        signed_name = 'static/signed/{}'.format(img_filename)

        print(json.dumps(manifest, indent=2))

        key = open('cryptography/key.pem', "rb").read()
        cert = open('cryptography/cert.pem', "rb").read()
        signer_info = c2pa.SignerInfo('es256', sign_cert=cert, private_key=key, ta_url="http://timestamp.digicert.com")
        c2pa.sign_file(image_name, signed_name, json.dumps(manifest), signer_info, directory_path)
        session['path'] = signed_name
        return render_template('signed.html', path=signed_name)

    return render_template('sign.html', upload=2, form=form)


@sign_blueprint.route('/update', methods=['GET', 'POST'])
def update():
    return render_template('sign.html', upload=0)


@sign_blueprint.route('/download', methods=['GET', 'POST'])
def download_image():
    print(session['path'])
    return send_file(session['path'], as_attachment=True)
