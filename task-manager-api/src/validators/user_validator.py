"""Validação de Usuário e de credenciais.

Regra única para criação e atualização; a regex de e-mail passa a exigir TLD (a do legado
aceitava `a@b`) e estava duplicada em três pontos.
"""
import re

from src.domain.constants import VALID_ROLES
from src.middlewares.error_handler import ValidationError

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9-]+(\.[a-zA-Z0-9-]+)+$")


def _validate_email(valor):
    email = str(valor or "").strip().lower()
    if not email:
        raise ValidationError("Email é obrigatório")
    if not EMAIL_REGEX.match(email):
        raise ValidationError("Email inválido")
    return email


def _validate_password(valor, minimo):
    senha = valor or ""
    if not senha:
        raise ValidationError("Senha é obrigatória")
    if len(senha) < minimo:
        raise ValidationError(f"Senha deve ter no mínimo {minimo} caracteres")
    return senha


def _validate_role(valor):
    if valor not in VALID_ROLES:
        raise ValidationError("Role inválido")
    return valor


def validate_user(dados, partial=False, password_min_length=8):
    if not dados:
        raise ValidationError("Dados inválidos")

    saida = {}

    if not partial or "name" in dados:
        nome = str(dados.get("name") or "").strip()
        if not nome:
            raise ValidationError("Nome é obrigatório")
        saida["name"] = nome

    if not partial or "email" in dados:
        saida["email"] = _validate_email(dados.get("email"))

    if not partial or "password" in dados:
        saida["password"] = _validate_password(dados.get("password"), password_min_length)

    if "role" in dados:
        saida["role"] = _validate_role(dados["role"])
    elif not partial:
        saida["role"] = _validate_role(dados.get("role", "user"))

    if "active" in dados:
        if not isinstance(dados["active"], bool):
            raise ValidationError("active deve ser booleano")
        saida["active"] = dados["active"]

    return saida


def validate_login(dados):
    if not dados:
        raise ValidationError("Dados inválidos")
    email = str(dados.get("email") or "").strip().lower()
    senha = dados.get("password") or ""
    if not email or not senha:
        raise ValidationError("Email e senha são obrigatórios")
    return {"email": email, "password": senha}
