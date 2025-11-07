# app/routes/admin.py
from datetime import datetime
from functools import wraps

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from sqlalchemy.orm import selectinload
from sqlalchemy import extract

from app.extensions import db  # 👈 usar extensions
from app.models import User, Recomendacion, Huerto, Bodega, Quimico, ActividadHuerto

from app.forms import (
    CreateTechnicianForm,
    CrearHuertoForm,
    BodegaForm,
    RegistrarActividadForm,
    QuimicoForm,
    AsignarRecomendacionForm,
    ResetPasswordForm,
)

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

# ======================
# Decorador: solo admin
# ======================
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "admin":
            flash("Acceso solo permitido a administradores.", "danger")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated

# ======================
# Helpers (scoped por empresa)
# ======================
def cargar_tecnicos_choices():
    tecnicos = (
        User.query
        .filter_by(role="tecnico", empresa_id=current_user.empresa_id)
        .order_by(User.name.asc())
        .all()
    )
    # Fallback a email si no hay name
    return [(u.id, (u.name or u.email or f"Técnico {u.id}")) for u in tecnicos]

def cargar_huertos_choices():
    huertos = (
        Huerto.query
        .filter_by(empresa_id=current_user.empresa_id)
        .order_by(Huerto.nombre.asc())
        .all()
    )
    return [(h.id, h.nombre) for h in huertos]

# ======================






