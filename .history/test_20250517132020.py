from app import db
from app.models import User, Bodega

tecnico = User.query.filter_by(email="tecnico@correo.com").first()
bodega = Bodega.query.get(1)

print(bodega in tecnico.bodegas_asignadas.all())  # 👉 debe ser True


# create_admin.py

from app import db
from app.models import User
from werkzeug.security import generate_password_hash

def create_admin():
    nombre = "G"
    email = "admin@demo.com"
    password = "admin123"  # Cambia por seguridad real en prod

    # ¿Ya existe?
    if User.query.filter_by(email=email).first():
        print("Ya existe un administrador con ese correo.")
        return

    user = User(
        name=nombre,
        email=email,
        password=generate_password_hash(password),
        role="admin",
        created_by=None  # Ningún creador porque es el primero
    )
    db.session.add(user)
    db.session.commit()
    print(f"✅ Usuario admin creado: {email} / {password}")

if __name__ == "__main__":
    from app import app  # Asegúrate de importar tu app Flask aquí
    with app.app_context():
        create_admin()
