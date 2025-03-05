import re
import random
from flask import Blueprint, request, render_template_string

quizz_bp = Blueprint('quizz', __name__)

QUIZZ_TEMPLATE = """ 
<!DOCTYPE html>
<html>
<head>
    <title>Quizz</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
</head>
<body class="quiz-mode">

    <a href="{{ url_for('index') }}" class="main-button">Main</a>
    <a href="{{ url_for('pichide.pichide') }}" class="image-hide-button">Image Hide</a>
    <a href="{{ url_for('coding.coding') }}" class="large-button coding-button">Coding</a>

    <form method="post">
        <textarea name="input_text" style="width:100%;height:120px;">{{ input_text }}</textarea><br>

        <label for="mode">Select quiz mode:</label>
        <select name="mode" id="mode">
            <option value="multiple_choice" {% if mode=='multiple_choice' %}selected{% endif %}>Multiple Choice</option>
            <option value="fill_blanks" {% if mode=='fill_blanks' %}selected{% endif %}>Fill in the Blanks</option>
        </select><br>

        <label for="missing_words">Number of missing words:</label>
        <select name="missing_words" id="missing_words">
            <option value="1" {% if missing_words=='1' %}selected{% endif %}>1</option>
            <option value="2" {% if missing_words=='2' %}selected{% endif %}>2</option>
            <option value="3" {% if missing_words=='3' %}selected{% endif %}>3</option>
            <option value="4" {% if missing_words=='4' %}selected{% endif %}>4</option>
            <option value="whole_sentence" {% if missing_words=='whole_sentence' %}selected{% endif %}>Whole sentence</option>
            <option value="chosen_words" {% if missing_words=='chosen_words' %}selected{% endif %}>Chosen words</option>
        </select><br>

        <input type="text" name="chosen_words" id="chosen_words_input" placeholder="Enter words separated by commas"
               style="display:none;">
        <input type="submit" value="Create Quiz">
    </form>

    <h3>Quiz:</h3>
    <div class="output-container">
      {% for question, options_list in quiz_questions %}
        <div class="word">
          {% if mode=='multiple_choice' %}
            <strong>{{ question }}</strong><br>
            {% for opts, correct_word in options_list %}
              {% for opt in opts %}
                <button class="choice" data-correct="{{ correct_word }}">{{ opt }}</button>
              {% endfor %}
              <br>
            {% endfor %}
          {% else %}
            <strong>{{ question|safe }}</strong>
          {% endif %}
        </div>
      {% endfor %}
    </div>

<script>
document.addEventListener("DOMContentLoaded",function(){

   // Показать/спрятать поле chosen_words
   document.getElementById("missing_words").addEventListener("change", function(){
     let val=this.value;
     if(val==="chosen_words"){
       document.getElementById("chosen_words_input").style.display='inline-block';
     } else {
       document.getElementById("chosen_words_input").style.display='none';
     }
   });

   // Multiple Choice
   document.querySelectorAll(".choice").forEach(btn=>{
     btn.addEventListener("click", function(){
       let cor = btn.dataset.correct.trim().toLowerCase();
       let txt = btn.textContent.trim().toLowerCase();
       if(txt===cor){
         btn.style.backgroundColor='lightgreen';
       } else {
         btn.style.backgroundColor='lightcoral';
       }
     });
   });

   // Fill in the Blanks
   // Добавим «нормализацию» строк, чтобы не ломаться из-за "умных кавычек" и знаков.
   function normalize(str){
     return str
       .toLowerCase()
       // убираем кавычки, точки, запятые, дефисы и т.д. (расширьте при необходимости)
       .replace(/[.,!?;:"“”‘’'()]/g, "")
       .replace(/\s+/g," ")
       .trim();
   }

   let fillInputs=document.querySelectorAll(".fill-input");
   fillInputs.forEach((inp, idx)=>{
     inp.addEventListener("input", function(){
       let corr = normalize(inp.dataset.correct || "");
       let typed = normalize(inp.value || "");
       if(typed === corr && typed!==""){
         // правильный ввод
         inp.classList.remove("incorrect");
         inp.classList.add("correct");
         inp.style.backgroundColor='lightgreen';
         // перейти к следующему
         let nxt=fillInputs[idx+1];
         if(nxt) nxt.focus();
       } else {
         // неверный ввод
         inp.classList.remove("correct");
         inp.classList.add("incorrect");
         inp.style.backgroundColor='lightcoral';
       }
     });
   });
});
</script>
</body>
</html>
"""


