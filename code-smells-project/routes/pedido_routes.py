from flask import Blueprint


def criar_pedido_blueprint(controller):
    bp = Blueprint("pedidos", __name__)
    bp.add_url_rule("/pedidos", "criar_pedido", controller.criar, methods=["POST"])
    bp.add_url_rule("/pedidos", "listar_todos_pedidos", controller.listar_todos, methods=["GET"])
    bp.add_url_rule(
        "/pedidos/usuario/<int:usuario_id>", "listar_pedidos_usuario", controller.listar_por_usuario, methods=["GET"]
    )
    bp.add_url_rule(
        "/pedidos/<int:pedido_id>/status", "atualizar_status_pedido", controller.atualizar_status, methods=["PUT"]
    )
    return bp
