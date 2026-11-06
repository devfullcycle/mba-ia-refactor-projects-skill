import logging

from werkzeug.exceptions import HTTPException

from services.excecoes import AppError
from views.respostas import resposta_erro

logger = logging.getLogger("app.erros")


def registrar_tratamento_erros(app):
    @app.errorhandler(AppError)
    def _erro_aplicacao(erro):
        return resposta_erro(erro.mensagem, erro.status)

    @app.errorhandler(Exception)
    def _erro_inesperado(erro):
        if isinstance(erro, HTTPException):
            return erro
        # Detalhe só no log; o cliente recebe mensagem genérica.
        logger.exception("Erro não tratado")
        return resposta_erro("Erro interno do servidor", 500)
