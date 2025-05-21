from app import app, db
from app.models import User
from werkzeug.security import generate_password_hash

with app.app_context():
    if not User.query.filter_by(email="admin@correo.com").first():
        admin = User(
            name="Administrador",
            email="admin@correo.com",
            password=generate_password_hash("admin123"),
            role="admin"
        )
        db.session.add(admin)
        db.session.commit()
        print("Admin creado")
    else:
        print("El admin ya existe")
