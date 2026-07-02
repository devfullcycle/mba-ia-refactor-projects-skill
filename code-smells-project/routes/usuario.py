from flask import Blueprint, request
from controllers import usuario

bp = Blueprint("usuarios", __name__)

@bp.route("/usuarios", methods=["GET"])
def listar():
    return usuario.listar()

@bp.route("/usuarios/<int:id>", methods=["GET"])
def buscar_por_id(id):
    return usuario.buscar_por_id(id)

@bp.route("/usuarios", methods=["POST"])
def criar():
    dados = request.get_json()
    return usuario.criar(dados)

@bp.route("/login", methods=["POST"])
def login():
    dados = request.get_json()
    return usuario.autenticar(dados)
