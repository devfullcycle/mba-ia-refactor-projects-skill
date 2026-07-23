from flask import Blueprint, jsonify
from controllers import produto_controller

produto_bp = Blueprint("produtos", __name__)


@produto_bp.route("/produtos", methods=["GET"])
def listar_produtos():
    body, status = produto_controller.listar_produtos()
    return jsonify(body), status


@produto_bp.route("/produtos/busca", methods=["GET"])
def buscar_produtos():
    body, status = produto_controller.buscar_produtos()
    return jsonify(body), status


@produto_bp.route("/produtos/<int:produto_id>", methods=["GET"])
def buscar_produto(produto_id):
    body, status = produto_controller.buscar_produto(produto_id)
    return jsonify(body), status


@produto_bp.route("/produtos", methods=["POST"])
def criar_produto():
    body, status = produto_controller.criar_produto()
    return jsonify(body), status


@produto_bp.route("/produtos/<int:produto_id>", methods=["PUT"])
def atualizar_produto(produto_id):
    body, status = produto_controller.atualizar_produto(produto_id)
    return jsonify(body), status


@produto_bp.route("/produtos/<int:produto_id>", methods=["DELETE"])
def deletar_produto(produto_id):
    body, status = produto_controller.deletar_produto(produto_id)
    return jsonify(body), status
