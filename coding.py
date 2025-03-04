from flask import Blueprint, render_template_string, request, redirect, url_for
from markupsafe import escape
import os, random

coding_bp = Blueprint('coding', __name__, url_prefix='/coding')

UPLOAD_FOLDER = "static/uploads"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

CODING_TEMPLATE = r"""
<!DOCTYPE html>
<html>
<head>
    <title>Coding Practice</title>
    <!-- Prism для подсветки (по умолчанию Python).
         Если в memory_mode текст - HTML, можно менять язык 
         (либо ставить <script src=.../prism-html.min.js> и т.д.) -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/prism.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-python.min.js"></script>

    <style>
      body {
        margin: 0; 
        padding: 20px;
        background: #1e1e1e;
        font-family: Consolas, "Courier New", monospace;
        display: flex; 
        flex-direction: column; 
        align-items: center;
        min-height: 100vh;
        color: #d4d4d4;
      }
      h1 {
        margin-top: 0;
        color: #d4d4d4;
      }
      .nav-buttons {
        margin-bottom: 20px;
        width: 100%;
        max-width: 1000px;
        display: flex;
        justify-content: space-between;
      }
      .nav-buttons a {
        text-decoration: none;
      }
      .main-btn {
        background: linear-gradient(135deg, #f44336, #ff9800);
        color: #fff;
        border: none;
        padding: 10px 20px;
        font-size: 16px;
        border-radius: 6px;
        cursor: pointer;
        transition: transform 0.3s, box-shadow 0.3s;
      }
      .main-btn:hover {
        transform: scale(1.1);
        box-shadow: 0 0 10px rgba(255,255,255,0.3);
      }
      .mode-btns {
        display: flex;
        gap: 10px;
      }
      .mode-btn {
        background: linear-gradient(135deg, #2196F3, #03A9F4);
        color: #fff;
        border: none;
        padding: 10px 20px;
        font-size: 16px;
        border-radius: 6px;
        cursor: pointer;
        transition: transform 0.3s, box-shadow 0.3s;
      }
      .mode-btn:hover {
        transform: scale(1.08);
        box-shadow: 0 0 8px rgba(255,255,255,0.3);
      }
      .mode-btn.active {
        background: linear-gradient(135deg, #03a9f4, #00bcd4);
        box-shadow: 0 0 10px rgba(255,255,255,0.3);
      }

      .container {
        width: 90%; 
        max-width: 1000px;
        background: #2e2e2e; 
        padding: 20px; 
        border-radius: 10px;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);
        margin-bottom: 20px; 
        overflow-x: auto;
      }
      .upload-section {
        margin-top: 10px;
      }
      textarea {
        width: 100%; 
        height: 120px;
        background: #1e1e1e; 
        color: #d4d4d4;
        border: 1px solid #444; 
        font-size: 16px;
      }
      pre {
        width: 100%;
        background: #1e1e1e; 
        padding: 20px; 
        border-radius: 10px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.3);
        overflow-x: auto;
        font-size: 18px; 
        line-height: 1.5;
        color: #d4d4d4;
        white-space: pre-wrap;   /* Сохранение переносов */
      }
      code {
        font-family: Consolas, "Courier New", monospace;
        white-space: pre-wrap;   /* Тоже для переносов */
      }

      /* ---- Trace Mode ---- */
      .char-hidden {
        opacity: 0.2;
        font-weight: normal;
        transition: all 0.2s;
      }
      .char-revealed {
        opacity: 1;
        font-weight: bold;
      }
      #tiny-input {
        position: fixed;
        top: 0; left: 0;
        width: 1px; 
        height: 1px;
        opacity: 0.01;
        z-index: 9999;
        color: transparent;
      }

      /* ---- Memory Mode ---- */
      .memory-missing {
        display: inline-block;
        border: 2px solid #444;
        border-radius: 4px;
        background: #1e1e1e;
        color: #d4d4d4;
        padding: 2px 6px;
        margin: 0 1px;
        font-size: 16px;
        vertical-align: middle;
      }
      .memory-missing.correct {
        background: #8bc34a;
        color: #000;
      }
      .memory-missing.incorrect {
        background: #e91e63;
        color: #fff;
      }
      /* Пример раскраски token (VS Code-like) */
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
    <h1>Coding Practice</h1>

    <div class="nav-buttons">
      <a href="{{ url_for('index') }}"><button class="main-btn">Main</button></a>
      <div class="mode-btns">
        <button id="traceModeBtn" class="mode-btn active">Trace Mode</button>
        <button id="memoryModeBtn" class="mode-btn">Memory Mode</button>
      </div>
    </div>

    <!-- TRACE MODE -->
    <div id="traceMode" class="container">
      <h2 style="margin-top:0;">Trace Mode</h2>
      <form method="post" id="traceForm" enctype="multipart/form-data">
        <textarea name="trace_code_input" id="trace-code-input">{{ trace_code }}</textarea><br>
        <div class="upload-section">
          <label>Import code file:
            <input type="file" name="trace_file" accept=".py,.ipynb,.cs,.cpp">
          </label>
        </div>
        <button type="button" id="trace-load-btn">Load Code</button>
      </form>
      <pre id="traceCodeOutput" class="language-python"></pre>
      <input id="tiny-input" type="text">
    </div>

    <!-- MEMORY MODE -->
    <div id="memoryMode" class="container" style="display:none;">
      <h2 style="margin-top:0;">Memory Mode</h2>
      <form method="post" id="memoryForm" enctype="multipart/form-data">
        <textarea name="memory_code_input" id="memory-code-input">{{ memory_code }}</textarea><br>
        <div class="upload-section">
          <label>Import code file:
            <input type="file" name="memory_file" accept=".py,.ipynb,.cs,.cpp">
          </label>
        </div>
        <label for="memory_percent">Hide words (%):</label>
        <select id="memory_percent">
          <option value="10">10%</option>
          <option value="20" selected>20%</option>
          <option value="30">30%</option>
          <option value="40">40%</option>
          <option value="50">50%</option>
          <option value="60">60%</option>
          <option value="70">70%</option>
          <option value="80">80%</option>
          <option value="90">90%</option>
          <option value="100">100%</option>
        </select><br>
        <button type="button" id="memory-generate-btn">Generate Missing Words</button>
      </form>
      <pre id="memoryCodeOutput" class="language-python"></pre>
    </div>

    <script>
      // =========== TRACE MODE ===========
      let traceChars = [];
      let traceIndex = 0;

      document.addEventListener('DOMContentLoaded', () => {
        const traceOut = document.getElementById('traceCodeOutput');
        const traceInp = document.getElementById('trace-code-input');
        const traceTiny = document.getElementById('tiny-input');
        const traceLoadBtn = document.getElementById('trace-load-btn');

        traceTiny.focus();
        document.addEventListener('click', ()=>traceTiny.focus());

        traceLoadBtn.addEventListener('click', async()=>{
          traceOut.innerHTML='';
          traceChars=[];
          traceIndex=0;

          let code = traceInp.value || '';
          let fInput = document.querySelector('input[name="trace_file"]');
          if (fInput.files && fInput.files.length>0){
            let file = fInput.files[0];
            code = await readFileAsText(file);
            traceInp.value = code;
          }

          let prismHTML = Prism.highlight(code, Prism.languages.python, 'python');
          let tempDiv = document.createElement('div');
          tempDiv.innerHTML = prismHTML;
          let frag = document.createDocumentFragment();
          transformTrace(tempDiv, frag, traceChars);
          traceOut.appendChild(frag);

          traceTiny.focus();
        });

        // Разрешаем вставку, обрабатывая все символы
        traceTiny.addEventListener('input',(e)=>{
          let typed = e.target.value;
          e.target.value='';
          if(!typed)return;
          for(let c of typed){
            if(traceIndex<traceChars.length){
              let ex = traceChars[traceIndex].textContent;
              if(c===ex){
                traceChars[traceIndex].classList.remove('char-hidden');
                traceChars[traceIndex].classList.add('char-revealed');
                traceIndex = skipWhite(traceChars, traceIndex+1);
              }
            }
          }
        });

        // =========== MEMORY MODE ===========
        const memInp = document.getElementById('memory-code-input');
        const memBtn = document.getElementById('memory-generate-btn');
        const memOut = document.getElementById('memoryCodeOutput');
        const memPercentSel = document.getElementById('memory_percent');

        memBtn.addEventListener('click', async()=>{
          memOut.innerHTML='';

          let code = memInp.value || '';
          let mfInput = document.querySelector('input[name="memory_file"]');
          if(mfInput.files && mfInput.files.length>0){
            let file = mfInput.files[0];
            code = await readFileAsText(file);
            memInp.value=code;
          }

          // Пускаем через Prism
          let prismHTML = Prism.highlight(code, Prism.languages.python, 'python');
          let tmp = document.createElement('div');
          tmp.innerHTML=prismHTML;

          // Собираем узлы
          let T=[];
          gatherTokens(tmp, T);

          // Определяем какие узлы можно скрывать
          let hideCandidates=[];
          for(let i=0;i<T.length;i++){
            let tk=T[i];
            // if punctuation => не скрываем
            if(isPunctuationToken(tk)){ 
              continue; 
            }
            // if whitespace => не скрываем
            if(isWhitespaceToken(tk)){ 
              continue;
            }
            hideCandidates.push(i);
          }

          let pVal=parseInt(memPercentSel.value||'20',10);
          let hideCount=Math.floor(hideCandidates.length*(pVal/100));
          shuffle(hideCandidates);
          let hideSet=new Set(hideCandidates.slice(0, hideCount));

          // Собираем готовый DOM
          let fragMem = buildMemory(T, hideSet);
          memOut.appendChild(fragMem);

          // Активация логики ввода
          memOut.querySelectorAll('input.memory-missing').forEach(inpEl=>{
            inpEl.addEventListener('input', function(){
              let correct=(this.dataset.correct||'').trim();
              let typed=this.value.trim();
              if(typed===correct){
                this.classList.remove('incorrect');
                this.classList.add('correct');
                this.readOnly=true;
                let nxt=findNextMissing(this);
                if(nxt)nxt.focus();
              }else{
                if(typed.length>0)this.classList.add('incorrect');
                else this.classList.remove('incorrect');
                this.classList.remove('correct');
              }
            });
          });
        });

        // Переключение режимов
        const traceDiv=document.getElementById('traceMode');
        const memDiv=document.getElementById('memoryMode');
        const tBtn=document.getElementById('traceModeBtn');
        const mBtn=document.getElementById('memoryModeBtn');

        tBtn.addEventListener('click',()=>{
          traceDiv.style.display='';
          memDiv.style.display='none';
          tBtn.classList.add('active');
          mBtn.classList.remove('active');
        });
        mBtn.addEventListener('click',()=>{
          traceDiv.style.display='none';
          memDiv.style.display='';
          mBtn.classList.add('active');
          tBtn.classList.remove('active');
        });
      });

      // ============ Trace Utils ============
      function transformTrace(src, dest, arr){
        for(let child of src.childNodes){
          if(child.nodeType===Node.TEXT_NODE){
            let txt=child.nodeValue;
            for(let c of txt){
              let span=document.createElement('span');
              span.classList.add('char-hidden');
              span.textContent=c;
              dest.appendChild(span);
              arr.push(span);
            }
          }else if(child.nodeType===Node.ELEMENT_NODE){
            let cloned=document.createElement(child.tagName);
            cloned.className=child.className;
            transformTrace(child, cloned, arr);
            dest.appendChild(cloned);
          }
        }
      }
      function skipWhite(a, idx){
        let i=idx;
        while(i<a.length){
          if(/\s/.test(a[i].textContent)){
            a[i].classList.remove('char-hidden');
            a[i].classList.add('char-revealed');
            i++;
          }else break;
        }
        return i;
      }

      // ============ Memory Utils ============
      // Сбор всех нод в список
      function gatherTokens(node, arr){
        for(let child of node.childNodes){
          if(child.nodeType===Node.TEXT_NODE){
            arr.push({type:'text', text:child.nodeValue});
          }else if(child.nodeType===Node.ELEMENT_NODE){
            // Prism даёт <span class="token ...">
            let sub={
              type:'element',
              className:child.className,
              tagName:child.tagName,
              children:[]
            };
            gatherTokens(child, sub.children);
            arr.push(sub);
          }
        }
      }

      // Собираем финальный DOM
      function buildMemory(tokens, hideSet, offset=0){
        let frag=document.createDocumentFragment();
        for(let i=0;i<tokens.length;i++){
          let realI=offset+i;
          let tk=tokens[i];
          if(tk.type==='text'){
            // text => возможно hide
            if(hideSet.has(realI)){
              // заменяем весь текст на input
              let input=document.createElement('input');
              input.type='text';
              input.classList.add('memory-missing');
              input.dataset.correct=tk.text; 
              // ширина
              let len=tk.text.replace(/\n/g,'').replace(/\r/g,'').length+2;
              if(len<2)len=2;
              input.style.width=len+'ch';
              frag.appendChild(input);
            }else{
              // просто текст (с переносами и пробелами)
              let span=document.createElement('span');
              span.textContent=tk.text;
              frag.appendChild(span);
            }
          }else{
            // element
            if(hideSet.has(realI) && !isPunctuationClass(tk.className)){ 
              // Если класс не punctuation - скрываем всё
              let inp=document.createElement('input');
              inp.type='text';
              inp.className='memory-missing';
              // Собираем «внутренний текст» для data-correct
              let innerTxt = getAllText(tk);
              let length = innerTxt.replace(/\n/g,'').replace(/\r/g,'').length+2;
              if(length<2)length=2;
              inp.style.width=length+'ch';
              inp.dataset.correct=innerTxt;
              frag.appendChild(inp);
            }else{
              // рендерим рекурсивно
              let el=document.createElement(tk.tagName);
              el.className=tk.className;
              let subFrag=buildMemory(tk.children, hideSet, realI*1000+i);
              el.appendChild(subFrag);
              frag.appendChild(el);
            }
          }
        }
        return frag;
      }

      // Определить, является ли элемент punctuation
      function isPunctuationClass(cls){
        return /\bpunctuation\b/.test(cls||'');
      }

      // Проверяем, punctuation ли данный токен
      function isPunctuationToken(tk){
        if(tk.type==='element'){
          if(isPunctuationClass(tk.className))return true;
          return false;
        }
        // text, надо проверить, не только ли знаки пунктуации
        // Но Prism обычно punctuation делает отдельный <span> 
        // text node punctuation - редкое
        // оставим as is => false
        return false;
      }

      // Проверяем, whitespace ли
      function isWhitespaceToken(tk){
        if(tk.type==='text'){
          return /^\s*$/.test(tk.text);
        }
        return false;
      }

      // Достаём весь текст из children
      function getAllText(obj){
        let buf='';
        if(obj.type==='text'){
          buf+=obj.text;
        }else if(obj.type==='element'){
          for(let c of obj.children){
            buf+=getAllText(c);
          }
        }
        return buf;
      }

      // Shuffle
      function shuffle(arr){
        for(let i=arr.length-1;i>0;i--){
          let j=Math.floor(Math.random()*(i+1));
          [arr[i],arr[j]]=[arr[j],arr[i]];
        }
      }

      // Находим следующее скрытое поле
      function findNextMissing(current){
        let all = [...document.querySelectorAll('input.memory-missing')];
        let idx=all.indexOf(current);
        if(idx>=0 && idx<all.length-1){
          return all[idx+1];
        }
        return null;
      }

    </script>
</body>
</html>
"""

@coding_bp.route('/', methods=['GET', 'POST'])
def coding():
    """
    trace_code / memory_code: тексты из textarea
    trace_file / memory_file: загружаемые файлы .py,.ipynb,.cs,.cpp
    """
    trace_code = ""
    memory_code = ""

    if request.method == 'POST':
        if 'trace_code_input' in request.form:
            trace_code = request.form.get('trace_code_input','').strip()
        if 'memory_code_input' in request.form:
            memory_code = request.form.get('memory_code_input','').strip()

    return render_template_string(
        CODING_TEMPLATE,
        trace_code=escape(trace_code),
        memory_code=escape(memory_code),
    )
