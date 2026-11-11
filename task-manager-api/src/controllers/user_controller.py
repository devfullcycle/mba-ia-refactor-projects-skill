import logging

from src.models import task as task_model
from src.models import user as user_model
from src.utils import validators
from src.utils.errors import ConflictError, ForbiddenError, NotFoundError
from src.utils.pagination import apply_page

logger = logging.getLogger(__name__)


def get_or_404(user_id):
    user = user_model.find_by_id(user_id)
    if user is None:
        raise NotFoundError("Usuário não encontrado")
    return user


def _validate_name(value):
    name = validators.required_string(value, "Nome é obrigatório")
    return validators.string_length(name, 1, user_model.NAME_MAX_LENGTH, "Nome é obrigatório", "Nome muito longo")


def _validate_password(value):
    password = validators.required_string(value, "Senha é obrigatória")
    min_length = user_model.PASSWORD_MIN_LENGTH
    return validators.string_length(
        password, min_length, 128, f"Senha deve ter no mínimo {min_length} caracteres", "Senha muito longa"
    )


def _validate_role(value):
    return validators.choice(value, user_model.VALID_ROLES, "Role inválido")


def _ensure_email_available(email, current_user_id=None):
    existing = user_model.find_by_email(email)
    if existing and existing.id != current_user_id:
        raise ConflictError("Email já cadastrado")


def list_users(page=None):
    query = user_model.list_with_task_count()
    total = user_model.count() if page else None
    result = []
    for user, task_count in apply_page(query, page).all():
        data = user.to_dict()
        data["task_count"] = task_count
        result.append(data)
    return result, total


def get_user(user_id):
    user = get_or_404(user_id)
    data = user.to_dict()
    data["tasks"] = [task.to_dict() for task in task_model.by_user(user_id).all()]
    return data


def create_user(data, actor=None):
    """Cadastro público sempre cria perfil 'user'; só um admin autenticado escolhe outro role."""
    data = validators.require_json_object(data)

    name = _validate_name(data.get("name"))
    email = validators.email(data.get("email"))
    password = _validate_password(data.get("password"))
    role = _validate_role(data.get("role", user_model.ROLE_USER))
    if role != user_model.ROLE_USER and not (actor and actor.is_admin()):
        raise ForbiddenError("Apenas administradores podem definir o role do usuário")

    _ensure_email_available(email)
    user = user_model.create(name=name, email=email, password=password, role=role)
    logger.info("Usuário criado: %s - %s", user.id, user.name)
    return user.to_dict()


def update_user(user_id, data, actor):
    user = get_or_404(user_id)
    if not actor.is_admin() and actor.id != user.id:
        raise ForbiddenError("Você só pode alterar o próprio perfil")
    data = validators.require_json_object(data)

    if ("role" in data or "active" in data) and not actor.is_admin():
        raise ForbiddenError("Apenas administradores podem alterar role ou status do usuário")

    if "name" in data:
        user.name = _validate_name(data["name"])
    if "email" in data:
        email = validators.email(data["email"])
        _ensure_email_available(email, user.id)
        user.email = email
    if "password" in data:
        user.set_password(_validate_password(data["password"]))
    if "role" in data:
        user.role = _validate_role(data["role"])
    if "active" in data:
        user.active = validators.boolean(data["active"], "active")

    user_model.save()
    return user.to_dict()


def delete_user(user_id, actor):
    user = get_or_404(user_id)
    if user.id == actor.id:
        raise ForbiddenError("Você não pode remover o próprio usuário")
    user_model.delete(user)
    logger.info("Usuário deletado: %s", user_id)
    return {"message": "Usuário deletado com sucesso"}


def get_user_tasks(user_id):
    get_or_404(user_id)
    return [task.to_user_task_item() for task in task_model.by_user(user_id).all()]
