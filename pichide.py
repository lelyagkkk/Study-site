import os
from flask import Blueprint, request, render_template, url_for
from werkzeug.utils import secure_filename

pichide_bp = Blueprint('pichide', __name__, url_prefix='/pichide')

UPLOAD_FOLDER = "static/uploads"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


@pichide_bp.route('/', methods=['GET','POST'])
def pichide():
    image_url = None
    if request.method == 'POST':
        file = request.files.get('file')
        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(file_path)
            image_url = url_for('static', filename=f'uploads/{filename}')
    return render_template('pichide.html', image_url=image_url)
