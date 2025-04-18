from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

from flask_migrate import Migrate

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    from app.models import User  # Importar aquí para evitar ciclos
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # ✅ REGISTRO DE BLUEPRINTS
    from .routes.auth import auth_bp
    from .routes.admin import admin_bp
    from .routes.tecnico import tecnico_bp # type: ignore
    from .routes.main import main_bp  # Asegúrate de tener este también
   

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(tecnico_bp)
    app.register_blueprint(main_bp)
   

    return app
