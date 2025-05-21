from app import db
from flask_login import UserMixin
from datetime import datetime

# ==============================
# Asociación muchos a muchos: Técnicos <-> Bodegas
# ==============================
tecnico_bodega = db.Table(
    'tecnico_bodega',
    db.Column('tecnico_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('bodega_id', db.Integer, db.ForeignKey('bodegas.id'))
)

# ==============================
# Mixin de timestamps
# ==============================
class TimestampMixin:
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# ==============================
# MODELO DE USUARIO
# ==============================
class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # "admin" o "tecnico"
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))

    creador = db.relationship('User', remote_side=[id], backref='tecnicos_creados')
    huertos_asignados = db.relationship('Huerto', back_populates='responsable', lazy=True)
    bodegas_asignadas = db.relationship(
        'Bodega',
        secondary=tecnico_bodega,
        back_populates='tecnicos_asignados',
        lazy='dynamic'
    )

    def __repr__(self):
        return f"<User {self.name}>"

# ==============================
# MODELO DE HUERTO
# ==============================
class Huerto(db.Model):
    __tablename__ = 'huertos'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    ubicacion = db.Column(db.String(200))
    superficie_ha = db.Column(db.Float)
    tipo_cultivo = db.Column(db.String(100))
    fecha_siembra = db.Column(db.Date)

    responsable_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    responsable = db.relationship('User', back_populates='huertos_asignados')

    bodegas = db.relationship('Bodega', back_populates='huerto', lazy=True)
    actividades = db.relationship(
        'ActividadHuerto',
        back_populates='huerto',
        cascade='all, delete-orphan'
    )

    def __repr__(self):
        return f"<Huerto {self.nombre}>"

# ==============================
# MODELO DE BODEGA
# ==============================
class Bodega(db.Model):
    __tablename__ = 'bodegas'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    ubicacion = db.Column(db.String(200))

    huerto_id = db.Column(db.Integer, db.ForeignKey('huertos.id'), nullable=False)
    huerto = db.relationship('Huerto', back_populates='bodegas')

    responsable_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    responsable = db.relationship('User', foreign_keys=[responsable_id])

    quimicos = db.relationship('Quimico', backref='bodega', lazy=True)

    tecnicos_asignados = db.relationship(
        'User',
        secondary=tecnico_bodega,
        back_populates='bodegas_asignadas',
        lazy='dynamic'
    )

    def __repr__(self):
        return f"<Bodega {self.nombre}>"

# ==============================
# MODELO DE QUÍMICO
# ==============================
class Quimico(db.Model):
    __tablename__ = 'quimicos'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    tipo = db.Column(db.String(50))
    descripcion = db.Column(db.Text)
    cantidad_litros = db.Column(db.Float)
    fecha_ingreso = db.Column(db.Date)

    bodega_id = db.Column(db.Integer, db.ForeignKey('bodegas.id'), nullable=False)

    def __repr__(self):
        return f"<Quimico {self.nombre}>"

# ==============================
# MODELO DE ACTIVIDAD DE HUERTO
# ==============================
class ActividadHuerto(db.Model):
    __tablename__ = 'actividad_huerto'

    id = db.Column(db.Integer, primary_key=True)
    huerto_id = db.Column(db.Integer, db.ForeignKey('huertos.id'), nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    tipo = db.Column(db.String(50))
    descripcion = db.Column(db.Text)
    responsable = db.Column(db.String(100))
    observaciones = db.Column(db.Text)
    producto = db.Column(db.String(100))
    dosis = db.Column(db.String(50))
    plaga = db.Column(db.String(100))
    nivel_infestacion = db.Column(db.String(20))
    resultado = db.Column(db.Text)
    fotos = db.Column(db.String(250))

    huerto = db.relationship('Huerto', back_populates='actividades')

    @property
    def anio(self):
        return self.fecha.year if self.fecha else None

    def __repr__(self):
        return f"<ActividadHuerto {self.tipo} {self.fecha}>"

# ==============================
# MODELO DE RECOMENDACIÓN
# ==============================
class Recomendacion(db.Model):
    __tablename__ = 'recomendacion'
    id = db.Column(db.Integer, primary_key=True)
    contenido = db.Column(db.Text, nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    categoria = db.Column(db.String(100))
    estado = db.Column(db.String(20), default="pendiente")
    adjunto = db.Column(db.String(200))

    tecnico_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    autor_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    tecnico = db.relationship('User', foreign_keys=[tecnico_id])
    autor = db.relationship('User', foreign_keys=[autor_id])

    def __repr__(self):
        return f"<Recomendacion {self.id}>"

# ==============================
# MODELO DE FORMULARIO DE TAREA
# ==============================
class FormularioTarea(db.Model):
    __tablename__ = 'formulario_tarea'
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(150), nullable=False)
    descripcion = db.Column(db.Text)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    estado = db.Column(db.String(20), default="pendiente")

    tecnico_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    huerto_id = db.Column(db.Integer, db.ForeignKey('huertos.id'))
    bodega_id = db.Column(db.Integer, db.ForeignKey('bodegas.id'))

    tecnico = db.relationship('User', foreign_keys=[tecnico_id])
    huerto = db.relationship('Huerto')
    bodega = db.relationship('Bodega')
    checklist_items = db.relationship('ChecklistItem', backref='formulario', cascade="all, delete-orphan")

    def __repr__(self):
        return f"<FormularioTarea {self.id}>"

# ==============================
# MODELO DE ITEM DE CHECKLIST
# ==============================
class ChecklistItem(db.Model):
    __tablename__ = 'checklist_item'
    id = db.Column(db.Integer, primary_key=True)
    descripcion = db.Column(db.String(200), nullable=False)
    realizado = db.Column(db.Boolean, default=False)
    comentario = db.Column(db.Text)
    formulario_id = db.Column(db.Integer, db.ForeignKey('formulario_tarea.id'))

    def __repr__(self):
        return f"<ChecklistItem {self.id} - {self.descripcion}>"
