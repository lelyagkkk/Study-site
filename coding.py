from flask import Blueprint, render_template_string, request
from markupsafe import escape
import os

coding_bp = Blueprint('coding', __name__, url_prefix='/coding')

UPLOAD_FOLDER = "static/uploads"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

CODING_TEMPLATE = r"""
<!DOCTYPE html>
<html>
<head>
    <title>Coding Practice</title>
    <!-- Prism: скрипты -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/prism.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-python.min.js"></script>
    <style>
      body {
        margin: 0; padding: 20px;
        background: #1e1e1e;
        font-family: Consolas, "Courier New", monospace;
        display: flex; flex-direction: column; align-items: center;
        min-height: 100vh;
      }
      h1 { color: #d4d4d4; margin-top: 0; }
      .editor-container {
        width: 90%; max-width: 1000px;
        background: #1e1e1e; padding: 20px; border-radius: 10px;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);
        margin-bottom: 20px; overflow-x: auto;
      }
      textarea {
        width: 100%; height: 120px;
        background: #1e1e1e; color: #d4d4d4;
        border: 1px solid #444; font-size: 16px;
      }
      button {
        margin-top: 10px; padding: 8px 16px;
        cursor: pointer;
      }
      pre {
        width: 90%; max-width: 1000px;
        background: #1e1e1e; padding: 20px; border-radius: 10px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.3);
        overflow-x: auto;
        font-size: 18px; line-height: 1.5;
        color: #d4d4d4;
      }
      code {
        font-family: Consolas, "Courier New", monospace;
      }
      /* Изначально символы скрыты (прозрачные) */
      .char-hidden {
        opacity: 0.2;
        font-weight: normal;
        transition: all 0.2s;
      }
      /* При раскрытии делаем непрозрачно и жирным */
      .char-revealed {
        opacity: 1;
        font-weight: bold;
      }
      /* Мини-инпут, чтобы видеть каретку */
      #tiny-input {
        position: fixed;
        top: 0; left: 0;
        width: 1px; height: 1px;
        opacity: 0.01;
        z-index: 9999;
        color: transparent;
      }

      /* Пример ручной раскраски токенов Prism (VS Code-like) */
      .token.comment { color: #6a9955; }
      .token.keyword { color: #c586c0; }
      .token.function { color: #dcdcaa; }
      .token.string { color: #ce9178; }
      .token.number, .token.boolean { color: #b5cea8; }
      .token.operator { color: #d4d4d4; }
      .token.punctuation { color: #d4d4d4; }
    </style>
</head>
<body>
    <h1>Trace Mode</h1>

    <div class="editor-container">
      <form method="post">
        <textarea name="code_input" id="code-input">{{ code_content }}</textarea><br>
        <button type="button" id="load-btn">Load Code</button>
      </form>
    </div>

    <!-- Тут будет раскрашенный код. Не contenteditable. -->
    <pre id="trace-code" class="language-python"></pre>

    <!-- Крошечный видимый input, чтобы пользователь видел каретку. -->
    <input id="tiny-input" type="text" />

    <script>
      let traceCode;
      let allChars = [];
      let currentIndex = 0;
      let tinyInput;

      document.addEventListener('DOMContentLoaded', () => {
        traceCode = document.getElementById('trace-code');
        tinyInput = document.getElementById('tiny-input');
        const loadBtn = document.getElementById('load-btn');
        const codeInput = document.getElementById('code-input');

        // Всегда фокусируем tiny-input, чтобы каретка была видна
        tinyInput.focus();
        document.addEventListener('click', () => {
          tinyInput.focus();
        });

        loadBtn.addEventListener('click', () => {
          // Сбрасываем состояние
          traceCode.innerHTML = '';
          allChars = [];
          currentIndex = 0;

          // Берём исходный код
          const code = codeInput.value;

          // Получаем раскрашенный Prism HTML
          let prismHTML = Prism.highlight(code, Prism.languages.python, 'python');
          // Переводим его в DOM, разбиваем каждый текстовый узел на <span class="char-hidden">
          let tempDiv = document.createElement('div');
          tempDiv.innerHTML = prismHTML;
          let frag = document.createDocumentFragment();
          transformNode(tempDiv, frag);
          traceCode.appendChild(frag);

          // tinyInput снова в фокус
          tinyInput.focus();
        });

        // При вводе символа
        tinyInput.addEventListener('input', (e) => {
          if (!e.data) {
            // Возможно backspace или enter
            tinyInput.value = '';
            return;
          }
          const typedChar = e.data;
          // Очищаем input после каждого символа
          tinyInput.value = '';

          // Сопоставляем
          if (currentIndex < allChars.length) {
            let expected = allChars[currentIndex].textContent;
            if (typedChar === expected) {
              allChars[currentIndex].classList.remove('char-hidden');
              allChars[currentIndex].classList.add('char-revealed');
              currentIndex++;
              skipWhitespace();
            }
          }
        });
      });

      // Пропускаем пробельные символы (пробел, таб, перенос)
      function skipWhitespace() {
        while (currentIndex < allChars.length) {
          const ch = allChars[currentIndex].textContent;
          if (/\s/.test(ch)) {
            allChars[currentIndex].classList.remove('char-hidden');
            allChars[currentIndex].classList.add('char-revealed');
            currentIndex++;
          } else {
            break;
          }
        }
      }

      // Рекурсивно разбиваем ноды Prism
      function transformNode(src, dest) {
        for (let child of src.childNodes) {
          if (child.nodeType === Node.TEXT_NODE) {
            let text = child.nodeValue;
            for (let c of text) {
              let span = document.createElement('span');
              span.classList.add('char-hidden');
              span.textContent = c;
              dest.appendChild(span);
              allChars.push(span);
            }
          } else if (child.nodeType === Node.ELEMENT_NODE) {
            let cloned = document.createElement(child.tagName);
            cloned.className = child.className;
            transformNode(child, cloned);
            dest.appendChild(cloned);
          }
        }
      }
    </script>
</body>
</html>
"""

@coding_bp.route('/', methods=['GET', 'POST'])
def coding():
    code_content = ""
    if request.method == 'POST':
        code_content = request.form.get('code_input', '').strip()
    return render_template_string(CODING_TEMPLATE, code_content=escape(code_content))
