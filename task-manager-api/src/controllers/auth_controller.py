import logging

from src.models import user as user_model
from src.services import auth_service
from src.utils import validators
from src.utils.errors import ForbiddenError, UnauthorizedError, ValidationError

logger = logging.getLogger(__name__)

INVALID_CREDENTIALS = "Credenciais inválidas"


def login(data):
    data = validators.require_json_object(data)
    email = data.get("email")
    password = data.get("password")
    if not isinstance(email, str) or not isinstance(password, str) or not email or not password:
        raise ValidationError("Email e senha são obrigatórios")

    user = user_model.find_by_email(email.strip())
    if user is None or not user.check_password(password):
        raise UnauthorizedError(INVALID_CREDENTIALS)
    if not user.active:
        raise ForbiddenError("Usuário inativo")

    if user.has_legacy_password():
        # Migração transparente: o hash MD5 legado é regravado no algoritmo atual.
        user.set_password(password)
        user_model.save()
        logger.info("Hash de senha legado migrado para o usuário %s", user.id)

    return {
        "message": "Login realizado com sucesso",
        "user": user.to_dict(),
        "token": auth_service.generate_token(user.id),
    }
