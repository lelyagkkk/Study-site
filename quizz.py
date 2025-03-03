from flask import Blueprint, request, render_template_string
import random

quizz_bp = Blueprint('quizz', __name__)

QUIZZ_TEMPLATE = """ 
<!DOCTYPE html>
<html>
<head>
    <title>Quizz</title>
    <link rel="stylesheet" type="text/css" href="{{ url_for('static', filename='style.css') }}">
</head>
<script>
    document.addEventListener("DOMContentLoaded", function() {
        let choices = document.querySelectorAll(".choice");
        
        choices.forEach(choice => {
            choice.addEventListener("click", function() {
                let correctWord = this.dataset.correct.trim().toLowerCase();
                let selectedWord = this.textContent.trim().toLowerCase();

                if (selectedWord === correctWord) {
                    this.style.backgroundColor = "lightgreen"; // Подсветка правильного ответа
                } else {
                    this.style.backgroundColor = "lightcoral"; // Подсветка неверного
                }
            });
        });

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
                if (event.key.length === 1 && this.value.length >= this.maxLength) {
                    event.preventDefault();
                }
            });
        });

        document.getElementById("missing_words").addEventListener("change", function() {
            document.getElementById("chosen_words_input").style.display = (this.value === "chosen_words") ? "inline-block" : "none";
        });
    });
</script>


<body class="quiz-mode"> <!-- Добавили class="quiz-mode" -->
    <a href="{{ url_for('index') }}" class="main-button">Main</a>
    
    <h2>Quizz Creator</h2>
    <form method="post">
        <textarea name="input_text">{{ input_text }}</textarea><br>

        <label for="mode">Select quiz mode:</label>
        <select name="mode" id="mode">
            <option value="multiple_choice" {% if mode == 'multiple_choice' %}selected{% endif %}>Multiple Choice</option>
            <option value="fill_blanks" {% if mode == 'fill_blanks' %}selected{% endif %}>Fill in the Blanks</option>
        </select><br>

        <label for="missing_words">Number of missing words:</label>
        <select name="missing_words" id="missing_words">
            <option value="1" {% if missing_words == '1' %}selected{% endif %}>1</option>
            <option value="2" {% if missing_words == '2' %}selected{% endif %}>2</option>
            <option value="3" {% if missing_words == '3' %}selected{% endif %}>3</option>
            <option value="4" {% if missing_words == '4' %}selected{% endif %}>4</option>
            {% if mode in ['fill_blanks', 'multiple_choice'] %}
                <option value="whole_sentence" {% if missing_words == 'whole_sentence' %}selected{% endif %}>The whole sentence</option>
            {% endif %}
            <option value="chosen_words" {% if missing_words == 'chosen_words' %}selected{% endif %}>Chosen words</option>
        </select><br>

        <input type="text" name="chosen_words" id="chosen_words_input" placeholder="Enter words separated by commas" style="display: none;">
        <input type="submit" value="Create Quiz">
    </form>

    <h3>Quiz:</h3>
    <div class="output-container">
        {% for question, options_list in quiz_questions %}
            <div class="word">
                {% if mode == "multiple_choice" %}
                    <strong>{{ question }}</strong><br>
                    {% for options, correct_word in options_list %}
                        {% for option in options %}
                            <button class="choice" data-correct="{{ correct_word }}">{{ option }}</button>
                        {% endfor %}
                        <br>
                    {% endfor %}
                {% elif mode == "fill_blanks" %}
                    <strong>{{ question|safe }}</strong>  
                {% endif %}
            </div>
        {% endfor %}
    </div>
</body>
</html>
"""



