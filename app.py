from flask import Flask, render_template, redirect, url_for, request, session
from werkzeug.utils import secure_filename

import os
import requests
from forms import UploadForm

from PIL import Image

app = Flask(__name__)
app.config['SECRET_KEY'] = 'longandrandomkey'


@app.errorhandler(404)  # Not Found
@app.route('/404', endpoint='internal_error_404')
def internal_error_404(error):
    return render_template('error/404.html'), 404


@app.errorhandler(500)  # Server error
@app.route('/404', endpoint='internal_error_500')
def internal_error_404(error):
    return render_template('error/500.html'), 500


from info.views import info_blueprint
from report.views import report_blueprint
from sign.views import sign_blueprint

app.register_blueprint(info_blueprint)
app.register_blueprint(report_blueprint)
app.register_blueprint(sign_blueprint)


@app.route('/', methods=['GET', 'POST'])
def index():
    form = UploadForm()
    if form.validate_on_submit():
        if form.upload.data:
            name = secure_filename(form.upload.data.filename)
            session['file'] = os.path.join('static/uploads', name)
            form.upload.data.save(os.path.join('static/uploads', name))
        else:
            file = Image.open(requests.get(form.url.data, stream=True).raw)
            name = secure_filename('url_image.jpg')
            session['file'] = os.path.join('static/uploads', name)
            file.save('static/uploads/{}'.format(name), format='JPEG')
        return redirect(url_for('report.report'))
    return render_template('upload.html', form=form)


@app.route('/sign', methods=['GET', 'POST'])
def sign():
    return render_template('sign.html')


if __name__ == '__main__':
    app.run(debug=True)
