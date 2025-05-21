from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash

app = create_app()  # CREA la app antes de todo

with app.app_context():
    email = "admin@demo.com"
    password = "admin123"
    nombre = "Administrador Principal"

    # Verifica si ya existe
    existe = User.query.filter_by(email=email).first()
    if existe:
        print("El usuario admin ya existe:", existe.email)
    else:
        admin = User(
            name=nombre,
            email=email,
            password=generate_password_hash(password),
            role="admin",
            created_by=None  # O el ID del admin que lo crea, si aplica
        )
        db.session.add(admin)
        db.session.commit()
        print(f"✅ Usuario admin creado: {email} / {password}")
