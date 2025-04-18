



# Mixin para incluir marcas de tiempo
class TimestampMixin:
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)







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
