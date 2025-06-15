# auth.py
import os, json
from flask import Blueprint, render_template, request, redirect, url_for, session
from markupsafe import escape

auth_bp = Blueprint('auth_bp', __name__, url_prefix='/auth')

USERDATA_FILE = 'users.json'  # In production, store in a real DB

def load_users():
    """Load user database from JSON file."""
    if not os.path.exists(USERDATA_FILE):
        return {}
    with open(USERDATA_FILE,'r',encoding='utf-8') as f:
        return json.load(f)

def save_users(users):
    with open(USERDATA_FILE,'w',encoding='utf-8') as f:
        json.dump(users,f,indent=2)

@auth_bp.route('/', methods=['GET'])
def auth_index():
    """Страница с формами регистрации / логина, статусом."""
    return render_template('auth.html', message="", session=session)

@auth_bp.route('/register', methods=['POST'])
def register():
    username = request.form.get('username','').strip()
    password = request.form.get('password','').strip()
    if not username or not password:
        return render_template('auth.html',
                               message="Username/Password cannot be empty",
                               session=session)
    users = load_users()
    if username in users:
        return render_template('auth.html',
                               message="Username already exists!",
                               session=session)
    users[username] = {"password": password}
    save_users(users)
    return render_template('auth.html', message="Registered OK! You can login now.", session=session)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('auth.html', message="", session=session)

    username = request.form.get('username','').strip()
    password = request.form.get('password','').strip()
    users = load_users()

    if username in users and users[username]["password"] == password:
        session['user_id'] = username
        # После логина перенаправляем в /account
        return redirect(url_for('account_bp.account'))
    else:
        return render_template('auth.html', 
                               message="Invalid username/password!",
                               session=session)

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Logout user."""
    session.pop('user_id', None)
    return redirect(url_for('auth_bp.auth_index'))
