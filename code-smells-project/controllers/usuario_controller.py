import logging

from flask import request

from config.logging_config import mascarar_email
from controllers import servicos
from controllers.validacao import validar_login, validar_usuario
from middlewares.auth import garantir_dono_ou_admin
from services.excecoes import AppError
from views.respostas import resposta
from views.serializers import usuario_login, usuario_publico

logger = logging.getLogger("app.usuarios")


def listar():
    usuarios = servicos().usuarios.listar()
    return resposta([usuario_publico(u) for u in usuarios])


def obter(usuario_id):
    garantir_dono_ou_admin(usuario_id)
    return resposta(usuario_publico(servicos().usuarios.obter(usuario_id)))


def criar():
    dados = validar_usuario(request.get_json(silent=True))
    usuario_id = servicos().usuarios.criar(dados["nome"], dados["email"], dados["senha"])
    logger.info("Usuário criado: id=%s", usuario_id)
    return resposta({"id": usuario_id}, status=201)


def login():
    dados = validar_login(request.get_json(silent=True))
    resultado = servicos().auth.login(dados["email"], dados["senha"])
    if resultado is None:
        logger.info("Login falhou: %s", mascarar_email(dados["email"]))
        raise AppError("Email ou senha inválidos", 401)
    usuario, token = resultado
    logger.info("Login bem-sucedido: usuario_id=%s", usuario["id"])
    return resposta(usuario_login(usuario, token), mensagem="Login OK")
