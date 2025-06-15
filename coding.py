from flask import Blueprint, render_template, request
from markupsafe import escape
import os

coding_bp = Blueprint('coding', __name__, url_prefix='/coding')

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)



@coding_bp.route('/', methods=['GET'])
def coding():
    """
    Два режима:
      - Trace (по-умолчанию)
      - Memory
    Данные берём из GET-параметров: ?mode=trace&trace_code_input=...
    """
    mode = request.args.get('mode','trace')
    trace_code = request.args.get('trace_code_input','')
    memory_code = request.args.get('memory_code_input','')
    return render_template(
        'coding.html',
        mode=mode,
        trace_code=trace_code,
        memory_code=memory_code
    )
