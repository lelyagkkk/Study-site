import os
from flask import Blueprint, request, render_template_string, url_for
from werkzeug.utils import secure_filename

pichide_bp = Blueprint('pichide', __name__, url_prefix='/pichide')

UPLOAD_FOLDER = "static/uploads"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

PIC_HIDE_TEMPLATE = r"""
<!DOCTYPE html>
<html>
<head>
    <title>Image Hide Tool</title>
    <style>
        body {
            background: linear-gradient(to bottom, #ffebf0, #d4f0ff);
            text-align: center;
            font-family: Arial, sans-serif;
            height: 100vh;
            margin: 0;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        }
        .nav-links {
            display: flex;
            justify-content: center;
            margin-bottom: 15px;
        }
        .nav-links a {
            background-color: #ff69b4;
            color: white;
            text-decoration: none;
            padding: 14px 20px;
            margin: 5px;
            border-radius: 12px;
            font-size: 18px;
            transition: 0.3s;
        }
        .nav-links a:hover {
            opacity: 0.8;
        }
        .nav-links a:nth-child(2) {
            background-color: #ff9800;
        }
        .container {
            background: white;
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.1);
            display: inline-block;
            text-align: center;
        }
        .btn {
            background-color: #ff69b4;
            color: white;
            border: none;
            padding: 12px 20px;
            margin: 5px;
            border-radius: 10px;
            font-size: 16px;
            cursor: pointer;
            transition: 0.3s;
        }
        .btn:hover {
            background-color: #ff4181;
        }
        .file-input {
            border: 2px solid #ff69b4;
            padding: 8px;
            border-radius: 10px;
            font-size: 16px;
            display: inline-block;
        }
        .button-container {
            display: flex;
            justify-content: center;
            gap: 10px;
            margin-top: 10px;
        }
        /* Кнопки: Process - синий, CleanAll - красный */
        .button-container button:nth-child(1) {
            background-color: #4285F4;
        }
        .button-container button:nth-child(2) {
            background-color: #EA4335;
        }
        .button-container button:hover {
            opacity: 0.8;
            transform: scale(1.1);
        }
        .large-button {
             font-size: 22px;
             padding: 16px 24px;
             border-radius: 14px;
        }
        .canvas-wrapper {
            position: relative;
            display: inline-block;
            margin-top: 20px;
        }
        #canvas {
            border: 2px solid black;
            cursor: crosshair;
            border-radius: 10px;
            display: block;
        }
        .resizer {
            position: absolute;
            width: 16px; 
            height: 16px;
            background: #ff69b4;
            right: 0; 
            bottom: 0;
            cursor: se-resize;
            border-radius: 4px;
        }
    </style>
</head>
<body>
    <h1 style="color: black;">Image Hide Tool</h1>

    <div class="nav-links">
        <a href="{{ url_for('index') }}" class="large-button">Main</a>
        <a href="{{ url_for('quizz.quizz') }}" class="large-button">Quizz</a>
        <a href="{{ url_for('coding.coding') }}" class="large-button coding-button">Coding</a>
    </div>

    <div class="container">
        <form method="post" enctype="multipart/form-data">
            <input type="file" name="file" accept="image/*" class="file-input">
            <button type="submit" class="btn">Upload</button>
        </form>
        <button onclick="pasteImage()" class="btn">Paste Image</button>
        
        <div class="button-container">
            <button onclick="toggleProcess()" class="btn">Process</button>
            <button onclick="cleanAll()" class="btn">Clean All</button>
        </div>
    </div>

    <div class="canvas-wrapper">
        <canvas id="canvas"></canvas>
        <div class="resizer" id="resizer"></div>
    </div>

<script>
    let canvas = document.getElementById("canvas");
    let ctx = canvas.getContext("2d");
    let resizer = document.getElementById("resizer");

    let img = new Image();

    // Исходные размеры картинки
    let origWidth=0, origHeight=0;
    // Текущие размеры canvas
    let canvasWidth=0, canvasHeight=0;
    let scale=1.0;

    /* hiddenAreas: каждый прямоугольник = {
         x,y,w,h,
         isTrans: false  // признак "полупрозрачный" (индивидуальный)
       }
    */
    let hiddenAreas=[];

    // "Process" - глобальный: 
    let isRevealed=false;

    // Рисование нового прямоугольника
    let isDragging=false;
    let didMove=false;
    let startX=0, startY=0, currentX=0, currentY=0;

    // Resize
    let resizing=false;
    let startMouseX=0, startMouseY=0;
    let startCanvasW=0, startCanvasH=0;

    {% if image_url %}
        img.src="{{ image_url }}";
        img.onload=function(){
            initImage();
        };
    {% endif %}

    function initImage(){
        origWidth=img.width;
        origHeight=img.height;
        let maxW=600;
        if(origWidth>maxW){
            scale=maxW/origWidth;
        } else {
            scale=1.0;
        }
        canvasWidth=origWidth*scale;
        canvasHeight=origHeight*scale;
        canvas.width=canvasWidth;
        canvas.height=canvasHeight;
        drawImage();
    }

    function drawImage(){
        // очистим
        ctx.clearRect(0,0,canvas.width,canvas.height);
        ctx.save();
        ctx.scale(scale, scale);
        // Рисуем картинку
        ctx.drawImage(img,0,0);
        // Рисуем все прямоугольники
        hiddenAreas.forEach(ar=>{
            // Выбираем цвет
            // если "глобальный" isRevealed == true ИЛИ у самого area.isTrans == true
            // -> полупрозрачный, иначе обычный
            let areaAlpha = (isRevealed || ar.isTrans) ? "rgba(255,255,0,0.3)" : "yellow";
            ctx.fillStyle= areaAlpha;
            ctx.fillRect(ar.x, ar.y, ar.w, ar.h);
            ctx.strokeStyle="black";
            ctx.lineWidth=2;
            ctx.strokeRect(ar.x, ar.y, ar.w, ar.h);
        });
        ctx.restore();
    }

    // -------- MOUSE EVENTS: draw new rect -----------
    canvas.addEventListener("mousedown",(e)=>{
        if(resizing)return;
        isDragging=true;
        didMove=false;
        let rect=canvas.getBoundingClientRect();
        startX=(e.clientX-rect.left)/scale;
        startY=(e.clientY-rect.top)/scale;
    });
    canvas.addEventListener("mousemove",(e)=>{
        if(!isDragging)return;
        didMove=true;
        let rect=canvas.getBoundingClientRect();
        currentX=(e.clientX-rect.left)/scale;
        currentY=(e.clientY-rect.top)/scale;
        drawImage();
        ctx.save();
        ctx.scale(scale,scale);
        ctx.fillStyle="rgba(255,255,0,0.5)";
        ctx.fillRect(startX,startY, currentX-startX, currentY-startY);
        ctx.strokeStyle="black";
        ctx.lineWidth=2;
        ctx.strokeRect(startX,startY, currentX-startX, currentY-startY);
        ctx.restore();
    });
    canvas.addEventListener("mouseup",(e)=>{
        if(!isDragging)return;
        isDragging=false;
        let rect=canvas.getBoundingClientRect();
        let w=currentX-startX;
        let h=currentY-startY;
        if(didMove){
            // drag + release => создаём новый прямоугольник
            if(Math.abs(w)>1 && Math.abs(h)>1){
                hiddenAreas.push({
                    x:Math.min(startX,currentX),
                    y:Math.min(startY,currentY),
                    w:Math.abs(w),
                    h:Math.abs(h),
                    isTrans:false // по умолчанию непрозрачный
                });
            }
            drawImage();
        } else {
            // маленький сдвиг => клик
            let cx=(e.clientX-rect.left)/scale;
            let cy=(e.clientY-rect.top)/scale;
            // Проверим, попали ли в прямоугольник
            for(let i=hiddenAreas.length-1;i>=0;i--){
                let ar=hiddenAreas[i];
                if(cx>=ar.x && cx<=ar.x+ar.w && cy>=ar.y && cy<=ar.y+ar.h){
                    // переключаем его isTrans
                    ar.isTrans=!ar.isTrans;
                    break;
                }
            }
            drawImage();
        }
    });

    // ---------- TOUCH (аналогично) ----------
    canvas.addEventListener("touchstart",(e)=>{
        e.preventDefault();
        if(resizing)return;
        isDragging=true;
        didMove=false;
        let rect=canvas.getBoundingClientRect();
        let t=e.touches[0];
        startX=(t.clientX-rect.left)/scale;
        startY=(t.clientY-rect.top)/scale;
    },{passive:false});
    canvas.addEventListener("touchmove",(e)=>{
        e.preventDefault();
        if(!isDragging)return;
        didMove=true;
        let rect=canvas.getBoundingClientRect();
        let t=e.touches[0];
        currentX=(t.clientX-rect.left)/scale;
        currentY=(t.clientY-rect.top)/scale;
        drawImage();
        ctx.save();
        ctx.scale(scale,scale);
        ctx.fillStyle="rgba(255,255,0,0.5)";
        ctx.fillRect(startX,startY, currentX-startX, currentY-startY);
        ctx.strokeStyle="black";
        ctx.lineWidth=2;
        ctx.strokeRect(startX,startY, currentX-startX, currentY-startY);
        ctx.restore();
    },{passive:false});
    canvas.addEventListener("touchend",(e)=>{
        e.preventDefault();
        if(!isDragging)return;
        isDragging=false;
        let rect=canvas.getBoundingClientRect();
        let w=currentX-startX;
        let h=currentY-startY;
        if(didMove){
            // drag
            if(Math.abs(w)>1 && Math.abs(h)>1){
                hiddenAreas.push({
                    x:Math.min(startX,currentX),
                    y:Math.min(startY,currentY),
                    w:Math.abs(w),
                    h:Math.abs(h),
                    isTrans:false
                });
            }
        } else {
            // click
            let t=e.changedTouches[0];
            let cx=(t.clientX-rect.left)/scale;
            let cy=(t.clientY-rect.top)/scale;
            for(let i=hiddenAreas.length-1;i>=0;i--){
                let ar=hiddenAreas[i];
                if(cx>=ar.x && cx<=ar.x+ar.w && cy>=ar.y && cy<=ar.y+ar.h){
                    ar.isTrans=!ar.isTrans;
                    break;
                }
            }
        }
        drawImage();
    },{passive:false});

    // ---------- PASTE ----------
    function pasteImage(){
        navigator.clipboard.read().then(data=>{
            for(let item of data){
                if(item.types.includes("image/png")||item.types.includes("image/jpeg")){
                    item.getType(item.types[0]).then(blob=>{
                        let reader=new FileReader();
                        reader.onload=function(e){
                            img.onload=function(){
                                initImage();
                            };
                            img.src=e.target.result;
                        };
                        reader.readAsDataURL(blob);
                    });
                }
            }
        }).catch(err=>alert("Clipboard image paste failed!"));
    }

    // ---------- PROCESS & CLEAN ----------
    function toggleProcess(){
        // Переключаем глобальный "isRevealed"
        isRevealed=!isRevealed;
        drawImage();
    }
    function cleanAll(){
        hiddenAreas=[];
        drawImage();
    }

    // ---------- RESIZER ----------
    resizer.addEventListener("mousedown",(e)=>{
        resizing=true;
        startMouseX=e.clientX;
        startMouseY=e.clientY;
        startCanvasW=canvasWidth;
        startCanvasH=canvasHeight;
        e.preventDefault();
        e.stopPropagation();
    });
    document.addEventListener("mousemove",(e)=>{
        if(!resizing)return;
        let dx=e.clientX - startMouseX;
        let newW=startCanvasW+dx;
        if(newW<50) newW=50;
        scale=newW/origWidth;
        if(scale<0.1) scale=0.1;
        canvasWidth=origWidth*scale;
        canvasHeight=origHeight*scale;
        canvas.width=canvasWidth;
        canvas.height=canvasHeight;
        drawImage();
    });
    document.addEventListener("mouseup",(e)=>{
        resizing=false;
    });
</script>
</body>
</html>
"""

@pichide_bp.route('/', methods=['GET','POST'])
def pichide():
    image_url = None
    if request.method == 'POST':
        file = request.files.get('file')
        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(file_path)
            image_url = url_for('static', filename=f'uploads/{filename}')
    return render_template_string(PIC_HIDE_TEMPLATE, image_url=image_url)
