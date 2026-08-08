"""Usuario and authentication business rules."""

from __future__ import annotations

import logging
from typing import Any

from werkzeug.security import check_password_hash, generate_password_hash

from src.models.usuario_model import UsuarioModel
from src.services.errors import DomainError, NotFoundError, UnauthorizedError

logger = logging.getLogger(__name__)


class UsuarioService:
    def __init__(self, model: UsuarioModel) -> None:
        self._model = model

    def listar(self) -> list[dict[str, Any]]:
        return self._model.listar_todos()

    def buscar_por_id(self, usuario_id: int) -> dict[str, Any]:
        usuario = self._model.buscar_por_id(usuario_id)
        if not usuario:
            raise NotFoundError("Usuário não encontrado")
        return usuario

    def criar(self, dados: dict[str, Any] | None) -> int:
        if not dados:
            raise DomainError("Dados inválidos")

        nome = str(dados.get("nome", "")).strip()
        email = str(dados.get("email", "")).strip()
        senha = str(dados.get("senha", ""))

        if not nome or not email or not senha:
            raise DomainError("Nome, email e senha são obrigatórios")

        usuario_id = self._model.criar(nome, email, generate_password_hash(senha))
        logger.info("Usuário criado: %s", email)
        return usuario_id

    def login(self, dados: dict[str, Any] | None) -> dict[str, Any]:
        if not dados:
            raise DomainError("Dados inválidos")

        email = str(dados.get("email", "")).strip()
        senha = str(dados.get("senha", ""))

        if not email or not senha:
            raise DomainError("Email e senha são obrigatórios")

        usuario = self._model.buscar_por_email(email)
        if not usuario or not check_password_hash(usuario["senha"], senha):
            logger.info("Login falhou: %s", email)
            raise UnauthorizedError("Email ou senha inválidos")

        logger.info("Login bem-sucedido: %s", email)
        return UsuarioModel.para_login(usuario)
