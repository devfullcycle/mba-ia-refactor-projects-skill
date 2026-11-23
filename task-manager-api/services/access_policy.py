"""Regras de autorização que dependem do recurso (dono, role, campos privilegiados).

Todas levantam ForbiddenError (403) e devem ser chamadas antes de persistir.
Matriz completa rota → regra: README.md, seção "Controle de acesso".
"""
from utils.constants import DEFAULT_ROLE, PRIVILEGED_USER_FIELDS
from utils.errors import ForbiddenError


# --- Usuários ---------------------------------------------------------------

def registration_requires_admin(fields):
    """Registro é público, mas role privilegiado ou `active` só com token de admin."""
    return fields.get('role', DEFAULT_ROLE) != DEFAULT_ROLE or 'active' in fields


def ensure_can_update_user(actor, target_user_id):
    """Só o próprio usuário ou um admin altera a conta."""
    if actor.id != target_user_id and not actor.is_admin():
        raise ForbiddenError('Sem permissão para alterar este usuário')


def ensure_can_set_user_fields(actor, fields):
    """role/active só por admin, inclusive sobre a própria conta (403, nunca ignorado)."""
    if PRIVILEGED_USER_FIELDS & fields.keys() and not actor.is_admin():
        raise ForbiddenError('Apenas administradores podem alterar role/active')


def ensure_can_view_user_report(actor, target_user_id):
    if actor.id != target_user_id and not actor.is_staff():
        raise ForbiddenError('Sem permissão para ver o relatório deste usuário')


# --- Tasks ------------------------------------------------------------------

def ensure_can_manage_task(actor, task):
    """Alterar/excluir: dono da task ou staff (admin/manager)."""
    if actor.is_staff():
        return
    if task.user_id is None or task.user_id != actor.id:
        raise ForbiddenError('Sem permissão para alterar esta task')


def resolve_task_owner(actor, fields, creating):
    """Usuário comum só cria/atribui tasks para si; staff atribui a qualquer um.

    Na criação sem `user_id`, a task de um usuário comum passa a ser dele
    (senão ficaria sem dono e ele não poderia editá-la).
    """
    if actor.is_staff():
        return fields
    if creating and fields.get('user_id') is None:
        return {**fields, 'user_id': actor.id}
    if 'user_id' in fields and fields['user_id'] != actor.id:
        # inclui `null` na atualização: usuário comum não deixa a task sem dono
        raise ForbiddenError('Apenas administradores e gerentes atribuem tasks a outros usuários')
    return fields
