from flask import render_template, Blueprint

info_blueprint = Blueprint('info', __name__, template_folder='templates')


@info_blueprint.route('/info', methods=['GET'])
def info_page():
    return render_template('additional_info.html')
