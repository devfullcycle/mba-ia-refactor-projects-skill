"""Validação de entrada de Usuário e Login."""
from models.user import MIN_PASSWORD_LENGTH, ROLE_USER, VALID_ROLES, is_valid_email
from utils.errors import ValidationError


def _require_dict(data):
    if not data or not isinstance(data, dict):
        raise ValidationError("Dados inválidos")


def _validate_role(role):
    if role not in VALID_ROLES:
        raise ValidationError("Role inválido")
    return role


def validate_new_user(data):
    _require_dict(data)
    for field, message in (("name", "Nome é obrigatório"),
                           ("email", "Email é obrigatório"),
                           ("password", "Senha é obrigatória")):
        if not data.get(field):
            raise ValidationError(message)

    if not is_valid_email(data["email"]):
        raise ValidationError("Email inválido")
    password = data["password"]
    if not isinstance(password, str) or len(password) < MIN_PASSWORD_LENGTH:
        raise ValidationError(f"Senha deve ter no mínimo {MIN_PASSWORD_LENGTH} caracteres")

    return {
        "name": data["name"],
        "email": data["email"],
        "password": password,
        "role": _validate_role(data.get("role", ROLE_USER)),
    }


def validate_user_update(data):
    _require_dict(data)
    fields = {}
    if "name" in data:
        fields["name"] = data["name"]
    if "email" in data:
        if not is_valid_email(data["email"]):
            raise ValidationError("Email inválido")
        fields["email"] = data["email"]
    if "password" in data:
        if not isinstance(data["password"], str) or len(data["password"]) < MIN_PASSWORD_LENGTH:
            raise ValidationError("Senha muito curta")
        fields["password"] = data["password"]
    if "role" in data:
        fields["role"] = _validate_role(data["role"])
    if "active" in data:
        fields["active"] = bool(data["active"])
    return fields


def validate_login(data):
    _require_dict(data)
    email, password = data.get("email"), data.get("password")
    if not email or not password or not isinstance(password, str):
        raise ValidationError("Email e senha são obrigatórios")
    return email, password
