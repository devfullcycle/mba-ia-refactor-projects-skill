"""Business policies independent from Flask and SQLite."""

from __future__ import annotations

from .errors import ValidationError

ORDER_STATUSES = {"pendente", "aprovado", "enviado", "entregue", "cancelado"}


def validate_user_registration(data: object) -> tuple[str, str, str]:
    if not isinstance(data, dict):
        raise ValidationError("Dados inválidos")
    nome = data.get("nome", "")
    email = data.get("email", "")
    senha = data.get("senha", "")
    if not isinstance(nome, str) or not isinstance(email, str) or not isinstance(senha, str) or not nome or not email or not senha:
        raise ValidationError("Nome, email e senha são obrigatórios")
    if len(nome.strip()) < 2:
        raise ValidationError("Nome muito curto")
    if "@" not in email or len(email) > 320:
        raise ValidationError("Email inválido")
    if len(senha) < 6:
        raise ValidationError("Senha deve conter pelo menos 6 caracteres")
    return nome.strip(), email.strip().lower(), senha


def validate_login(data: object) -> tuple[str, str]:
    if not isinstance(data, dict):
        raise ValidationError("Dados inválidos")
    email = data.get("email", "")
    senha = data.get("senha", "")
    if not isinstance(email, str) or not isinstance(senha, str) or not email or not senha:
        raise ValidationError("Email e senha são obrigatórios")
    return email.strip().lower(), senha


def validate_order_status(status: object) -> str:
    if not isinstance(status, str) or status not in ORDER_STATUSES:
        raise ValidationError("Status inválido")
    return status
