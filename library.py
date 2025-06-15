import os
import shutil
import json
from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from markupsafe import escape
from werkzeug.utils import secure_filename
from urllib.parse import quote

try:
    import mammoth
except ImportError:
    mammoth = None

try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

library_bp = Blueprint('library_bp', __name__, url_prefix='/library')

################################################################################
# Вспомогательные функции
################################################################################

def get_user_library_root():
    """Возвращает путь к папке пользователя (или _guest)."""
    if 'user_id' not in session:
        user = '_guest'
    else:
        user = session['user_id']
    root = os.path.join('static', 'library', user)
    os.makedirs(root, exist_ok=True)
    return root

def gather_all_folders(base_dir, rel=""):
    """Сканируем папки рекурсивно (для Move-модалки)."""
    results = []
    folder_path = os.path.join(base_dir, rel)
    if os.path.isdir(folder_path):
        for entry in os.listdir(folder_path):
            full = os.path.join(folder_path, entry)
            if os.path.isdir(full):
                sub_rel = os.path.join(rel, entry).replace("\\","/")
                results.append(sub_rel if sub_rel else ".")
                results.extend(gather_all_folders(base_dir, sub_rel))
    return results

def convert_docx_to_html(filepath):
    """Используем mammoth для doc/docx -> html."""
    if not mammoth:
        return "<p><b>[mammoth not installed!]</b></p>"
    def inline_img_handler(img):
        import base64
        with img.open() as f:
            bin_data = f.read()
        encoded = base64.b64encode(bin_data).decode('ascii')
        return {
            "src": f"data:{img.content_type};base64,{encoded}",
            "alt": img.alt_text if img.alt_text else ""
        }
    options = {"convert_image": mammoth.images.inline(inline_img_handler)}
    with open(filepath,"rb") as f:
        result = mammoth.convert_to_html(f, convert_image=options["convert_image"])
        return result.value

