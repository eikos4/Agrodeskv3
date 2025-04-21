# 🌿 AgroCLOUD

**AgroCLOUD** es un sistema web de gestión agrícola diseñado para ingenieros agrónomos, técnicos y administradores de campo. La plataforma permite registrar, visualizar y administrar información sobre huertos, bodegas, químicos y recomendaciones técnicas, optimizando las operaciones en terreno.

---

## 🛠️ Tecnologías utilizadas

- **Python 3.11+**
- **Flask**
- **Flask-Login**
- **Flask-Migrate**
- **SQLAlchemy**
- **Bootstrap 5**
- **SQLite** (modo local, puede migrar fácilmente a PostgreSQL)

---

## 🗂️ Estructura del proyecto

```
AgroCLOUD/
│
├── app/
│   ├── __init__.py            # Configuración principal Flask
│   ├── models.py              # Modelos SQLAlchemy
│   ├── routes/                # Blueprints (admin, tecnico, auth, main)
│   ├── templates/             # HTML con Jinja2
│   └── forms.py               # Formularios WTForms
│
├── migrations/                # Archivos de migración de la DB
├── static/                    # Archivos estáticos (CSS, JS, imágenes)
├── config.py                  # Configuración general de Flask
├── requirements.txt           # Dependencias del proyecto
└── run.py                     # Script principal para iniciar la app
```

---

## 🚀 Instrucciones de instalación

1. **Clonar el repositorio**

```bash
git clone https://github.com/tu-usuario/AgroCLOUD.git
cd AgroCLOUD
```

2. **Crear entorno virtual**

```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

3. **Instalar dependencias**

```bash
pip install -r requirements.txt
```

4. **Configurar la base de datos**

```bash
flask db init
flask db migrate -m "Inicial"
flask db upgrade
```

5. **Ejecutar la aplicación**

```bash
flask run
```

---

## 👨‍🌾 Funcionalidades

- Registro y login con control de roles (`admin`, `tecnico`)
- Panel administrativo con gestión de técnicos, huertos, bodegas y químicos
- Panel técnico con acceso a recomendaciones personalizadas y formularios
- Asociación entre técnicos, huertos y bodegas
- Inventario en tiempo real de químicos por bodega

---

## 📸 Capturas de pantalla (opcional)

_Añade imágenes de tu sistema aquí para mostrar la interfaz_

---

## 📄 Licencia

MIT © 2025 — AgroCLOUD