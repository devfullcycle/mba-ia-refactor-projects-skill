"""Endpoints HTTP do domínio de produtos."""

from flask import Blueprint
from controllers import produto_controller

produtos_bp = Blueprint("produtos", __name__)

produtos_bp.add_url_rule("/produtos", "listar_produtos", produto_controller.listar_produtos, methods=["GET"])
produtos_bp.add_url_rule("/produtos/busca", "buscar_produtos", produto_controller.buscar_produtos, methods=["GET"])
produtos_bp.add_url_rule("/produtos/<int:produto_id>", "buscar_produto", produto_controller.buscar_produto, methods=["GET"])
produtos_bp.add_url_rule("/produtos", "criar_produto", produto_controller.criar_produto, methods=["POST"])
produtos_bp.add_url_rule("/produtos/<int:produto_id>", "atualizar_produto", produto_controller.atualizar_produto, methods=["PUT"])
produtos_bp.add_url_rule("/produtos/<int:produto_id>", "deletar_produto", produto_controller.deletar_produto, methods=["DELETE"])