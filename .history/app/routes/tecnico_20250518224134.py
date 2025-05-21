from datetime import datetime
from flask import Blueprint, flash, render_template, redirect, request, url_for
from flask_login import login_required, current_user
from app.models import Bodega, Huerto, Recomendacion, Quimico, FormularioTarea, ChecklistItem, db
from app.forms import QuimicoForm, ResponderFormularioForm, ChecklistItemForm, RegistrarActividadForm
from functools import wraps

tecnico_bp = Blueprint('tecnico', __name__)

# === Decorador: solo técnicos pueden acceder ===
def tecnico_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'tecnico':
            flash("Acceso solo permitido a técnicos.", "danger")
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

# === Helpers de permisos ===
def tecnico_puede_acceder_a_bodega(bodega):
    # Puede acceder si está asignado por relación o es responsable principal
    return (
        bodega in current_user.bodegas_asignadas.all() or
        bodega.responsable_id == current_user.id
    )

def tecnico_puede_acceder_a_huerto(huerto):
    # Acceso si está asignado al técnico o es responsable principal
    return (
        huerto in current_user.huertos_asignados or
        huerto.responsable_id == current_user.id
    )

# === Dashboard técnico ===
@tecnico_bp.route('/tecnico/dashboard')
@login_required
@tecnico_required
def tecnico_dashboard():
    # Bodegas por relación y responsabilidad
    bodegas = list(
        set(current_user.bodegas_asignadas.all()) |
        set(Bodega.query.filter_by(responsable_id=current_user.id).all())
    )
    huertos = list(
        set(current_user.huertos_asignados) |
        set(Huerto.query.filter_by(responsable_id=current_user.id).all())
    )
    recomendaciones = Recomendacion.query.filter_by(tecnico_id=current_user.id).all()
    return render_template(
        'tecnico/tecnico_dashboard.html',
        bodegas=bodegas, huertos=huertos, recomendaciones=recomendaciones
    )

# === Recomendaciones ===
@tecnico_bp.route('/recomendaciones')
@login_required
@tecnico_required
def ver_recomendaciones():
    todas = Recomendacion.query.filter_by(tecnico_id=current_user.id).order_by(Recomendacion.fecha.desc()).all()
    recomendaciones_pendientes = [r for r in todas if r.estado != 'completada']
    recomendaciones_completadas = [r for r in todas if r.estado == 'completada']
    return render_template(
        "tecnico/recomendaciones.html",
        recomendaciones_pendientes=recomendaciones_pendientes,
        recomendaciones_completadas=recomendaciones_completadas
    )

@tecnico_bp.route('/recomendacion/<int:reco_id>/completar', methods=['POST'])
@login_required
@tecnico_required
def completar_recomendacion(reco_id):
    recomendacion = Recomendacion.query.get_or_404(reco_id)
    if recomendacion.tecnico_id != current_user.id:
        flash("No puedes modificar esta recomendación.", "danger")
        return redirect(url_for('tecnico.ver_recomendaciones'))
    recomendacion.estado = 'completada'
    db.session.commit()
    flash("¡Recomendación marcada como completada!", "success")
    return redirect(url_for('tecnico.ver_recomendaciones'))

# === Huertos asignados ===
@tecnico_bp.route('/mis_huertos')
@login_required
@tecnico_required
def mis_huertos():
    huertos = list(
        set(current_user.huertos_asignados) |
        set(Huerto.query.filter_by(responsable_id=current_user.id).all())
    )
    return render_template('tecnico/mis_huertos.html', huertos=huertos)

# === Bitácora de huerto técnico (con filtros) ===
@tecnico_bp.route('/huerto/<int:huerto_id>/bitacora')
@login_required
@tecnico_required
def bitacora_huerto(huerto_id):
    huerto = Huerto.query.get_or_404(huerto_id)
    if not tecnico_puede_acceder_a_huerto(huerto):
    flash("No tienes acceso a este huerto.", "danger")
    return redirect(url_for('tecnico.mis_huertos'))
    actividades = huerto.actividades
    return render_template('tecnico/bitacora_huerto.html', huerto=huerto, actividades=actividades)


# === Registrar actividad en huerto técnico ===
@tecnico_bp.route('/huerto/<int:huerto_id>/registrar_actividad', methods=['GET', 'POST'])
@login_required
@tecnico_required
def registrar_actividad_huerto(huerto_id):
    huerto = Huerto.query.get_or_404(huerto_id)
    if not tecnico_puede_acceder_a_huerto(huerto):
        flash("No tienes acceso a este huerto.", "danger")
        return redirect(url_for('tecnico.mis_huertos'))
    form = RegistrarActividadForm()
    if form.validate_on_submit():
        try:
            from app.models import ActividadHuerto
            actividad = ActividadHuerto(
                huerto_id=huerto.id,
                fecha=form.fecha.data,
                tipo=form.tipo.data,
                descripcion=form.descripcion.data,
                responsable=current_user.name,
                producto=form.producto.data,
                dosis=form.dosis.data,
                plaga=form.plaga.data,
                nivel_infestacion=form.nivel_infestacion.data,
                resultado=form.resultado.data,
                fotos='',
                observaciones=form.observaciones.data,
            )
            db.session.add(actividad)
            db.session.commit()
            flash("✅ Actividad registrada exitosamente.", "success")
            return redirect(url_for('tecnico.bitacora_huerto', huerto_id=huerto.id))
        except Exception as e:
            db.session.rollback()
            flash(f"Error registrando actividad: {e}", "danger")
    return render_template('tecnico/registrar_actividad.html', form=form, huerto=huerto)