# Dashboard
# ======================
@admin_bp.route("/dashboard")
@login_required
@admin_required
def admin_dashboard():
    page = request.args.get("page", 1, type=int)
    per_page = 9

    # Huertos paginados (evitar N+1)
    huertos_paginados = (
        Huerto.query.filter_by(empresa_id=current_user.empresa_id)
        .options(
            selectinload(Huerto.bodegas),
            selectinload(Huerto.responsable),
        )
        .order_by(Huerto.nombre.asc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    # Bodegas + relaciones
    bodegas = (
        Bodega.query.filter_by(empresa_id=current_user.empresa_id)
        .options(
            selectinload(Bodega.huerto),
            selectinload(Bodega.responsable),
        )
        .order_by(Bodega.nombre.asc())
        .all()
    )

    tecnicos = (
        User.query
        .filter_by(role="tecnico", empresa_id=current_user.empresa_id)
        .order_by(User.name.asc())
        .all()
    )

    q_rec = (
        Recomendacion.query
        .options(
            selectinload(Recomendacion.tecnico),
            selectinload(Recomendacion.autor),
        )
        .order_by(Recomendacion.fecha.desc())
    )
    # Si Recomendacion tiene empresa_id, filtra:
    if hasattr(Recomendacion, "empresa_id"):
        q_rec = q_rec.filter(Recomendacion.empresa_id == current_user.empresa_id)

    ultimas_recomendaciones = q_rec.limit(5).all()

    return render_template(
        "admin/admin_dashboard.html",
        huertos_paginados=huertos_paginados,
        huertos=huertos_paginados.items,
        bodegas=bodegas,
        tecnicos=tecnicos,
        ultimas_recomendaciones=ultimas_recomendaciones,
    )

# ======================
# Técnicos
# ======================
@admin_bp.route("/crear_tecnico", methods=["GET", "POST"])
@login_required
@admin_required
def crear_tecnico():
    form = CreateTechnicianForm()
    if form.validate_on_submit():
        try:
            hashed_pw = generate_password_hash(form.password.data)
            new_user = User(
                name=form.name.data.strip(),
                email=form.email.data.strip().lower(),
                password=hashed_pw,
                role="tecnico",
                created_by=current_user.id,
                empresa_id=current_user.empresa_id,  # 👈 clave
            )
            db.session.add(new_user)
            db.session.commit()
            flash("✅ Técnico creado exitosamente", "success")
            return redirect(url_for("admin.admin_dashboard"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error creando técnico: {e}", "danger")
    return render_template("admin/crear_tecnico.html", form=form)

@admin_bp.route('/tecnico/<int:tecnico_id>/reset_password', methods=['GET', 'POST'], endpoint='reset_password')
@login_required
@admin_required
def reset_password(tecnico_id):
    tecnico = (
        User.query
        .filter_by(id=tecnico_id, role='tecnico', empresa_id=current_user.empresa_id)
        .first_or_404()
    )
    form = ResetPasswordForm()

    if form.validate_on_submit():
        tecnico.password = generate_password_hash(form.password.data)
        db.session.commit()
        flash(f"Contraseña de {tecnico.name or tecnico.email} actualizada correctamente ✅", "success")
        next_url = request.args.get("next")
        return redirect(next_url or url_for("admin.admin_dashboard"))

    return render_template("admin/reset_password.html", form=form, tecnico=tecnico)

# ======================
# Recomendaciones
# ======================
@admin_bp.route("/recomendar", methods=["GET", "POST"])
@login_required
@admin_required
def recomendar():
    form = AsignarRecomendacionForm()
    # Cargar opciones del select de técnicos (scoped)
    form.tecnico_id.choices = cargar_tecnicos_choices()

    if form.validate_on_submit():
        # Construcción segura por si el modelo no tiene empresa_id
        rec_kwargs = dict(
            contenido=form.contenido.data,
            tecnico_id=form.tecnico_id.data,
            autor_id=current_user.id,
            fecha=datetime.utcnow(),
        )
        if hasattr(Recomendacion, "empresa_id"):
            rec_kwargs["empresa_id"] = current_user.empresa_id

        rec = Recomendacion(**rec_kwargs)
        db.session.add(rec)
        db.session.commit()
        flash("Recomendación enviada con éxito.", "success")
        return redirect(url_for("admin.recomendar"))

    # Listado (scoped)
    q = (
        Recomendacion.query
        .options(
            selectinload(Recomendacion.tecnico),
            selectinload(Recomendacion.huerto),
            selectinload(Recomendacion.autor),
        )
        .order_by(Recomendacion.fecha.desc())
    )
    if hasattr(Recomendacion, "empresa_id"):
        q = q.filter(Recomendacion.empresa_id == current_user.empresa_id)

    recomendaciones = q.limit(200).all()

    return render_template("admin/recomendar.html", form=form, recomendaciones=recomendaciones)

@admin_bp.route("/actualizar_recomendacion/<int:recomendacion_id>", methods=["POST"])
@login_required
@admin_required
def actualizar_recomendacion(recomendacion_id):
    q = Recomendacion.query
    if hasattr(Recomendacion, "empresa_id"):
        q = q.filter(Recomendacion.empresa_id == current_user.empresa_id)
    rec = q.filter(Recomendacion.id == recomendacion_id).first_or_404()

    rec.estado = request.form.get("estado", rec.estado)
    db.session.commit()
    flash("Estado de la recomendación actualizado", "success")
    return redirect(url_for("admin.admin_dashboard"))

# ======================
# Huertos
# ======================
@admin_bp.route("/crear_huerto", methods=["GET", "POST"])
@login_required
@admin_required
def crear_huerto():
    form = CrearHuertoForm()
    form.responsable_id.choices = [(0, "— Sin asignar —")] + cargar_tecnicos_choices()
    if form.validate_on_submit():
        try:
            responsable_id = form.responsable_id.data or None
            if responsable_id == 0:
                responsable_id = None
            h = Huerto(
                nombre=form.nombre.data,
                ubicacion=form.ubicacion.data,
                superficie_ha=form.superficie_ha.data,
                tipo_cultivo=form.tipo_cultivo.data,
                fecha_siembra=form.fecha_siembra.data,
                responsable_id=responsable_id,
                empresa_id=current_user.empresa_id,  # 👈
            )
            db.session.add(h)
            db.session.commit()
            flash("✅ Huerto creado exitosamente", "success")
            return redirect(url_for("admin.admin_dashboard"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error creando huerto: {e}", "danger")
    elif request.method == "POST":
        flash("❌ Formulario inválido", "danger")
    return render_template("admin/crear_huerto.html", form=form)

@admin_bp.route("/huerto/<int:huerto_id>/bitacora")
@login_required
@admin_required
def bitacora_huerto(huerto_id):
    huerto = Huerto.query.filter_by(id=huerto_id, empresa_id=current_user.empresa_id).first_or_404()

    anio_seleccionado = request.args.get("anio", type=int)
    tipo_seleccionado = request.args.get("tipo", default=None, type=str)

    q = ActividadHuerto.query.filter_by(huerto_id=huerto.id)
    if anio_seleccionado:
        q = q.filter(extract("year", ActividadHuerto.fecha) == anio_seleccionado)
    if tipo_seleccionado:
        q = q.filter(ActividadHuerto.tipo == tipo_seleccionado)

    actividades = q.order_by(ActividadHuerto.fecha.desc()).all()

    # años disponibles
    anios = (
        db.session.query(extract("year", ActividadHuerto.fecha))
        .filter(ActividadHuerto.huerto_id == huerto.id)
        .distinct()
        .all()
    )
    lista_anios = sorted({int(a[0]) for a in anios}, reverse=True)

    return render_template(
        "admin/bitacora_huerto.html",
        huerto=huerto,
        actividades=actividades,
        lista_anios=lista_anios,
        anio_seleccionado=anio_seleccionado,
        tipo_seleccionado=tipo_seleccionado,
    )

@admin_bp.route("/huerto/<int:huerto_id>/registrar_actividad", methods=["GET", "POST"])
@login_required
@admin_required
def registrar_actividad_huerto(huerto_id):
    huerto = Huerto.query.filter_by(id=huerto_id, empresa_id=current_user.empresa_id).first_or_404()
    form = RegistrarActividadForm()
    if form.validate_on_submit():
        try:
            actividad = ActividadHuerto(
                empresa_id=huerto.empresa_id or current_user.empresa_id,  # 👈 clave
                huerto_id=huerto.id,
                fecha=form.fecha.data,
                tipo=form.tipo.data,
                descripcion=form.descripcion.data or "",
                responsable=(form.responsable.data.strip() if form.responsable.data else (current_user.name or current_user.email)),
                producto=form.producto.data or "",
                dosis=form.dosis.data or "",
                plaga=form.plaga.data or "",
                nivel_infestacion=form.nivel_infestacion.data or "",
                resultado=form.resultado.data or "",
                fotos="",  # TODO: gestionar uploads si corresponde
                observaciones=form.observaciones.data or "",
            )
            db.session.add(actividad)
            db.session.commit()
            flash("✅ Actividad registrada exitosamente", "success")
            return redirect(url_for("admin.bitacora_huerto", huerto_id=huerto.id))
        except Exception as e:
            db.session.rollback()
            flash(f"Error registrando actividad: {e}", "danger")
    return render_template("admin/registrar_actividad.html", form=form, huerto=huerto)


# ======================
# Bodegas
# ======================
@admin_bp.route("/bodegas")
@login_required
@admin_required
def listar_bodegas():
    bodegas = (
        Bodega.query.filter_by(empresa_id=current_user.empresa_id)
        .options(
            selectinload(Bodega.huerto),
            selectinload(Bodega.responsable),
        )
        .order_by(Bodega.nombre.asc())
        .all()
    )
    return render_template("admin/bodegas.html", bodegas=bodegas)

@admin_bp.route("/crear_bodega", methods=["GET", "POST"])
@login_required
@admin_required
def crear_bodega():
    form = BodegaForm()
    form.huerto_id.choices = cargar_huertos_choices()
    form.responsable_id.choices = [(0, "— Sin asignar —")] + cargar_tecnicos_choices()

    if form.validate_on_submit():
        try:
            responsable_id = form.responsable_id.data if form.responsable_id.data != 0 else None
            b = Bodega(
                nombre=form.nombre.data,
                ubicacion=form.ubicacion.data,
                huerto_id=form.huerto_id.data,
                responsable_id=responsable_id,
                empresa_id=current_user.empresa_id,  # 👈
            )
            db.session.add(b)
            db.session.commit()
            flash("Bodega registrada correctamente ✅", "success")
            return redirect(url_for("admin.listar_bodegas"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error creando bodega: {e}", "danger")
    return render_template("admin/bodega_form.html", form=form)

@admin_bp.route("/editar_bodega/<int:bodega_id>", methods=["GET", "POST"])
@login_required
@admin_required
def editar_bodega(bodega_id):
    bodega = Bodega.query.filter_by(id=bodega_id, empresa_id=current_user.empresa_id).first_or_404()
    form = BodegaForm(obj=bodega)
    form.huerto_id.choices = cargar_huertos_choices()
    form.responsable_id.choices = [(0, "— Sin asignar —")] + cargar_tecnicos_choices()
    if bodega.responsable_id is None:
        form.responsable_id.data = 0

    if form.validate_on_submit():
        try:
            bodega.nombre = form.nombre.data
            bodega.ubicacion = form.ubicacion.data
            bodega.huerto_id = form.huerto_id.data
            bodega.responsable_id = form.responsable_id.data if form.responsable_id.data != 0 else None
            db.session.commit()
            flash("Bodega actualizada correctamente ✅", "success")
            return redirect(url_for("admin.listar_bodegas"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error al actualizar la bodega: {e}", "danger")
    return render_template("admin/editar_bodega.html", form=form, bodega=bodega)

@admin_bp.route("/eliminar_bodega/<int:bodega_id>", methods=["POST"])
@login_required
@admin_required
def eliminar_bodega(bodega_id):
    bodega = Bodega.query.filter_by(id=bodega_id, empresa_id=current_user.empresa_id).first_or_404()
    try:
        db.session.delete(bodega)
        db.session.commit()
        flash("Bodega eliminada correctamente ✅", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error al eliminar la bodega: {e}", "danger")
    return redirect(url_for("admin.listar_bodegas"))

# ======================
# Químicos
# ======================
@admin_bp.route("/bodega/<int:bodega_id>/quimicos")
@login_required
@admin_required
def ver_quimicos(bodega_id):
    bodega = (
        Bodega.query
        .filter_by(id=bodega_id, empresa_id=current_user.empresa_id)
        .options(selectinload(Bodega.quimicos), selectinload(Bodega.huerto))
        .first_or_404()
    )
    return render_template("admin/quimicos_bodega.html", bodega=bodega, quimicos=bodega.quimicos)

@admin_bp.route("/quimico/<int:quimico_id>/editar", methods=["GET", "POST"])
@login_required
@admin_required
def editar_quimico(quimico_id):
    quimico = (
        Quimico.query
        .join(Bodega, Quimico.bodega_id == Bodega.id)
        .filter(Quimico.id == quimico_id, Bodega.empresa_id == current_user.empresa_id)
        .first_or_404()
    )
    form = QuimicoForm(obj=quimico)
    if form.validate_on_submit():
        quimico.nombre = form.nombre.data
        quimico.tipo = form.tipo.data
        quimico.descripcion = form.descripcion.data
        quimico.cantidad_litros = form.cantidad_litros.data
        quimico.fecha_ingreso = form.fecha_ingreso.data
        db.session.commit()
        flash("Químico actualizado correctamente", "success")
        return redirect(url_for("admin.ver_quimicos", bodega_id=quimico.bodega_id))
    return render_template("admin/editar_quimico.html", form=form, quimico=quimico)

@admin_bp.route("/quimico/<int:quimico_id>/eliminar", methods=["POST"])
@login_required
@admin_required
def eliminar_quimico(quimico_id):
    quimico = (
        Quimico.query
        .join(Bodega, Quimico.bodega_id == Bodega.id)
        .filter(Quimico.id == quimico_id, Bodega.empresa_id == current_user.empresa_id)
        .first_or_404()
    )
    try:
        db.session.delete(quimico)
        db.session.commit()
        flash("Químico eliminado correctamente ✅", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error al eliminar el químico: {e}", "danger")
    return redirect(url_for("admin.ver_quimicos", bodega_id=quimico.bodega_id))

# ======================
# Utilidades para timeline (Jinja)
# ======================
@admin_bp.app_context_processor
def inject_timeline_utils():
    def tipo_color(tipo):
        return {
            "fertilizacion": "bg-fertilizacion",
            "riego": "bg-riego",
            "poda": "bg-poda",
            "cosecha": "bg-cosecha",
            "control_plagas": "bg-control_plagas",
            "otra": "bg-otra",
        }.get(tipo, "bg-otra")

    def tipo_icono(tipo):
        return {
            "fertilizacion": "bi-droplet-half",
            "riego": "bi-water",
            "poda": "bi-scissors",
            "cosecha": "bi-basket",
            "control_plagas": "bi-bug",
            "otra": "bi-gear",
        }.get(tipo, "bi-gear")

    return dict(tipo_color=tipo_color, tipo_icono=tipo_icono)


@admin_bp.route("/huerto/<int:huerto_id>/asignar", methods=["GET", "POST"])
@login_required
@admin_required
def asignar_responsable_huerto(huerto_id):
    huerto = Huerto.query.filter_by(id=huerto_id, empresa_id=current_user.empresa_id).first_or_404()
    form = CrearHuertoForm(obj=huerto)
    # solo usamos el campo responsable_id acá
    form.responsable_id.choices = [(0, "— Sin asignar —")] + cargar_tecnicos_choices()

    if request.method == "GET":
        form.responsable_id.data = huerto.responsable_id or 0

    if form.validate_on_submit():
        rid = form.responsable_id.data or None
        if rid == 0:
            rid = None
        huerto.responsable_id = rid
        db.session.commit()
        flash("Responsable actualizado correctamente ✅", "success")
        return redirect(url_for("admin.admin_dashboard"))

    return render_template("admin/asignar_responsable_huerto.html", form=form, huerto=huerto)
