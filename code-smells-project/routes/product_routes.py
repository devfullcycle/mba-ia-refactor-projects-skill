from flask import Blueprint, request, jsonify
from controllers import product_controller
from middlewares.error_handler import handle_errors

bp = Blueprint("produtos", __name__)


@bp.route("/produtos", methods=["GET"])
@handle_errors
def listar_produtos():
    result, status = product_controller.list_all()
    return jsonify(result), status


@bp.route("/produtos/busca", methods=["GET"])
@handle_errors
def buscar_produtos():
    termo = request.args.get("q", "")
    categoria = request.args.get("categoria", None)
    preco_min = request.args.get("preco_min", None)
    preco_max = request.args.get("preco_max", None)

    if preco_min:
        preco_min = float(preco_min)
    if preco_max:
        preco_max = float(preco_max)

    result, status = product_controller.search(termo, categoria, preco_min, preco_max)
    return jsonify(result), status


@bp.route("/produtos/<int:id>", methods=["GET"])
@handle_errors
def buscar_produto(id):
    result, status = product_controller.get_by_id(id)
    return jsonify(result), status


@bp.route("/produtos", methods=["POST"])
@handle_errors
def criar_produto():
    dados = request.get_json()
    result, status = product_controller.create(dados)
    return jsonify(result), status


@bp.route("/produtos/<int:id>", methods=["PUT"])
@handle_errors
def atualizar_produto(id):
    dados = request.get_json()
    result, status = product_controller.update(id, dados)
    return jsonify(result), status


@bp.route("/produtos/<int:id>", methods=["DELETE"])
@handle_errors
def deletar_produto(id):
    result, status = product_controller.delete(id)
    return jsonify(result), status
