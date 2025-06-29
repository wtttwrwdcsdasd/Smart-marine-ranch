from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from flask_login import login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from ..models import db, User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not password:
            flash('请输入用户名和密码', 'danger')
            return render_template('login.html')

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user) 

            # 跳转不同的 Dashboard
            if user.role == 'admin':
                return redirect(url_for('main.user_dashboard'))
            else:
                return redirect(url_for('main.user_dashboard'))
        else:
            flash('用户名或密码错误', 'danger')
            return render_template('login.html')

    return render_template('login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')
        role = request.form.get('role', 'user')

        # 空字段校验
        if not username or not password or not confirm:
            flash('请填写所有字段', 'danger')
            return render_template('register.html')

        # 用户名是否已存在
        if User.query.filter_by(username=username).first():
            flash('用户名已存在', 'danger')
            return render_template('register.html')

        # 密码一致性
        if password != confirm:
            flash('两次密码不一致，请重新输入', 'danger')
            return render_template('register.html')

        # 注册成功
        new_user = User(username=username, password_hash=generate_password_hash(password), role=role)
        db.session.add(new_user)
        db.session.commit()
        flash('注册成功，请登录', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html')


@auth_bp.route('/logout')
@login_required
def logout():
    session.clear()
    return redirect(url_for('main.home'))
