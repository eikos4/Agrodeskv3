from datetime import datetime
from flask import Blueprint, flash, render_template, redirect, request, url_for
from flask_login import login_required, current_user
from app.models import Bodega, Huerto, Recomendacion, Quimico, FormularioTarea, ChecklistItem, db
from app.forms import QuimicoForm, ResponderFormularioForm, ChecklistItemForm

tecnico_bp = Blueprint('tecnico', __name__)

# ---------------------------------
# Función reutilizable de permisos
# ---------------------------------
def tecnico_puede_acceder_a_bodega(bodega):
    return bodega in current_user.bodegas_asignadas.all()


# -------------------------------
# Ver recomendaciones técnicas
# -------------------------------
@tecnico_bp.route('/recomendaciones')
@login_required
def ver_recomendaciones():
    if current_user.role != "tecnico":
        return "No autorizado", 403

    recomendaciones = Recomendacion.query.filter_by(tecnico_id=current_user.id).all()
    huertos = current_user.huertos_asignados
    bodegas = current_user.bodegas

    return render_template(
        "recomendaciones.html", 
        recomendaciones=recomendaciones,
        huertos=huertos,
        bodegas=bodegas
    )

# -------------------------------
# Ver químicos en una bodega
# -------------------------------
@tecnico_bp.route('/bodega/<int:bodega_id>/quimicos')
@login_required
def ver_quimicos(bodega_id):
    bodega = Bodega.query.get_or_404(bodega_id)

    if not tecnico_puede_acceder_a_bodega(bodega):
        flash("No tienes permiso para acceder a esta bodega.", "danger")
        return redirect(url_for('tecnico.ver_recomendaciones'))

    quimicos = Quimico.query.filter_by(bodega_id=bodega.id).all()
    return render_template('tecnico/quimicos.html', bodega=bodega, quimicos=quimicos)


# -------------------------------
# Agregar nuevo químico
# -------------------------------
@tecnico_bp.route('/bodega/<int:bodega_id>/quimicos/nuevo', methods=['GET', 'POST'])
@login_required
def agregar_quimico(bodega_id):
    bodega = Bodega.query.get_or_404(bodega_id)

    if not tecnico_puede_acceder_a_bodega(bodega):
        flash("No tienes permiso para agregar químicos en esta bodega.", "danger")
        return redirect(url_for('tecnico.ver_recomendaciones'))

    if request.method == 'POST':
        nombre = request.form.get('nombre')
        tipo = request.form.get('tipo')
        descripcion = request.form.get('descripcion')
        cantidad_litros = request.form.get('cantidad_litros')
        fecha_ingreso_str = request.form.get('fecha_ingreso')

        try:
            fecha_ingreso = datetime.strptime(fecha_ingreso_str, '%Y-%m-%d')
        except ValueError:
            flash("Formato de fecha incorrecto.", "danger")
            return redirect(url_for('tecnico.agregar_quimico', bodega_id=bodega_id))

        nuevo_quimico = Quimico(
            nombre=nombre,
            tipo=tipo,
            descripcion=descripcion,
            cantidad_litros=cantidad_litros,
            fecha_ingreso=fecha_ingreso,
            bodega_id=bodega_id
        )
        db.session.add(nuevo_quimico)
        db.session.commit()
        flash("✅ Químico agregado correctamente.", "success")
        return redirect(url_for('tecnico.ver_recomendaciones'))

    return render_template('agregar_quimico.html', bodega=bodega)


# -------------------------------
# Editar químico existente
# -------------------------------
@tecnico_bp.route('/quimicos/<int:quimico_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_quimico(quimico_id):
    quimico = Quimico.query.get_or_404(quimico_id)
    bodega = quimico.bodega
    if not tecnico_puede_acceder_a_bodega(bodega):
        flash("No tienes permiso para editar químicos en esta bodega.", "danger")
        return redirect(url_for('tecnico.ver_recomendaciones'))

    if request.method == 'POST':
        quimico.nombre = request.form.get('nombre')
        quimico.tipo = request.form.get('tipo')
        quimico.descripcion = request.form.get('descripcion')
        quimico.cantidad_litros = request.form.get('cantidad_litros')
        fecha_ingreso_str = request.form.get('fecha_ingreso')
        try:
            quimico.fecha_ingreso = datetime.strptime(fecha_ingreso_str, '%Y-%m-%d')
        except ValueError:
            flash("Formato de fecha incorrecto.", "danger")
            return redirect(url_for('tecnico.editar_quimico', quimico_id=quimico_id))
        db.session.commit()
        flash("Químico actualizado exitosamente.", "success")
        return redirect(url_for('tecnico.ver_recomendaciones'))

    return render_template('editar_quimico.html', quimico=quimico)

# -------------------------------
# Responder formulario técnico
# -------------------------------
@tecnico_bp.route('/formulario/<int:formulario_id>', methods=['GET', 'POST'])
@login_required
def responder_formulario(formulario_id):
    formulario = FormularioTarea.query.get_or_404(formulario_id)
    if formulario.tecnico_id != current_user.id:
        flash("No tienes acceso a este formulario.", "danger")
        return redirect(url_for('tecnico.ver_recomendaciones'))

    items = formulario.checklist_items
    form = ResponderFormularioForm()

    if not form.is_submitted():
        form.items.entries.clear()
        for item in items:
            form_item = ChecklistItemForm()
            form_item.descripcion.data = item.descripcion
            form_item.realizado.data = item.realizado
            form_item.comentario.data = item.comentario
            form.items.append_entry(form_item)

    if form.validate_on_submit():
        for i, item_form in enumerate(form.items):
            items[i].realizado = item_form.realizado.data
            items[i].comentario = item_form.comentario.data

        formulario.estado = "completado"
        db.session.commit()
        flash("Formulario respondido correctamente.", "success")
        return redirect(url_for('tecnico.ver_recomendaciones'))

    return render_template("formulario_responder.html", form=form, formulario_tarea=formulario)

# -------------------------------
# Dashboard técnico
# -------------------------------
@tecnico_bp.route('/tecnico/dashboard')
@login_required
def tecnico_dashboard():
    if current_user.role != 'tecnico':
        flash("Acceso no autorizado", "danger")
        return redirect(url_for('tecnico.ver_recomendaciones'))

    bodegas = current_user.bodegas
    huertos = Huerto.query.filter_by(responsable_id=current_user.id).all()
    recomendaciones = Recomendacion.query.filter_by(tecnico_id=current_user.id).all()

    return render_template('tecnico_dashboard.html', bodegas=bodegas, huertos=huertos, recomendaciones=recomendaciones)