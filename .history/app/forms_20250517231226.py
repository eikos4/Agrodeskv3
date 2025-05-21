from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, SelectField
from wtforms.validators import InputRequired, Email, Length

# app/forms.py

from wtforms import StringField, FloatField, DateField, SelectField, SubmitField
from wtforms.validators import DataRequired



from wtforms import StringField, BooleanField, TextAreaField, FieldList, FormField, SubmitField



   
from wtforms import StringField, TextAreaField, FloatField, SelectField, SubmitField, DateField


class CrearHuertoForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired()])
    ubicacion = StringField('Ubicación', validators=[DataRequired()])
    superficie_ha = FloatField('Superficie (ha)', validators=[DataRequired()])
    tipo_cultivo = StringField('Tipo de cultivo', validators=[DataRequired()])
    fecha_siembra = DateField('Fecha de siembra', validators=[DataRequired()])
    responsable_id = SelectField('Técnico responsable', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Guardar')



from wtforms.validators import DataRequired

class LoginForm(FlaskForm):
    email = StringField("Email", validators=[InputRequired(), Email()])
    password = PasswordField("Contraseña", validators=[InputRequired()])
    submit = SubmitField("Iniciar Sesión")

class CreateTechnicianForm(FlaskForm):
    name = StringField("Nombre", validators=[InputRequired()])
    email = StringField("Email", validators=[Email()])
    password = PasswordField("Contraseña", validators=[InputRequired(), Length(min=6)])
    submit = SubmitField("Crear Técnico")

class RecommendationForm(FlaskForm):
    contenido = TextAreaField("Contenido", validators=[InputRequired()])
    tecnico_id = SelectField("Técnico", coerce=int)
    submit = SubmitField("Asignar Recomendación")

class HuertoForm(FlaskForm):
    nombre = StringField("Nombre del Huerto", validators=[DataRequired()])
    ubicacion = StringField("Ubicación")
    superficie_ha = FloatField("Superficie (ha)")
    tipo_cultivo = StringField("Tipo de Cultivo")
    fecha_siembra = DateField("Fecha de Siembra", format='%Y-%m-%d')
    responsable_id = SelectField("Técnico Responsable", coerce=int)
    submit = SubmitField("Guardar")

class BodegaForm(FlaskForm):
    nombre = StringField("Nombre de la Bodega", validators=[DataRequired()])
    ubicacion = StringField("Ubicación")
    huerto_id = SelectField("Huerto asociado", coerce=int, validators=[DataRequired()])
    responsable_id = SelectField("Responsable (opcional)", coerce=int, validate_choice=False)
    submit = SubmitField("Guardar Bodega")


class QuimicoForm(FlaskForm):
    nombre = StringField("Nombre del Químico", validators=[DataRequired()])
    tipo = SelectField("Tipo de Químico", choices=[
        ("herbicida", "Herbicida"),
        ("fungicida", "Fungicida"),
        ("insecticida", "Insecticida"),
        ("fertilizante", "Fertilizante"),
        ("otro", "Otro")
    ], validators=[DataRequired()])
    descripcion = TextAreaField("Descripción")
    fecha_ingreso = DateField("Fecha de Ingreso", validators=[DataRequired()])
    cantidad_litros = FloatField("Cantidad (L)", validators=[DataRequired()])
    submit = SubmitField("Guardar Químico")



class ChecklistItemForm(FlaskForm):
    descripcion = StringField("Actividad", render_kw={'readonly': True})
    realizado = BooleanField("Realizado")
    comentario = TextAreaField("Comentario (opcional)")

class ResponderFormularioForm(FlaskForm):
    items = FieldList(FormField(ChecklistItemForm), min_entries=1)
    submit = SubmitField("Enviar Respuesta")


# forms.py

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, DateField, FloatField, FileField, IntegerField, SubmitField
from wtforms.validators import DataRequired, Optional

class ActividadHuertoForm(FlaskForm):
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
    responsable = StringField('Responsable', validators=[DataRequired()])
    producto = StringField('Producto Aplicado (si corresponde)', validators=[Optional()])
    dosis = StringField('Dosis Aplicada', validators=[Optional()])
    plaga = StringField('Plaga/Enfermedad Detectada', validators=[Optional()])
    nivel_infestacion = StringField('Nivel de Infestación (% o Bajo/Medio/Alto)', validators=[Optional()])
    resultado = TextAreaField('Resultado/Seguimiento', validators=[Optional()])
    fotos = FileField('Foto (opcional)', validators=[Optional()])
    observaciones = TextAreaField('Observaciones Generales', validators=[Optional()])
    anio = IntegerField('Año de la actividad', validators=[Optional()])  # normalmente lo obtienes de la fecha, pero puede ser útil para filtrar
    submit = SubmitField('Registrar Actividad')



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
    # Campos adicionales para control de plagas o actividad específica:
    plaga = StringField('Plaga/Enfermedad', validators=[Optional()])
    nivel_infestacion = StringField('Nivel de Infestación', validators=[Optional()])
    producto = StringField('Producto Aplicado', validators=[Optional()])
    dosis = StringField('Dosis Aplicada', validators=[Optional()])
    resultado = TextAreaField('Resultado/Seguimiento', validators=[Optional()])
    fotos = FileField('Fotos', validators=[Optional()])
    observaciones = TextAreaField('Observaciones', validators=[Optional()])