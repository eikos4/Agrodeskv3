# app/routes/geo_admin.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.models import Parcela, Huerto, ActivityType
from app.forms import ParcelaForm, ActivityTypeForm
from app import db
import json

geo_admin_bp = Blueprint('geo_admin', __name__, url_prefix='/admin/geo')
geo_types_bp = Blueprint('geo_types', __name__, url_prefix='/admin/geo/tipos')

def _huertos_choices():
    return [(h.id, h.nombre) for h in Huerto.query.order_by(Huerto.nombre.asc()).all()]

# ===== Parcelas =====
@geo_admin_bp.route('/parcelas')
@login_required
def parcelas_list():
    huerto_id = request.args.get('huerto_id', type=int)
    q = Parcela.query
    if huerto_id: q = q.filter_by(huerto_id=huerto_id)
    parcelas = q.order_by(Parcela.huerto_id.asc(), Parcela.nombre.asc()).all()
    return render_template('admin/parcelas_list.html', parcelas=parcelas, huerto_id=huerto_id)

@geo_admin_bp.route('/parcelas/nueva', methods=['GET','POST'])
@login_required
def parcela_nueva():
    form = ParcelaForm()
    form.huerto_id.choices = _huertos_choices()
    if form.validate_on_submit():
        try:
            json.loads(form.geom_geojson.data)  # valida JSON
            p = Parcela(nombre=form.nombre.data.strip(),
                        huerto_id=form.huerto_id.data,
                        geom_geojson=form.geom_geojson.data.strip())
            db.session.add(p); db.session.commit()
            flash("Parcela creada ✅", "success")
            return redirect(url_for('geo_admin.parcelas_list', huerto_id=p.huerto_id))
        except Exception as e:
            db.session.rollback(); flash(f"Error: {e}", "danger")
    return render_template('admin/parcela_form.html', form=form)

@geo_admin_bp.route('/parcelas/<int:parcela_id>/editar', methods=['GET','POST'])
@login_required
def parcela_editar(parcela_id):
    p = Parcela.query.get_or_404(parcela_id)
    form = ParcelaForm(obj=p)
    form.huerto_id.choices = _huertos_choices()
    if form.validate_on_submit():
        try:
            json.loads(form.geom_geojson.data)
            p.nombre = form.nombre.data.strip()
            p.huerto_id = form.huerto_id.data
            p.geom_geojson = form.geom_geojson.data.strip()
            db.session.commit()
            flash("Parcela actualizada ✅", "success")
            return redirect(url_for('geo_admin.parcelas_list', huerto_id=p.huerto_id))
        except Exception as e:
            db.session.rollback(); flash(f"Error: {e}", "danger")
    return render_template('admin/parcela_form.html', form=form, parcela=p)

@geo_admin_bp.route('/parcelas/<int:parcela_id>/eliminar', methods=['POST'])
@login_required
def parcela_eliminar(parcela_id):
    p = Parcela.query.get_or_404(parcela_id)
    try:
        db.session.delete(p); db.session.commit()
        flash("Parcela eliminada ✅","success")
    except Exception as e:
        db.session.rollback(); flash(f"Error: {e}", "danger")
    return redirect(url_for('geo_admin.parcelas_list'))

# ===== Tipos de actividad (estilos) =====
@geo_types_bp.route('/')
@login_required
def tipos_list():
    tipos = ActivityType.query.order_by(ActivityType.nombre.asc()).all()
    return render_template('admin/activity_types_list.html', tipos=tipos)

@geo_types_bp.route('/nuevo', methods=['GET','POST'])
@login_required
def tipo_nuevo():
    form = ActivityTypeForm()
    if form.validate_on_submit():
        if ActivityType.query.filter_by(key=form.key.data.strip()).first():
            flash("La clave ya existe", "danger")
        else:
            t = ActivityType(
                key=form.key.data.strip(),
                nombre=form.nombre.data.strip(),
                color=form.color.data.strip(),
                fill_color=(form.fill_color.data.strip() or None),
                icon=form.icon.data.strip()
            )
            db.session.add(t); db.session.commit()
            flash("Tipo creado ✅","success")
            return redirect(url_for('geo_types.tipos_list'))
    return render_template('admin/activity_type_form.html', form=form, creating=True)

@geo_types_bp.route('/<int:tipo_id>/editar', methods=['GET','POST'])
@login_required
def tipo_editar(tipo_id):
    t = ActivityType.query.get_or_404(tipo_id)
    form = ActivityTypeForm(obj=t)
    if form.validate_on_submit():
        t.nombre = form.nombre.data.strip()
        t.color = form.color.data.strip()
        t.fill_color = (form.fill_color.data.strip() or None)
        t.icon = form.icon.data.strip()
        db.session.commit()
        flash("Tipo actualizado ✅","success")
        return redirect(url_for('geo_types.tipos_list'))
    return render_template('admin/activity_type_form.html', form=form, tipo=t, creating=False)

@geo_types_bp.route('/<int:tipo_id>/eliminar', methods=['POST'])
@login_required
def tipo_eliminar(tipo_id):
    t = ActivityType.query.get_or_404(tipo_id)
    try:
        db.session.delete(t); db.session.commit()
        flash("Tipo eliminado ✅","success")
    except Exception as e:
        db.session.rollback(); flash(f"Error: {e}","danger")
    return redirect(url_for('geo_types.tipos_list'))
