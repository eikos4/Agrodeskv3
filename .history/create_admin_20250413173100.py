# create_admin.py
from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash

app = create_app()
with app.app_context():
    if not User.query.filter_by(email="guido@agrocloud.cl").first():
        user = User(
            name="Guido Castilla Mora",
            email="guido@gmail.com",
            password=generate_password_hash("admin123"),
            role="admin"
        )
        db.session.add(user)
        db.session.commit()
        print("Usuario admin creado correctamente.")
    else:
        print("Ya existe un usuario con ese correo.")
