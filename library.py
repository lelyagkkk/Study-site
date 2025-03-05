import os
from flask import Blueprint, render_template_string, request, redirect, url_for, send_from_directory
from markupsafe import escape
from werkzeug.utils import secure_filename
from urllib.parse import quote
import PyPDF2  # Для PDF извлечения текста
import shutil

library_bp = Blueprint('library', __name__, url_prefix='/library')

LIBRARY_FOLDER = "static/library"
os.makedirs(LIBRARY_FOLDER, exist_ok=True)

# HTML шаблон главной страницы библиотеки
LIBRARY_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>My Library</title>
    <style>
      body {
        margin: 0;
        font-family: Arial, sans-serif;
        background: linear-gradient(to bottom, #a8edea, #fed6e3);
        min-height: 100vh;
        display: flex;
        flex-direction: column;
        align-items: center;
        color: #333;
      }
      h1 {
        margin-top: 20px;
        text-align: center;
      }
      .library-container {
        background: white;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.1);
        width: 90%;
        max-width: 600px;
        margin-top: 20px;
      }
      .nav-links {
        display: flex;
        gap: 10px;
        margin: 20px;
      }
      .nav-links a {
        text-decoration: none;
        padding: 14px 20px;
        border-radius: 12px;
        font-size: 18px;
        transition: 0.3s;
        color: white;
        background-color: #ff69b4;
      }
      .nav-links a:hover {
        opacity: 0.8;
      }
      .folder-list, .file-list {
        list-style: none;
        padding-left: 0;
      }
      .folder-list li, .file-list li {
        margin: 5px 0;
        display: flex;
        align-items: center;
        gap: 10px;
      }
      .item-link {
        color: #007bff;
        text-decoration: none;
        transition: color 0.2s;
      }
      .item-link:hover {
        color: #0056b3;
        text-decoration: underline;
      }
      .delete-btn {
        padding: 4px 8px;
        background: #f44336;
        color: #fff;
        border: none;
        border-radius: 6px;
        font-size: 14px;
        cursor: pointer;
        transition: transform 0.2s;
      }
      .delete-btn:hover {
        transform: scale(1.05);
      }
      form {
        margin: 10px 0;
      }
      input[type="text"] {
        padding: 6px;
        border: 2px solid #ddd;
        border-radius: 6px;
      }
      .btn {
        padding: 6px 14px;
        border-radius: 6px;
        border: none;
        background: linear-gradient(135deg, #2196F3, #03A9F4);
        color: white;
        cursor: pointer;
        transition: transform 0.3s, box-shadow 0.3s;
      }
      .btn:hover {
        transform: scale(1.08);
        box-shadow: 0 0 8px rgba(255,255,255,0.3);
      }
      .back-link a {
        color: #f44336;
        text-decoration: none;
        font-weight: bold;
      }
      .back-link a:hover {
        text-decoration: underline;
      }
    </style>
</head>
<body>
  <h1>My Library</h1>

  <div class="nav-links">
    <a href="{{ url_for('index') }}">Main</a>
    <a href="{{ url_for('pichide.pichide') }}">Pichide</a>
    <a href="{{ url_for('coding.coding') }}">Coding</a>
    <a href="{{ url_for('quizz.quizz') }}">Quizz</a>
  </div>

  <div class="library-container">
    {% if parent_folder %}
      <div class="back-link">
        <a href="{{ url_for('library.browse_library', subpath=parent_folder) }}">← Up to parent folder</a>
      </div>
    {% endif %}

    <h3>Folders in {{ current_folder|default('root') }}</h3>
    <ul class="folder-list">
      {% for f in folders %}
        <li>
          <a class="item-link" href="{{ url_for('library.browse_library', subpath=(subpath + '/' + f).strip('/')) }}">
            📁 {{ f }}
          </a>
          <form method="post" action="{{ url_for('library.delete_item', subpath=(subpath + '/' + f).strip('/')) }}" style="display:inline;">
            <button type="submit" class="delete-btn">Delete</button>
          </form>
        </li>
      {% endfor %}
    </ul>

    <h3>Files in {{ current_folder|default('root') }}</h3>
    <ul class="file-list">
      {% for file in files %}
        <li>
          <a class="item-link" href="{{ url_for('library.open_file', subpath=subpath, filename=file) }}">
            📄 {{ file }}
          </a>
          <form method="post" action="{{ url_for('library.delete_item', subpath=(subpath + '/' + file).strip('/')) }}" style="display:inline;">
            <button type="submit" class="delete-btn">Delete</button>
          </form>
        </li>
      {% endfor %}
    </ul>

    <!-- Создать подпапку -->
    <form method="post" action="{{ url_for('library.create_folder', subpath=subpath) }}">
      <input type="text" name="folder_name" placeholder="New folder name">
      <button type="submit" class="btn">Create Folder</button>
    </form>

    <!-- Загрузить файл -->
    <form method="post" action="{{ url_for('library.upload_file', subpath=subpath) }}" enctype="multipart/form-data">
      <input type="file" name="file">
      <button type="submit" class="btn">Upload File</button>
    </form>
  </div>
</body>
</html>
"""

#
# 1) Просмотр папки
#
@library_bp.route('/', defaults={'subpath':''})
@library_bp.route('/<path:subpath>')
def browse_library(subpath):
    """Отображает содержимое папки subpath (список подпапок и файлов)."""
    target_dir = os.path.join(LIBRARY_FOLDER, subpath)
    if not os.path.exists(target_dir):
        return f"Folder {escape(subpath)} does not exist", 404

    folders, files = [], []
    for entry in os.listdir(target_dir):
        fullpath = os.path.join(target_dir, entry)
        if os.path.isdir(fullpath):
            folders.append(entry)
        else:
            files.append(entry)

    # Родительская папка (кнопка "Up")
    parent_folder = None
    if subpath:
        parts = subpath.strip('/').split('/')
        if len(parts) > 1:
            parent_folder = '/'.join(parts[:-1])
        else:
            parent_folder = ''  # корень

    return render_template_string(
        LIBRARY_TEMPLATE,
        subpath=subpath,
        current_folder=subpath if subpath else 'root',
        parent_folder=parent_folder,
        folders=sorted(folders),
        files=sorted(files),
    )

#
# 2) Создать подпапку
#
@library_bp.route('/create_folder', defaults={'subpath':''}, methods=['POST'])
@library_bp.route('/<path:subpath>/create_folder', methods=['POST'])
def create_folder(subpath):
    folder_name = request.form.get('folder_name','').strip()
    if folder_name:
        target_dir = os.path.join(LIBRARY_FOLDER, subpath, folder_name)
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)
    return redirect(url_for('library.browse_library', subpath=subpath))

#
# 3) Загрузить файл
#
@library_bp.route('/upload_file', defaults={'subpath':''}, methods=['POST'])
@library_bp.route('/<path:subpath>/upload_file', methods=['POST'])
def upload_file(subpath):
    file = request.files.get('file')
    if file:
        filename = secure_filename(file.filename)
        if filename:
            path = os.path.join(LIBRARY_FOLDER, subpath, filename)
            file.save(path)
    return redirect(url_for('library.browse_library', subpath=subpath))

#
# 4) Удалить файл/папку
#
@library_bp.route('/<path:subpath>', methods=['POST'])
def delete_item(subpath):
    """Удаляем либо файл, либо папку (рекурсивно)."""
    target_path = os.path.join(LIBRARY_FOLDER, subpath)
    if os.path.exists(target_path):
        if os.path.isfile(target_path):
            os.remove(target_path)
        else:
            shutil.rmtree(target_path)
    # Вернёмся к родительской папке
    parts = subpath.strip('/').split('/')
    if len(parts)>1:
        parent = '/'.join(parts[:-1])
    else:
        parent = ''
    return redirect(url_for('library.browse_library', subpath=parent))

#
# 5) Открыть файл
#
@library_bp.route('/<path:subpath>/file/<filename>')
def open_file(subpath, filename):
    """
    Открывает файл и даёт возможность:
    - Copy all (если текст)
    - Перейти в разные режимы: 
      * для изображений => Image Hide
      * для кода => (trace/memory)
      * для txt/pdf => main(fill/remove), quiz(mc/fill).
    """
    fullpath = os.path.join(LIBRARY_FOLDER, subpath, filename)
    if not os.path.exists(fullpath):
        return "File not found", 404

    ext = os.path.splitext(filename)[1].lower()

    # Базовая заготовка под кнопку "Copy all" (для текстовых форматов)
    copy_button = """
    <button onclick="navigator.clipboard.writeText(document.getElementById('textToCopy').innerText)">
      Copy all
    </button>
    """

    # ============ Изображения ============
    if ext in ['.png','.jpg','.jpeg','.gif']:
        file_url = url_for('static', filename=f'library/{subpath}/{filename}')
        # Единственный доступный режим: Image Hide
        return f"""
        <h3>Image: {escape(filename)}</h3>
        <img src="{file_url}" style="max-width:400px;border:1px solid #ccc">

        <p><strong>Available Mode:</strong><br>
          <a href="{url_for('pichide.pichide')}">Image Hide</a>
        </p>
        """

    # ============ Код-файлы ============
    elif ext in ['.py','.cs','.cpp','.ipynb']:  
        # Прочитаем как текст
        with open(fullpath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        text_quoted = quote(content)

        # Coding Practice => trace mode, memory mode
        trace_url = url_for('coding.coding') + "?mode=trace&trace_code_input=" + text_quoted
        memory_url = url_for('coding.coding') + "?mode=memory&trace_code_input=" + text_quoted

        return f"""
        <h3>Code File {escape(filename)}</h3>
        <div id="textToCopy" style="background:#f0f0f0;white-space:pre-wrap;max-height:300px;overflow:auto">
{escape(content)}
        </div>
        {copy_button}
        <p><strong>Available Modes (Coding):</strong><br>
          <a href="{trace_url}" target="_blank">Trace Mode</a> |
          <a href="{memory_url}" target="_blank">Memory Mode</a>
        </p>
        """

    # ============ PDF / Тексты (для Main/Quiz) ============
    elif ext == '.pdf':
        # Пробуем извлечь текст
        try:
            with open(fullpath, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            return f"Error reading PDF: {escape(str(e))}"

        # "Main" => fill / remove
        # "Quiz" => multiple choice / fill
        text_quoted = quote(text)
        main_fill = "/?mode=fill&input_text=" + text_quoted
        main_remove = "/?mode=remove&input_text=" + text_quoted

        quiz_mc = url_for('quizz.quizz') + "?mode=multiple_choice&input_text=" + text_quoted
        quiz_fill = url_for('quizz.quizz') + "?mode=fill_blanks&input_text=" + text_quoted

        return f"""
        <h3>PDF File: {escape(filename)}</h3>
        <div id="textToCopy" style="background:#f0f0f0;white-space:pre-wrap;max-height:300px;overflow:auto">
{escape(text)}
        </div>
        {copy_button}
        <p><strong>Available Modes:</strong><br>
          <b>Main</b>:
            <a href="{main_fill}" target="_blank">Fill in the Blanks</a> |
            <a href="{main_remove}" target="_blank">Remove Letters</a>
          <br>
          <b>Quiz</b>:
            <a href="{quiz_mc}" target="_blank">Multiple Choice</a> |
            <a href="{quiz_fill}" target="_blank">Fill in the Blanks</a>
        </p>
        """

    elif ext in ['.txt','.md']:
        # Аналогично: Main => fill/remove, Quiz => multiple/fill
        with open(fullpath, 'r', encoding='utf-8', errors='replace') as f:
            text = f.read()
        text_quoted = quote(text)

        main_fill = "/?mode=fill&input_text=" + text_quoted
        main_remove = "/?mode=remove&input_text=" + text_quoted
        quiz_mc = url_for('quizz.quizz') + "?mode=multiple_choice&input_text=" + text_quoted
        quiz_fill = url_for('quizz.quizz') + "?mode=fill_blanks&input_text=" + text_quoted

        return f"""
        <h3>Text File: {escape(filename)}</h3>
        <div id="textToCopy" style="background:#f0f0f0;white-space:pre-wrap;max-height:300px;overflow:auto;">
{escape(text)}
        </div>
        {copy_button}
        <p><strong>Available Modes:</strong><br>
          <b>Main</b>:
            <a href="{main_fill}" target="_blank">Fill in the Blanks</a> |
            <a href="{main_remove}" target="_blank">Remove Letters</a>
          <br>
          <b>Quiz</b>:
            <a href="{quiz_mc}" target="_blank">Multiple Choice</a> |
            <a href="{quiz_fill}" target="_blank">Fill in the Blanks</a>
        </p>
        """

    else:
        # Остальные файлы => скачать
        return send_from_directory(os.path.join(LIBRARY_FOLDER, subpath), filename, as_attachment=True)
