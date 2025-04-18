from . import db
from flask_login import UserMixin
from datetime import datetime

# Definición de la clase User

class TimestampMixin:
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class User(db.Model, UserMixin, TimestampMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # "admin", "tecnico"

    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    creador = db.relationship('User', remote_side=[id], backref='tecnicos_creados')

    # Relación con bodegas usando back_populates para evitar conflictos
    bodegas = db.relationship('Bodega', back_populates='responsable', lazy=True)

    def __repr__(self):
        return f"<User {self.name}>"

# Definición de la clase Huerto
class Huerto(db.Model):
    __tablename__ = 'huertos'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    ubicacion = db.Column(db.String(200))
    superficie_ha = db.Column(db.Float)
    tipo_cultivo = db.Column(db.String(100))
    fecha_siembra = db.Column(db.Date)
    responsable_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    responsable = db.relationship('User', backref='huertos_asignados')
    # Usamos back_populates en vez de backref para evitar conflicto con Bodega
    bodegas = db.relationship('Bodega', back_populates='huerto', lazy=True)

    def __repr__(self):
        return f"<Huerto {self.nombre}>"

# Definición de la clase Recomendacion
class Recomendacion(db.Model):
    __tablename__ = 'recomendacion'

    id = db.Column(db.Integer, primary_key=True)  # Clave primaria requerida
    contenido = db.Column(db.Text, nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

    categoria = db.Column(db.String(100))  # Ej: "Riego", "Fertilización"
    estado = db.Column(db.String(20), default="pendiente")
    adjunto = db.Column(db.String(200))  # Nombre del archivo adjunto, si existe

    tecnico_id = db.Column(db.Integer, db.ForeignKey('users.id'))  # Referencia a 'users.id'
    autor_id = db.Column(db.Integer, db.ForeignKey('users.id'))    # Referencia a 'users.id'

    tecnico = db.relationship('User', foreign_keys=[tecnico_id])
    autor = db.relationship('User', foreign_keys=[autor_id])

    def __repr__(self):
        return f"<Recomendacion {self.id}>"

# Definición de la clase Quimico
class Quimico(db.Model):
    __tablename__ = 'quimico'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    tipo = db.Column(db.String(50))  # ej: Herbicida, Insecticida
    descripcion = db.Column(db.Text)
    fecha_ingreso = db.Column(db.Date)
    cantidad_litros = db.Column(db.Float)

    bodega_id = db.Column(db.Integer, db.ForeignKey('bodegas.id'))  # Referencia a 'bodegas.id'
    bodega = db.relationship('Bodega', backref='quimicos')

    def __repr__(self):
        return f"<Quimico {self.nombre}>"

# Definición de la clase FormularioTarea
class FormularioTarea(db.Model):
    __tablename__ = 'formulario_tarea'

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(150), nullable=False)
    descripcion = db.Column(db.Text)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    estado = db.Column(db.String(20), default="pendiente")  # pendiente, completado, rechazado

    tecnico_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    huerto_id = db.Column(db.Integer, db.ForeignKey('huertos.id'))
    bodega_id = db.Column(db.Integer, db.ForeignKey('bodegas.id'))  # Clave foránea a Bodega

    tecnico = db.relationship('User', foreign_keys=[tecnico_id])
    huerto = db.relationship('Huerto')
    bodega = db.relationship('Bodega')
    checklist_items = db.relationship('ChecklistItem', backref='formulario', cascade="all, delete-orphan")

    def __repr__(self):
        return f"<FormularioTarea {self.id}>"

# Definición de la clase ChecklistItem
class ChecklistItem(db.Model):
    __tablename__ = 'checklist_item'

    id = db.Column(db.Integer, primary_key=True)
    descripcion = db.Column(db.String(200), nullable=False)
    realizado = db.Column(db.Boolean, default=False)
    comentario = db.Column(db.Text)

    formulario_id = db.Column(db.Integer, db.ForeignKey('formulario_tarea.id'))

# Definición de la clase Bodega
class Bodega(db.Model):
    __tablename__ = 'bodegas'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))
    ubicacion = db.Column(db.String(100))

    responsable_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    # Definimos la relación con back_populates para evitar duplicidad en el mapper
    responsable = db.relationship('User', back_populates='bodegas', lazy=True)

    huerto_id = db.Column(db.Integer, db.ForeignKey('huertos.id'), nullable=False)
    # Usamos back_populates también en la relación con Huerto
    huerto = db.relationship('Huerto', back_populates='bodegas')

    def __repr__(self):
        return f"<Bodega {self.nombre}>"
    




    
