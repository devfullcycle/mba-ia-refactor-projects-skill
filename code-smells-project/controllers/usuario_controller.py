from flask import request
from core.errors import AuthError, NotFoundError, ValidationError
from models import usuario_model
from services import auth_service


def _validate_user_payload(data):
    if not data:
        raise ValidationError("Dados invalidos")
    nome = data.get("nome", "")
    email = data.get("email", "")
    senha = data.get("senha", "")
    if not nome or not email or not senha:
        raise ValidationError("Nome, email e senha sao obrigatorios")
    return nome, email, senha


def listar_usuarios():
    return {"dados": usuario_model.list_all(), "sucesso": True}, 200


def buscar_usuario(usuario_id):
    usuario = usuario_model.get_by_id(usuario_id)
    if not usuario:
        raise NotFoundError("Usuario nao encontrado")
    return {"dados": usuario, "sucesso": True}, 200


def criar_usuario():
    nome, email, senha = _validate_user_payload(request.get_json() or {})
    novo_id = usuario_model.create(
        nome, email, auth_service.hash_password(senha)
    )
    return {"dados": {"id": novo_id}, "sucesso": True}, 201


def login():
    data = request.get_json() or {}
    email = data.get("email", "")
    senha = data.get("senha", "")
    if not email or not senha:
        raise ValidationError("Email e senha sao obrigatorios")

    user = usuario_model.get_with_password_by_email(email)
    if not user or not auth_service.verify_password(senha, user["senha"]):
        raise AuthError()
    return (
        {
            "dados": {
                "id": user["id"],
                "nome": user["nome"],
                "email": user["email"],
                "tipo": user["tipo"],
            },
            "sucesso": True,
            "mensagem": "Login OK",
        },
        200,
    )
