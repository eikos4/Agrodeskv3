# seed_admin.py
from app import create_app
from app.extensions import db
from app.models import User, Empresa
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    EMPRESA_SLUG   = "agrodesk-agro"     # slug (minúsculas/sin espacios)
    EMPRESA_NOMBRE = "AgroDESK"     # nombre visible

    ADMIN_EMAIL  = "parral@agrodesk.cl"
    ADMIN_PASS   = "admi"
    ADMIN_NOMBRE = "Nicolas Parra"

    # 1) Crear/obtener empresa
    empresa = Empresa.query.filter_by(slug=EMPRESA_SLUG).first()
    if empresa:
        print(f"ℹ️  Empresa encontrada: {empresa.nombre} (id={empresa.id})")
    else:
        empresa = Empresa(nombre=EMPRESA_NOMBRE, slug=EMPRESA_SLUG)
        db.session.add(empresa)
        db.session.commit()
        print(f"✅ Empresa creada: {empresa.nombre} (id={empresa.id})")

    # 2) Crear/obtener admin
    admin = User.query.filter_by(
        empresa_id=empresa.id,
        email=ADMIN_EMAIL.lower().strip()
    ).first()

    if admin:
        print(f"ℹ️  Usuario admin ya existe: {admin.email}")
    else:
        admin = User(
            name=ADMIN_NOMBRE,
            email=ADMIN_EMAIL.lower().strip(),
            password=generate_password_hash(ADMIN_PASS),
            role="admin",
            empresa_id=empresa.id
        )
        db.session.add(admin)
        db.session.commit()
        print(f"✅ Usuario admin creado: {ADMIN_EMAIL} / {ADMIN_PASS}")
