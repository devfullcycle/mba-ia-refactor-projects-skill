from flask import Blueprint, jsonify
from config.settings import VERSION
import controllers.produto_controller as produto_ctrl
import controllers.usuario_controller as usuario_ctrl
import controllers.pedido_controller as pedido_ctrl

api_bp = Blueprint("api", __name__)


@api_bp.route("/")
def index():
    return jsonify({
        "mensagem": "Bem-vindo à API da Loja",
        "versao": VERSION,
        "endpoints": {
            "produtos": "/produtos",
            "usuarios": "/usuarios",
            "pedidos": "/pedidos",
            "login": "/login",
            "relatorios": "/relatorios/vendas",
            "health": "/health",
        },
    })


# Products
api_bp.add_url_rule("/produtos", view_func=produto_ctrl.listar_produtos, methods=["GET"])
api_bp.add_url_rule("/produtos/busca", view_func=produto_ctrl.buscar_produtos, methods=["GET"])
api_bp.add_url_rule("/produtos/<int:id>", view_func=produto_ctrl.buscar_produto, methods=["GET"])
api_bp.add_url_rule("/produtos", view_func=produto_ctrl.criar_produto, methods=["POST"])
api_bp.add_url_rule("/produtos/<int:id>", view_func=produto_ctrl.atualizar_produto, methods=["PUT"])
api_bp.add_url_rule("/produtos/<int:id>", view_func=produto_ctrl.deletar_produto, methods=["DELETE"])

# Users
api_bp.add_url_rule("/usuarios", view_func=usuario_ctrl.listar_usuarios, methods=["GET"])
api_bp.add_url_rule("/usuarios/<int:id>", view_func=usuario_ctrl.buscar_usuario, methods=["GET"])
api_bp.add_url_rule("/usuarios", view_func=usuario_ctrl.criar_usuario, methods=["POST"])
api_bp.add_url_rule("/login", view_func=usuario_ctrl.login, methods=["POST"])

# Orders
api_bp.add_url_rule("/pedidos", view_func=pedido_ctrl.criar_pedido, methods=["POST"])
api_bp.add_url_rule("/pedidos", view_func=pedido_ctrl.listar_todos_pedidos, methods=["GET"])
api_bp.add_url_rule("/pedidos/usuario/<int:usuario_id>", view_func=pedido_ctrl.listar_pedidos_usuario, methods=["GET"])
api_bp.add_url_rule("/pedidos/<int:pedido_id>/status", view_func=pedido_ctrl.atualizar_status_pedido, methods=["PUT"])

# Reports
api_bp.add_url_rule("/relatorios/vendas", view_func=pedido_ctrl.relatorio_vendas, methods=["GET"])

# Health
api_bp.add_url_rule("/health", view_func=usuario_ctrl.health_check, methods=["GET"])
