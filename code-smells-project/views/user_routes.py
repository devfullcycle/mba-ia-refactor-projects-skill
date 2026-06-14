from flask import Blueprint, request, jsonify
from database import get_db
from models.user_model import UserModel
from controllers.user_controller import UserController

usuarios_bp = Blueprint("usuarios", __name__)


def _controller():
    return UserController(UserModel(get_db()))


@usuarios_bp.route("/usuarios", methods=["GET"])
def listar_usuarios():
    result, status = _controller().list_all()
    return jsonify(result), status


@usuarios_bp.route("/usuarios/<int:id>", methods=["GET"])
def buscar_usuario(id):
    result, status = _controller().get_by_id(id)
    return jsonify(result), status


@usuarios_bp.route("/usuarios", methods=["POST"])
def criar_usuario():
    result, status = _controller().create(request.get_json())
    return jsonify(result), status


@usuarios_bp.route("/login", methods=["POST"])
def login():
    result, status = _controller().login(request.get_json())
    return jsonify(result), status
