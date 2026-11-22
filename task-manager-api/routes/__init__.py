from routes.category_routes import category_bp
from routes.health_routes import health_bp
from routes.report_routes import report_bp
from routes.task_routes import task_bp
from routes.user_routes import user_bp


def register_routes(app):
    for blueprint in (health_bp, task_bp, user_bp, category_bp, report_bp):
        app.register_blueprint(blueprint)
