from src.routes.auth_routes import auth_bp
from src.routes.category_routes import category_bp
from src.routes.report_routes import report_bp
from src.routes.system_routes import system_bp
from src.routes.task_routes import task_bp
from src.routes.user_routes import user_bp

BLUEPRINTS = (system_bp, auth_bp, task_bp, user_bp, category_bp, report_bp)


def register_routes(app):
    for blueprint in BLUEPRINTS:
        app.register_blueprint(blueprint)
