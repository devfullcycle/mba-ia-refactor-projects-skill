from flask import Blueprint, request
from controllers import produto

bp = Blueprint("produtos", __name__, url_prefix="/produtos")

@bp.route("", methods=["GET"])
def listar():
    return produto.listar()

@bp.route("/<int:id>", methods=["GET"])
def buscar_por_id(id):
    return produto.buscar_por_id(id)

@bp.route("", methods=["POST"])
def criar():
    dados = request.get_json()
    return produto.criar(dados)

@bp.route("/<int:id>", methods=["PUT"])
def atualizar(id):
    dados = request.get_json()
    return produto.atualizar(id, dados)

@bp.route("/<int:id>", methods=["DELETE"])
def deletar(id):
    return produto.deletar(id)

@bp.route("/busca", methods=["GET"])
def buscar():
    termo = request.args.get("q", "")
    categoria = request.args.get("categoria", None)
    preco_min = request.args.get("preco_min", None)
    preco_max = request.args.get("preco_max", None)

    if preco_min:
        preco_min = float(preco_min)
    if preco_max:
        preco_max = float(preco_max)

    return produto.buscar(termo, categoria, preco_min, preco_max)
