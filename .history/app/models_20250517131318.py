from app import db
from flask_login import UserMixin
from datetime import datetime

# Tabla de asociación muchos a muchos entre técnicos y bodegas
tecnico_bodega = db.Table(
    'tecnico_bodega',
    db.Column('tecnico_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('bodega_id', db.Integer, db.ForeignKey('bodegas.id'))
)

# -------------------------------
# Mixin para incluir marcas de tiempo
# -------------------------------
class TimestampMixin:
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# -------------------------------
# MODELO DE USUARIO
# -------------------------------
class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # "admin" o "tecnico"
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    creador = db.relationship('User', remote_side=[id], backref='tecnicos_creados')

    # Relación con huertos asignados (como responsable)
    huertos_asignados = db.relationship('Huerto', back_populates='responsable', lazy=True)

    # Relación muchos a muchos con bodegas asignadas
    bodegas_asignadas = db.relationship(
        'Bodega',
        secondary=tecnico_bodega,
        back_populates='tecnicos_asignados',
        lazy='dynamic'
    )

    def __repr__(self):
        return f"<User {self.name}>"

# -------------------------------
# MODELO DE HUERTO
# -------------------------------
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

    # Relación con bodegas del huerto
    bodegas = db.relationship('Bodega', back_populates='huerto', lazy=True)

    # Relación con actividades del huerto
    actividades = db.relationship('ActividadHuerto', back_populates='huerto', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Huerto {self.nombre}>"

# -------------------------------
# MODELO DE BODEGA
# -------------------------------
class Bodega(db.Model):
    __tablename__ = 'bodegas'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    ubicacion = db.Column(db.String(200))
    huerto_id = db.Column(db.Integer, db.ForeignKey('huertos.id'), nullable=False)
    huerto = db.relationship('Huerto', back_populates='bodegas')

    # Relación con químicos
    quimicos = db.relationship('Quimico', backref='bodega', lazy=True)

    # Relación con técnicos asignados (muchos a muchos)
    tecnicos_asignados = db.relationship(
        'User',
        secondary=tecnico_bodega,
        back_populates='bodegas_asignadas',
        lazy='dynamic'
    )

    def __repr__(self):
        return f"<Bodega {self.nombre}>"

# -------------------------------
# MODELO DE QUÍMICO
# -------------------------------
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

# -------------------------------
# MODELO DE ACTIVIDAD DE HUERTO
# -------------------------------
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

    # Relación a Huerto, bien definida
    huerto = db.relationship('Huerto', back_populates='actividades')

    @property
    def anio(self):
        return self.fecha.year if self.fecha else None

    def __repr__(self):
        return f"<ActividadHuerto {self.tipo} {self.fecha}>"

# Modelo de Recomendación
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


# Modelo de Formulario de Tarea
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

# Modelo de Item de Checklist
class ChecklistItem(db.Model):
    __tablename__ = 'checklist_item'

    id = db.Column(db.Integer, primary_key=True)
    descripcion = db.Column(db.String(200), nullable=False)
    realizado = db.Column(db.Boolean, default=False)
    comentario = db.Column(db.Text)

    formulario_id = db.Column(db.Integer, db.ForeignKey('formulario_tarea.id'))



