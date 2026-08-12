"""Serviço de usuários — regras de negócio e autenticação."""

import re

from database import db
from models.user import User
from models.task import Task
from config import settings
from middlewares.error_handler import ApiError


class UserServiceError(ApiError):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.status = status


EMAIL_RE = re.compile(r"^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$")


def list_users():
    users = User.query.all()
    result = []
    for u in users:
        data = u.to_dict()  # sem password
        data["task_count"] = len(u.tasks)
        result.append(data)
    return result


def get_user(user_id):
    user = User.query.get(user_id)
    if not user:
        raise UserServiceError("Usuário não encontrado", 404)
    data = user.to_dict()
    data["tasks"] = [t.serializable() for t in Task.query.filter_by(user_id=user_id).all()]
    return data


def create_user(data):
    if not data:
        raise UserServiceError("Dados inválidos", 400)
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")
    role = data.get("role", "user")

    if not name:
        raise UserServiceError("Nome é obrigatório", 400)
    if not email:
        raise UserServiceError("Email é obrigatório", 400)
    if not password:
        raise UserServiceError("Senha é obrigatória", 400)
    if not EMAIL_RE.match(email):
        raise UserServiceError("Email inválido", 400)
    if len(password) < settings.MIN_PASSWORD_LENGTH:
        raise UserServiceError("Senha deve ter no mínimo %s caracteres" % settings.MIN_PASSWORD_LENGTH, 400)
    if role not in settings.VALID_ROLES:
        raise UserServiceError("Role inválido", 400)
    if User.query.filter_by(email=email).first():
        raise UserServiceError("Email já cadastrado", 409)

    user = User()
    user.name = name
    user.email = email
    user.set_password(password)
    user.role = role
    db.session.add(user)
    _commit()
    return user.to_dict()


def update_user(user_id, data):
    user = User.query.get(user_id)
    if not user:
        raise UserServiceError("Usuário não encontrado", 404)
    if not data:
        raise UserServiceError("Dados inválidos", 400)

    if "name" in data:
        user.name = data["name"]
    if "email" in data:
        if not EMAIL_RE.match(data["email"]):
            raise UserServiceError("Email inválido", 400)
        existing = User.query.filter_by(email=data["email"]).first()
        if existing and existing.id != user_id:
            raise UserServiceError("Email já cadastrado", 409)
        user.email = data["email"]
    if "password" in data:
        if len(data["password"]) < settings.MIN_PASSWORD_LENGTH:
            raise UserServiceError("Senha muito curta", 400)
        user.set_password(data["password"])
    if "role" in data:
        if data["role"] not in settings.VALID_ROLES:
            raise UserServiceError("Role inválido", 400)
        user.role = data["role"]
    if "active" in data:
        user.active = data["active"]

    db.session.commit()
    return user.to_dict()


def delete_user(user_id):
    user = User.query.get(user_id)
    if not user:
        raise UserServiceError("Usuário não encontrado", 404)
    for t in Task.query.filter_by(user_id=user_id).all():
        db.session.delete(t)
    db.session.delete(user)
    _commit()


def get_user_tasks(user_id):
    user = User.query.get(user_id)
    if not user:
        raise UserServiceError("Usuário não encontrado", 404)
    return [t.serializable() for t in Task.query.filter_by(user_id=user_id).all()]


def login(email, password):
    import jwt
    import datetime

    if not email or not password:
        raise UserServiceError("Email e senha são obrigatórios", 400)
    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        raise UserServiceError("Credenciais inválidas", 401)
    if not user.active:
        raise UserServiceError("Usuário inativo", 403)

    payload = {
        'user_id': user.id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

    return {
        "message": "Login realizado com sucesso",
        "user": user.to_dict(),
        "token": token,
    }


def _commit():
    db.session.commit()