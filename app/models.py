# app/models.py
from datetime import datetime, date
from flask_login import UserMixin
from app.extensions import db
from sqlalchemy import Float, Text, Boolean, UniqueConstraint, select, event
from sqlalchemy.orm import relationship, declarative_mixin, declared_attr

# ==============================
# EMPRESA
# ==============================
class Empresa(db.Model):
    __tablename__ = "empresas"
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    slug = db.Column(db.String(80), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Empresa {self.id} {self.nombre!r}>"

# ==============================
# Mixin multiempresa
# ==============================
@declarative_mixin
class TenantMixin:
    @declared_attr
    def empresa_id(cls):
        return db.Column(db.Integer, db.ForeignKey("empresas.id"), nullable=False, index=True)

    @declared_attr
    def empresa(cls):
        return db.relationship("Empresa")

# ==============================
# Asociación muchos-a-muchos: Técnicos <-> Bodegas
# ==============================
tecnico_bodega = db.Table(
    "tecnico_bodega",
    db.Column("tecnico_id", db.Integer, db.ForeignKey("users.id"), primary_key=True),
    db.Column("bodega_id", db.Integer, db.ForeignKey("bodegas.id"), primary_key=True),
)

# ==============================
# USUARIO
# ==============================
class User(db.Model, UserMixin, TenantMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), nullable=False, index=True)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False, index=True)  # "admin" | "tecnico"
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"))

    __table_args__ = (
        UniqueConstraint("empresa_id", "email", name="uq_user_email_empresa"),
    )

    creador = db.relationship("User", remote_side=[id], backref="tecnicos_creados")
    huertos_asignados = db.relationship("Huerto", back_populates="responsable", lazy=True)
    bodegas_asignadas = db.relationship(
        "Bodega",
        secondary=tecnico_bodega,
        back_populates="tecnicos_asignados",
        lazy="dynamic",
    )

    def __repr__(self):
        return f"<User {self.id} {self.email!r} ({self.role})>"

# ==============================
# HUERTO
# ==============================
class Huerto(db.Model, TenantMixin):
    __tablename__ = "huertos"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    ubicacion = db.Column(db.String(200))
    superficie_ha = db.Column(db.Float)
    tipo_cultivo = db.Column(db.String(120))
    fecha_siembra = db.Column(db.Date)

    responsable_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    responsable = db.relationship("User", back_populates="huertos_asignados")

    center_lat = db.Column(Float)
    center_lng = db.Column(Float)
    bounds_geojson = db.Column(Text)

    bodegas = db.relationship("Bodega", back_populates="huerto", lazy=True)
    actividades_huerto = db.relationship(
        "ActividadHuerto", back_populates="huerto", cascade="all, delete-orphan", lazy=True
    )
    parcelas = db.relationship("Parcela", back_populates="huerto", cascade="all, delete-orphan", lazy=True)
    actividades_geo = db.relationship("ActividadCampo", back_populates="huerto", cascade="all, delete-orphan", lazy=True)

    def __repr__(self):
        return f"<Huerto {self.id} {self.nombre!r}>"

# ==============================
# BODEGA
# ==============================
class Bodega(db.Model, TenantMixin):
    __tablename__ = "bodegas"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    ubicacion = db.Column(db.String(200))

    huerto_id = db.Column(db.Integer, db.ForeignKey("huertos.id"), nullable=False)
    huerto = db.relationship("Huerto", back_populates="bodegas")

    responsable_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    responsable = db.relationship("User", foreign_keys=[responsable_id])

    quimicos = db.relationship("Quimico", backref="bodega", lazy=True)

    tecnicos_asignados = db.relationship(
        "User",
        secondary=tecnico_bodega,
        back_populates="bodegas_asignadas",
        lazy="dynamic",
    )

    def __repr__(self):
        return f"<Bodega {self.id} {self.nombre!r}>"

# ==============================
# QUÍMICO
# ==============================
class Quimico(db.Model, TenantMixin):
    __tablename__ = "quimicos"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    tipo = db.Column(db.String(50))
    descripcion = db.Column(db.Text)
    cantidad_litros = db.Column(db.Float)
    fecha_ingreso = db.Column(db.Date)

    bodega_id = db.Column(db.Integer, db.ForeignKey("bodegas.id"), nullable=False)

    def __repr__(self):
        return f"<Quimico {self.id} {self.nombre!r}>"

# ==============================
# ACTIVIDAD DE HUERTO
# ==============================
class ActividadHuerto(db.Model, TenantMixin):
    __tablename__ = "actividad_huerto"

    id = db.Column(db.Integer, primary_key=True)
    huerto_id = db.Column(db.Integer, db.ForeignKey("huertos.id"), nullable=False, index=True)

    fecha = db.Column(db.Date, nullable=False, default=date.today)
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

    huerto = db.relationship("Huerto", back_populates="actividades_huerto")

    @property
    def anio(self):
        return self.fecha.year if self.fecha else None

    def __repr__(self):
        return f"<ActividadHuerto {self.id} huerto={self.huerto_id} tipo={self.tipo!r}>"

