# app/__init__.py
from flask import Flask, render_template, g, session
from flask_login import LoginManager
from flask_migrate import Migrate
from app.extensions import db

def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")

    # === Extensiones ===
    db.init_app(app)
    migrate = Migrate()
    migrate.init_app(app, db)

    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "info"
    login_manager.init_app(app)

    # Importa modelos (registra relaciones y hooks)
    with app.app_context():
        from app import models  # noqa: F401

    # === Autenticación ===
    @login_manager.user_loader
    def load_user(user_id: str):
        from app.models import User
        return User.query.get(int(user_id))

    # === Multi-empresa (tenant) ===
    @app.before_request
    def load_tenant():
        from app.models import Empresa
        eid = session.get("empresa_id")
        g.empresa = Empresa.query.get(eid) if eid else None

    # === Estilos para tipos de actividad (opcional) ===
    @app.context_processor
    def inject_activity_styles():
        styles = {}
        try:
            # Si existe el modelo ActivityType, lo usamos; si no, fallback
            from app.models import ActivityType  # type: ignore
            tipos = ActivityType.query.all()
            for t in tipos:
                styles[t.key] = {
                    "color": t.color,
                    "fill": t.fill_color or f"{t.color}33",
                    "icon": t.icon,
                    "nombre": t.nombre,
                }
        except Exception:
            pass

        styles.setdefault(
            "otra",
            {"color": "#6c757d", "fill": "#6c757d33", "icon": "bi-gear", "nombre": "Otra"},
        )
        return dict(activity_styles=styles)

    # === Blueprints ===
    from app.routes.auth import auth_bp
    from app.routes.admin import admin_bp
    from app.routes.tecnico import tecnico_bp
    from app.routes.main import main_bp
    from app.routes.docs import docs_bp
    from app.routes.geo import geo_bp
    from app.routes.geo_admin import geo_admin_bp, geo_types_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(tecnico_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(docs_bp)
    app.register_blueprint(geo_bp)
    app.register_blueprint(geo_admin_bp)
    app.register_blueprint(geo_types_bp)

    # === Errores ===
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template("500.html"), 500

    return app
