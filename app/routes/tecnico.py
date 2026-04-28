# app/routes/tecnico.py
from datetime import datetime
from functools import wraps

from flask import Blueprint, flash, render_template, redirect, request, url_for, abort
from flask_login import login_required, current_user
from sqlalchemy import extract
from sqlalchemy.orm import selectinload

from app.extensions import db  # 👈 DB desde extensions
from app.models import (
    Bodega, Huerto, Recomendacion, Quimico,
    FormularioTarea, ChecklistItem, ActividadHuerto, MovimientoInventario
)
from app.forms import (
    QuimicoForm, ResponderFormularioForm, ChecklistItemForm, RegistrarActividadForm,
    BodegaForm, CrearHuertoForm
)

tecnico_bp = Blueprint("tecnico", __name__, url_prefix="/tecnico")


# =============== Decoradores / helpers acceso ===============
def tecnico_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "tecnico":
            flash("Acceso solo permitido a técnicos.", "danger")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated_function


def _same_empresa(obj) -> bool:
    """Chequea que el objeto pertenezca a la misma empresa del usuario."""
    return getattr(obj, "empresa_id", None) == getattr(current_user, "empresa_id", None)


def tecnico_puede_acceder_a_bodega(bodega: Bodega) -> bool:
    """Misma empresa y (responsable == técnico) o asignado vía M2M."""
    if not bodega or not _same_empresa(bodega):
        return False
    # responsable directo
    if bodega.responsable_id == current_user.id:
        return True
    # asignación M2M (lazy='dynamic' → .filter()/.count() evita cargar todo)
    try:
        return bodega.tecnicos_asignados.filter_by(id=current_user.id).count() > 0
    except Exception:
        # Si la relación no es dynamic:
        return current_user in getattr(bodega, "tecnicos_asignados", [])


def tecnico_puede_acceder_a_huerto(huerto: Huerto) -> bool:
    """Misma empresa y (responsable == técnico) o aparece en su lista asignada."""
    if not huerto or not _same_empresa(huerto):
        return False
    if huerto.responsable_id == current_user.id:
        return True
    # Si mantienes una relación de asignación explícita, valida aquí.
    try:
        return huerto in getattr(current_user, "huertos_asignados", [])
    except Exception:
        return False


def _get_huerto_or_404(huerto_id: int) -> Huerto:
    return Huerto.query.filter_by(
        id=huerto_id, empresa_id=current_user.empresa_id
    ).first_or_404()


def _get_bodega_or_404(bodega_id: int) -> Bodega:
    return Bodega.query.filter_by(
        id=bodega_id, empresa_id=current_user.empresa_id
    ).first_or_404()


