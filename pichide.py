import os
from flask import Blueprint, request, render_template_string, url_for
from werkzeug.utils import secure_filename

pichide_bp = Blueprint('pichide', __name__, url_prefix='/pichide')

UPLOAD_FOLDER = "static/uploads"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

PIC_HIDE_TEMPLATE = """ 
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
        .container {
            background: white;
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.1);
            display: inline-block;
            text-align: center;
        }
        canvas {
            border: 2px solid black;
            cursor: crosshair;
            display: block;
            margin: auto;
            border-radius: 10px;
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
        .nav-links {
            display: flex;
            justify-content: center;
            margin-bottom: 15px;
        }
        .nav-links a {
            background-color: #ff69b4; /* Розовый цвет для Main */
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
        .button-container {
            display: flex;
            justify-content: center;
            gap: 10px;
            margin-top: 10px;
        }
        .nav-links a:nth-child(2) {
            background-color: #ff9800; /* Оранжевый цвет для Quizz */
        }
        .button-container button:nth-child(1) { /* Hide - синий */
            background-color: #4285F4;
        }

        .button-container button:nth-child(2) { /* Reveal - зелёный */
            background-color: #34A853;
        }

        .button-container button:nth-child(3) { /* Clean All - красный */
            background-color: #EA4335;
        }

        .button-container button {
            color: white;
            padding: 14px 22px;
            margin: 5px;
            border-radius: 10px;
            font-size: 18px;
            cursor: pointer;
            transition: 0.3s;
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

    <br>
    <canvas id="canvas"></canvas>

    <script>
        let canvas = document.getElementById("canvas");
        let ctx = canvas.getContext("2d");
        let img = new Image();
        let isDragging = false;
        let startX, startY, currentX, currentY;
        let hiddenAreas = [];
        let isRevealed = false;

        {% if image_url %}
            img.src = "{{ image_url }}";
            img.onload = function() {
                canvas.width = img.width;
                canvas.height = img.height;
                drawImage();
            };
        {% endif %}

        function drawImage() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
            hiddenAreas.forEach(area => {
                ctx.fillStyle = isRevealed ? "rgba(255, 255, 0, 0.3)" : "yellow";  
                ctx.fillRect(area.x, area.y, area.w, area.h);
                ctx.strokeStyle = "black";
                ctx.lineWidth = 2;
                ctx.strokeRect(area.x, area.y, area.w, area.h);
            });
        }

        function pasteImage() {
            navigator.clipboard.read().then(data => {
                for (let item of data) {
                    if (item.types.includes("image/png") || item.types.includes("image/jpeg")) {
                        item.getType(item.types[0]).then(blob => {
                            let reader = new FileReader();
                            reader.onload = function(e) {
                                img.onload = function() {
                                    canvas.width = img.width;
                                    canvas.height = img.height;
                                    drawImage();
                                };
                                img.src = e.target.result;
                            };
                            reader.readAsDataURL(blob);
                        });
                    }
                }
            }).catch(err => alert("Clipboard image paste failed!"));
        }

        canvas.addEventListener("mousedown", function(event) {
            isDragging = true;
            startX = event.offsetX;
            startY = event.offsetY;
        });

        canvas.addEventListener("mousemove", function(event) {
            if (isDragging) {
                currentX = event.offsetX;
                currentY = event.offsetY;
                drawImage();
                ctx.fillStyle = "rgba(255, 255, 0, 0.7)";
                ctx.fillRect(startX, startY, currentX - startX, currentY - startY);
                ctx.strokeStyle = "black";
                ctx.lineWidth = 2;
                ctx.strokeRect(startX, startY, currentX - startX, currentY - startY);
            }
        });

        canvas.addEventListener("mouseup", function(event) {
            if (isDragging) {
                let endX = event.offsetX;
                let endY = event.offsetY;
                let width = endX - startX;
                let height = endY - startY;

                if (width > 5 && height > 5) {
                    hiddenAreas.push({ x: startX, y: startY, w: width, h: height });
                }
                drawImage();
            }
            isDragging = false;
        });


        function toggleProcess() {
            isRevealed = !isRevealed;
            drawImage();
        }

        function cleanAll() {
            hiddenAreas = [];
            drawImage();
        }
        // Обработчик для мобильных устройств
canvas.addEventListener("touchstart", function(event) {
    isDragging = true;
    let touch = event.touches[0];
    let rect = canvas.getBoundingClientRect();
    startX = touch.clientX - rect.left;
    startY = touch.clientY - rect.top;
    event.preventDefault();
});

canvas.addEventListener("touchmove", function(event) {
    if (isDragging) {
        let touch = event.touches[0];
        let rect = canvas.getBoundingClientRect();
        currentX = touch.clientX - rect.left;
        currentY = touch.clientY - rect.top;
        drawImage();
        ctx.fillStyle = "rgba(255, 255, 0, 0.7)";
        ctx.fillRect(startX, startY, currentX - startX, currentY - startY);
        ctx.strokeStyle = "black";
        ctx.lineWidth = 2;
        ctx.strokeRect(startX, startY, currentX - startX, currentY - startY);
    }
    event.preventDefault();
});

canvas.addEventListener("touchend", function(event) {
    if (isDragging) {
        let rect = canvas.getBoundingClientRect();
        let endX = currentX;
        let endY = currentY;
        let width = endX - startX;
        let height = endY - startY;

        if (width > 5 && height > 5) {
            hiddenAreas.push({ x: startX, y: startY, w: width, h: height });
        }
        drawImage();
    }
    isDragging = false;
    event.preventDefault();
});
    </script>
</body>
</html>
"""

@pichide_bp.route('/', methods=['GET', 'POST'])
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
