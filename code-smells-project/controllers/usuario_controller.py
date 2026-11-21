import logging

from flask import jsonify, request

from middlewares.error_handler import AppError
from validators import validar_login, validar_novo_usuario

logger = logging.getLogger(__name__)


class UsuarioController:
    def __init__(self, usuario_model, usuario_service):
        self._usuarios = usuario_model
        self._service = usuario_service

    def listar(self):
        return jsonify({"dados": self._usuarios.listar(), "sucesso": True}), 200

    def buscar(self, usuario_id):
        usuario = self._usuarios.buscar_por_id(usuario_id)
        if not usuario:
            raise AppError("Usuário não encontrado", 404)
        return jsonify({"dados": usuario, "sucesso": True}), 200

    def criar(self):
        dados = validar_novo_usuario(request.get_json(silent=True))
        usuario_id = self._service.criar(**dados)
        logger.info("Usuário criado (id=%s)", usuario_id)
        return jsonify({"dados": {"id": usuario_id}, "sucesso": True}), 201

    def login(self):
        credenciais = validar_login(request.get_json(silent=True))
        usuario = self._service.autenticar(**credenciais)
        return jsonify({"dados": usuario, "sucesso": True, "mensagem": "Login OK"}), 200
