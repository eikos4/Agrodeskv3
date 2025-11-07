# app/forms.py
from flask_wtf import FlaskForm
from flask_wtf.file import FileField as FileUploadField, FileAllowed, FileRequired

from wtforms import (
    StringField, PasswordField, SubmitField, TextAreaField, SelectField,
    FloatField, DateField, BooleanField, FieldList, FormField, HiddenField,
    IntegerField
)
from wtforms.validators import (
    InputRequired, Email, Length, DataRequired, Optional, EqualTo
)
from app.models import Empresa


def _norm(s: str) -> str:
    return (s or "").strip().lower()

class LoginForm(FlaskForm):
    # Cambia a SelectField
    empresa = SelectField(
        "Empresa",
        validators=[DataRequired(message="Selecciona tu empresa.")],
        choices=[],                           # se llena en __init__
        render_kw={"placeholder": "Selecciona tu empresa"}
    )
    email = StringField(
        "Email",
        validators=[DataRequired(message="Ingresa tu correo."), Email(), Length(max=150)],
        filters=[_norm],
        render_kw={"placeholder": "tu@correo.com"}
    )
    password = PasswordField(
        "Contraseña",
        validators=[DataRequired(message="Ingresa tu contraseña."), Length(min=6, max=128)],
        render_kw={"placeholder": "••••••••"}
    )
    remember = BooleanField("Recordarme")
    submit = SubmitField("Iniciar Sesión")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Cargar empresas ordenadas (value=slug, label=nombre)
        empresas = Empresa.query.order_by(Empresa.nombre.asc()).all()
        self.empresa.choices = [(e.slug, e.nombre) for e in empresas]

        # Si hay solo una empresa, pré-selecciona
        if len(self.empresa.choices) == 1:
            self.empresa.data = self.empresa.choices[0][0]


# --- CREAR TÉCNICO ---
class CreateTechnicianForm(FlaskForm):
    name = StringField("Nombre", validators=[InputRequired()])
    email = StringField("Email", validators=[Email()])
    password = PasswordField("Contraseña", validators=[InputRequired(), Length(min=6)])
    submit = SubmitField("Crear Técnico")


# --- RECOMENDACIÓN ---
class AsignarRecomendacionForm(FlaskForm):
    tecnico_id = SelectField("Técnico", coerce=int, validators=[DataRequired()])
    contenido = TextAreaField("Recomendación", validators=[DataRequired(), Length(min=5, max=2000)])
    submit = SubmitField("Enviar")

# Alias retrocompatible
RecommendationForm = AsignarRecomendacionForm


# --- HUERTO ---
class CrearHuertoForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired()])
    ubicacion = StringField('Ubicación', validators=[DataRequired()])
    superficie_ha = FloatField('Superficie (ha)', validators=[DataRequired()])
    tipo_cultivo = StringField('Tipo de cultivo', validators=[DataRequired()])
    fecha_siembra = DateField('Fecha de siembra', validators=[DataRequired()])
    # 0 = “Sin asignar” (se maneja en la vista)
    responsable_id = SelectField('Técnico responsable', coerce=int, validators=[Optional()])
    submit = SubmitField('Guardar')


# --- BODEGA ---
class BodegaForm(FlaskForm):
    nombre = StringField("Nombre de la Bodega", validators=[DataRequired()])
    ubicacion = StringField("Ubicación")
    huerto_id = SelectField("Huerto asociado", coerce=int, validators=[DataRequired()])
    # Permitimos 0 (“Sin asignar”)
    responsable_id = SelectField("Responsable (opcional)", coerce=int, validate_choice=False)
    submit = SubmitField("Guardar Bodega")


# --- QUÍMICO ---
class QuimicoForm(FlaskForm):
    nombre = StringField("Nombre del Químico", validators=[DataRequired()])
    tipo = SelectField(
        "Tipo de Químico",
        choices=[
            ("herbicida", "Herbicida"),
            ("fungicida", "Fungicida"),
            ("insecticida", "Insecticida"),
            ("fertilizante", "Fertilizante"),
            ("otro", "Otro"),
        ],
        validators=[DataRequired()]
    )
    descripcion = TextAreaField("Descripción")
    fecha_ingreso = DateField("Fecha de Ingreso", validators=[DataRequired()])
    cantidad_litros = FloatField("Cantidad (L)", validators=[DataRequired()])
    submit = SubmitField("Guardar Químico")


