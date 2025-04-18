from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, login_user, logout_user, current_user
from werkzeug.security import check_password_hash
from app.forms import LoginForm
from app.models import User

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # Si ya está autenticado, redirige según su rol
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin.admin_dashboard'))
        elif current_user.role == 'tecnico':
            return redirect(url_for('tecnico.ver_recomendaciones'))
        else:
            return redirect(url_for('main.dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            flash(f"Bienvenido, {user.name}", "success")

            # Redirección por rol
            if user.role == 'admin':
                return redirect(url_for('admin.admin_dashboard'))
            elif user.role == 'tecnico':
                return redirect(url_for('tecnico.ver_recomendaciones'))
            else:
                return redirect(url_for('main.dashboard'))

        flash('Correo o contraseña incorrectos', 'danger')

    return render_template("login.html", form=form)



@auth_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
