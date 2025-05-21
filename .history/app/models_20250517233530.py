from app import db
from flask_login import UserMixin
from datetime import datetime

# ======================
# Asociación muchos a muchos: Técnicos <-> Bodegas
# ======================
tecnico_bodega = db.Table(
    'tecnico_bodega',
    db.Column('tecnico_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('bodega_id', db.Integer, db.ForeignKey('bodegas.id'))
)

# ======================
# Mixin para timestamps
# ======================
class TimestampMixin:
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# ======================
# MODELO DE USUARIO
# ======================
class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # "admin" o "tecnico"
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))  # Relación autoref a quién creó este user

    # Relación de quién creó a quién (útil si quieres trazar la genealogía de cuentas técnicas)
    creador = db.relationship('User', remote_side=[id], backref='tecnicos_creados')

    # Un técnico puede ser responsable de varios huertos (relación 1-N)
    huertos_asignados = db.relationship('Huerto', back_populates='responsable', lazy=True)

    # Relación muchos a muchos con bodegas (un técnico puede estar asignado a varias bodegas)
    bodegas_asignadas = db.relationship(
        'Bodega',
        secondary=tecnico_bodega,
        back_populates='tecnicos_asignados',
        lazy='dynamic'
    )

    def __repr__(self):
        return f"<User {self.name}>"

# ======================
# MODELO DE HUERTO
# ======================
class Huerto(db.Model):
    __tablename__ = 'huertos'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    ubicacion = db.Column(db.String(200))
    superficie_ha = db.Column(db.Float)
    tipo_cultivo = db.Column(db.String(100))
    fecha_siembra = db.Column(db.Date)

    # Responsable principal del huerto (user técnico)
    responsable_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    responsable = db.relationship('User', back_populates='huertos_asignados')

    # Relación 1-N con bodegas y actividades
    bodegas = db.relationship('Bodega', back_populates='huerto', lazy=True)
    actividades = db.relationship(
        'ActividadHuerto',
        back_populates='huerto',
        cascade='all, delete-orphan'
    )

    def __repr__(self):
        return f"<Huerto {self.nombre}>"

# ======================
# MODELO DE BODEGA
# ======================
class Bodega(db.Model):
    __tablename__ = 'bodegas'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    ubicacion = db.Column(db.String(200))

    huerto_id = db.Column(db.Integer, db.ForeignKey('huertos.id'), nullable=False)
    huerto = db.relationship('Huerto', back_populates='bodegas')
    responsable_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # <- Agregado
    # <-

    quimicos = db.relationship('Quimico', backref='bodega', lazy=True)

    # Relación muchos a muchos con técnicos
    tecnicos_asignados = db.relationship(
        'User',
        secondary=tecnico_bodega,
        back_populates='bodegas_asignadas',
        lazy='dynamic'
    )

    def __repr__(self):
        return f"<Bodega {self.nombre}>"

# ======================
# MODELO DE QUÍMICO
# ======================
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

# ======================
# MODELO DE ACTIVIDAD DE HUERTO (registro de controles, históricos, plagas, etc)
# ======================
class ActividadHuerto(db.Model):
    __tablename__ = 'actividad_huerto'

    id = db.Column(db.Integer, primary_key=True)
    huerto_id = db.Column(db.Integer, db.ForeignKey('huertos.id'), nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    tipo = db.Column(db.String(50))  # Ej: 'control_plagas', 'poda', etc.
    descripcion = db.Column(db.Text)
    responsable = db.Column(db.String(100))
    observaciones = db.Column(db.Text)
    producto = db.Column(db.String(100))  # Si aplica
    dosis = db.Column(db.String(50))      # Si aplica
    plaga = db.Column(db.String(100))     # Para control de plagas
    nivel_infestacion = db.Column(db.String(20)) # Bajo/Medio/Alto/%/N°/ha
    resultado = db.Column(db.Text)        # Resultado/seguimiento
    fotos = db.Column(db.String(250))     # Path a fotos, opcional

    huerto = db.relationship('Huerto', back_populates='actividades')

    # Calcula automáticamente el año desde la fecha (útil para filtros y dashboard)
    @property
    def anio(self):
        return self.fecha.year if self.fecha else None

    def __repr__(self):
        return f"<ActividadHuerto {self.tipo} {self.fecha}>"

# ======================
# MODELOS EXTRAS (puedes agregar los tuyos aquí abajo, ejemplo Recomendacion, FormularioTarea, ChecklistItem, etc)
# ======================
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

class ChecklistItem(db.Model):
    __tablename__ = 'checklist_item'
    id = db.Column(db.Integer, primary_key=True)
    descripcion = db.Column(db.String(200), nullable=False)
    realizado = db.Column(db.Boolean, default=False)
    comentario = db.Column(db.Text)
    formulario_id = db.Column(db.Integer, db.ForeignKey('formulario_tarea.id'))

    def __repr__(self):
        return f"<ChecklistItem {self.id} - {self.descripcion}>"

