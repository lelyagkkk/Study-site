import os
import random
from flask import Blueprint, request, render_template
from werkzeug.utils import secure_filename
import docx  # pip install python-docx

matching_bp = Blueprint('matching_bp', __name__, url_prefix='/matching')

# Сколько итоговых вариантов показывать для каждого вопроса
# (1 правильный + (MAX_OPTIONS - 1) неправильных).
MAX_OPTIONS = 4

def parse_docx_into_blocks(filepath):
    """
    Читаем .docx-файл и делим содержимое на «блоки»:
      - Строки без "↔" считаем заголовком блока (title).
      - Строки с "↔" добавляем как пару (left, right) в текущий блок.
    Пример структуры блока:
      {
        "title": "Epileptic Seizures",
        "pairs": [("Generalized seizure", "Loss of consciousness"), ...]
      }
    Возвращаем список таких блоков.
    """
    doc = docx.Document(filepath)
    lines = []
    for p in doc.paragraphs:
        txt = p.text.strip()
        if txt:
            lines.append(txt)

    blocks = []
    current_block = {"title": None, "pairs": []}

    for line in lines:
        if "↔" in line:
            left, right = line.split("↔", 1)
            left = left.strip()
            right = right.strip()
            current_block["pairs"].append((left, right))
        else:
            # считаем это заголовком нового блока
            if current_block["title"] or current_block["pairs"]:
                blocks.append(current_block)
            current_block = {
                "title": line,
                "pairs": []
            }
    # Добавляем последний блок
    if current_block["title"] or current_block["pairs"]:
        blocks.append(current_block)

    return blocks

def parse_text_into_blocks(raw_text):
    """
    Аналогичная логика, но для текста, введённого вручную:
      - Строки без "↔" => заголовок
      - Строки с "↔" => пара (left, right)
    """
    lines = [l.strip() for l in raw_text.splitlines() if l.strip()]
    blocks = []
    current_block = {"title": None, "pairs": []}

    for line in lines:
        if "↔" in line:
            left, right = line.split("↔", 1)
            left = left.strip()
            right = right.strip()
            current_block["pairs"].append((left, right))
        else:
            if current_block["title"] or current_block["pairs"]:
                blocks.append(current_block)
            current_block = {
                "title": line,
                "pairs": []
            }
    if current_block["title"] or current_block["pairs"]:
        blocks.append(current_block)

    return blocks

@matching_bp.route('/', methods=['GET','POST'])
def matching():
    """
    /matching:
    - Пользователь загружает .docx-файл либо вводит вручную (строки "A ↔ B").
    - Формируем список блоков (каждый со своим title и pairs).
    - Для каждой пары выдаём 1 правильный + (MAX_OPTIONS-1) неправильных вариантов.
    - Наверху NavBar, внизу бегущий человечек, при 100% правильных ответов → фейерверк.
    """
    blocks = []
    error_message = ""

    if request.method == 'POST':
        if 'word_file' in request.files and request.files['word_file'].filename:
            f = request.files['word_file']
            filename = secure_filename(f.filename)
            ext = os.path.splitext(filename)[1].lower()
            upload_dir = os.path.join('static', 'uploads')
            os.makedirs(upload_dir, exist_ok=True)
            full_path = os.path.join(upload_dir, filename)
            f.save(full_path)

            if ext == ".docx":
                try:
                    blocks = parse_docx_into_blocks(full_path)
                except Exception as e:
                    error_message = f"Error reading .docx: {e}"
            elif ext == ".doc":
                error_message = "File .doc is not supported. Please convert to .docx."
            else:
                error_message = f"Unsupported file format {ext}. Please use .docx or paste text."

            # Удалим файл, чтобы не захламлять
            os.remove(full_path)
        else:
            # Попытка прочитать текст вручную
            raw_text = request.form.get("input_text","").strip()
            if raw_text:
                blocks = parse_text_into_blocks(raw_text)

    # Собираем все "right"-стороны для генерации wrong-вариантов
    all_right = []
    for blk in blocks:
        for (l, r) in blk["pairs"]:
            all_right.append(r)

    final_blocks = []
    for blk in blocks:
        new_rows = []
        for (left, correct) in blk["pairs"]:
            wrong_candidates = [x for x in all_right if x != correct]
            random.shuffle(wrong_candidates)
            chosen_wrongs = wrong_candidates[:(MAX_OPTIONS - 1)]
            opts = [correct] + chosen_wrongs
            random.shuffle(opts)
            new_rows.append({
                "left": left,
                "correct": correct,
                "options": opts
            })
        final_blocks.append({
            "title": blk["title"],
            "rows": new_rows
        })

    return render_template(
        "matching.html",
        blocks=final_blocks,
        error_message=error_message
    )
