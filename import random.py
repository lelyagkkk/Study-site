import random
import re
from flask import Flask, request, session, render_template
from flask_login import LoginManager
from bs4 import BeautifulSoup

# Подключаем Blueprint’ы
from quizz import quizz_bp
from pichide import pichide_bp
from coding import coding_bp
from library import library_bp
from mycalendar import mycalendar_bp
from auth import auth_bp
from account import account_bp
from mc_quiz_word import mc_quiz_word_bp
from matching import matching_bp

app = Flask(__name__)
app.secret_key = "MY_SUPER_SECRET_KEY"

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth_bp.login'

# Регистрируем Blueprint’ы
app.register_blueprint(pichide_bp)
app.register_blueprint(quizz_bp)
app.register_blueprint(coding_bp)
app.register_blueprint(library_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(mycalendar_bp)
app.register_blueprint(account_bp)
app.register_blueprint(mc_quiz_word_bp)
app.register_blueprint(matching_bp)

##############################################################################
# Функции, которые обрабатывают HTML и прячут буквы
##############################################################################

def split_into_tokens_preserve_spaces(text):
    """
    Делим текст на "токены": слова (\\w+), пробелы (\\s+), и любую другую 
    не-пробельную пунктуацию, чтобы сохранить форматирование.
    """
    return re.findall(r'\s+|[^\w\s]+|\w+', text)

def hide_letters_in_word(word, prob=0.2, fill_mode=False):
    """
    Прячет случайные буквы в слове:
      - если fill_mode=True -> <input ...>
      - иначе -> "_"
    """
    if not word:
        return word
    arr = list(word)
    n_hide = max(1, int(len(word)*prob)) if len(word) > 1 else 1
    indices = random.sample(range(len(word)), min(n_hide, len(word)))

    for i in indices:
        if fill_mode:
            correct_letter = arr[i]
            # === Дополняем: оборачиваем input + вопросик ===
            arr[i] = (
                f'<span class="hint-wrapper" style="position:relative; display:inline-block;">'
                f'  <input type="text" class="fill-input" maxlength="1" '
                f'         data-correct="{correct_letter}">'
                # Небольшой вопросик, при наведении (или нажатии) показывает букву
                f'  <span class="hint-icon" '
                f'        style="position:absolute; top:-1.3em; left:0; '
                f'               cursor:pointer; font-size:12px; color:#999;" '
                f'        onmouseover="this.textContent=\'{correct_letter}\'" '
                f'        onmouseout="this.textContent=\'?\'" '
                f'        onclick="this.textContent=\'{correct_letter}\'" '
                f'>?</span>'
                f'</span>'
            )
        else:
            arr[i] = "_"
    return "".join(arr)

def transform_text_for_mode(text, removal_prob=0.2, fill_mode=False):
    """
    Разбивает на токены (слова, пробелы, пунктуация).
    Если слово => прячем часть букв,
    иначе оставляем как есть.
    """
    tokens = split_into_tokens_preserve_spaces(text)
    out = []
    for t in tokens:
        if t.isspace():
            out.append(t)
        else:
            if re.match(r'^\w+$', t):
                replaced = hide_letters_in_word(t, removal_prob, fill_mode)
            else:
                replaced = t
            out.append(f'<span class="word">{replaced}</span>')
    return "".join(out)

def process_rich_html(html, removal_prob=0.2, fill_mode=False):
    """
    Парсим HTML через BeautifulSoup, обрабатываем только текстовые узлы,
    превращая буквы в "_" или <input>.
    """
    soup = BeautifulSoup(html, "html.parser")

    for element in soup.find_all(string=True):
        orig_text = str(element)
        new_html = transform_text_for_mode(orig_text, removal_prob, fill_mode)
        new_frag = BeautifulSoup(new_html, "html.parser")
        element.replace_with(new_frag)
    return str(soup)


##############################################################################
# Flask-Login (заглушка)
##############################################################################

@login_manager.user_loader
def load_user(user_id):
    return None


##############################################################################
# Главная страница ("/")
##############################################################################

@app.route('/', methods=['GET','POST'])
def index():
    mode = "remove"
    hidden_percentage = 20
    editor_initial = ""
    output_html = ""

    if request.method == 'POST':
        mode = request.form.get("mode", "remove")
        hidden_percentage = int(request.form.get("hidden_percentage", "20"))
        input_text = request.form.get("input_text", "")

        fill_mode = (mode == "fill")
        prob = hidden_percentage / 100.0 if fill_mode else 0.2

        output_html = process_rich_html(input_text, removal_prob=prob, fill_mode=fill_mode)
        editor_initial = input_text

    return render_template(
        "import_random.html",
        mode=mode,
        hidden_percentage=hidden_percentage,
        editor_initial=editor_initial,
        output_html=output_html
    )


if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True, port=5000)
