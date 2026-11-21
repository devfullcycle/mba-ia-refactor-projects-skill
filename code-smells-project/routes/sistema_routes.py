from flask import Blueprint

from middlewares.auth import require_admin


def criar_sistema_blueprint(controller):
    bp = Blueprint("sistema", __name__)
    bp.add_url_rule("/", "index", controller.index, methods=["GET"])
    bp.add_url_rule("/health", "health_check", controller.health, methods=["GET"])
    bp.add_url_rule("/admin/reset-db", "reset_database", require_admin(controller.resetar_banco), methods=["POST"])
    return bp