def read_pdf_text(filepath):
    """Извлекаем текст из PDF (PyPDF2)."""
    if not PyPDF2:
        return "(PyPDF2 not installed.)"
    try:
        with open(filepath, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            out = ""
            for page in reader.pages:
                out += (page.extract_text() or "")
                out += "\n"
        return out
    except Exception as e:
        return f"Error reading PDF: {e}"

def read_text_file(filepath):
    """Просто читаем текст (если двоичный — заменяем ошибки)."""
    try:
        with open(filepath,'r', encoding='utf-8', errors='replace') as f:
            return f.read()
    except:
        return "Unable to read file as text."

################################################################################
# Основные маршруты
################################################################################

@library_bp.route('/all_folders_json')
def all_folders_json():
    """Для Move-модалки."""
    root = get_user_library_root()
    folds = gather_all_folders(root, "")
    if "." not in folds:
        folds.insert(0, ".")
    return jsonify(folds)

@library_bp.route('/move_item', methods=['POST'])
def move_item():
    """Move (или rename путем)."""
    root = get_user_library_root()
    old_path = request.form.get("old_path","").strip()
    new_path = request.form.get("new_path","").strip()

    old_full = os.path.join(root, old_path)
    if not old_path or not os.path.exists(old_full):
        return "Invalid old path", 400
    if not new_path:
        return "No new path", 400

    new_full = os.path.join(root, new_path)
    os.makedirs(os.path.dirname(new_full), exist_ok=True)
    os.rename(old_full, new_full)

    # Родитель
    parts = old_path.strip("/").split("/")
    if len(parts)>1:
        parent = "/".join(parts[:-1])
    else:
        parent = ""
    return redirect(url_for("library_bp.browse_library", subpath=parent))

@library_bp.route('/rename_item', methods=['POST'])
def rename_item():
    """Rename (old_path, new_name)."""
    root = get_user_library_root()
    old_path = request.form.get("old_path","").strip()
    new_name = request.form.get("new_name","").strip()

    old_full = os.path.join(root, old_path)
    if not old_path or not os.path.exists(old_full):
        return "Invalid old path",400
    if not new_name:
        return "No new name",400

    parts = old_path.strip("/").split("/")
    if len(parts)>1:
        parent = "/".join(parts[:-1])
    else:
        parent = ""
    new_full = os.path.join(root, parent, new_name)
    os.rename(old_full, new_full)
    return redirect(url_for("library_bp.browse_library", subpath=parent))

@library_bp.route('/', defaults={'subpath':''})
@library_bp.route('/<path:subpath>')
def browse_library(subpath):
    """
    Отображаем файлы/папки, doc/docx => предпросмотр + Multiple choice / Matching
    html => открываем по старой схеме (open_file).
    """
    root = get_user_library_root()
    target_dir = os.path.join(root, subpath) if subpath else root

    if not os.path.exists(target_dir):
        return f"Folder {escape(subpath)} does not exist",404

    folders, files = [], []
    for entry in os.listdir(target_dir):
        full = os.path.join(target_dir, entry)
        if os.path.isdir(full):
            folders.append(entry)
        else:
            files.append(entry)

    # parent
    parent_folder=None
    if subpath:
        parts = subpath.strip('/').split('/')
        if len(parts)>1:
            parent_folder = '/'.join(parts[:-1])
        else:
            parent_folder = ''

    return render_template(
        "library.html",
        subpath=subpath,
        current_folder=subpath if subpath else '.',
        parent_folder=parent_folder,
        folders=sorted(folders),
        files=sorted(files)
    )

@library_bp.route('/create_folder', defaults={'subpath':''}, methods=['POST'])
@library_bp.route('/<path:subpath>/create_folder', methods=['POST'])
def create_folder(subpath):
    """Создаем папку."""
    root = get_user_library_root()
    target_dir = os.path.join(root, subpath) if subpath else root
    folder_name = request.form.get("folder_name","").strip()
    if folder_name:
        new_folder = os.path.join(target_dir, folder_name)
        os.makedirs(new_folder, exist_ok=True)
    return redirect(url_for('library_bp.browse_library', subpath=subpath))

@library_bp.route('/upload_file', defaults={'subpath':''}, methods=['POST'])
@library_bp.route('/<path:subpath>/upload_file', methods=['POST'])
def upload_file(subpath):
    """Загрузка файла."""
    root = get_user_library_root()
    target_dir = os.path.join(root, subpath) if subpath else root
    file = request.files.get('file')
    if file:
        filename = secure_filename(file.filename)
        if filename:
            path = os.path.join(target_dir, filename)
            file.save(path)
    return redirect(url_for('library_bp.browse_library', subpath=subpath))

@library_bp.route('/<path:subpath>', methods=['POST'])
def delete_item(subpath):
    """Удаляем файл/папку."""
    root = get_user_library_root()
    target_path = os.path.join(root, subpath)
    if os.path.exists(target_path):
        if os.path.isfile(target_path):
            os.remove(target_path)
        else:
            shutil.rmtree(target_path)
    parts = subpath.strip('/').split('/')
    if len(parts)>1:
        parent='/'.join(parts[:-1])
    else:
        parent=''
    return redirect(url_for('library_bp.browse_library', subpath=parent))

@library_bp.route('/<path:subpath>/file/<filename>')
def open_file(subpath, filename):
    """Открываем файл inline, html => показываем iframe, (без raw HTML)."""
    if subpath==".":
        subpath=""
    root = get_user_library_root()
    target_dir = os.path.join(root, subpath)
    fullpath = os.path.join(target_dir, filename)
    if not os.path.exists(fullpath):
        return "File not found",404

    ext = os.path.splitext(filename)[1].lower()

    # 1) Изображения
    if ext in ['.png','.jpg','.jpeg','.gif','.bmp','.webp']:
        file_url = url_for('static', filename=f'library/{session.get("user_id","_guest")}/{subpath}/{filename}')
        return f"""
        <!DOCTYPE html><html><head><meta charset="UTF-8"><title>{escape(filename)}</title></head>
        <body style="font-family:Arial; background:#f0f0f0; text-align:center; padding:20px;">
          <h3>Image: {escape(filename)}</h3>
          <img src="{file_url}" style="max-width:80%; border:1px solid #ccc;"/>
          <p>You can right-click or drag to copy the image.</p>
          <p><a href="{url_for('library_bp.browse_library', subpath=subpath)}">← Back</a></p>
        </body>
        </html>"""

    # 2) doc/docx => mammoth => HTML
    elif ext in ['.doc','.docx']:
        html_code = convert_docx_to_html(fullpath)
        return f"""
        <h3>{escape(filename)}</h3>
        <div style="white-space:pre-wrap;">{html_code}</div>
        <p><a href="{url_for('library_bp.browse_library', subpath=subpath)}">← Back</a></p>
        """

    # 3) PDF => iframe + extracted text
    elif ext=='.pdf':
        file_url=url_for('static', filename=f'library/{session.get("user_id","_guest")}/{subpath}/{filename}')
        text_extract=read_pdf_text(fullpath)
        return f"""
        <h3>PDF File: {escape(filename)}</h3>
        <iframe src="{file_url}" style="width:80%;height:600px;"></iframe>
        <hr>
        <h4>Extracted text:</h4>
        <div style="white-space:pre-wrap;">{escape(text_extract)}</div>
        <p><a href="{url_for('library_bp.browse_library', subpath=subpath)}">← Back</a></p>
        """

    # 4) HTML/HTM => iframe ONLY (убрали raw HTML)
    elif ext in ['.html','.htm']:
        file_url=url_for('static', filename=f'library/{session.get("user_id","_guest")}/{subpath}/{filename}')
        return f"""
        <h3>HTML File: {escape(filename)}</h3>
        <iframe src="{file_url}" style="width:80%; height:600px; border:2px solid #666;"></iframe>
        <p><a href="{url_for('library_bp.browse_library', subpath=subpath)}">← Back</a></p>
        """

    # 5) txt/md/py/cs/cpp/json/yaml
    elif ext in ['.txt','.md','.py','.cs','.cpp','.json','.yaml']:
        text=read_text_file(fullpath)
        return f"""
        <h3>{escape(filename)}</h3>
        <div style="white-space:pre-wrap;">{escape(text)}</div>
        <p><a href="{url_for('library_bp.browse_library', subpath=subpath)}">← Back</a></p>
        """

    # fallback
    else:
        content=read_text_file(fullpath)
        return f"""
        <h3>{escape(filename)}</h3>
        <div style="white-space:pre-wrap;">{escape(content)}</div>
        <p><a href="{url_for('library_bp.browse_library', subpath=subpath)}">← Back</a></p>
        """

@library_bp.route('/preview_doc')
def preview_doc():
    """Для doc/docx AJAX-просмотра."""
    subpath = request.args.get("subpath","").strip()
    filename= request.args.get("filename","").strip()
    root = get_user_library_root()
    folder= os.path.join(root, subpath)
    full = os.path.join(folder, filename)
    if not os.path.exists(full):
        return "File not found"
    ext = os.path.splitext(filename)[1].lower()
    if ext not in [".doc",".docx"]:
        return "Not a doc/docx file!"
    html_code= convert_docx_to_html(full)
    return html_code
