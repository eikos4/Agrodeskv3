from flask import Blueprint, render_template

from app.models import User, Recomendacion, Huerto
from app.models import Bodega

from flask_login import login_required, current_user

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('index.html')




@main_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == "admin":
        tecnicos = User.query.filter_by(role="tecnico").all()
        ultimas_recomendaciones = Recomendacion.query.order_by(Recomendacion.fecha.desc()).limit(5).all()
        huertos = Huerto.query.order_by(Huerto.fecha_siembra.desc()).all()
        return render_template(
            "dashboard.html",
            tecnicos=tecnicos,
            ultimas_recomendaciones=ultimas_recomendaciones,
            huertos=huertos
        )
    else:
        recomendaciones = Recomendacion.query.filter_by(tecnico_id=current_user.id).order_by(Recomendacion.fecha.desc()).limit(5).all()
        huertos = Huerto.query.filter_by(responsable_id=current_user.id).order_by(Huerto.fecha_siembra.desc()).all()
        bodegas = Bodega.query.filter_by(responsable_id=current_user.id).all()
        return render_template(
            "dashboard.html",
            recomendaciones=recomendaciones,
            huertos=huertos,
            bodegas=bodegas  # ✅ ahora se pasan las bodegas al template
        )
