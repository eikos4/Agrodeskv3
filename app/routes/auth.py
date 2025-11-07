from flask import Blueprint, render_template, redirect, url_for, flash, session
from flask_login import login_user, logout_user, current_user
from werkzeug.security import check_password_hash
from app.forms import LoginForm
from app.models import User, Empresa

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return _redirect_by_role(current_user.role)

    form = LoginForm()
    if form.validate_on_submit():
        empresa = Empresa.query.filter_by(slug=form.empresa.data.strip().lower()).first()
        if not empresa:
            flash("Empresa no encontrada.", "danger")
            return render_template("login.html", form=form)

        user = User.query.filter_by(
            empresa_id=empresa.id,
            email=form.email.data.strip().lower()
        ).first()

        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            session["empresa_id"] = empresa.id
            flash(f"Bienvenido, {user.name}", "success")
            return _redirect_by_role(user.role)

        flash('Correo o contraseña incorrectos', 'danger')

    return render_template("login.html", form=form)

def _redirect_by_role(role):
    if role == 'admin':
        return redirect(url_for('admin.admin_dashboard'))
    elif role == 'tecnico':
        return redirect(url_for('tecnico.tecnico_dashboard'))
    flash("Rol no reconocido. Contacta al administrador.", "danger")
    return redirect(url_for('auth.login'))

@auth_bp.route('/logout')
def logout():
    session.pop("empresa_id", None)
    logout_user()
    return redirect(url_for('auth.login'))
