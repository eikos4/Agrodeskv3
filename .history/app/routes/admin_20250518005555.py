from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from functools import wraps
from app.forms import CreateTechnicianForm, RecommendationForm, CrearHuertoForm, BodegaForm
from app.models import User, Recomendacion, Huerto, Bodega, Quimico
from app import db
from app.forms import RegistrarActividadForm

admin_bp = Blueprint('admin', __name__)

# --- Decorador de permiso admin robusto ---
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash("Acceso solo permitido a administradores.", "danger")
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

# --- Helpers para cargar choices ---
def cargar_tecnicos_choices():
    return [(u.id, u.name) for u in User.query.filter_by(role='tecnico').all()]

def cargar_huertos_choices():
    return [(h.id, h.nombre) for h in Huerto.query.all()]

# ---------- RUTAS ADMIN ----------

@admin_bp.route('/crear_tecnico', methods=['GET', 'POST'])
@login_required
@admin_required
def crear_tecnico():
    form = CreateTechnicianForm()
    if form.validate_on_submit():
        try:
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
            flash("✅ Técnico creado exitosamente", "success")
            return redirect(url_for('admin.admin_dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error creando técnico: {e}", "danger")
    return render_template("admin/crear_tecnico.html", form=form)

@admin_bp.route('/recomendar', methods=['GET', 'POST'])
@login_required
@admin_required
def recomendar():
    form = RecommendationForm()
    form.tecnico_id.choices = cargar_tecnicos_choices()
    if form.validate_on_submit():
        try:
            recomendacion = Recomendacion(
                contenido=form.contenido.data,
                tecnico_id=form.tecnico_id.data
            )
            db.session.add(recomendacion)
            db.session.commit()
            flash("Recomendación asignada", "success")
            return redirect(url_for('admin.admin_dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error asignando recomendación: {e}", "danger")
    return render_template("admin/recomendar.html", form=form)

@admin_bp.route('/crear_huerto', methods=['GET', 'POST'])
@login_required
@admin_required
def crear_huerto():
    form = CrearHuertoForm()
    form.responsable_id.choices = cargar_tecnicos_choices()
    if form.validate_on_submit():
        try:
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
            flash("✅ Huerto creado exitosamente", "success")
            return redirect(url_for('admin.admin_dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error creando huerto: {e}", "danger")
    elif request.method == 'POST':
        flash("❌ Formulario inválido", "danger")
    return render_template('admin/crear_huerto.html', form=form)

@admin_bp.route('/bodegas')
@login_required
@admin_required
def listar_bodegas():
    bodegas = Bodega.query.order_by(Bodega.nombre.asc()).all()
    return render_template("admin/bodegas.html", bodegas=bodegas)



@admin_bp.route('/bodega/<int:bodega_id>/quimicos')
@login_required
@admin_required
def ver_quimicos(bodega_id):
    bodega = Bodega.query.get_or_404(bodega_id)
    quimicos = bodega.quimicos
    return render_template('quimicos/ver_quimicos.html', bodega=bodega, quimicos=quimicos, es_admin=True)


@admin_bp.route('/crear_bodega', methods=['GET', 'POST'])
@login_required
@admin_required
def crear_bodega():
    form = BodegaForm()
    form.huerto_id.choices = cargar_huertos_choices()
    form.responsable_id.choices = [(0, "--- Sin asignar ---")] + cargar_tecnicos_choices()
    if form.validate_on_submit():
        try:
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
        except Exception as e:
            db.session.rollback()
            flash(f"Error creando bodega: {e}", "danger")
    return render_template("admin/bodega_form.html", form=form)

@admin_bp.route('/bodega/<int:bodega_id>/quimicos')
@login_required
@admin_required
def ver_quimicos(bodega_id):
    bodega = Bodega.query.get_or_404(bodega_id)
    quimicos = bodega.quimicos
    return render_template('admin/quimicos_bodega.html', bodega=bodega, quimicos=quimicos)

@admin_bp.route('/quimico/<int:quimico_id>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_quimico(quimico_id):
    quimico = Quimico.query.get_or_404(quimico_id)
    if request.method == 'POST':
        try:
            quimico.nombre = request.form['nombre']
            quimico.tipo = request.form['tipo']
            quimico.descripcion = request.form['descripcion']
            quimico.cantidad_litros = float(request.form['cantidad_litros'])
            db.session.commit()
            flash("Químico actualizado correctamente", "success")
            return redirect(url_for('admin.ver_quimicos', bodega_id=quimico.bodega_id))
        except Exception as e:
            db.session.rollback()
            flash(f"Error actualizando químico: {e}", "danger")
    return render_template('admin/editar_quimico.html', quimico=quimico)

@admin_bp.route('/huerto/<int:huerto_id>/bitacora')
@login_required
@admin_required
def bitacora_huerto(huerto_id):
    huerto = Huerto.query.get_or_404(huerto_id)
    actividades = huerto.actividades  # O aplica filtros aquí si deseas
    return render_template('admin/bitacora_huerto.html', huerto=huerto, actividades=actividades)

@admin_bp.route('/huerto/<int:huerto_id>/registrar_actividad', methods=['GET', 'POST'])
@login_required
@admin_required
def registrar_actividad_huerto(huerto_id):
    huerto = Huerto.query.get_or_404(huerto_id)
    form = RegistrarActividadForm()
    if form.validate_on_submit():
        try:
            # Aquí va la lógica para registrar la actividad
            # actividad = ActividadHuerto(...)
            # db.session.add(actividad)
            db.session.commit()
            flash("✅ Actividad registrada exitosamente", "success")
            return redirect(url_for('admin.bitacora_huerto', huerto_id=huerto.id))
        except Exception as e:
            db.session.rollback()
            flash(f"Error registrando actividad: {e}", "danger")
    return render_template('admin/registrar_actividad.html', form=form, huerto=huerto)

@admin_bp.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    bodegas = Bodega.query.order_by(Bodega.nombre.asc()).all()
    tecnicos = User.query.filter_by(role='tecnico').all()
    huertos = Huerto.query.order_by(Huerto.nombre.asc()).all()
    ultimas_recomendaciones = (
        Recomendacion.query
        .order_by(Recomendacion.fecha.desc())
        .limit(5)
        .all()
    )
    return render_template(
        'admin/admin_dashboard.html',
        bodegas=bodegas,
        tecnicos=tecnicos,
        huertos=huertos,
        ultimas_recomendaciones=ultimas_recomendaciones
    )

@admin_bp.route('/admin/actualizar_recomendacion/<int:recomendacion_id>', methods=['POST'])
@login_required
@admin_required
def actualizar_recomendacion(recomendacion_id):
    recomendacion = Recomendacion.query.get_or_404(recomendacion_id)
    recomendacion.estado = request.form['estado']
    db.session.commit()
    flash("Estado de la recomendación actualizado exitosamente", "success")
    return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/admin/tecnico/<int:tecnico_id>/reset_password', methods=['GET', 'POST'])
@login_required
@admin_required
def reset_password(tecnico_id):
    tecnico = User.query.get_or_404(tecnico_id)
    if request.method == 'POST':
        nueva = request.form['password']
        tecnico.password = generate_password_hash(nueva)
        db.session.commit()
        flash(f"Contraseña de {tecnico.name} actualizada.", "success")
        return redirect(url_for('admin.admin_dashboard'))
    return render_template('admin/reset_password.html', tecnico=tecnico)
