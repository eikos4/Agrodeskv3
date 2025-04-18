from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
import os

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    
    # Cargar la configuración del objeto Config definido en config.py.
    # Se recomienda usar variables de entorno para datos sensibles.
    app.config.from_object('config.Config')
    
    # Inicializar extensiones
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    # Configurar el login manager
    login_manager.login_view = "auth.login"        # Ruta o endpoint de la página de login
    login_manager.login_message_category = "info"   # Categoría para mensajes flash

    # Importar los modelos después de inicializar las extensiones para evitar ciclos
    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Registro de Blueprints
    from .routes.auth import auth_bp
    from .routes.admin import admin_bp
    from .routes.tecnico import tecnico_bp  # type: ignore
    from .routes.main import main_bp
    from flask_login import current_user

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(tecnico_bp)
    app.register_blueprint(main_bp)

    # Registro de manejadores de errores personalizados
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template("404.html"), 404
    
    @app.context_processor
    def inject_user():
        return dict(user=current_user)


    @app.errorhandler(500)
    def internal_error(error):
        # Rollback de la sesión si ocurre un error interno para evitar bloqueos de transacciones
        db.session.rollback()
        return render_template("500.html"), 500

    return app
