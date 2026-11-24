import logging

from flask import jsonify, request

from exceptions import NotFoundError, UnauthorizedError
from models import usuario_model
from services import usuario_service
from validators import usuario_validator
from views import serializers

logger = logging.getLogger(__name__)


def listar_usuarios():
    usuarios = usuario_model.listar_todos()
    return jsonify({"dados": serializers.usuarios(usuarios), "sucesso": True}), 200


def buscar_usuario(id):
    usuario = usuario_model.buscar_por_id(id)
    if not usuario:
        raise NotFoundError("Usuário não encontrado")
    return jsonify({"dados": serializers.usuario(usuario), "sucesso": True}), 200


def criar_usuario():
    campos = usuario_validator.validar_usuario(request.get_json(silent=True))
    novo_id = usuario_service.criar_usuario(**campos)
    logger.info("Usuário criado: %s", campos["email"])
    return jsonify({"dados": {"id": novo_id}, "sucesso": True}), 201


def login():
    email, senha = usuario_validator.validar_login(request.get_json(silent=True))
    usuario = usuario_service.autenticar(email, senha)
    if not usuario:
        logger.info("Login falhou: %s", email)
        raise UnauthorizedError("Email ou senha inválidos", {"sucesso": False})
    logger.info("Login bem-sucedido: %s", email)
    return jsonify({
        "dados": serializers.usuario_login(usuario),
        "sucesso": True,
        "mensagem": "Login OK",
    }), 200
