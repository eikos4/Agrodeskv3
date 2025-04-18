from app import create_app, db
from app.models import User, Bodega

app = create_app()

with app.app_context():
    tecnico = User.query.filter_by(email="swap.1319@gmail.com").first()
    bodega = Bodega.query.get(1)

    if tecnico and bodega:
        tecnico.bodegas_asignadas.append(bodega)
        db.session.commit()
        print("✅ Técnico asignado correctamente a la bodega.")
    else:
        print("⚠️ Técnico o bodega no encontrados.")
