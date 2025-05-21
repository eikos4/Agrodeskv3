# app/forms.py

from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, TextAreaField, FloatField,
    DateField, BooleanField, FieldList, FormField, SubmitField
)
from wtforms.validators import (
    DataRequired, InputRequired, Email, Length,
    NumberRange
)
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from yourapp.models import Technician, Huerto, Bodega, Quimico  # ajusta import

class BaseForm(FlaskForm):
    class Meta:
        csrf = True
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self._fields.values():
            if hasattr(field, 'render_kw'):
                field.render_kw = {**field.render_kw, 'class': 'form-control'}

class LoginForm(BaseForm):
    email = StringField(
        "Email",
        validators=[InputRequired(), Email()],
        render_kw={'placeholder': 'usuario@ejemplo.com'}
    )
    password = PasswordField(
        "Contraseña",
        validators=[InputRequired()],
        render_kw={'placeholder': '*******'}
    )
    submit = SubmitField("Iniciar Sesión", render_kw={'class':'btn btn-primary'})

class CreateTechnicianForm(BaseForm):
    name = StringField("Nombre", validators=[InputRequired()])
    email = StringField("Email", validators=[Email()])
    password = PasswordField("Contraseña", validators=[InputRequired(), Length(min=6)])
    submit = SubmitField("Crear Técnico", render_kw={'class':'btn btn-success'})

class CrearHuertoForm(BaseForm):
    nombre = StringField("Nombre", validators=[DataRequired()])
    ubicacion = StringField("Ubicación", validators=[DataRequired()])
    superficie_ha = FloatField(
        "Superficie (ha)",
        validators=[DataRequired(), NumberRange(min=0.1)]
    )
    tipo_cultivo = StringField("Tipo de cultivo", validators=[DataRequired()])
    fecha_siembra = DateField(
        "Fecha de siembra",
        format='%Y-%m-%d',
        validators=[DataRequired()],
        render_kw={'type':'date'}
    )
    responsable = QuerySelectField(
        "Técnico responsable",
        query_factory=lambda: Technician.query.all(),
        get_label="name",
        allow_blank=False
    )
    submit = SubmitField("Guardar", render_kw={'class':'btn btn-primary'})

class BodegaForm(BaseForm):
    nombre = StringField("Nombre de la Bodega", validators=[DataRequired()])
    ubicacion = StringField("Ubicación")
    huerto = QuerySelectField(
        "Huerto asociado",
        query_factory=lambda: Huerto.query.all(),
        get_label="nombre",
        allow_blank=False
    )
    responsable = QuerySelectField(
        "Responsable (opcional)",
        query_factory=lambda: Technician.query.all(),
        get_label="name",
        allow_blank=True
    )
    submit = SubmitField("Guardar Bodega", render_kw={'class':'btn btn-primary'})

class QuimicoForm(BaseForm):
    nombre = StringField("Nombre del Químico", validators=[DataRequired()])
    tipo = SelectField(
        "Tipo de Químico",
        choices=[
            ("herbicida", "Herbicida"),
            ("fungicida", "Fungicida"),
            ("insecticida", "Insecticida"),
            ("fertilizante", "Fertilizante"),
            ("otro", "Otro")
        ],
        validators=[DataRequired()]
    )
    descripcion = TextAreaField("Descripción")
    fecha_ingreso = DateField(
        "Fecha de Ingreso",
        format='%Y-%m-%d',
        validators=[DataRequired()],
        render_kw={'type':'date'}
    )
    cantidad_litros = FloatField(
        "Cantidad (L)",
        validators=[DataRequired(), NumberRange(min=0.01)]
    )
    submit = SubmitField("Guardar Químico", render_kw={'class':'btn btn-primary'})

class ChecklistItemForm(BaseForm):
    descripcion = StringField("Actividad", render_kw={'readonly': True})
    realizado = BooleanField("Realizado", render_kw={'class':'form-check-input'})
    comentario = TextAreaField("Comentario (opcional)")

class ResponderFormularioForm(BaseForm):
    items = FieldList(FormField(ChecklistItemForm), min_entries=1)
    submit = SubmitField("Enviar Respuesta", render_kw={'class':'btn btn-success'})
