from flask import Blueprint, jsonify
from controllers import usuario_controller

usuario_bp = Blueprint("usuarios", __name__)


@usuario_bp.route("/usuarios", methods=["GET"])
def listar_usuarios():
    body, status = usuario_controller.listar_usuarios()
    return jsonify(body), status


@usuario_bp.route("/usuarios/<int:usuario_id>", methods=["GET"])
def buscar_usuario(usuario_id):
    body, status = usuario_controller.buscar_usuario(usuario_id)
    return jsonify(body), status


@usuario_bp.route("/usuarios", methods=["POST"])
def criar_usuario():
    body, status = usuario_controller.criar_usuario()
    return jsonify(body), status


@usuario_bp.route("/login", methods=["POST"])
def login():
    body, status = usuario_controller.login()
    return jsonify(body), status
