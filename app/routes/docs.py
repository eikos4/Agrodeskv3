# app/routes/docs.py
import os
import time
import json
from datetime import datetime

from flask import (
    Blueprint, jsonify, render_template, request, redirect,
    url_for, flash, current_app, send_from_directory, abort,
    Response, stream_with_context
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.extensions import db
from app.models import Documento, Huerto

docs_bp = Blueprint("docs", __name__, url_prefix="/docs")

# ----------------- Helpers -----------------
def is_allowed(filename: str) -> bool:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    allowed = current_app.config.get("ALLOWED_DOC_EXT") or {
        "pdf", "png", "jpg", "jpeg", "webp", "txt", "csv", "xlsx", "docx"
    }
    return ext in allowed

def ensure_folder(path: str):
    os.makedirs(path, exist_ok=True)

def is_admin() -> bool:
    return current_user.is_authenticated and getattr(current_user, "role", None) == "admin"

def current_empresa_id() -> int | None:
    """Devuelve la empresa del usuario actual (si existe)."""
    return getattr(current_user, "empresa_id", None)

def resolve_empresa_for_doc(huerto_id: int | None) -> int | None:
    """
    Determina el empresa_id para el documento:
    1) Por defecto: empresa del usuario logueado.
    2) Si viene huerto_id: se valida y se usa la empresa del huerto.
       - Si el usuario tiene empresa, se exige que coincida con la del huerto.
    """
    emp_user = current_empresa_id()
    if huerto_id:
        huerto = Huerto.query.get(huerto_id)
        if not huerto:
            return None
        if emp_user and huerto.empresa_id != emp_user and not is_admin():
            # Aislamiento tenant básico
            return None
        return huerto.empresa_id
    return emp_user

# ----------------- Panel Admin -----------------
@docs_bp.route("/admin", methods=["GET", "POST"])
@login_required
def admin_panel():
    if not is_admin():
        flash("No autorizado", "danger")
        return redirect(url_for("main.index"))

    # Parámetros opcionales para filtrar y volver
    huerto_id_param = request.args.get("huerto_id", type=int)
    next_url = request.args.get("next")

    # Cargar choices de huertos (opcionalmente filtrados por empresa)
    from app.forms import DocumentoForm  # evitar ciclos
    form = DocumentoForm()

    emp_id = current_empresa_id()
    huertos_q = Huerto.query
    if emp_id:
        huertos_q = huertos_q.filter(Huerto.empresa_id == emp_id)
    form.huerto_id.choices = [(0, "— General —")] + [
        (h.id, h.nombre) for h in huertos_q.order_by(Huerto.nombre).all()
    ]
    if huerto_id_param:
        form.huerto_id.data = huerto_id_param

    # POST: subir
    if request.method == "POST" and form.validate_on_submit():
        f = form.archivo.data
        if not f or not is_allowed(f.filename):
            flash("Formato no permitido.", "danger")
            return redirect(url_for("docs.admin_panel", huerto_id=huerto_id_param, next=next_url))

        # === RESOLVER empresa_id (FIX PRINCIPAL) ===
        huerto_id_val = form.huerto_id.data if form.huerto_id.data != 0 else None
        empresa_id = resolve_empresa_for_doc(huerto_id_val)
        if not empresa_id:
            flash("No se pudo determinar la empresa del documento.", "danger")
            return redirect(url_for("docs.admin_panel", huerto_id=huerto_id_param, next=next_url))

        upload_folder = current_app.config["UPLOAD_FOLDER"]
        ensure_folder(upload_folder)

        safe_name = secure_filename(f.filename)
        final_name = f"{int(time.time())}_{safe_name}"
        save_path = os.path.join(upload_folder, final_name)
        f.save(save_path)

        doc = Documento(
            titulo=form.titulo.data,
            categoria=form.categoria.data or None,
            filename=final_name,
            mimetype=f.mimetype,
            huerto_id=huerto_id_val,
            subido_por_id=current_user.id,
            empresa_id=empresa_id,                    # <- **OBLIGATORIO**
            created_at=datetime.utcnow(),
        )
        try:
            db.session.add(doc)
            db.session.commit()
            flash("Documento subido.", "success")
        except IntegrityError as e:
            db.session.rollback()
            current_app.logger.exception("Error integridad al subir documento")
            flash("No se pudo guardar el documento (restricción de integridad).", "danger")
            return redirect(url_for("docs.admin_panel", huerto_id=huerto_id_param, next=next_url))
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.exception("Error BD al subir documento")
            flash("Error de base de datos al guardar el documento.", "danger")
            return redirect(url_for("docs.admin_panel", huerto_id=huerto_id_param, next=next_url))

        # Volver a donde estabas si se envió 'next'
        if next_url:
            return redirect(next_url)

        return redirect(url_for("docs.admin_panel", huerto_id=huerto_id_param))

    # GET: listar (opcional: filtrar por huerto + generales) y SIEMPRE por empresa
    q = Documento.query
    if emp_id:
        q = q.filter(Documento.empresa_id == emp_id)
    if huerto_id_param:
        q = q.filter((Documento.huerto_id == huerto_id_param) | (Documento.huerto_id.is_(None)))
    documentos = q.order_by(Documento.created_at.desc()).all()

    return render_template(
        "docs/admin.html",
        form=form,
        documentos=documentos,
        huerto_id=huerto_id_param
    )

# ----------------- Archivos -----------------
@docs_bp.route("/download/<int:doc_id>")
@login_required
def download(doc_id):
    doc = Documento.query.get_or_404(doc_id)
    # Aislamiento por empresa
    emp_id = current_empresa_id()
    if emp_id and doc.empresa_id != emp_id and not is_admin():
        abort(403)

    folder = current_app.config["UPLOAD_FOLDER"]
    path = os.path.join(folder, doc.filename)
    if not os.path.isfile(path):
        abort(404)
    # download_name: usa el título si existe, si no, el filename
    download_name = (doc.titulo or doc.filename)
    return send_from_directory(folder, doc.filename, as_attachment=True, download_name=download_name)

@docs_bp.route("/view/<int:doc_id>")
@login_required
def view(doc_id):
    doc = Documento.query.get_or_404(doc_id)
    emp_id = current_empresa_id()
    if emp_id and doc.empresa_id != emp_id and not is_admin():
        abort(403)

    folder = current_app.config["UPLOAD_FOLDER"]
    path = os.path.join(folder, doc.filename)
    if not os.path.isfile(path):
        abort(404)
    return send_from_directory(folder, doc.filename)

@docs_bp.route("/delete/<int:doc_id>", methods=["POST"])
@login_required
def delete(doc_id):
    if not is_admin():
        flash("No autorizado", "danger")
        return redirect(url_for("main.index"))

    doc = Documento.query.get_or_404(doc_id)
    # (Opcional) Si tu admin también está restringido a una empresa concreta:
    emp_id = current_empresa_id()
    if emp_id and doc.empresa_id != emp_id:
        flash("No puedes eliminar documentos de otra empresa.", "danger")
        return redirect(url_for("docs.admin_panel"))

    folder = current_app.config["UPLOAD_FOLDER"]
    try:
        try:
            os.remove(os.path.join(folder, doc.filename))
        except Exception:
            pass
        db.session.delete(doc)
        db.session.commit()
        flash("Documento eliminado.", "success")
    except SQLAlchemyError:
        db.session.rollback()
        flash("No se pudo eliminar el documento.", "danger")

    # Respeta ?huerto_id en retorno
    huerto_back = request.args.get("huerto_id", type=int)
    return redirect(url_for("docs.admin_panel", huerto_id=huerto_back) if huerto_back else url_for("docs.admin_panel"))

# ----------------- API JSON (para Técnico / UI) -----------------
@docs_bp.route("/list")
@login_required
def list_docs():
    try:
        emp_id = current_empresa_id()
        if not emp_id:
            return jsonify({"items": []})

        huerto_id = request.args.get("huerto_id", type=int)
        q = Documento.query.filter(Documento.empresa_id == emp_id)
        if huerto_id:
            q = q.filter((Documento.huerto_id == huerto_id) | (Documento.huerto_id.is_(None)))
        docs = q.order_by(Documento.created_at.desc()).all()

        def fmt_date(dt):
            try:
                return dt.strftime("%Y-%m-%d %H:%M") if dt else ""
            except Exception:
                return ""

        items = [{
            "id": d.id,
            "titulo": d.titulo or "(sin título)",
            "categoria": d.categoria,
            "fecha": fmt_date(d.created_at)
        } for d in docs]

        return jsonify({"items": items})
    except Exception as e:
        current_app.logger.exception("Error en /docs/list")
        return jsonify({"error": str(e)}), 500

# ----------------- SSE (Opcional: “tiempo real”) -----------------
@docs_bp.route("/stream")
@login_required
def stream():
    @stream_with_context
    def event_stream():
        # Ejemplo simple: ping inicial y pings de keep-alive
        yield f"data: {json.dumps({'type': 'hello', 'ts': time.time()})}\n\n"
        while True:
            time.sleep(25)
            yield f"data: {json.dumps({'type': 'keepalive', 'ts': time.time()})}\n\n"

    return Response(event_stream(), mimetype="text/event-stream")