def generate_quiz(text, mode, missing_words_count, chosen_words=None):
    """
    Разделяем text на предложения «по точкам/вопросительным/восклицательным знакам + пробел».
    Затем внутри каждого предложения прячем слова в зависимости от режима.
    Добавлена логика multiple_choice / fill_blanks.
    """
    # Разделяем чуть умнее (по . ? !, используя lookbehind)
    sentences = re.split(r'(?<=[.?!])\s+', text.strip())
    all_words = list(set(text.split()))

    # Если chosen_words
    if missing_words_count == 'chosen_words':
        if isinstance(chosen_words, str):
            chosen_words = chosen_words.split(',')
        chosen_words = [w.strip().lower() for w in chosen_words if w.strip() in all_words]

    quiz_questions = []
    for sent in sentences:
        words = sent.split()
        if len(words) <= 4:
            continue

        if missing_words_count == 'whole_sentence':
            missing_idxs = list(range(len(words)))
        elif missing_words_count == 'chosen_words':
            missing_idxs = [i for i, w in enumerate(words) if w.lower() in chosen_words]
        else:
            try:
                num = int(missing_words_count)
            except:
                num = 1
            if num > len(words):
                num = len(words)
            missing_idxs = sorted(random.sample(range(len(words)), num))

        if not missing_idxs:
            continue

        # Собираем "правильные" слова
        corrects = [words[i] for i in missing_idxs]

        if mode == 'multiple_choice':
            # На каждое пропущенное слово - 2 неправильных
            opts_list = []
            for idx in missing_idxs:
                correct_word = words[idx]
                incands = [w for w in all_words if w != correct_word]
                if incands:
                    wrongs = random.sample(incands, min(2, len(incands)))
                else:
                    wrongs = []
                opts = [correct_word] + wrongs
                random.shuffle(opts)
                opts_list.append((opts, correct_word))

                # Замена в тексте
                words[idx] = "______"

            question_str = " ".join(words).strip()
            quiz_questions.append((question_str, opts_list))

        else:  # fill_blanks
            new_words = words[:]
            for idx in missing_idxs:
                cor = words[idx]
                wlen = len(cor)
                inp_html = (f'<input type="text" class="fill-input" data-correct="{cor}" '
                            f'style="width:{max(wlen*2.5,5)}ch" maxlength="{wlen}">')
                new_words[idx] = inp_html

            question_str = " ".join(new_words).strip()
            quiz_questions.append((question_str, []))

    return quiz_questions


@quizz_bp.route('/quizz', methods=['GET', 'POST'])
def quizz():
    input_text = ""
    quiz_questions = []
    mode = "multiple_choice"
    missing_words = "1"
    chosen_list = []

    # Считывание GET‐параметров (если нужно)
    if request.method == 'GET':
        if 'input_text' in request.args:
            input_text = request.args['input_text']
        if 'mode' in request.args:
            mode = request.args['mode']

    # Обработка формы (POST)
    if request.method == 'POST':
        input_text = request.form.get('input_text', '')
        mode = request.form.get('mode', 'multiple_choice')
        missing_words = request.form.get('missing_words', '1')
        if missing_words == 'chosen_words':
            chosen_str = request.form.get('chosen_words', '')
            chosen_list = [w for w in chosen_str.split(',') if w.strip()]

        quiz_questions = generate_quiz(input_text, mode, missing_words, chosen_list)

    return render_template_string(
        QUIZZ_TEMPLATE,
        input_text=input_text,
        mode=mode,
        missing_words=missing_words,
        quiz_questions=quiz_questions
    )
