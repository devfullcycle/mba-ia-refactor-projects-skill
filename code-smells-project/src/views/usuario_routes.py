"""Rotas de Usuário e autenticação."""
from flask import Blueprint, jsonify, request


def create_usuario_blueprint(controller):
    blueprint = Blueprint("usuarios", __name__)

    @blueprint.route("/usuarios", methods=["GET"])
    def listar_usuarios():
        body, status = controller.listar()
        return jsonify(body), status

    @blueprint.route("/usuarios/<int:usuario_id>", methods=["GET"])
    def buscar_usuario(usuario_id):
        body, status = controller.buscar(usuario_id)
        return jsonify(body), status

    @blueprint.route("/usuarios", methods=["POST"])
    def criar_usuario():
        body, status = controller.criar(request.get_json(silent=True))
        return jsonify(body), status

    @blueprint.route("/login", methods=["POST"])
    def login():
        body, status = controller.login(request.get_json(silent=True))
        return jsonify(body), status

    return blueprint
