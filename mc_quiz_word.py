import re
import random
import os
from flask import Blueprint, request, render_template
from markupsafe import escape
import docx  # Не забудьте: pip install python-docx

mc_quiz_word_bp = Blueprint('mc_quiz_word', __name__)

def process_word_quiz(doc_path):
    """
    Считывает doc/docx-файл, где каждая группа выглядит так:
      (строка вопроса)
      ✓ - вариант
      ✗ - вариант
      ...
    (пустая строка) => конец группы
    """
    document = docx.Document(doc_path)
    paragraphs = [p.text.strip() for p in document.paragraphs if p.text.strip()]

    quiz_questions = []
    i = 0
    question_index = 0
    while i < len(paragraphs):
        question = paragraphs[i]
        i += 1
        options = []
        correct_answer = None

        # собираем варианты: строки начинаются с "✓" или "✗"
        while i < len(paragraphs) and (paragraphs[i].startswith("✓") or paragraphs[i].startswith("✗")):
            line = paragraphs[i]
            parts = line.split("-", 1)
            if len(parts) == 2:
                marker = parts[0].strip()
                option_text = parts[1].strip()
                options.append(option_text)
                if marker.startswith("✓"):
                    correct_answer = option_text
            i += 1

        # Если всё ок, генерируем HTML
        if question and options and correct_answer:
            html = f'<p>{escape(question)}</p>'
            html += '<div class="mc-options" data-correct="{escape(correct_answer)}">'

            random.shuffle(options)
            for opt in options:
                html += (
                    f'<div class="mc-option-row" data-correct="{escape(correct_answer)}">'
                    f'  <input type="radio" name="q_{question_index}">'
                    f'  <span class="mc-option-label">{escape(opt)}</span>'
                    f'  <span class="trash-icon">🗑</span>'
                    f'</div>'
                )
            html += '</div>'
            quiz_questions.append(html)
            question_index += 1

    return quiz_questions

def process_text_quiz(raw_text):
    """
    Парсит обычный текстовый ввод, где:
      1) строка вопроса
      2) строки вида "✓ - ..." или "✗ - ...",
      3) пустая строка => конец текущего вопроса, переход к следующему
    """
    lines = [l.strip() for l in raw_text.splitlines()]
    # убираем совсем пустые строки, но они будут служить «разделителями»
    # так что используем их для break, но не теряем их совсем
    # Для надёжности – оставим raw_lines, а потом детально парсить
    # Однако проще всё же убрать и использовать логику «как только строка не нач с ✓/✗ => новая группа»
    # Ниже – один из вариантов
    lines = [l for l in lines if l]  # убрали пустые

    i = 0
    n = len(lines)
    quiz_questions = []
    question_index = 0

    while i < n:
        # Первая строка – question
        question = lines[i]
        i += 1
        options = []
        correct_answer = None

        # собираем варианты до встречи «следующей» строки,
        # которая не начинается с ✓ / ✗ (значит, это новый вопрос)
        while i < n:
            line = lines[i]
            if line.startswith("✓") or line.startswith("✗"):
                parts = line.split("-", 1)
                if len(parts) == 2:
                    marker = parts[0].strip()
                    option_text = parts[1].strip()
                    options.append(option_text)
                    if marker.startswith("✓"):
                        correct_answer = option_text
                i += 1
            else:
                # встретили новую «вопросную» строку
                break

        # Генерируем html
        if question and options and correct_answer:
            html = f'<p>{escape(question)}</p>'
            html += '<div class="mc-options" data-correct="{escape(correct_answer)}">'

            random.shuffle(options)
            for opt in options:
                html += (
                    f'<div class="mc-option-row" data-correct="{escape(correct_answer)}">'
                    f'  <input type="radio" name="q_{question_index}">'
                    f'  <span class="mc-option-label">{escape(opt)}</span>'
                    f'  <span class="trash-icon">🗑</span>'
                    f'</div>'
                )
            html += '</div>'
            quiz_questions.append(html)
            question_index += 1

    return quiz_questions

@mc_quiz_word_bp.route('/mc_quiz_word', methods=['GET','POST'])
def mc_quiz_word():
    """
    Страница Multiple Choice:
      - Можно загрузить doc/docx
      - Или вставить текст (с вопросами/вариантами)
      - Показываем красивый quiz
    """
    quiz_questions = []

    if request.method == 'POST':
        # Загрузили Word-файл?
        if 'word_file' in request.files and request.files['word_file'].filename:
            file = request.files['word_file']
            from werkzeug.utils import secure_filename
            filename = secure_filename(file.filename)
            upload_dir = os.path.join('static', 'uploads')
            os.makedirs(upload_dir, exist_ok=True)
            file_path = os.path.join(upload_dir, filename)
            file.save(file_path)

            quiz_questions = process_word_quiz(file_path)
            os.remove(file_path)
        else:
            # Иначе смотрим input_text
            input_text = request.form.get("input_text","").strip()
            if input_text:
                quiz_questions = process_text_quiz(input_text)

    return render_template("mc_quiz_word.html", quiz_questions=quiz_questions)
