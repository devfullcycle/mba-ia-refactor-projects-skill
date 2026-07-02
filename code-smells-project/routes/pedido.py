from flask import Blueprint, request
from controllers import pedido

bp = Blueprint("pedidos", __name__)

@bp.route("/pedidos", methods=["POST"])
def criar():
    dados = request.get_json()
    return pedido.criar(dados)

@bp.route("/pedidos", methods=["GET"])
def listar_todos():
    return pedido.listar_todos()

@bp.route("/pedidos/usuario/<int:usuario_id>", methods=["GET"])
def listar_por_usuario(usuario_id):
    return pedido.listar_por_usuario(usuario_id)

@bp.route("/pedidos/<int:pedido_id>/status", methods=["PUT"])
def atualizar_status(pedido_id):
    dados = request.get_json()
    return pedido.atualizar_status(pedido_id, dados)

@bp.route("/relatorios/vendas", methods=["GET"])
def relatorio_vendas():
    return pedido.relatorio_vendas()
