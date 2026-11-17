from flask import Blueprint
from controllers.produto_controller import ProdutoController

produto_bp = Blueprint("produtos", __name__)

produto_bp.route("/produtos", methods=["GET"])(ProdutoController.listar_produtos)
produto_bp.route("/produtos/busca", methods=["GET"])(ProdutoController.buscar_produtos)
produto_bp.route("/produtos/<int:id>", methods=["GET"])(ProdutoController.buscar_produto)
produto_bp.route("/produtos", methods=["POST"])(ProdutoController.criar_produto)
produto_bp.route("/produtos/<int:id>", methods=["PUT"])(ProdutoController.atualizar_produto)
produto_bp.route("/produtos/<int:id>", methods=["DELETE"])(ProdutoController.deletar_produto)
