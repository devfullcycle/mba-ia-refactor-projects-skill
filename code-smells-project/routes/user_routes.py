from flask import Blueprint, request, jsonify
from controllers import user_controller
from middlewares.error_handler import handle_errors

bp = Blueprint("usuarios", __name__)


@bp.route("/usuarios", methods=["GET"])
@handle_errors
def listar_usuarios():
    result, status = user_controller.list_all()
    return jsonify(result), status


@bp.route("/usuarios/<int:id>", methods=["GET"])
@handle_errors
def buscar_usuario(id):
    result, status = user_controller.get_by_id(id)
    return jsonify(result), status


@bp.route("/usuarios", methods=["POST"])
@handle_errors
def criar_usuario():
    dados = request.get_json()
    result, status = user_controller.create(dados)
    return jsonify(result), status


@bp.route("/login", methods=["POST"])
@handle_errors
def login():
    dados = request.get_json()
    result, status = user_controller.login(dados)
    return jsonify(result), status