# --- CHECKLIST FORMULARIOS TÉCNICOS ---
class ChecklistItemForm(FlaskForm):
    descripcion = StringField("Actividad", render_kw={'readonly': True})
    realizado = BooleanField("Realizado")
    comentario = TextAreaField("Comentario (opcional)")


class ResponderFormularioForm(FlaskForm):
    items = FieldList(FormField(ChecklistItemForm), min_entries=1)
    submit = SubmitField("Enviar Respuesta")


# --- FORMULARIO REGISTRO ACTIVIDAD DE HUERTO ---
class RegistrarActividadForm(FlaskForm):
    fecha = DateField('Fecha', validators=[DataRequired()])
    tipo = SelectField(
        'Tipo de Actividad',
        choices=[
            ('control_plagas', 'Control de Plagas'),
            ('poda', 'Poda'),
            ('riego', 'Riego'),
            ('fertilizacion', 'Fertilización'),
            ('cosecha', 'Cosecha'),
            ('otra', 'Otra')
        ],
        validators=[DataRequired()]
    )
    descripcion = TextAreaField('Descripción', validators=[DataRequired()])
    responsable = StringField('Responsable', validators=[Optional()])
    plaga = StringField('Plaga/Enfermedad', validators=[Optional()])
    nivel_infestacion = StringField('Nivel de Infestación', validators=[Optional()])
    producto = StringField('Producto Aplicado', validators=[Optional()])
    dosis = StringField('Dosis Aplicada', validators=[Optional()])
    resultado = TextAreaField('Resultado/Seguimiento', validators=[Optional()])
    fotos = FileUploadField('Fotos', validators=[Optional()])
    observaciones = TextAreaField('Observaciones', validators=[Optional()])
    anio = IntegerField('Año de la actividad', validators=[Optional()])
    submit = SubmitField('Registrar Actividad')


# --- PARCELAS / GEO ---
class ParcelaForm(FlaskForm):
    nombre = StringField("Nombre de parcela", validators=[DataRequired()])
    huerto_id = SelectField("Huerto", coerce=int, validators=[DataRequired()])
    geom_geojson = HiddenField("GeoJSON", validators=[Optional()])
    submit = SubmitField("Guardar Parcela")


class ActividadForm(FlaskForm):
    huerto_id = SelectField("Huerto", coerce=int, validators=[DataRequired()])
    parcela_id = SelectField("Parcela", coerce=int, validators=[Optional()])
    tipo = StringField("Tipo", validators=[DataRequired()])
    descripcion = TextAreaField("Descripción", validators=[Optional()])
    lat = FloatField("Lat", validators=[Optional()])
    lng = FloatField("Lng", validators=[Optional()])
    ruta_geojson = HiddenField("Ruta/Área (GeoJSON)", validators=[Optional()])
    duracion_min = IntegerField("Duración (min)", default=0)
    submit = SubmitField("Registrar")


# --- DOCUMENTOS ---
class DocumentoForm(FlaskForm):
    titulo = StringField("Título", validators=[DataRequired()])
    categoria = StringField("Categoría", validators=[Optional()])
    huerto_id = SelectField("Huerto", coerce=int, validators=[Optional()])  # 0 = general si así lo manejas
    archivo = FileUploadField(
        "Archivo",
        validators=[
            FileRequired(),
            FileAllowed(["pdf", "png", "jpg", "jpeg", "doc", "docx", "xlsx"], "Formato no permitido"),
        ],
    )
    submit = SubmitField("Subir documento")


# --- TIPOS DE ACTIVIDAD (catálogo del mapa/bitácora) ---
class ActivityTypeForm(FlaskForm):
    key = StringField("Clave", validators=[DataRequired()])                 # ej: riego, poda
    nombre = StringField("Nombre", validators=[DataRequired()])             # ej: Riego
    color = StringField("Color (hex)", validators=[DataRequired()])         # ej: #198754
    fill_color = StringField("Relleno (hex)", validators=[Optional()])      # ej: #19875433
    icon = StringField("Icono (Bootstrap Icons)", validators=[DataRequired()])  # ej: bi-water
    submit = SubmitField("Guardar")


# --- RESET PASSWORD (admin -> técnico) ---
class ResetPasswordForm(FlaskForm):
    password = PasswordField(
        "Nueva contraseña",
        validators=[InputRequired(), Length(min=6, message="Mínimo 6 caracteres")]
    )
    confirm = PasswordField(
        "Confirmar contraseña",
        validators=[InputRequired(), EqualTo("password", message="Las contraseñas no coinciden")]
    )
    submit = SubmitField("Actualizar contraseña")
