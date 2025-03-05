from flask import Blueprint, render_template_string, request
from markupsafe import escape
import os

coding_bp = Blueprint('coding', __name__, url_prefix='/coding')

UPLOAD_FOLDER = "static/uploads"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

CODING_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Coding Practice</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/themes/prism-tomorrow.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/prism.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-python.min.js"></script>
</head>
<body>
    <div class="nav-links">
        <a href="{{ url_for('index') }}" class="large-button">Main</a>
        <a href="{{ url_for('quizz.quizz') }}" class="large-button">Quizz</a>
        <a href="{{ url_for('pichide.pichide') }}" class="large-button">Image Hide</a>
        <a href="{{ url_for('coding.coding') }}" class="large-button coding-button">Coding</a>
    </div>

    <h1>Welcome to Coding Practice</h1>

    <form method="post" enctype="multipart/form-data">
        <label for="code-input">Paste Code:</label><br>
        <textarea name="code_input" id="code-input" rows="8">{{ code_content }}</textarea><br><br>

        <label for="code-upload">Upload Code File:</label>
        <input type="file" name="file" id="code-upload" accept=".py,.txt"><br><br>

        <label for="mode">Select Mode:</label>
        <select name="mode" id="mode">
            <option value="trace">Trace Mode</option>
            <option value="memory">Memory Mode</option>
        </select><br><br>

        <input type="submit" value="Load Code">
    </form>

    <h2>Code Editor</h2>

    <div id="trace-mode" style="display: none;">
        <h3>Trace Mode</h3>
        <p>Type the code below:</p>
        <pre class="language-python"><code id="trace-code"></code></pre>
        <textarea id="trace-input" class="trace-input" placeholder="Start typing..."></textarea>
    </div>

    <div id="memory-mode" style="display: none;">
        <h3>Memory Mode</h3>
        <p>Fill in the missing parts of the code:</p>
        <pre class="language-python"><code id="memory-code"></code></pre>
    </div>

    <script>
        document.addEventListener("DOMContentLoaded", function() {
            let modeSelect = document.getElementById("mode");
            let traceMode = document.getElementById("trace-mode");
            let memoryMode = document.getElementById("memory-mode");
            let traceCode = document.getElementById("trace-code");
            let memoryCode = document.getElementById("memory-code");
            let traceInput = document.getElementById("trace-input");
            let codeTextarea = document.getElementById("code-input");

            function setupTraceMode(code) {
                traceCode.innerHTML = "";
                traceInput.value = "";
                let formattedCode = "";
                
                for (let char of code) {
                    formattedCode += `<span class="trace-char hidden">${char}</span>`;
                }
                
                traceCode.innerHTML = formattedCode;
                Prism.highlightAll();

                traceInput.addEventListener("input", function() {
                    let typedText = traceInput.value;
                    let characters = document.querySelectorAll(".trace-char");
                    
                    for (let i = 0; i < typedText.length; i++) {
                        if (characters[i] && characters[i].innerText === typedText[i]) {
                            characters[i].classList.remove("hidden");
                        }
                    }

                    if (typedText.length >= characters.length) {
                        traceInput.disabled = true;
                    }
                });
            }

            function setupMemoryMode(code) {
                let words = code.split(" ");
                let modifiedCode = words.map(word => Math.random() > 0.7 ? "_____" : word).join(" ");
                memoryCode.innerHTML = modifiedCode;
                Prism.highlightAll();
            }

            modeSelect.addEventListener("change", function() {
                let code = codeTextarea.value.trim();
                if (modeSelect.value === "trace") {
                    traceMode.style.display = "block";
                    memoryMode.style.display = "none";
                    setupTraceMode(code);
                } else {
                    traceMode.style.display = "none";
                    memoryMode.style.display = "block";
                    setupMemoryMode(code);
                }
            });

            Prism.highlightAll();
        });
    </script>

    <style>
        .trace-char {
            opacity: 0.1;
            transition: opacity 0.2s;
        }

        .trace-char.hidden {
            opacity: 0.1;
        }

        .trace-char:not(.hidden) {
            opacity: 1;
        }

        .trace-input {
            font-family: monospace;
            font-size: 18px;
            border: 2px solid #ccc;
            padding: 5px;
            width: 100%;
            margin-top: 10px;
            text-align: left;
            height: 150px;
            background: #282c34;
            color: white;
        }
    </style>
</body>
</html>
"""

@coding_bp.route('/', methods=['GET', 'POST'])
def coding():
    code_content = ""

    if request.method == 'POST':
        # Получаем код из текстового поля
        code_content = request.form.get('code_input', '').strip()

        # Если загружен файл, читаем его содержимое
        file = request.files.get('file')
        if file and file.filename.endswith(('.py', '.txt')):
            filename = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(filename)
            with open(filename, "r", encoding="utf-8") as f:
                code_content = f.read().strip()

    return render_template_string(CODING_TEMPLATE, code_content=escape(code_content))
