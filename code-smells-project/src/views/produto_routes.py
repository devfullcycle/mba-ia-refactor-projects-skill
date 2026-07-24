"""Rotas de Produto — apenas mapeamento caminho → controller."""
from flask import Blueprint, jsonify, request


def create_produto_blueprint(controller):
    blueprint = Blueprint("produtos", __name__)

    @blueprint.route("/produtos", methods=["GET"])
    def listar_produtos():
        body, status = controller.listar()
        return jsonify(body), status

    @blueprint.route("/produtos/busca", methods=["GET"])
    def buscar_produtos():
        body, status = controller.pesquisar(request.args)
        return jsonify(body), status

    @blueprint.route("/produtos/<int:produto_id>", methods=["GET"])
    def buscar_produto(produto_id):
        body, status = controller.buscar(produto_id)
        return jsonify(body), status

    @blueprint.route("/produtos", methods=["POST"])
    def criar_produto():
        body, status = controller.criar(request.get_json(silent=True))
        return jsonify(body), status

    @blueprint.route("/produtos/<int:produto_id>", methods=["PUT"])
    def atualizar_produto(produto_id):
        body, status = controller.atualizar(produto_id, request.get_json(silent=True))
        return jsonify(body), status

    @blueprint.route("/produtos/<int:produto_id>", methods=["DELETE"])
    def deletar_produto(produto_id):
        body, status = controller.deletar(produto_id)
        return jsonify(body), status

    return blueprint
