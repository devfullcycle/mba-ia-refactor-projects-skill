from flask import request

from utils.errors import ValidationError


def get_json_body():
    """Corpo JSON como dict, ou levanta 400 se ausente, vazio ou malformado."""
    body = request.get_json(silent=True)
    if not isinstance(body, dict) or not body:
        raise ValidationError('Dados inválidos')
    return body
