import os
import json
import datetime
from flask import Blueprint, request, render_template, redirect, url_for, jsonify

mycalendar_bp = Blueprint('mycalendar_bp', __name__, url_prefix='/calendar')

EVENTS_FILE = "calendar_events.json"

def save_events(events):
    with open(EVENTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(events, f, indent=2, ensure_ascii=False)

def load_events():
    """
    Считываем объекты (категории + дедлайны) из JSON,
    если нет файла – создаём пустой список.
    Проверяем/добавляем 'id', 'subtasks' (для дедлайнов).
    """
    if os.path.exists(EVENTS_FILE):
        with open(EVENTS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        data = []

    max_id=0
    for obj in data:
        if isinstance(obj.get('id'), int) and obj['id']>max_id:
            max_id=obj['id']

    changed=False
    for obj in data:
        if 'id' not in obj:
            max_id+=1
            obj['id']=max_id
            changed=True
        if not obj.get('isCategory'):
            if 'subtasks' not in obj:
                obj['subtasks']=[]
                changed=True

    if changed:
        save_events(data)
    return data

def parse_date_with_formats(date_str):
    """
    Пытаемся распарсить строку, проверяя несколько форматов:
      - YYYY-MM-DD
      - MM/DD/YYYY
      - DD/MM/YYYY
    При успехе возвращаем datetime.datetime, иначе None.
    """
    fmts = ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y")
    for fmt in fmts:
        try:
            dt = datetime.datetime.strptime(date_str, fmt)
            return dt
        except:
            pass
    return None

@mycalendar_bp.route('/', methods=['GET'])
def index_calendar():
    """
    Главная страница.
    - Форма Add Category (название + цвет)
    - Форма Add Deadline (дата + заголовок + цвет + категория)
    - Категории (isCategory) со сворачиванием.
    - Дедлайны внутри категорий, плюс "No category".
    """
    data=load_events()

    categories=[c for c in data if c.get('isCategory')]
    deadlines=[d for d in data if not d.get('isCategory')]

    # Вычислим day-of-week для каждого дедлайна
    for d in deadlines:
        d['weekday']=''
        if 'date' in d:
            dt = parse_date_with_formats(d['date'])
            if dt:
                d['weekday']=dt.strftime("%A")  # Monday, Tuesday, ...
            # иначе пустая строка

    # Сортируем дедлайны
    deadlines.sort(key=lambda x: x.get('date','9999-12-31'))

    # Нумеруем подзадачи
    for d in deadlines:
        enumerated=[]
        for i, st in enumerate(d['subtasks']):
            enumerated.append({"idx": i, "text": st['text'], "done": st['done']})
        d['_subtasks_enumerated']=enumerated

    return render_template('mycalendar.html',
                           categories=categories,
                           deadlines=deadlines)

@mycalendar_bp.route('/add_category', methods=['POST'])
def add_category():
    name = request.form.get("category_name","").strip()
    color= request.form.get("category_color","#666666").strip()
    if not name:
        return redirect(url_for('mycalendar_bp.index_calendar'))

    data=load_events()
    new_id=1 if not data else max(o["id"] for o in data)+1

    data.append({
        "id": new_id,
        "isCategory": True,
        "title": name,
        "color": color
    })
    save_events(data)
    return redirect(url_for('mycalendar_bp.index_calendar'))

@mycalendar_bp.route('/add_deadline', methods=['POST'])
def add_deadline():
    date=request.form.get("date","").strip()
    title=request.form.get("title","").strip()
    color=request.form.get("color","#ff69b4").strip()
    cat_id=int(request.form.get("category_id","0"))

    if not date or not title:
        return redirect(url_for('mycalendar_bp.index_calendar'))

    data=load_events()
    new_id=1 if not data else max(o["id"] for o in data)+1

    data.append({
        "id": new_id,
        "isCategory": False,
        "date": date,
        "title": title,
        "color": color,
        "subtasks": [],
        "category_id": cat_id
    })
    save_events(data)
    return redirect(url_for('mycalendar_bp.index_calendar'))

@mycalendar_bp.route('/delete_deadline/<int:item_id>', methods=['POST'])
def delete_deadline(item_id):
    data=load_events()
    new_data=[obj for obj in data if obj['id']!=item_id]
    save_events(new_data)
    return "OK"

@mycalendar_bp.route('/add_subtask', methods=['POST'])
def add_subtask():
    did=int(request.form.get("deadline_id","-1"))
    st_text=request.form.get("subtask_text","").strip()
    if not st_text:
        return redirect(url_for('mycalendar_bp.index_calendar'))

    data=load_events()
    for d in data:
        if d['id']==did and not d.get('isCategory'):
            d['subtasks'].append({"text": st_text, "done":False})
            break
    save_events(data)
    return redirect(url_for('mycalendar_bp.index_calendar'))

@mycalendar_bp.route('/mark_subtask', methods=['POST'])
def mark_subtask():
    info=request.get_json()
    did=info.get("deadline_id",-1)
    idx=info.get("subtask_index",-1)
    done=info.get("done",False)

    data=load_events()
    for d in data:
        if d['id']==did and not d.get('isCategory'):
            if 0<=idx<len(d['subtasks']):
                d['subtasks'][idx]['done']=bool(done)
            break
    save_events(data)
    return "OK"

@mycalendar_bp.route('/delete_subtask', methods=['POST'])
def delete_subtask():
    info=request.get_json()
    did=info.get("deadline_id",-1)
    idx=info.get("subtask_index",-1)

    data=load_events()
    for d in data:
        if d['id']==did and not d.get('isCategory'):
            if 0<=idx<len(d['subtasks']):
                d['subtasks'].pop(idx)
            break
    save_events(data)
    return "OK"
