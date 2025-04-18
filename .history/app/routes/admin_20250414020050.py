from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from app.forms import CreateTechnicianForm, RecommendationForm
from app.models import User, Recomendacion
from app import db






from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.forms import HuertoForm
from app.models import Huerto
from app.models import Bodega
from app.forms import BodegaForm



admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/crear_tecnico', methods=['GET', 'POST'])
@login_required
def crear_tecnico():
    if current_user.role != 'admin':
        return "No autorizado", 403
    form = CreateTechnicianForm()
    if form.validate_on_submit():
        hashed_pw = generate_password_hash(form.password.data)
        new_user = User(
            name=form.name.data,
            email=form.email.data,
            password=hashed_pw,
            role="tecnico",
            created_by=current_user.id
        )
        db.session.add(new_user)
        db.session.commit()
        flash("Técnico creado exitosamente", "success")
        return redirect(url_for('main.dashboard'))
    return render_template("crear_tecnico.html", form=form)

@admin_bp.route('/recomendar', methods=['GET', 'POST'])
@login_required
def recomendar():
    if current_user.role != 'admin':
        return "No autorizado", 403
    form = RecommendationForm()
    form.tecnico_id.choices = [(u.id, u.name) for u in User.query.filter_by(role="tecnico").all()]
    if form.validate_on_submit():
        recomendacion = Recomendacion(
            contenido=form.contenido.data,
            tecnico_id=form.tecnico_id.data
        )
        db.session.add(recomendacion)
        db.session.commit()
        flash("Recomendación asignada", "success")
        return redirect(url_for('main.dashboard'))
    return render_template("recomendar.html", form=form)




@admin_bp.route('/crear_huerto', methods=['GET', 'POST'])
@login_required
def crear_huerto():
    if current_user.role != "admin":
        flash("No tienes permiso para acceder a esta página", "danger")
        return redirect(url_for('main.dashboard'))

    form = HuertoForm()
    
    # Llena el select con los técnicos disponibles
    form.responsable_id.choices = [
        (t.id, t.name) for t in User.query.filter_by(role="tecnico").all()
    ]

    if form.validate_on_submit():
        nuevo_huerto = Huerto(
            nombre=form.nombre.data,
            ubicacion=form.ubicacion.data,
            superficie_ha=form.superficie_ha.data,
            tipo_cultivo=form.tipo_cultivo.data,
            fecha_siembra=form.fecha_siembra.data,
            responsable_id=form.responsable_id.data
        )
        db.session.add(nuevo_huerto)
        db.session.commit()
        flash("Huerto creado exitosamente ✅", "success")
        return redirect(url_for('main.dashboard'))

    return render_template("huerto_form.html", form=form)




@admin_bp.route('/bodegas')
@login_required
def listar_bodegas():
    if current_user.role != "admin":
        flash("Acceso no autorizado", "danger")
        return redirect(url_for('main.dashboard'))

    bodegas = Bodega.query.order_by(Bodega.nombre.asc()).all()  # Ensure this query works correctly
    return render_template("bodegas.html", bodegas=bodegas)




@admin_bp.route('/crear_bodega', methods=['GET', 'POST'])
@login_required
def crear_bodega():
    if current_user.role != "admin":
        flash("Acceso denegado", "danger")
        return redirect(url_for('main.dashboard'))

    form = BodegaForm()
    
    # Cargar huertos y técnicos
    form.huerto_id.choices = [(h.id, h.nombre) for h in Huerto.query.all()]
    form.responsable_id.choices = [(0, "--- Sin asignar ---")] + [(t.id, t.name) for t in User.query.filter_by(role="tecnico")]

    if form.validate_on_submit():
        responsable_id = form.responsable_id.data if form.responsable_id.data != 0 else None
        nueva_bodega = Bodega(
            nombre=form.nombre.data,
            ubicacion=form.ubicacion.data,
            huerto_id=form.huerto_id.data,
            responsable_id=responsable_id
        )
        db.session.add(nueva_bodega)
        db.session.commit()
        flash("Bodega registrada correctamente ✅", "success")
        return redirect(url_for('admin.listar_bodegas'))

    return render_template("bodega_form.html", form=form)


@admin_bp.route('/bodega/<int:bodega_id>/quimicos')
@login_required
def ver_quimicos(bodega_id):
    # Aquí puedes listar los químicos de esa bodega más adelante
    return f"Químicos de la bodega {bodega_id}"



@admin_bp.route('/admin/dashboard')

@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash("Acceso no autorizado", "danger")
        return redirect(url_for('main.dashboard'))

    bodegas = Bodega.query.all()  # Asegúrate de obtener las bodegas correctamente
    tecnicos = User.query.filter_by(role='tecnico').all()  # Si también pasas los técnicos
    ultimas_recomendaciones = Recomendacion.query.order_by(Recomendacion.fecha.desc()).limit(5).all()
    return render_template('admin/admin_dashboard.html', bodegas=bodegas, tecnicos=tecnicos, ultimas_recomendaciones=ultimas_recomendaciones)


@admin_bp.route('/admin/actualizar_recomendacion/<int:recomendacion_id>', methods=['POST'])
@login_required
def actualizar_recomendacion(recomendacion_id):
    if current_user.role != 'admin':
        flash("Acceso no autorizado", "danger")
        return redirect(url_for('main.dashboard'))

    recomendacion = Recomendacion.query.get_or_404(recomendacion_id)
    recomendacion.estado = request.form['estado']
    db.session.commit()

    flash("Estado de la recomendación actualizado exitosamente", "success")
    return redirect(url_for('admin.listar_recomendaciones'))
