import re
from sqlalchemy import select, func, delete as sa_delete
from flask import request
from database import db
from models.user import User
from models.task import Task
from core.constants import VALID_ROLES, MIN_PASSWORD_LENGTH
from core.errors import AppError, NotFoundError, ValidationError, AuthError

_EMAIL_RE = re.compile(r"^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$")


def list_users():
    users = db.session.execute(select(User)).scalars().all()
    result = []
    for u in users:
        data = u.to_dict()
        data["task_count"] = (
            db.session.scalar(
                select(func.count(Task.id)).where(Task.user_id == u.id)
            )
            or 0
        )
        result.append(data)
    return result, 200


def get_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        raise NotFoundError("Usuario nao encontrado")
    data = user.to_dict()
    tasks = (
        db.session.execute(select(Task).where(Task.user_id == user_id))
        .scalars()
        .all()
    )
    data["tasks"] = [t.to_dict() for t in tasks]
    return data, 200


def _validate_user_payload(data):
    if not data:
        raise ValidationError("Dados invalidos")
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")
    if not name or not email or not password:
        raise ValidationError("Nome, email e senha sao obrigatorios")
    if not _EMAIL_RE.match(email):
        raise ValidationError("Email invalido")
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValidationError(f"Senha deve ter no minimo {MIN_PASSWORD_LENGTH} caracteres")
    return name, email, password


def create_user():
    data = request.get_json() or {}
    name, email, password = _validate_user_payload(data)

    role = data.get("role", "user")
    if role not in VALID_ROLES:
        raise ValidationError("Role invalido")

    existing = db.session.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if existing:
        raise AppError("Email ja cadastrado", 409)

    user = User(name=name, email=email, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user.to_dict(), 201


def update_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        raise NotFoundError("Usuario nao encontrado")

    data = request.get_json() or {}

    if "name" in data:
        user.name = data["name"]
    if "email" in data:
        if not _EMAIL_RE.match(data["email"]):
            raise ValidationError("Email invalido")
        existing = db.session.execute(
            select(User).where(User.email == data["email"])
        ).scalar_one_or_none()
        if existing and existing.id != user_id:
            raise ValidationError("Email ja cadastrado")
        user.email = data["email"]
    if "password" in data:
        if len(data["password"]) < MIN_PASSWORD_LENGTH:
            raise ValidationError("Senha muito curta")
        user.set_password(data["password"])
    if "role" in data:
        if data["role"] not in VALID_ROLES:
            raise ValidationError("Role invalido")
        user.role = data["role"]
    if "active" in data:
        if not isinstance(data["active"], bool):
            raise ValidationError("active deve ser booleano")
        user.active = data["active"]

    db.session.commit()
    return user.to_dict(), 200


def delete_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        raise NotFoundError("Usuario nao encontrado")
    db.session.execute(sa_delete(Task).where(Task.user_id == user_id))
    db.session.delete(user)
    db.session.commit()
    return {"message": "Usuario deletado com sucesso"}, 200


def user_tasks(user_id):
    user = db.session.get(User, user_id)
    if not user:
        raise NotFoundError("Usuario nao encontrado")
    tasks = (
        db.session.execute(select(Task).where(Task.user_id == user_id)).scalars().all()
    )
    result = []
    for t in tasks:
        data = t.to_dict()
        data["overdue"] = t.is_overdue()
        result.append(data)
    return result, 200


def login():
    data = request.get_json() or {}
    email = data.get("email")
    password = data.get("password")
    if not email or not password:
        raise ValidationError("Email e senha sao obrigatorios")

    user = db.session.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if not user or not user.check_password(password):
        raise AuthError()
    if not user.active:
        raise AuthError("Usuario inativo")

    return (
        {
            "message": "Login realizado com sucesso",
            "user": user.to_dict(),
            "token": f"jwt-token-{user.id}",
        },
        200,
    )
