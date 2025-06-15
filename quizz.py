import re
import random
import os
from flask import Blueprint, request, render_template, redirect, url_for, session
from markupsafe import escape
from bs4 import BeautifulSoup

import pandas as pd  # Новый импорт для работы с Excel (не забудьте установить pandas!)

quizz_bp = Blueprint('quizz', __name__)

def get_user_library_root():
    """Возвращает путь к папке библиотеки (user_id или _guest)."""
    if 'user_id' not in session:
        user = '_guest'
    else:
        user = session['user_id']
    root = os.path.join('static', 'library', user)
    os.makedirs(root, exist_ok=True)
    return root

def get_plain_text(html):
    """Если нужно извлекать обычный текст без HTML."""
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text(separator="\n")

def quizz_process(html, mode, hide_percent, chosen_words=None):
    """
    Обрабатывает HTML, пряча некоторый процент слов 
    (multiple_choice / missing_words_write / missing_words_no_write).
    Если hide_percent равен "chosen", то скрываются только слова, указанные в chosen_words (через запятую).
    """
    soup = BeautifulSoup(html, "html.parser")
    text_nodes = []
    # Собираем все текстовые узлы
    for node in soup.find_all(string=True):
        raw = node
        if raw.strip():
            # Разбиваем строку на (\s+), (\w+) и "не-пробельные символы"
            tokens = re.findall(r'\s+|[^\w\s]+|\w+', raw)
            text_nodes.append((node, tokens))

    # Собираем все слова (только \w+)
    all_words = []
    for nodeIdx, (nd, toks) in enumerate(text_nodes):
        for tokIdx, tok in enumerate(toks):
            if re.match(r'^\w+$', tok):
                all_words.append((nodeIdx, tokIdx, tok))

    if hide_percent == "chosen":
        chosen_set = set(word.strip().lower() for word in chosen_words.split(",") if word.strip()) if chosen_words else set()
    else:
        # Сколько слов прятать
        n_hide = int(len(all_words) * (hide_percent / 100.0)) if all_words else 0
        if n_hide > len(all_words):
            n_hide = len(all_words)
        indices = list(range(len(all_words)))
        random.shuffle(indices)
        hideSet = set(indices[:n_hide])

    # Уникальные слова (если надо для multiple choice)
    unique_words = set(w for (_, _, w) in all_words)

    # Обходим все слова, вставляем замену
    global_idx = 0
    for nodeIdx, (nd, toks) in enumerate(text_nodes):
        newToks = []
        for tokIdx, tok in enumerate(toks):
            if re.match(r'^\w+$', tok):
                hide_this = False
                if hide_percent == "chosen":
                    if tok.lower() in chosen_set:
                        hide_this = True
                else:
                    if global_idx in hideSet:
                        hide_this = True

                if hide_this:
                    # Прячем это слово в зависимости от mode
                    if mode == "multiple_choice":
                        correct = tok
                        inc = [w for w in unique_words if w != correct]
                        wrongs = []
                        if len(inc) > 2:
                            wrongs = random.sample(inc, 2)
                        elif inc:
                            wrongs = inc[:2]
                        wr = "|".join(wrongs)
                        replaced = (
                            f'<span class="mc-gap" data-correct="{escape(correct)}" '
                            f'data-wrongs="{escape(wr)}">???</span>'
                        )
                        newToks.append(replaced)
                    elif mode == "missing_words_write":
                        wlen = len(tok)
                        replaced = (
                            f'<input type="text" class="fill-input" data-correct="{escape(tok)}" '
                            f'style="width:{max(wlen*1.3,5)}ch" maxlength="{wlen}">'
                        )
                        newToks.append(replaced)
                    else:
                        # missing_words_no_write
                        replaced = (
                            f'<span class="hidden-word" data-original="{escape(tok)}" '
                            f'style="width:{max(len(tok)*1.3,4)}ch;"></span>'
                        )
                        newToks.append(replaced)
                else:
                    # Слово не скрывается
                    newToks.append(escape(tok))
                global_idx += 1
            else:
                # пробелы/пунктуация
                newToks.append(escape(tok))
        replaced = "".join(newToks)
        frag = BeautifulSoup(replaced, "html.parser")
        nd.replace_with(frag)

    return str(soup)

@quizz_bp.route('/quizz', methods=['GET', 'POST'])
def quizz():
    """
    Страница квиза:
      - Пользователь вводит HTML в #editor или импортирует Excel-файл,
      - Выбирает mode и hide_percent,
      - Нажимает Create Quiz => обрабатываем (quizz_process) или импортируем квиз из Excel,
      - Показываем результат.
    """
    mode = "multiple_choice"
    hide_percent = 30
    editor_initial = ""
    quiz_questions = []
    chosen_words = ""

    if request.method == 'POST':
        # Проверяем: загружен ли Excel?
        if 'excel_file' in request.files and request.files['excel_file'].filename:
            file = request.files['excel_file']
            from werkzeug.utils import secure_filename
            filename = secure_filename(file.filename)
            excel_path = os.path.join('static', 'uploads', filename)
            os.makedirs(os.path.join('static', 'uploads'), exist_ok=True)
            file.save(excel_path)

            df = pd.read_excel(excel_path)

            for idx, row in df.iterrows():
                question = row['Question']
                correct = row['Correct']
                wrong1 = row['Option1']
                wrong2 = row['Option2']
                wrong3 = row['Option3']
                options = [correct, wrong1, wrong2, wrong3]
                random.shuffle(options)
                question_html = f'<div class="quiz-question"><p>{question}</p>'
                for opt in options:
                    question_html += (
                        f'<button class="mc-option-btn" data-correct="{escape(correct)}">{opt}</button>'
                    )
                question_html += '</div>'
                quiz_questions.append(question_html)

            os.remove(excel_path)

        else:
            # Обработка HTML из редактора
            editor_initial = request.form.get("input_text", "")
            mode = request.form.get("mode", "multiple_choice")
            hide_percent = request.form.get("hide_percent", "30")
            if hide_percent == "chosen":
                chosen_words = request.form.get("chosen_words", "")
            else:
                try:
                    hide_percent = int(hide_percent)
                except:
                    hide_percent = 30
            out = quizz_process(editor_initial, mode, hide_percent, chosen_words)
            quiz_questions = [out]

    return render_template("quizz.html",
                           mode=mode,
                           hide_percent=hide_percent,
                           editor_initial=editor_initial,
                           quiz_questions=quiz_questions,
                           chosen_words=chosen_words)

@quizz_bp.route('/save_original', methods=['POST'])
def save_original():
    """
    Сохраняем оригинальный HTML (не модифицированный) в библиотеку.
    """
    filename = request.form.get("filename", "quiz_saved.html").strip()
    original_html = request.form.get("original_html", "<p>Empty</p>")

    if not filename.lower().endswith(".html"):
        filename += ".html"

    user = session.get('user_id', '_guest')
    root = os.path.join('static', 'library', user)
    os.makedirs(root, exist_ok=True)

    path = os.path.join(root, filename)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(original_html)

    return redirect(url_for("library_bp.browse_library"))
