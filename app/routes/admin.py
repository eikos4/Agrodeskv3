# app/routes/admin.py
from datetime import datetime
from functools import wraps

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from sqlalchemy.orm import selectinload
from sqlalchemy import extract

from app.extensions import db  # 👈 usar extensions
from app.models import User, Recomendacion, Huerto, Bodega, Quimico, ActividadHuerto, Parcela, ActividadCampo, Documento

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
    # Solo técnicos asignados a este administrador
    tecnicos = (
        User.query
        .filter_by(role="tecnico", empresa_id=current_user.empresa_id, created_by=current_user.id)
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
    page_huertos = request.args.get("page_huertos", 1, type=int)
    page_tecnicos = request.args.get("page_tecnicos", 1, type=int)
    per_page_huertos = 9
    per_page_tecnicos = 8

    # Huertos paginados (evitar N+1)
    huertos_paginados = (
        Huerto.query.filter_by(empresa_id=current_user.empresa_id)
        .options(
            selectinload(Huerto.bodegas),
            selectinload(Huerto.responsable),
        )
        .order_by(Huerto.nombre.asc())
        .paginate(page=page_huertos, per_page=per_page_huertos, error_out=False)
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

    # Solo técnicos asignados a este administrador (paginados)
    tecnicos_paginados = (
        User.query
        .filter_by(role="tecnico", empresa_id=current_user.empresa_id, created_by=current_user.id)
        .order_by(User.name.asc())
        .paginate(page=page_tecnicos, per_page=per_page_tecnicos, error_out=False)
    )

    # Estadísticas de huertos
    total_huertos = Huerto.query.filter_by(empresa_id=current_user.empresa_id).count()
    huertos_con_responsable = Huerto.query.filter_by(empresa_id=current_user.empresa_id).filter(Huerto.responsable_id.isnot(None)).count()
    huertos_sin_responsable = total_huertos - huertos_con_responsable
    
    # Estadísticas de superficie por cultivo
    superficie_por_cultivo = db.session.query(
        Huerto.tipo_cultivo,
        db.func.sum(Huerto.superficie_ha).label('total_superficie'),
        db.func.count(Huerto.id).label('cantidad')
    ).filter_by(empresa_id=current_user.empresa_id).group_by(Huerto.tipo_cultivo).all()
    
    # Calcular superficie total
    total_superficie = sum(s.total_superficie or 0 for s in superficie_por_cultivo)
    
    # Estadísticas de técnicos
    tecnicos_con_telefono = User.query.filter_by(
        role="tecnico", 
        empresa_id=current_user.empresa_id, 
        created_by=current_user.id
    ).filter(User.telefono.isnot(None)).count()
    
    # Actividades recientes (si existe el modelo)
    actividades_recientes = []
    try:
        from app.models import ActividadHuerto
        actividades_recientes = (
            ActividadHuerto.query
            .join(Huerto, ActividadHuerto.huerto_id == Huerto.id)
            .filter(Huerto.empresa_id == current_user.empresa_id)
            .order_by(ActividadHuerto.fecha.desc())
            .limit(5)
            .all()
        )
    except ImportError:
        pass

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
        tecnicos_paginados=tecnicos_paginados,
        tecnicos=tecnicos_paginados.items,
        ultimas_recomendaciones=ultimas_recomendaciones,
        total_superficie=total_superficie,
        superficie_por_cultivo=superficie_por_cultivo,
        total_huertos=total_huertos,
        huertos_con_responsable=huertos_con_responsable,
        huertos_sin_responsable=huertos_sin_responsable,
        tecnicos_con_telefono=tecnicos_con_telefono,
        actividades_recientes=actividades_recientes,
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
                telefono=form.telefono.data.strip() if form.telefono.data else None,
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


@admin_bp.route("/editar_tecnico/<int:tecnico_id>", methods=["GET", "POST"])
@login_required
@admin_required
def editar_tecnico(tecnico_id):
    # Solo puede editar técnicos que él creó
    tecnico = User.query.filter_by(id=tecnico_id, role="tecnico", empresa_id=current_user.empresa_id, created_by=current_user.id).first_or_404()
    form = CreateTechnicianForm(obj=tecnico)  # Reutiliza el mismo formulario

    if form.validate_on_submit():
        try:
            tecnico.name = form.name.data.strip()
            tecnico.email = form.email.data.strip().lower()
            # Solo actualiza contraseña si se ingresó una nueva
            if form.password.data:
                tecnico.password = generate_password_hash(form.password.data)
                flash("🔐 Se cambió la contraseña. Recuerda informar al técnico en terreno.", "warning")

            db.session.commit()
            flash("✅ Técnico actualizado correctamente", "success")
            return redirect(url_for("admin.admin_dashboard"))
        except Exception as e:
            db.session.rollback()
            flash(f"❌ Error actualizando técnico: {e}", "danger")

    return render_template("admin/editar_tecnico.html", form=form, tecnico=tecnico)



@admin_bp.route('/tecnico/<int:tecnico_id>/reset_password', methods=['GET', 'POST'], endpoint='reset_password')
@login_required
@admin_required
def reset_password(tecnico_id):
    # Solo puede resetear contraseñas de técnicos que él creó
    tecnico = (
        User.query
        .filter_by(id=tecnico_id, role='tecnico', empresa_id=current_user.empresa_id, created_by=current_user.id)
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
    
    # Cargar huertos para el selector de actividades fitosanitarias
    huertos = Huerto.query.filter_by(empresa_id=current_user.empresa_id).all()

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

    # Listado (solo recomendaciones a técnicos del admin actual)
    q = (
        Recomendacion.query
        .join(User, Recomendacion.tecnico_id == User.id)
        .filter(User.created_by == current_user.id)
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

    return render_template("admin/recomendar.html", form=form, recomendaciones=recomendaciones, huertos=huertos)

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
                # IDENTIFICACION GENERAL DEL PREDIO
                propietario=form.propietario.data,
                rut=form.rut.data,
                codigo_productor=form.codigo_productor.data,
                localidad=form.localidad.data,
                comuna=form.comuna.data,
                provincia=form.provincia.data,
                region=form.region.data,
                distrito_agroclimatico=form.distrito_agroclimatico.data,
                telefono=form.telefono.data,
                administrador=form.administrador.data,
                encargado_huerto=form.encargado_huerto.data,
                direccion=form.direccion.data,
                empresas=form.empresas.data,
                exportadoras=form.exportadoras.data,
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

@admin_bp.route("/huerto/<int:huerto_id>/editar", methods=["GET", "POST"])
@login_required
@admin_required
def editar_huerto(huerto_id):
    huerto = Huerto.query.get_or_404(huerto_id)
    
    # Verificar que el huerto pertenezca a la empresa del usuario actual
    if huerto.empresa_id != current_user.empresa_id:
        flash("No tienes permiso para editar este huerto", "danger")
        return redirect(url_for("admin.admin_dashboard"))
    
    form = CrearHuertoForm()
    form.responsable_id.choices = [(0, "— Sin asignar —")] + cargar_tecnicos_choices()
    
    if request.method == "GET":
        # Precargar el formulario con los datos actuales del huerto
        form.nombre.data = huerto.nombre
        form.ubicacion.data = huerto.ubicacion
        form.superficie_ha.data = huerto.superficie_ha
        form.tipo_cultivo.data = huerto.tipo_cultivo
        form.fecha_siembra.data = huerto.fecha_siembra
        form.responsable_id.data = huerto.responsable_id or 0
        
        # IDENTIFICACION GENERAL DEL PREDIO
        form.propietario.data = huerto.propietario
        form.rut.data = huerto.rut
        form.codigo_productor.data = huerto.codigo_productor
        form.localidad.data = huerto.localidad
        form.comuna.data = huerto.comuna
        form.provincia.data = huerto.provincia
        form.region.data = huerto.region
        form.distrito_agroclimatico.data = huerto.distrito_agroclimatico
        form.telefono.data = huerto.telefono
        form.administrador.data = huerto.administrador
        form.encargado_huerto.data = huerto.encargado_huerto
        form.direccion.data = huerto.direccion
        form.empresas.data = huerto.empresas
        form.exportadoras.data = huerto.exportadoras
    
    if form.validate_on_submit():
        try:
            responsable_id = form.responsable_id.data or None
            if responsable_id == 0:
                responsable_id = None
                
            # Actualizar datos del huerto
            huerto.nombre = form.nombre.data
            huerto.ubicacion = form.ubicacion.data
            huerto.superficie_ha = form.superficie_ha.data
            huerto.tipo_cultivo = form.tipo_cultivo.data
            huerto.fecha_siembra = form.fecha_siembra.data
            huerto.responsable_id = responsable_id
            
            # IDENTIFICACION GENERAL DEL PREDIO
            huerto.propietario = form.propietario.data
            huerto.rut = form.rut.data
            huerto.codigo_productor = form.codigo_productor.data
            huerto.localidad = form.localidad.data
            huerto.comuna = form.comuna.data
            huerto.provincia = form.provincia.data
            huerto.region = form.region.data
            huerto.distrito_agroclimatico = form.distrito_agroclimatico.data
            huerto.telefono = form.telefono.data
            huerto.administrador = form.administrador.data
            huerto.encargado_huerto = form.encargado_huerto.data
            huerto.direccion = form.direccion.data
            huerto.empresas = form.empresas.data
            huerto.exportadoras = form.exportadoras.data
            
            db.session.commit()
            flash("✅ Huerto actualizado exitosamente", "success")
            return redirect(url_for("admin.admin_dashboard"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error actualizando huerto: {e}", "danger")
    elif request.method == "POST":
        flash("❌ Formulario inválido", "danger")
    
    return render_template("admin/editar_huerto.html", form=form, huerto=huerto)

@admin_bp.route("/huerto/<int:huerto_id>/vista-global")
@login_required
@admin_required
def vista_global_huerto(huerto_id):
    huerto = Huerto.query.filter_by(id=huerto_id, empresa_id=current_user.empresa_id).first_or_404()
    
    # Obtener toda la información relacionada
    actividades = ActividadHuerto.query.filter_by(huerto_id=huerto.id).order_by(ActividadHuerto.fecha.desc()).limit(10).all()
    recomendaciones = Recomendacion.query.filter_by(huerto_id=huerto.id).order_by(Recomendacion.fecha.desc()).limit(10).all()
    bodegas = Bodega.query.filter_by(huerto_id=huerto.id).all()
    parcelas = Parcela.query.filter_by(huerto_id=huerto.id).all()
    actividades_geo = ActividadCampo.query.filter_by(huerto_id=huerto.id).order_by(ActividadCampo.fecha.desc()).limit(5).all()
    documentos = Documento.query.filter_by(huerto_id=huerto.id).order_by(Documento.created_at.desc()).limit(5).all()
    
    # Estadísticas
    total_actividades = ActividadHuerto.query.filter_by(huerto_id=huerto.id).count()
    total_recomendaciones = Recomendacion.query.filter_by(huerto_id=huerto.id).count()
    total_quimicos = 0
    for bodega in bodegas:
        total_quimicos += len(bodega.quimicos)
    
    return render_template("admin/vista_global_huerto.html", 
                         huerto=huerto,
                         actividades=actividades,
                         recomendaciones=recomendaciones,
                         bodegas=bodegas,
                         parcelas=parcelas,
                         actividades_geo=actividades_geo,
                         documentos=documentos,
                         total_actividades=total_actividades,
                         total_recomendaciones=total_recomendaciones,
                         total_quimicos=total_quimicos)

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
                fecha=form.fecha.data,
                tipo=form.tipo.data,
                descripcion=form.descripcion.data,
                responsable=form.responsable.data,
                observaciones=form.observaciones.data,
                huerto_id=huerto.id,
                empresa_id=current_user.empresa_id,
            )
            # Campos específicos para control de plagas
            if hasattr(form, 'plaga') and form.plaga.data:
                actividad.plaga = form.plaga.data
                actividad.nivel_infestacion = form.nivel_infestacion.data
                actividad.producto = form.producto.data
                actividad.dosis = form.dosis.data
                actividad.resultado = form.resultado.data
            db.session.add(actividad)
            db.session.commit()
            flash(" Actividad registrada exitosamente", "success")
            return redirect(url_for("admin.bitacora_huerto", huerto_id=huerto.id))
        except Exception as e:
            db.session.rollback()
            flash(f"Error registrando actividad: {e}", "danger")
    return render_template("admin/registrar_actividad.html", form=form, huerto=huerto)

@admin_bp.route("/huerto/<int:huerto_id>/actividades_fitosanitarias")
@login_required
@admin_required
def actividades_fitosanitarias(huerto_id):
    huerto = Huerto.query.filter_by(id=huerto_id, empresa_id=current_user.empresa_id).first_or_404()
    return render_template("admin/actividades_fitosanitarias.html", huerto=huerto)

@admin_bp.route("/huerto/<int:huerto_id>/registrar_control_plagas", methods=["GET", "POST"])
@login_required
@admin_required
def registrar_control_plagas(huerto_id):
    huerto = Huerto.query.filter_by(id=huerto_id, empresa_id=current_user.empresa_id).first_or_404()
    form = RegistrarActividadForm()
    if form.validate_on_submit():
        try:
            actividad = ActividadHuerto(
                fecha=form.fecha.data,
                tipo="control_plagas",
                descripcion=form.descripcion.data,
                responsable=form.responsable.data,
                observaciones=form.observaciones.data,
                huerto_id=huerto.id,
                empresa_id=current_user.empresa_id,
            )
            # Guardar campos específicos del formulario
            actividad.plaga = request.form.get('plaga')
            actividad.nivel_infestacion = request.form.get('nivel_infestacion')
            actividad.producto = request.form.get('producto')
            actividad.dosis = request.form.get('dosis')
            db.session.add(actividad)
            db.session.commit()
            flash(" Control de plagas registrado exitosamente", "success")
            return redirect(url_for("admin.bitacora_huerto", huerto_id=huerto.id))
        except Exception as e:
            db.session.rollback()
            flash(f"Error registrando control de plagas: {e}", "danger")
    return render_template("admin/registrar_control_plagas.html", form=form, huerto=huerto)

@admin_bp.route("/huerto/<int:huerto_id>/registrar_herbicida", methods=["GET", "POST"])
@login_required
@admin_required
def registrar_herbicida(huerto_id):
    huerto = Huerto.query.filter_by(id=huerto_id, empresa_id=current_user.empresa_id).first_or_404()
    form = RegistrarActividadForm()
    if form.validate_on_submit():
        try:
            actividad = ActividadHuerto(
                fecha=form.fecha.data,
                tipo="aplicacion_herbicida",
                descripcion=form.descripcion.data,
                responsable=form.responsable.data,
                observaciones=form.observaciones.data,
                huerto_id=huerto.id,
                empresa_id=current_user.empresa_id,
            )
            # Guardar campos específicos del formulario
            actividad.producto = request.form.get('producto')
            actividad.dosis = request.form.get('dosis')
            db.session.add(actividad)
            db.session.commit()
            flash(" Aplicación de herbicida registrada exitosamente", "success")
            return redirect(url_for("admin.bitacora_huerto", huerto_id=huerto.id))
        except Exception as e:
            db.session.rollback()
            flash(f"Error registrando aplicación de herbicida: {e}", "danger")
    return render_template("admin/registrar_herbicida.html", form=form, huerto=huerto)

@admin_bp.route("/huerto/<int:huerto_id>/registrar_fertilizante", methods=["GET", "POST"])
@login_required
@admin_required
def registrar_fertilizante(huerto_id):
    huerto = Huerto.query.filter_by(id=huerto_id, empresa_id=current_user.empresa_id).first_or_404()
    form = RegistrarActividadForm()
    if form.validate_on_submit():
        try:
            actividad = ActividadHuerto(
                fecha=form.fecha.data,
                tipo="aplicacion_fertilizante",
                descripcion=form.descripcion.data,
                responsable=form.responsable.data,
                observaciones=form.observaciones.data,
                huerto_id=huerto.id,
                empresa_id=current_user.empresa_id,
            )
            # Guardar campos específicos del formulario
            actividad.producto = request.form.get('producto')
            actividad.dosis = request.form.get('dosis')
            db.session.add(actividad)
            db.session.commit()
            flash(" Aplicación de fertilizante registrada exitosamente", "success")
            return redirect(url_for("admin.bitacora_huerto", huerto_id=huerto.id))
        except Exception as e:
            db.session.rollback()
            flash(f"Error registrando aplicación de fertilizante: {e}", "danger")
    return render_template("admin/registrar_fertilizante.html", form=form, huerto=huerto)


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

@admin_bp.route("/quimico/crear", methods=["GET", "POST"])
@login_required
@admin_required
def crear_quimico():
    form = QuimicoForm()
    # Obtener bodegas de la empresa para el select
    bodegas = Bodega.query.filter_by(empresa_id=current_user.empresa_id).all()
    form.bodega_id.choices = [(b.id, f"{b.nombre} - {b.ubicacion or 'Sin ubicación'}") for b in bodegas]
    
    if form.validate_on_submit():
        try:
            nuevo_quimico = Quimico(
                nombre=form.nombre.data,
                tipo=form.tipo.data,
                descripcion=form.descripcion.data,
                cantidad_litros=form.cantidad_litros.data,
                unidad=form.unidad.data,
                fecha_ingreso=form.fecha_ingreso.data,
                fecha_vencimiento=form.fecha_vencimiento.data,
                bodega_id=form.bodega_id.data
            )
            db.session.add(nuevo_quimico)
            db.session.commit()
            flash("✅ Químico agregado exitosamente", "success")
            return redirect(url_for("admin.admin_dashboard"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error al agregar químico: {e}", "danger")
    
    return render_template("admin/crear_quimico.html", form=form, bodegas=bodegas)

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
