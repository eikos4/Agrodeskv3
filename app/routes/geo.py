# app/routes/geo.py
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from functools import wraps
from app.extensions import db
from app.models import Huerto, Parcela, ActividadCampo
from app.forms import ParcelaForm, ActividadForm
import json

geo_bp = Blueprint("geo", __name__, url_prefix="/geo")

# --- helper: solo admin ---
def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "admin":
            flash("No autorizado", "danger")
            return redirect(url_for("main.index"))
        return f(*args, **kwargs)
    return wrapper

# --- PÁGINAS ---
@geo_bp.route("/map", endpoint="mapa")
@login_required
def mapa():
    # Centro por defecto: Chile
    center = {"lat": -35.6751, "lng": -71.5430, "zoom": 6}
    first = Huerto.query.first()
    if first and getattr(first, "center_lat", None) and getattr(first, "center_lng", None):
        center = {"lat": first.center_lat, "lng": first.center_lng, "zoom": 14}
    # Render normal (NO redirect aquí)
    return render_template("geo/map.html", center=center)

@geo_bp.route("/parcelas/nueva", methods=["GET", "POST"], endpoint="nueva_parcela")
@login_required
@admin_required
def nueva_parcela():
    form = ParcelaForm()
    form.huerto_id.choices = [(h.id, h.nombre) for h in Huerto.query.order_by(Huerto.nombre).all()]

    if request.method == "POST" and form.validate_on_submit():
        parcela = Parcela(
            nombre=form.nombre.data,
            huerto_id=form.huerto_id.data,
            geom_geojson=form.geom_geojson.data or None
        )
        db.session.add(parcela)
        db.session.commit()
        flash("Parcela creada correctamente.", "success")
        # Redirige con focus al recién creado
        return redirect(url_for("geo.mapa", focus=f"parcela:{parcela.id}"))

    return render_template("geo/parcelas_form.html", form=form)

@geo_bp.route("/actividades/nueva", methods=["GET", "POST"], endpoint="nueva_actividad")
@login_required
def nueva_actividad():
    form = ActividadForm()
    form.huerto_id.choices = [(h.id, h.nombre) for h in Huerto.query.order_by(Huerto.nombre).all()]
    form.parcela_id.choices = [(0, "— (sin parcela) —")] + [
        (p.id, p.nombre) for p in Parcela.query.order_by(Parcela.nombre).all()
    ]

    if request.method == "POST" and form.validate_on_submit():
        act = ActividadCampo(
            huerto_id=form.huerto_id.data,
            parcela_id=form.parcela_id.data if form.parcela_id.data else None,
            tipo=form.tipo.data,
            descripcion=form.descripcion.data,
            lat=form.lat.data,
            lng=form.lng.data,
            ruta_geojson=form.ruta_geojson.data or None,
            duracion_min=form.duracion_min.data or 0
        )
        db.session.add(act)
        db.session.commit()
        flash("Actividad registrada.", "success")
        # Redirige con focus a la nueva actividad
        return redirect(url_for("geo.mapa", focus=f"actividad:{act.id}"))

    return render_template("geo/actividades_form.html", form=form)

# --- APIS GEOJSON (colecciones) ---
@geo_bp.route("/api/huertos", endpoint="api_huertos")
@login_required
def api_huertos():
    features = []
    for h in Huerto.query.all():
        center = [h.center_lng or -71.5430, h.center_lat or -35.6751]
        feature = {
            "type": "Feature",
            "geometry": None,
            "properties": {"id": h.id, "nombre": h.nombre, "center": center}
        }
        if h.bounds_geojson:
            try:
                feature["geometry"] = json.loads(h.bounds_geojson)
            except Exception:
                feature["geometry"] = None
        features.append(feature)
    return jsonify({"type": "FeatureCollection", "features": features})

@geo_bp.route("/api/parcelas", endpoint="api_parcelas")
@login_required
def api_parcelas():
    features = []
    for p in Parcela.query.all():
        geom = None
        if p.geom_geojson:
            try:
                geom = json.loads(p.geom_geojson)
            except Exception:
                geom = None
        features.append({
            "type": "Feature",
            "geometry": geom,
            "properties": {"id": p.id, "nombre": p.nombre, "huerto_id": p.huerto_id}
        })
    return jsonify({"type": "FeatureCollection", "features": features})

@geo_bp.route("/api/actividades", endpoint="api_actividades")
@login_required
def api_actividades():
    features = []
    for a in ActividadCampo.query.order_by(ActividadCampo.fecha.desc()).limit(500).all():
        geom = None
        if a.ruta_geojson:
            try:
                geom = json.loads(a.ruta_geojson)
            except Exception:
                geom = None
        if a.lat and a.lng and not geom:
            geom = {"type": "Point", "coordinates": [a.lng, a.lat]}
        features.append({
            "type": "Feature",
            "geometry": geom,
            "properties": {
                "id": a.id,
                "tipo": a.tipo,
                "descripcion": a.descripcion,
                "huerto_id": a.huerto_id,
                "parcela_id": a.parcela_id,
                "fecha": a.fecha.isoformat() if a.fecha else None,
                "duracion_min": a.duracion_min
            }
        })
    return jsonify({"type": "FeatureCollection", "features": features})

# --- APIS GEOJSON (uno por id) para 'focus' ---
@geo_bp.route("/api/parcelas/<int:pid>", endpoint="api_parcela")
@login_required
def api_parcela(pid):
    p = Parcela.query.get_or_404(pid)
    geom = None
    if p.geom_geojson:
        try:
            geom = json.loads(p.geom_geojson)
        except Exception:
            pass
    return jsonify({
        "type": "Feature",
        "geometry": geom,
        "properties": {"id": p.id, "nombre": p.nombre, "huerto_id": p.huerto_id}
    })

@geo_bp.route("/api/actividades/<int:aid>", endpoint="api_actividad")
@login_required
def api_actividad(aid):
    a = ActividadCampo.query.get_or_404(aid)
    geom = None
    if a.ruta_geojson:
        try:
            geom = json.loads(a.ruta_geojson)
        except Exception:
            pass
    if a.lat and a.lng and not geom:
        geom = {"type": "Point", "coordinates": [a.lng, a.lat]}
    return jsonify({
        "type": "Feature",
        "geometry": geom,
        "properties": {
            "id": a.id,
            "tipo": a.tipo,
            "descripcion": a.descripcion,
            "huerto_id": a.huerto_id,
            "parcela_id": a.parcela_id,
            "fecha": a.fecha.isoformat() if a.fecha else None,
            "duracion_min": a.duracion_min
        }
    })



@geo_bp.route('/map')
@login_required
def map_view():
    default_center = {"lat": -36.82, "lng": -73.05, "zoom": 8}
    center_arg = request.args.get('center')  # podría venir como string JSON
    try:
        center = json.loads(center_arg) if center_arg else default_center
        if not isinstance(center, dict):
            center = default_center
    except Exception:
        center = default_center
    return render_template('geo/map.html', center=center)