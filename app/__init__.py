from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from flask_migrate import Migrate

# Inicialización de extensiones
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()

def create_app():
    app = Flask(__name__)

    # Cargar configuración desde config.py (asegúrate que existe 'Config' en config.py)
    app.config.from_object('config.Config')

    # Inicializar extensiones
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    # Configuración del Login Manager
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "info"

    # Cargar modelos después de inicializar extensiones para evitar errores circulares
    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Registrar Blueprints
    from .routes.auth import auth_bp
    from .routes.admin import admin_bp
    from .routes.tecnico import tecnico_bp
    from .routes.main import main_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(tecnico_bp)
    app.register_blueprint(main_bp)

    # Inyectar usuario actual en todas las plantillas
    @app.context_processor
    def inject_user():
        return dict(user=current_user)

    # Manejadores de errores personalizados
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template("500.html"), 500

    return app
