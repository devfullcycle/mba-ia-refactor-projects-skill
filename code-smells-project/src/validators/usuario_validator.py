"""Validação de Usuário e de credenciais de login."""
import re

from src.middlewares.error_handler import ValidationError
from src.models.usuario_model import TIPOS_VALIDOS

SENHA_MIN = 6
# Exige TLD — o padrão do legado aceitava endereços como "a@b".
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9-]+(\.[a-zA-Z0-9-]+)+$")


def validate_usuario(dados):
    if not dados:
        raise ValidationError("Dados inválidos")

    nome = str(dados.get("nome", "")).strip()
    email = str(dados.get("email", "")).strip().lower()
    senha = dados.get("senha", "")

    if not nome or not email or not senha:
        raise ValidationError("Nome, email e senha são obrigatórios")
    if not EMAIL_REGEX.match(email):
        raise ValidationError("Email inválido")
    if len(senha) < SENHA_MIN:
        raise ValidationError(f"Senha deve ter no mínimo {SENHA_MIN} caracteres")

    tipo = dados.get("tipo", "cliente")
    if tipo not in TIPOS_VALIDOS:
        raise ValidationError("Tipo inválido. Válidos: " + str(list(TIPOS_VALIDOS)))

    return {"nome": nome, "email": email, "senha": senha, "tipo": tipo}


def validate_login(dados):
    if not dados:
        raise ValidationError("Dados inválidos")

    email = str(dados.get("email", "")).strip().lower()
    senha = dados.get("senha", "")
    if not email or not senha:
        raise ValidationError("Email e senha são obrigatórios")

    return {"email": email, "senha": senha}
