from flask import Blueprint


def criar_usuario_blueprint(controller):
    bp = Blueprint("usuarios", __name__)
    bp.add_url_rule("/usuarios", "listar_usuarios", controller.listar, methods=["GET"])
    bp.add_url_rule("/usuarios/<int:usuario_id>", "buscar_usuario", controller.buscar, methods=["GET"])
    bp.add_url_rule("/usuarios", "criar_usuario", controller.criar, methods=["POST"])
    bp.add_url_rule("/login", "login", controller.login, methods=["POST"])
    return bp
