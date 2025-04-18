from app import create_app, db
from werkzeug.security import generate_password_hash

app = create_app()

# Reemplazar la importación de Bodega aquí
with app.app_context():
    from app.models import User, Bodega  # Mover importación aquí

    if not User.query.filter_by(email="guido@agrocloud.cl").first():  # Verifica si ya existe un usuario con este correo
        user = User(
            name="Guido Castilla Mora",
            email="guido@agrocloud.cl",
            password=generate_password_hash("admin123"),  # Contraseña segura
            role="admin"  # Rol de administrador
        )
        db.session.add(user)
        db.session.commit()  # Guarda el nuevo usuario
        print("Usuario admin creado correctamente.")
    else:
        print("Ya existe un usuario con ese correo.")
