from app import db
from app.models import User, Bodega

tecnico = User.query.filter_by(email="tecnico@correo.com").first()
bodega = Bodega.query.get(1)

print(bodega in tecnico.bodegas_asignadas.all())  # 👉 debe ser True
