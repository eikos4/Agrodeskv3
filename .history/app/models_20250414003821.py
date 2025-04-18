from . import db
from flask_login import UserMixin
from datetime import datetime



class Recomendacion(db.Model):
    __tablename__ = 'recomendacion'

    id = db.Column(db.Integer, primary_key=True)  # 🔥 Clave primaria requerida
    contenido = db.Column(db.Text, nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

    categoria = db.Column(db.String(100))        # Ej: "Riego", "Fertilización"
    estado = db.Column(db.String(20), default="pendiente")
    adjunto = db.Column(db.String(200))          # Nombre del archivo adjunto, si existe

    tecnico_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    autor_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    tecnico = db.relationship('User', foreign_keys=[tecnico_id])
    autor = db.relationship('User', foreign_keys=[autor_id])




class Quimico(db.Model):
    __tablename__ = 'quimico'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    tipo = db.Column(db.String(50))  # ej: Herbicida, Insecticida
    descripcion = db.Column(db.Text)
    fecha_ingreso = db.Column(db.Date)
    cantidad_litros = db.Column(db.Float)

    bodega_id = db.Column(db.Integer, db.ForeignKey('bodega.id'))
    bodega = db.relationship('Bodega', backref='quimicos')


class FormularioTarea(db.Model):
    __tablename__ = 'formulario_tarea'

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(150), nullable=False)
    descripcion = db.Column(db.Text)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    estado = db.Column(db.String(20), default="pendiente")  # pendiente, completado, rechazado

    tecnico_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    huerto_id = db.Column(db.Integer, db.ForeignKey('huerto.id'))
    bodega_id = db.Column(db.Integer, db.ForeignKey('bodega.id'))

    tecnico = db.relationship('User', foreign_keys=[tecnico_id])
    huerto = db.relationship('Huerto')
    bodega = db.relationship('Bodega')

    checklist_items = db.relationship('ChecklistItem', backref='formulario', cascade="all, delete-orphan")



class ChecklistItem(db.Model):
    __tablename__ = 'checklist_item'

    id = db.Column(db.Integer, primary_key=True)
    descripcion = db.Column(db.String(200), nullable=False)
    realizado = db.Column(db.Boolean, default=False)
    comentario = db.Column(db.Text)

    formulario_id = db.Column(db.Integer, db.ForeignKey('formulario_tarea.id'))

