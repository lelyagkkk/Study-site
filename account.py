from flask import Blueprint, render_template, session, redirect, url_for
# from flask_login import login_required  # если хотите использовать login_required

account_bp = Blueprint('account_bp', __name__, url_prefix='/account')

@account_bp.route('/', methods=['GET'])
def account():
    """
    Страница личного кабинета. 
    Если пользователь не залогинен, перебрасываем на страницу логина.
    """
    if 'user_id' not in session:
        return redirect(url_for('auth_bp.auth_index'))  
    # Если хотим использовать flask_login: 
    # @login_required над функцией + проверка current_user.is_authenticated

    return render_template('account.html')
