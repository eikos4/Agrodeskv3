from app import app, db
from app.models import User
from werkzeug.security import generate_password_hash

with app.app_context():
    email = "admin@demo.com"
    password = "admin123"
    nombre = "Guido Castilla"

    # Busca si ya existe
    existe = User.query.filter_by(email=email).first()
    if existe:
        print("El usuario admin ya existe:", existe.email)
    else:
        admin = User(
            name=nombre,
            email=email,
            password=generate_password_hash(password),
            role="admin",
            created_by=None  # Es el root admin, nadie lo creó
        )
        db.session.add(admin)
        db.session.commit()
        print(f"✅ Usuario admin creado: {email} / {password}")