def generate_quiz(text, mode, missing_words_count, chosen_words=None):
    sentences = text.split(". ")  # Разделяем текст на предложения
    all_words = list(set(text.split()))  # Уникальные слова текста
    quiz_questions = []

    # ✅ Обрабатываем режим "chosen_words"
    if missing_words_count == "chosen_words":
        if isinstance(chosen_words, str):  
            chosen_words = chosen_words.lower().split(",") if chosen_words else []
        chosen_words = [word.strip() for word in chosen_words if word.strip() in all_words]  # Фильтруем только слова из текста

    for sentence in sentences:
        words = sentence.split()
        if len(words) <= 4:  # Пропускаем короткие предложения
            continue  

        # ✅ Определяем, какие слова будут пропущены
        if missing_words_count == "whole_sentence":
            missing_indices = list(range(len(words)))  # Пропускаем все слова
        elif missing_words_count == "chosen_words":
            missing_indices = [i for i, w in enumerate(words) if w.lower() in chosen_words]
        else:
            num_missing = min(int(missing_words_count), len(words))  
            missing_indices = sorted(random.sample(range(len(words)), num_missing))

        if not missing_indices:  
            continue  

        correct_words = [words[i] for i in missing_indices]

        # ✅ Multiple Choice - The whole sentence (слово-по-слову)
        if mode == "multiple_choice":
            options_list = []
            if missing_words_count == "whole_sentence":  
                for i in missing_indices:
                    correct_word = words[i]
                    incorrect_candidates = [w for w in all_words if w != correct_word]
                    num_incorrect = min(2, len(incorrect_candidates))  
                    incorrect_words = random.sample(incorrect_candidates, num_incorrect) if num_incorrect > 0 else []
                    
                    options = [correct_word] + incorrect_words
                    random.shuffle(options)
                    options_list.append((options, correct_word))

                    words[i] = "______"  # Замена слова в предложении

                question = " ".join(words).strip()

            else:
                for correct_word in correct_words:
                    incorrect_candidates = [w for w in all_words if w != correct_word]
                    num_incorrect = min(2, len(incorrect_candidates))  
                    incorrect_words = random.sample(incorrect_candidates, num_incorrect) if num_incorrect > 0 else []
                    
                    options = [correct_word] + incorrect_words
                    random.shuffle(options)
                    options_list.append((options, correct_word))

                for i in missing_indices:
                    words[i] = "______"

                question = " ".join(words).strip()

            quiz_questions.append((question, options_list))

        # ✅ Fill in the Blanks (учитываем "whole_sentence", исправляем ввод одной буквы, делаем шире инпут)
        elif mode == "fill_blanks":
            if missing_words_count == "whole_sentence":
                words = [
                    f'<input type="text" class="fill-input" data-correct="{word}" '
                    f'style="width: {max(len(word) * 2.5, 5)}ch; min-width: 4ch; max-width: 35ch;" '
                    f'maxlength="{len(word)}" size="{max(len(word), 2)}">'  # Увеличена ширина для 1-2 букв
                    for word in words
                ]
            else:
                for i in missing_indices:
                    correct_word = words[i]
                    words[i] = (
                        f'<input type="text" class="fill-input" data-correct="{correct_word}" '
                        f'style="width: {max(len(correct_word) * 2.5, 5)}ch; min-width: 4ch; max-width: 35ch;" '
                        f'maxlength="{len(correct_word)}" size="{max(len(correct_word), 2)}">'  # Увеличена ширина для 1-2 букв
                    )

            question = " ".join(words).strip()
            quiz_questions.append((question, []))
    
    return quiz_questions



@quizz_bp.route('/quizz', methods=['GET', 'POST'])
def quizz():
    input_text = ""
    quiz_questions = []
    mode = "multiple_choice"
    missing_words_count = 1  # Значение по умолчанию
    chosen_words = []

    if request.method == 'POST':
        input_text = request.form.get('input_text', '')
        mode = request.form.get('mode', 'multiple_choice')
        missing_words_value = request.form.get('missing_words', '1')

        # Проверяем, выбраны ли "chosen_words" или "whole_sentence"
        if missing_words_value.isdigit():
            missing_words_count = int(missing_words_value)  # Если число, преобразуем
        else:
            missing_words_count = missing_words_value  # Иначе оставляем строку

        if missing_words_count == "chosen_words":
            chosen_words_input = request.form.get('chosen_words', '')
            chosen_words = [word.strip().lower() for word in chosen_words_input.split(',') if word.strip()]

        quiz_questions = generate_quiz(input_text, mode, missing_words_count, chosen_words)

    return render_template_string(QUIZZ_TEMPLATE, input_text=input_text, quiz_questions=quiz_questions, mode=mode, missing_words=missing_words_count, chosen_words=",".join(chosen_words))
