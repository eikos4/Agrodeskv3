# app/seed.py (ejecuta una vez en consola de Flask)
from app import db
from app.models import ActivityType

defaults = [
  dict(key='riego', nombre='Riego', color='#0dcaf0', fill_color='#0dcaf033', icon='bi-water'),
  dict(key='poda', nombre='Poda', color='#6f42c1', fill_color='#6f42c133', icon='bi-scissors'),
  dict(key='fertilizacion', nombre='Fertilización', color='#198754', fill_color='#19875433', icon='bi-droplet-half'),
  dict(key='cosecha', nombre='Cosecha', color='#fd7e14', fill_color='#fd7e1433', icon='bi-basket'),
  dict(key='control_plagas', nombre='Control de Plagas', color='#dc3545', fill_color='#dc354533', icon='bi-bug'),
  dict(key='otra', nombre='Otra', color='#6c757d', fill_color='#6c757d33', icon='bi-gear'),
]
for d in defaults:
    if not ActivityType.query.filter_by(key=d['key']).first():
        db.session.add(ActivityType(**d))
db.session.commit()
