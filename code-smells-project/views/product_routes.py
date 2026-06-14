from flask import Blueprint, request, jsonify
from database import get_db
from models.product_model import ProductModel
from controllers.product_controller import ProductController

produtos_bp = Blueprint("produtos", __name__)


def _controller():
    return ProductController(ProductModel(get_db()))


@produtos_bp.route("/produtos", methods=["GET"])
def listar_produtos():
    result, status = _controller().list_all()
    return jsonify(result), status


@produtos_bp.route("/produtos/busca", methods=["GET"])
def buscar_produtos():
    result, status = _controller().search(
        request.args.get("q", ""),
        request.args.get("categoria"),
        request.args.get("preco_min"),
        request.args.get("preco_max"),
    )
    return jsonify(result), status


@produtos_bp.route("/produtos/<int:id>", methods=["GET"])
def buscar_produto(id):
    result, status = _controller().get_by_id(id)
    return jsonify(result), status


@produtos_bp.route("/produtos", methods=["POST"])
def criar_produto():
    result, status = _controller().create(request.get_json())
    return jsonify(result), status


@produtos_bp.route("/produtos/<int:id>", methods=["PUT"])
def atualizar_produto(id):
    result, status = _controller().update(id, request.get_json())
    return jsonify(result), status


@produtos_bp.route("/produtos/<int:id>", methods=["DELETE"])
def deletar_produto(id):
    result, status = _controller().delete(id)
    return jsonify(result), status
