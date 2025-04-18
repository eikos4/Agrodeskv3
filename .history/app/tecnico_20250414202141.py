from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models import Recomendacion

tecnico_bp = Blueprint('tecnico', __name__)

@tecnico_bp.route('/recomendaciones')
@login_required
def ver_recomendaciones():
    if current_user.role != "tecnico":
        return "No autorizado", 403
    recomendaciones = Recomendacion.query.filter_by(tecnico_id=current_user.id).all()
    huertos = Huerto.query.filter_by(responsable_id=current_user.id).all()
    bodegas = Bodega.query.filter_by(responsable_id=current_user.id).all()
    return render_template("recomendaciones.html", 
                           recomendaciones=recomendaciones,
                           huertos=huertos,
                           bodegas=bodegas)


from app.models import Bodega

@tecnico_bp.route('/mis_bodegas')
@login_required
def mis_bodegas():
    bodegas = Bodega.query.join(Bodega.huerto).filter(
        Bodega.responsable_id == current_user.id
    ).order_by(Bodega.nombre.asc()).all()
    return render_template("mis_bodegas.html", bodegas=bodegas)