# ================== Dashboard técnico ==================
@tecnico_bp.route("/tecnico/dashboard")
@login_required
@tecnico_required
def tecnico_dashboard():
    page = request.args.get("page", 1, type=int)
    per_page = 6

    # Huertos donde es responsable (del mismo tenant)
    huertos_paginados = (
        Huerto.query.filter_by(
            responsable_id=current_user.id,
            empresa_id=current_user.empresa_id
        )
        .order_by(Huerto.nombre.asc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    # Bodegas donde es responsable (del mismo tenant)
    bodegas = (
        Bodega.query.filter_by(
            responsable_id=current_user.id,
            empresa_id=current_user.empresa_id
        )
        .order_by(Bodega.nombre.asc())
        .all()
    )

    recomendaciones = (
        Recomendacion.query.filter_by(
            tecnico_id=current_user.id,
            empresa_id=current_user.empresa_id
        )
        .order_by(Recomendacion.fecha.desc())
        .limit(5)
        .all()
    )

    return render_template(
        "tecnico/tecnico_dashboard.html",
        huertos_paginados=huertos_paginados,
        huertos=huertos_paginados.items,
        bodegas=bodegas,
        recomendaciones=recomendaciones,
        notificaciones=[],
    )

@tecnico_bp.route("/bodega/crear", methods=["GET", "POST"])
@login_required
@tecnico_required
def crear_bodega():
    form = BodegaForm()
    
    # Filtrar huertos para que solo pueda asociar a los que él administra
    huertos = Huerto.query.filter_by(
        responsable_id=current_user.id, 
        empresa_id=current_user.empresa_id
    ).order_by(Huerto.nombre.asc()).all()
    
    form.huerto_id.choices = [(h.id, h.nombre) for h in huertos]
    
    # El responsable siempre será el técnico, por lo que las opciones de responsable 
    # se pueden obviar o fijar a él mismo. Para que el formulario valide (si es SelectField),
    # le pasamos solo su opción.
    form.responsable_id.choices = [(current_user.id, current_user.name)]
    form.responsable_id.data = current_user.id

    if form.validate_on_submit():
        try:
            b = Bodega(
                nombre=form.nombre.data,
                ubicacion=form.ubicacion.data,
                huerto_id=form.huerto_id.data,
                responsable_id=current_user.id, # Se fuerza a sí mismo
                empresa_id=current_user.empresa_id,
            )
            db.session.add(b)
            db.session.commit()
            flash("Bodega creada correctamente ✅", "success")
            return redirect(url_for("tecnico.tecnico_dashboard"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error creando bodega: {e}", "danger")
            
    return render_template("admin/bodega_form.html", form=form)


# ================== Recomendaciones ==================
@tecnico_bp.route("/recomendaciones")
@login_required
@tecnico_required
def ver_recomendaciones():
    todas = (
        Recomendacion.query.filter_by(
            tecnico_id=current_user.id,
            empresa_id=current_user.empresa_id
        )
        .order_by(Recomendacion.fecha.desc())
        .all()
    )
    pendientes = [r for r in todas if r.estado != "completada"]
    hechas = [r for r in todas if r.estado == "completada"]
    return render_template(
        "tecnico/recomendaciones.html",
        recomendaciones_pendientes=pendientes,
        recomendaciones_completadas=hechas,
    )


@tecnico_bp.route("/recomendacion/<int:reco_id>/completar", methods=["POST"])
@login_required
@tecnico_required
def completar_recomendacion(reco_id):
    r = Recomendacion.query.filter_by(
        id=reco_id, tecnico_id=current_user.id, empresa_id=current_user.empresa_id
    ).first_or_404()
    r.estado = "completada"
    db.session.commit()
    flash("¡Recomendación marcada como completada!", "success")
    return redirect(url_for("tecnico.ver_recomendaciones"))


# ================== Mis huertos ==================
@tecnico_bp.route("/mis_huertos")
@login_required
@tecnico_required
def mis_huertos():
    # Responsable
    q1 = Huerto.query.filter_by(
        responsable_id=current_user.id, empresa_id=current_user.empresa_id
    )
    # Si tienes otra relación de asignación explícita, agrégala aquí.
    huertos = list({*q1.all()})
    return render_template("tecnico/mis_huertos.html", huertos=huertos)

@tecnico_bp.route("/huerto/<int:huerto_id>/editar", methods=["GET", "POST"])
@login_required
@tecnico_required
def editar_huerto(huerto_id):
    huerto = _get_huerto_or_404(huerto_id)
    if not tecnico_puede_acceder_a_huerto(huerto):
        flash("No tienes acceso a este huerto.", "danger")
        return redirect(url_for("tecnico.mis_huertos"))
        
    form = CrearHuertoForm()
    # Ocultar o proteger el responsable: lo forzamos al mismo usuario
    # para que un técnico no pueda transferir el huerto a otro técnico.
    form.responsable_id.choices = [(current_user.id, current_user.name)]
    
    if request.method == "GET":
        form.nombre.data = huerto.nombre
        form.ubicacion.data = huerto.ubicacion
        form.superficie_ha.data = huerto.superficie_ha
        form.tipo_cultivo.data = huerto.tipo_cultivo
        form.fecha_siembra.data = huerto.fecha_siembra
        form.responsable_id.data = current_user.id
        
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
            huerto.nombre = form.nombre.data
            huerto.ubicacion = form.ubicacion.data
            huerto.superficie_ha = form.superficie_ha.data
            huerto.tipo_cultivo = form.tipo_cultivo.data
            huerto.fecha_siembra = form.fecha_siembra.data
            # Mantenemos al usuario actual como responsable siempre
            huerto.responsable_id = current_user.id
            
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
            flash("✅ Información del huerto actualizada exitosamente.", "success")
            return redirect(url_for("tecnico.mis_huertos"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error actualizando huerto: {e}", "danger")
    elif request.method == "POST":
        flash("❌ Formulario inválido", "danger")

    return render_template("admin/editar_huerto.html", form=form, huerto=huerto)


# ================== Bitácora de huerto ==================
@tecnico_bp.route("/huerto/<int:huerto_id>/bitacora")
@login_required
@tecnico_required
def bitacora_huerto(huerto_id):
    huerto = _get_huerto_or_404(huerto_id)
    if not tecnico_puede_acceder_a_huerto(huerto):
        flash("No tienes acceso a este huerto.", "danger")
        return redirect(url_for("tecnico.mis_huertos"))

    anio = request.args.get("anio", type=int)
    tipo = request.args.get("tipo", default=None, type=str)

    q = ActividadHuerto.query.filter_by(huerto_id=huerto.id)
    if anio:
        q = q.filter(extract("year", ActividadHuerto.fecha) == anio)
    if tipo:
        q = q.filter(ActividadHuerto.tipo == tipo)

    actividades = q.order_by(ActividadHuerto.fecha.desc()).all()
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
        anio_seleccionado=anio,
        tipo_seleccionado=tipo,
    )


# ================== Registrar actividad ==================
@tecnico_bp.route("/huerto/<int:huerto_id>/registrar_actividad", methods=["GET", "POST"])
@login_required
@tecnico_required
def registrar_actividad_huerto(huerto_id):
    huerto = _get_huerto_or_404(huerto_id)
    if not tecnico_puede_acceder_a_huerto(huerto):
        flash("No tienes acceso a este huerto.", "danger")
        return redirect(url_for("tecnico.mis_huertos"))

    
    form = RegistrarActividadForm()
    quimicos_disponibles = Quimico.query.join(Bodega).filter(Bodega.empresa_id == current_user.empresa_id).all()
    form.quimico_id.choices = [(0, "— Sin químico del inventario —")] + [(q.id, f"{q.nombre} (Stock: {q.cantidad_litros})") for q in quimicos_disponibles]
    
    if form.validate_on_submit():
        try:
            act = ActividadHuerto(
                huerto_id=huerto.id,
                fecha=form.fecha.data,
                tipo=form.tipo.data,
                descripcion=form.descripcion.data,
                responsable=(current_user.name or current_user.email),
                producto=form.producto.data,
                dosis=form.dosis.data,
                plaga=form.plaga.data,
                nivel_infestacion=form.nivel_infestacion.data,
                resultado=form.resultado.data,
                fotos="",
                observaciones=form.observaciones.data,
            )
            # Si ActividadHuerto tiene empresa_id NOT NULL en tu modelo, descomenta:
            # act.empresa_id = current_user.empresa_id
            
            act.quimico_id = form.quimico_id.data if form.quimico_id.data != 0 else None
            act.cantidad_aplicada = form.cantidad_aplicada.data
            db.session.add(act)
            db.session.flush() # Para obtener el ID
            
            if act.quimico_id and act.cantidad_aplicada:
                q = Quimico.query.get(act.quimico_id)
                if q and q.cantidad_litros >= act.cantidad_aplicada:
                    q.cantidad_litros -= act.cantidad_aplicada
                    mov = MovimientoInventario(quimico_id=q.id, tipo="egreso", cantidad=act.cantidad_aplicada, usuario_id=current_user.id, referencia_actividad_id=act.id, empresa_id=current_user.empresa_id)
                    db.session.add(mov)

            db.session.commit()
            flash("✅ Actividad registrada exitosamente.", "success")
            return redirect(url_for("tecnico.bitacora_huerto", huerto_id=huerto.id))
        except Exception as e:
            db.session.rollback()
            flash(f"Error registrando actividad: {e}", "danger")

    return render_template("tecnico/registrar_actividad.html", form=form, huerto=huerto)


# ================== Mis bodegas ==================
@tecnico_bp.route("/mis_bodegas")
@login_required
@tecnico_required
def mis_bodegas():
    # M2M + responsable, siempre filtrando por empresa
    bodegas_set = set()

    # Many-to-many (si es lazy='dynamic', usa .all())
    try:
        for b in current_user.bodegas_asignadas.filter_by(empresa_id=current_user.empresa_id).all():
            bodegas_set.add(b)
    except Exception:
        for b in getattr(current_user, "bodegas_asignadas", []):
            if _same_empresa(b):
                bodegas_set.add(b)

    # Responsable
    for b in Bodega.query.filter_by(
        responsable_id=current_user.id, empresa_id=current_user.empresa_id
    ).all():
        bodegas_set.add(b)

    bodegas = sorted(list(bodegas_set), key=lambda x: (x.nombre or "").lower())
    return render_template("tecnico/mis_bodegas.html", bodegas=bodegas)


# ================== Químicos (ver/agregar/editar/eliminar) ==================
@tecnico_bp.route("/bodega/<int:bodega_id>/quimicos")
@login_required
@tecnico_required
def ver_quimicos(bodega_id):
    bodega = _get_bodega_or_404(bodega_id)
    if not tecnico_puede_acceder_a_bodega(bodega):
        flash("No tienes permiso para acceder a esta bodega.", "danger")
        return redirect(url_for("tecnico.mis_bodegas"))

    bodega = (
        Bodega.query.filter_by(id=bodega.id, empresa_id=current_user.empresa_id)
        .options(selectinload(Bodega.quimicos), selectinload(Bodega.huerto))
        .first_or_404()
    )
    return render_template("tecnico/quimicos.html", bodega=bodega, quimicos=bodega.quimicos)


@tecnico_bp.route("/bodega/<int:bodega_id>/quimicos/nuevo", methods=["GET", "POST"])
@login_required
@tecnico_required
def agregar_quimico(bodega_id):
    bodega = _get_bodega_or_404(bodega_id)
    if not tecnico_puede_acceder_a_bodega(bodega):
        flash("No tienes permiso para agregar químicos en esta bodega.", "danger")
        return redirect(url_for("tecnico.mis_bodegas"))

    form = QuimicoForm()
    if form.validate_on_submit():
        try:
            q = Quimico(
                nombre=form.nombre.data.strip(),
                tipo=form.tipo.data,
                descripcion=form.descripcion.data or "",
                cantidad_litros=form.cantidad_litros.data,
                fecha_ingreso=form.fecha_ingreso.data,
                bodega_id=bodega.id,
                empresa_id=current_user.empresa_id,  # 👈 evita IntegrityError NOT NULL
            )
            db.session.add(q)
            db.session.commit()

            if request.form.get("seguir"):
                flash("Químico agregado. Puedes cargar otro.", "success")
                return redirect(url_for("tecnico.agregar_quimico", bodega_id=bodega.id))

            flash("✅ Químico agregado correctamente.", "success")
            return redirect(url_for("tecnico.ver_quimicos", bodega_id=bodega.id))
        except Exception as e:
            db.session.rollback()
            flash(f"Error al agregar químico: {e}", "danger")

    return render_template("tecnico/agregar_quimico.html", form=form, bodega=bodega)


@tecnico_bp.route("/quimicos/<int:quimico_id>/editar", methods=["GET", "POST"])
@login_required
@tecnico_required
def editar_quimico(quimico_id):
    quimico = Quimico.query.filter_by(
        id=quimico_id, empresa_id=current_user.empresa_id
    ).first_or_404()
    bodega = quimico.bodega
    if not tecnico_puede_acceder_a_bodega(bodega):
        flash("No tienes permiso para editar químicos en esta bodega.", "danger")
        return redirect(url_for("tecnico.mis_bodegas"))

    form = QuimicoForm(obj=quimico)
    if form.validate_on_submit():
        try:
            quimico.nombre = form.nombre.data.strip()
            quimico.tipo = form.tipo.data
            quimico.descripcion = form.descripcion.data or ""
            quimico.cantidad_litros = form.cantidad_litros.data
            quimico.fecha_ingreso = form.fecha_ingreso.data
            # quimico.empresa_id se mantiene
            db.session.commit()
            flash("Químico actualizado exitosamente.", "success")
            return redirect(url_for("tecnico.ver_quimicos", bodega_id=bodega.id))
        except Exception as e:
            db.session.rollback()
            flash(f"Error al actualizar químico: {e}", "danger")

    return render_template("tecnico/editar_quimico.html", form=form, quimico=quimico)


@tecnico_bp.route("/quimicos/<int:quimico_id>/eliminar", methods=["POST"])
@login_required
@tecnico_required
def eliminar_quimico(quimico_id):
    quimico = Quimico.query.filter_by(
        id=quimico_id, empresa_id=current_user.empresa_id
    ).first_or_404()
    bodega = quimico.bodega
    if not tecnico_puede_acceder_a_bodega(bodega):
        flash("No tienes permiso para eliminar químicos en esta bodega.", "danger")
        return redirect(url_for("tecnico.mis_bodegas"))
    try:
        db.session.delete(quimico)
        db.session.commit()
        flash("🗑️ Químico eliminado exitosamente.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error al eliminar químico: {e}", "danger")
    return redirect(url_for("tecnico.ver_quimicos", bodega_id=bodega.id))


# ================== Formularios (Checklist) ==================
@tecnico_bp.route("/formulario/<int:formulario_id>", methods=["GET", "POST"])
@login_required
@tecnico_required
def responder_formulario(formulario_id):
    formulario = FormularioTarea.query.filter_by(
        id=formulario_id, empresa_id=current_user.empresa_id
    ).first_or_404()
    if formulario.tecnico_id != current_user.id:
        flash("No tienes acceso a este formulario.", "danger")
        return redirect(url_for("tecnico.tecnico_dashboard"))

    form = ResponderFormularioForm()
    items = formulario.checklist_items

    if not form.is_submitted():
        form.items.entries.clear()
        for item in items:
            fi = ChecklistItemForm()
            fi.descripcion.data = item.descripcion
            fi.realizado.data = item.realizado
            fi.comentario.data = item.comentario
            form.items.append_entry(fi)

    if form.validate_on_submit():
        try:
            for i, item_form in enumerate(form.items):
                items[i].realizado = item_form.realizado.data
                items[i].comentario = item_form.comentario.data
            formulario.estado = "completado"
            db.session.commit()
            flash("Formulario respondido correctamente.", "success")
            return redirect(url_for("tecnico.tecnico_dashboard"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error al responder formulario: {e}", "danger")

    return render_template("tecnico/formulario_responder.html", form=form, formulario_tarea=formulario)


# ================== Todos los químicos (debug vista) ==================
@tecnico_bp.route("/todos_los_quimicos")
@login_required
@tecnico_required
def todos_los_quimicos():
    print("=== DEBUG DETALLADO ===")
    print(f"Usuario actual: {current_user.name} (ID: {current_user.id})")

    bodegas_m2m = []
    try:
        bodegas_m2m = current_user.bodegas_asignadas.filter_by(empresa_id=current_user.empresa_id).all()
    except Exception:
        bodegas_m2m = [b for b in getattr(current_user, "bodegas_asignadas", []) if _same_empresa(b)]
    print(f"1) M2M bodegas: {len(bodegas_m2m)}")

    bodegas_resp = Bodega.query.filter_by(responsable_id=current_user.id, empresa_id=current_user.empresa_id).all()
    print(f"2) Bodegas responsable: {len(bodegas_resp)}")

    # Consolidado
    bodegas = list({*bodegas_m2m, *bodegas_resp})
    quimicos = []
    for b in bodegas:
        quimicos.extend(b.quimicos)

    return render_template("tecnico/todos_los_quimicos.html", quimicos=quimicos, bodegas=bodegas)


# ================== Selector de huerto rápido ==================
@tecnico_bp.route("/actividad/nueva", methods=["GET"], endpoint="registrar_actividad")
@login_required
@tecnico_required
def registrar_actividad():
    huerto_id = request.args.get("huerto_id", type=int)
    if huerto_id:
        return redirect(url_for("tecnico.registrar_actividad_huerto", huerto_id=huerto_id))

    huertos = (
        Huerto.query.filter_by(empresa_id=current_user.empresa_id, responsable_id=current_user.id)
        .order_by(Huerto.nombre.asc())
        .all()
    )
    return render_template("tecnico/elegir_huerto.html", huertos=huertos)
