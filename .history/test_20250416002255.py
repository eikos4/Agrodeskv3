from app import create_app, db
from app.models import Bodega
app = create_app()
with app.app_context():
    print("Total de bodegas:", len(Bodega.query.all()))