# ==============================
# RECOMENDACIÓN
# ==============================
class Recomendacion(db.Model, TenantMixin):
    __tablename__ = "recomendacion"

    id = db.Column(db.Integer, primary_key=True)
    contenido = db.Column(db.Text, nullable=False)
    fecha = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    categoria = db.Column(db.String(100))
    estado = db.Column(db.String(20), default="pendiente")
    adjunto = db.Column(db.String(200))

    tecnico_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    autor_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    huerto_id = db.Column(db.Integer, db.ForeignKey("huertos.id"), index=True)

    tecnico = db.relationship("User", foreign_keys=[tecnico_id], backref="recomendaciones_asignadas")
    autor = db.relationship("User", foreign_keys=[autor_id], backref="recomendaciones_creadas")
    huerto = db.relationship("Huerto", backref="recomendaciones")

    def __repr__(self):
        return f"<Recomendacion {self.id}>"

# ==============================
# FORMULARIO DE TAREA / CHECKLIST
# ==============================
class FormularioTarea(db.Model, TenantMixin):
    __tablename__ = "formulario_tarea"

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(150), nullable=False)
    descripcion = db.Column(db.Text)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    estado = db.Column(db.String(20), default="pendiente")

    tecnico_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    huerto_id = db.Column(db.Integer, db.ForeignKey("huertos.id"))
    bodega_id = db.Column(db.Integer, db.ForeignKey("bodegas.id"))

    tecnico = db.relationship("User", foreign_keys=[tecnico_id])
    huerto = db.relationship("Huerto")
    bodega = db.relationship("Bodega")

    checklist_items = db.relationship("ChecklistItem", backref="formulario", cascade="all, delete-orphan", lazy=True)

    def __repr__(self):
        return f"<FormularioTarea {self.id}>"

class ChecklistItem(db.Model):
    __tablename__ = "checklist_item"

    id = db.Column(db.Integer, primary_key=True)
    descripcion = db.Column(db.String(200), nullable=False)
    realizado = db.Column(Boolean, default=False)
    comentario = db.Column(db.Text)

    formulario_id = db.Column(db.Integer, db.ForeignKey("formulario_tarea.id"))

    def __repr__(self):
        return f"<ChecklistItem {self.id} - {self.descripcion}>"

# ==============================
# AUDIO MENSAJE
# ==============================
class AudioMensaje(db.Model, TenantMixin):
    __tablename__ = "audio_mensaje"

    id = db.Column(db.Integer, primary_key=True)
    tecnico_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    archivo = db.Column(db.String(255), nullable=False)
    fecha_envio = db.Column(db.DateTime, default=datetime.utcnow)

    tecnico = db.relationship("User", backref="audios_enviados", foreign_keys=[tecnico_id])

    def __repr__(self):
        return f"<AudioMensaje {self.id} - Técnico: {self.tecnico_id}>"

# ==============================
# PARCELA / ACTIVIDAD CAMPO
# ==============================
class Parcela(db.Model, TenantMixin):
    __tablename__ = "parcelas"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    huerto_id = db.Column(db.Integer, db.ForeignKey("huertos.id"), nullable=False)
    huerto = db.relationship("Huerto", back_populates="parcelas")
    geom_geojson = db.Column(Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Parcela {self.id} {self.nombre!r}>"

class ActividadCampo(db.Model, TenantMixin):
    __tablename__ = "actividades_campo"

    id = db.Column(db.Integer, primary_key=True)
    huerto_id = db.Column(db.Integer, db.ForeignKey("huertos.id"), nullable=False)
    huerto = db.relationship("Huerto", back_populates="actividades_geo")

    parcela_id = db.Column(db.Integer, db.ForeignKey("parcelas.id"))
    parcela = db.relationship("Parcela")

    tipo = db.Column(db.String(80), nullable=False)
    descripcion = db.Column(db.String(255))
    lat = db.Column(Float)
    lng = db.Column(Float)
    ruta_geojson = db.Column(Text)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    duracion_min = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f"<ActividadCampo {self.id} {self.tipo!r}>"

# ==============================
# DOCUMENTO
# ==============================
class Documento(db.Model, TenantMixin):
    __tablename__ = "documentos"

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    mimetype = db.Column(db.String(120))
    categoria = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    huerto_id = db.Column(db.Integer, db.ForeignKey("huertos.id"))
    huerto = db.relationship("Huerto")

    subido_por_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    subido_por = db.relationship("User")

    def __repr__(self):
        return f"<Documento {self.id} {self.titulo!r}>"

# ==============================
# TIPOS DE ACTIVIDAD (para estilos)
# ==============================
class ActivityType(db.Model, TenantMixin):
    __tablename__ = "activity_type"

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), nullable=False)  # único por empresa
    nombre = db.Column(db.String(100), nullable=False)
    color = db.Column(db.String(20), nullable=False, default="#0d6efd")
    fill_color = db.Column(db.String(20))
    icon = db.Column(db.String(50), nullable=False, default="bi-gear")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("empresa_id", "key", name="uq_activity_type_empresa_key"),
    )

    def __repr__(self):
        return f"<ActivityType {self.id} {self.key!r}>"

# ==============================
# Hook: completar empresa_id en ActividadHuerto
# ==============================
@event.listens_for(ActividadHuerto, "before_insert")
def completar_empresa_id_actividad(mapper, connection, target):
    """
    Si alguien olvida setear empresa_id al crear una actividad,
    se completa automáticamente desde el huerto relacionado.
    """
    if getattr(target, "empresa_id", None):
        return
    if getattr(target, "huerto_id", None):
        empresa_id = connection.execute(
            select(Huerto.empresa_id).where(Huerto.id == target.huerto_id)
        ).scalar_one_or_none()
        if empresa_id:
            target.empresa_id = empresa_id