# === Ver bodegas asignadas (por relación y/o responsable) ===
@tecnico_bp.route('/mis_bodegas')
@login_required
@tecnico_required
def mis_bodegas():
    bodegas = list(
        set(current_user.bodegas_asignadas.all()) |
        set(Bodega.query.filter_by(responsable_id=current_user.id).all())
    )
    return render_template("tecnico/mis_bodegas.html", bodegas=bodegas)

# === Ver químicos en una bodega ===
@tecnico_bp.route('/bodega/<int:bodega_id>/quimicos')
@login_required
@tecnico_required
def ver_quimicos(bodega_id):
    bodega = Bodega.query.get_or_404(bodega_id)
    if not tecnico_puede_acceder_a_bodega(bodega):
        flash("No tienes permiso para acceder a esta bodega.", "danger")
        return redirect(url_for('tecnico.mis_bodegas'))
    quimicos = bodega.quimicos
    return render_template('tecnico/quimicos.html', bodega=bodega, quimicos=quimicos)

# === Agregar nuevo químico ===
@tecnico_bp.route('/bodega/<int:bodega_id>/quimicos/nuevo', methods=['GET', 'POST'])
@login_required
@tecnico_required
def agregar_quimico(bodega_id):
    bodega = Bodega.query.get_or_404(bodega_id)
    if not tecnico_puede_acceder_a_bodega(bodega):
        flash("No tienes permiso para agregar químicos en esta bodega.", "danger")
        return redirect(url_for('tecnico.mis_bodegas'))
    form = QuimicoForm()
    if form.validate_on_submit():
        try:
            nuevo_quimico = Quimico(
                nombre=form.nombre.data,
                tipo=form.tipo.data,
                descripcion=form.descripcion.data,
                cantidad_litros=form.cantidad_litros.data,
                fecha_ingreso=form.fecha_ingreso.data,
                bodega_id=bodega.id
            )
            db.session.add(nuevo_quimico)
            db.session.commit()
            flash("✅ Químico agregado correctamente.", "success")
            return redirect(url_for('tecnico.ver_quimicos', bodega_id=bodega.id))
        except Exception as e:
            db.session.rollback()
            flash("Error al agregar químico: " + str(e), "danger")
    return render_template('tecnico/agregar_quimico.html', form=form, bodega=bodega)

# === Editar químico existente ===
@tecnico_bp.route('/quimicos/<int:quimico_id>/editar', methods=['GET', 'POST'])
@login_required
@tecnico_required
def editar_quimico(quimico_id):
    quimico = Quimico.query.get_or_404(quimico_id)
    bodega = quimico.bodega
    if not tecnico_puede_acceder_a_bodega(bodega):
        flash("No tienes permiso para editar químicos en esta bodega.", "danger")
        return redirect(url_for('tecnico.mis_bodegas'))
    form = QuimicoForm(obj=quimico)
    if form.validate_on_submit():
        try:
            quimico.nombre = form.nombre.data
            quimico.tipo = form.tipo.data
            quimico.descripcion = form.descripcion.data
            quimico.cantidad_litros = form.cantidad_litros.data
            quimico.fecha_ingreso = form.fecha_ingreso.data
            db.session.commit()
            flash("Químico actualizado exitosamente.", "success")
            return redirect(url_for('tecnico.ver_quimicos', bodega_id=bodega.id))
        except Exception as e:
            db.session.rollback()
            flash("Error al actualizar químico: " + str(e), "danger")
    return render_template('tecnico/editar_quimico.html', form=form, quimico=quimico)

# === Responder formulario técnico (checklist) ===
@tecnico_bp.route('/formulario/<int:formulario_id>', methods=['GET', 'POST'])
@login_required
@tecnico_required
def responder_formulario(formulario_id):
    formulario = FormularioTarea.query.get_or_404(formulario_id)
    if formulario.tecnico_id != current_user.id:
        flash("No tienes acceso a este formulario.", "danger")
        return redirect(url_for('tecnico.tecnico_dashboard'))
    form = ResponderFormularioForm()
    items = formulario.checklist_items
    if not form.is_submitted():
        form.items.entries.clear()
        for item in items:
            form_item = ChecklistItemForm()
            form_item.descripcion.data = item.descripcion
            form_item.realizado.data = item.realizado
            form_item.comentario.data = item.comentario
            form.items.append_entry(form_item)
    if form.validate_on_submit():
        try:
            for i, item_form in enumerate(form.items):
                items[i].realizado = item_form.realizado.data
                items[i].comentario = item_form.comentario.data
            formulario.estado = "completado"
            db.session.commit()
            flash("Formulario respondido correctamente.", "success")
            return redirect(url_for('tecnico.tecnico_dashboard'))
        except Exception as e:
            db.session.rollback()
            flash("Error al responder formulario: " + str(e), "danger")
    return render_template("tecnico/formulario_responder.html", form=form, formulario_tarea=formulario)
