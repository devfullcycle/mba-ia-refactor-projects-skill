"""Roteamento: apenas mapeia método + caminho para o controller."""
from flask import Blueprint

from controllers import (
    pedido_controller,
    produto_controller,
    relatorio_controller,
    sistema_controller,
    usuario_controller,
)
from middlewares.auth import admin_required


def _blueprint(name, rules):
    bp = Blueprint(name, __name__)
    for path, view, methods in rules:
        bp.add_url_rule(path, view_func=view, methods=methods)
    return bp


produtos_bp = _blueprint("produtos", [
    ("/produtos", produto_controller.listar_produtos, ["GET"]),
    ("/produtos/busca", produto_controller.buscar_produtos, ["GET"]),
    ("/produtos/<int:id>", produto_controller.buscar_produto, ["GET"]),
    ("/produtos", produto_controller.criar_produto, ["POST"]),
    ("/produtos/<int:id>", produto_controller.atualizar_produto, ["PUT"]),
    ("/produtos/<int:id>", produto_controller.deletar_produto, ["DELETE"]),
])

usuarios_bp = _blueprint("usuarios", [
    ("/usuarios", usuario_controller.listar_usuarios, ["GET"]),
    ("/usuarios/<int:id>", usuario_controller.buscar_usuario, ["GET"]),
    ("/usuarios", usuario_controller.criar_usuario, ["POST"]),
    ("/login", usuario_controller.login, ["POST"]),
])

pedidos_bp = _blueprint("pedidos", [
    ("/pedidos", pedido_controller.criar_pedido, ["POST"]),
    ("/pedidos", pedido_controller.listar_todos_pedidos, ["GET"]),
    ("/pedidos/usuario/<int:usuario_id>", pedido_controller.listar_pedidos_usuario, ["GET"]),
    ("/pedidos/<int:pedido_id>/status", pedido_controller.atualizar_status_pedido, ["PUT"]),
])

relatorios_bp = _blueprint("relatorios", [
    ("/relatorios/vendas", relatorio_controller.relatorio_vendas, ["GET"]),
])

sistema_bp = _blueprint("sistema", [
    ("/", sistema_controller.index, ["GET"]),
    ("/health", sistema_controller.health_check, ["GET"]),
    ("/admin/reset-db", admin_required(sistema_controller.reset_database), ["POST"]),
    ("/admin/query", admin_required(sistema_controller.executar_query), ["POST"]),
])


def register_routes(app):
    for bp in (produtos_bp, usuarios_bp, pedidos_bp, relatorios_bp, sistema_bp):
        app.register_blueprint(bp)
