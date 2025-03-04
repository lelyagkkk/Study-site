import random
import re
from flask import Flask, render_template_string, request
from quizz import quizz_bp  # Импортируем Blueprint
from pichide import pichide_bp  # Импортируем Blueprint
from coding import coding_bp


app = Flask(__name__)

app.register_blueprint(pichide_bp)  # Регистрируем Blueprint
app.register_blueprint(quizz_bp)
app.register_blueprint(coding_bp)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Random Letter Removal</title>
    <link rel="stylesheet" type="text/css" href="{{ url_for('static', filename='style.css') }}">

    <script>
document.addEventListener("DOMContentLoaded", function() {
    function toggleHiddenPercentage() {
        document.getElementById("hidden_percentage_container").style.display = 
            document.querySelector('input[name="mode"]:checked').value === "fill" ? "inline-block" : "none";
    }

    function updateBodyClass() {
        document.body.classList.toggle("fill-mode", document.querySelector('input[name="mode"]:checked').value === "fill");
    }

    document.querySelectorAll('input[name="mode"]').forEach(mode => {
        mode.addEventListener("change", function() {
            toggleHiddenPercentage();
            updateBodyClass();
        });
    });

    toggleHiddenPercentage();  
    updateBodyClass();  // Запуск при загрузке страницы

    let inputs = document.querySelectorAll(".fill-input");
    inputs.forEach((input, index) => {
        input.addEventListener("input", function() {
            let correctValue = this.dataset.correct.trim().toLowerCase();
            let enteredValue = this.value.trim().toLowerCase();

            if (enteredValue === correctValue) {
                this.classList.add("correct");
                this.style.color = 'black'; 
                this.style.backgroundColor = 'lightgreen';
                this.classList.remove("incorrect");

                this.value = correctValue;
                this.setAttribute("readonly", "true");  

                let nextInput = inputs[index + 1];
                if (nextInput) {
                    nextInput.focus();
                }
            } else {
                this.classList.add("incorrect");
                this.style.backgroundColor = 'lightcoral';
                this.classList.remove("correct");
            }
        });

        input.addEventListener("keydown", function(event) {
            if (event.key.length === 1 && this.value.length >= 1) {
                event.preventDefault();
                this.value = event.key;  
                this.setSelectionRange(1, 1);
            }
        });

        input.addEventListener("focus", function() {
            if (!this.classList.contains("correct")) {
                this.value = "";
            }
        });
    });
});


    </script>
</head>
<body>
    <h2>Your text</h2>
    <form method="post">
        <textarea name="input_text">{{ input_text }}</textarea><br>

        <label><input type="radio" name="mode" value="remove" {% if mode == 'remove' %}checked{% endif %}> Remove Letters</label>
        <label><input type="radio" name="mode" value="fill" {% if mode == 'fill' %}checked{% endif %}> Fill in the Blanks</label><br>

        <div id="hidden_percentage_container">
            <label for="hidden_percentage">Hidden letters (%):</label>
            <select name="hidden_percentage" id="hidden_percentage">
                {% for percent in [10, 20, 30, 40, 50, 60, 70, 80, 90, 100] %}
                    <option value="{{ percent }}" {% if hidden_percentage == percent %}selected{% endif %}>{{ percent }}%</option>
                {% endfor %}
            </select>
        </div><br>

        <input type="submit" value="Process">
    </form>

    {% if output_words %}
        <h3>Output:</h3>
        <div class="output-container">
        {% for word, original in output_words %}
            <div class="word">
                {% if mode == 'fill' %}
                    {% for char in word %}
                        {% if char == '_' %}
                            <input type="text" class="fill-input" maxlength="1" data-correct="{{ original[loop.index0] }}">
                        {% else %}
                            {{ char }}
                        {% endif %}
                    {% endfor %}
                {% else %}
                    {{ word.replace('_', '_') }}
                {% endif %}
            </div>
        {% endfor %}
        </div>
    {% endif %}
    <br><br>
    <a href="{{ url_for('quizz.quizz') }}" class="quiz-button">Quiz Mode</a>
    <a href="{{ url_for('coding.coding') }}" class="coding-button">Coding</a>
    <a href="/pichide" class="image-hide-button">Image Hide</a>

</html>
"""

def remove_random_letters(text, removal_prob=0.2):
    words = re.findall(r'\b\w+\b|\S', text)  # Разбиваем текст на слова и знаки препинания
    output_words = []

    for word in words:
        if re.match(r'\w+', word):  # Если это слово, а не пунктуация
            num_to_hide = max(1, int(len(word) * removal_prob))  # Скрываем минимум 1 букву
            indices = random.sample(range(len(word)), num_to_hide) if len(word) > 1 else [0]  

            modified_word = list(word)
            for i in indices:
                modified_word[i] = "_"

            output_words.append(("".join(modified_word), word))  # Сохраняем скрытый вариант + оригинал
        else:
            output_words.append((word, word))  

    return output_words


@app.route('/', methods=['GET', 'POST'])
def index():
    input_text = ""
    output_words = []
    mode = "remove"
    hidden_percentage = 20  # Значение по умолчанию

    if request.method == 'POST':
        input_text = request.form.get('input_text', '')
        mode = request.form.get('mode', 'remove')
        hidden_percentage = int(request.form.get("hidden_percentage", 20))  # Получаем процент скрытых букв

        if mode == "fill":
            output_words = remove_random_letters(input_text, hidden_percentage / 100)  # Преобразуем в 0.0-1.0
        else:
            output_words = remove_random_letters(input_text)  # Используем дефолтные 20%

    return render_template_string(
        HTML_TEMPLATE,
        input_text=input_text,
        output_words=output_words,
        mode=mode,
        hidden_percentage=hidden_percentage
    )



if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
