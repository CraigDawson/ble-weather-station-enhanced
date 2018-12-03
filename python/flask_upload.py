import os

from flask import (Flask, flash, jsonify, redirect, render_template, request,
                   send_from_directory, url_for)
from icecream import ic
from werkzeug import secure_filename

UPLOAD_FOLDER = './uploads'
ALLOWED_EXTENSIONS = set(
    ['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'svg', 'csv'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# public example: app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
app.secret_key = b'%\x81\xc7\x86\xa3\xbdl\x0e\xc8\xa6{\x8dM!\xe29'

icoPath = os.path.join(app.root_path, 'static')

UPLOAD_DIRECTORY = './uploads'


@app.route('/filesBarriersEngagingTelecomRelating')  # show files
def list_files():
    """Endpoint to list files on the server."""
    files = []
    for filename in os.listdir(UPLOAD_DIRECTORY):
        path = os.path.join(UPLOAD_DIRECTORY, filename)
        ic(path, filename)
        if os.path.isfile(path):
            files.append(filename)
    return jsonify(files)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/favicon.ico')
def favicon():
    ''' Standard favicon.ico delevery '''
    return send_from_directory(
        icoPath, 'favicon.ico', mimetype='image/vnd.microsoft.icon')


@app.route('/uploadAlgeriaFreedomBraceletWorlds', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(url_for('uploaded_files', filename=filename))
    return render_template("upload.html")


@app.route('/')
def main_page():
    return render_template("index.html")


@app.route('/uploads/<filename>')
def uploaded_files(filename):
    ic(app.config['UPLOAD_FOLDER'])
    ic(filename)
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
