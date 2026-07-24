"""Controller de Tarefa — orquestra validação, model e notificação.

Esta camada não existia: os handlers de rota faziam validação, regra de negócio e
serialização (o maior tinha 70 linhas).
"""
import logging

from src.domain.constants import TERMINAL_STATUSES
from src.extensions import db
from src.middlewares.error_handler import NotFoundError
from src.models.category import Category
from src.models.task import Task
from src.models.user import User
from src.validators.task_validator import validate_search_filters, validate_task

logger = logging.getLogger(__name__)


class TaskController:
    def __init__(self, notification_service):
        self._notifications = notification_service

    # --- consultas ---

    def list(self):
        tarefas = Task.list_with_relations()
        return [tarefa.to_dict_with_relations() for tarefa in tarefas], 200

    def get(self, task_id):
        tarefa = self._get_or_fail(task_id)
        return tarefa.to_dict_with_overdue(), 200

    def search(self, args):
        filtros = validate_search_filters(args)
        tarefas = Task.search(**filtros)
        return [tarefa.to_dict() for tarefa in tarefas], 200

    def stats(self):
        por_status = Task.count_by_status()
        total = sum(por_status.values())
        concluidas = por_status.get("done", 0)
        return {
            "total": total,
            "pending": por_status.get("pending", 0),
            "in_progress": por_status.get("in_progress", 0),
            "done": concluidas,
            "cancelled": por_status.get("cancelled", 0),
            "overdue": len(Task.overdue_tasks()),
            "completion_rate": (
                round((concluidas / total) * 100, 2) if total > 0 else 0
            ),
        }, 200

    # --- escrita ---

    def create(self, dados):
        campos = validate_task(dados)
        self._validate_relations(campos)

        tarefa = Task()
        self._apply(tarefa, campos)

        db.session.add(tarefa)
        db.session.commit()
        logger.info("Task criada", extra={"task_id": tarefa.id})

        self._notify_assignment(tarefa)
        return tarefa.to_dict(), 201

    def update(self, task_id, dados):
        tarefa = self._get_or_fail(task_id)
        campos = validate_task(dados, partial=True)
        self._validate_relations(campos)

        responsavel_anterior = tarefa.user_id
        self._apply(tarefa, campos)
        db.session.commit()
        logger.info("Task atualizada", extra={"task_id": tarefa.id})

        if tarefa.user_id and tarefa.user_id != responsavel_anterior:
            self._notify_assignment(tarefa)
        return tarefa.to_dict(), 200

    def delete(self, task_id):
        tarefa = self._get_or_fail(task_id)
        db.session.delete(tarefa)
        db.session.commit()
        logger.info("Task removida", extra={"task_id": task_id})
        return {"message": "Task deletada com sucesso"}, 200

    # --- apoio ---

    @staticmethod
    def _get_or_fail(task_id):
        tarefa = Task.get(task_id)
        if tarefa is None:
            raise NotFoundError("Task não encontrada")
        return tarefa

    @staticmethod
    def _validate_relations(campos):
        if campos.get("user_id") is not None and User.get(campos["user_id"]) is None:
            raise NotFoundError("Usuário não encontrado")
        if (
            campos.get("category_id") is not None
            and Category.get(campos["category_id"]) is None
        ):
            raise NotFoundError("Categoria não encontrada")

    @staticmethod
    def _apply(tarefa, campos):
        for campo in ("title", "description", "status", "priority", "user_id", "category_id", "due_date"):
            if campo in campos:
                setattr(tarefa, campo, campos[campo])
        if "tags" in campos:
            tarefa.set_tags(campos["tags"])

    def _notify_assignment(self, tarefa):
        """Notifica o responsável — o `NotificationService` do legado nunca era chamado."""
        if not tarefa.user_id or tarefa.status in TERMINAL_STATUSES:
            return
        self._notifications.task_assigned(User.get(tarefa.user_id), tarefa)
