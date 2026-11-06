"""Regras de negócio do domínio de tarefas."""

from datetime import date, datetime

from errors import ForbiddenError, NotFoundError, ValidationError
from repositories.category_repository import CategoryRepository
from repositories.task_repository import TaskRepository
from repositories.user_repository import UserRepository
from utils.helpers import calculate_percentage, utcnow
from validators.schemas import TaskCreateSchema, TaskUpdateSchema, validate_schema


class TaskService:
    def __init__(self, task_repo=None, user_repo=None, category_repo=None):
        self.tasks = task_repo or TaskRepository()
        self.users = user_repo or UserRepository()
        self.categories = category_repo or CategoryRepository()

    # --- consultas -----------------------------------------------------
    def list_tasks(self):
        return [self._with_relations(task) for task in self.tasks.get_all()]

    def get_task(self, task_id):
        task = self._get_or_404(task_id)
        data = task.to_dict()
        data['overdue'] = task.is_overdue()
        return data

    def search_tasks(self, query=None, status=None, priority=None, user_id=None):
        priority = self._optional_int(priority, 'Prioridade inválida')
        user_id = self._optional_int(user_id, 'Usuário inválido')
        return [
            task.to_dict()
            for task in self.tasks.search(
                query=query or None,
                status=status or None,
                priority=priority,
                user_id=user_id,
            )
        ]

    def stats(self):
        by_status = self.tasks.count_by_status()
        total = sum(by_status.values())
        return {
            'total': total,
            'pending': by_status['pending'],
            'in_progress': by_status['in_progress'],
            'done': by_status['done'],
            'cancelled': by_status['cancelled'],
            'overdue': len(self.tasks.get_overdue(utcnow())),
            'completion_rate': calculate_percentage(by_status['done'], total),
        }

    # --- comandos ------------------------------------------------------
    def create_task(self, payload, actor_id=None, actor_role=None):
        data = validate_schema(TaskCreateSchema(), payload)
        data['user_id'] = self._resolve_owner(data.get('user_id'), actor_id, actor_role)
        self._ensure_user(data.get('user_id'))
        self._ensure_category(data.get('category_id'))

        task = self.tasks.create(
            title=data['title'],
            description=data.get('description', ''),
            status=data['status'],
            priority=data['priority'],
            user_id=data.get('user_id'),
            category_id=data.get('category_id'),
            due_date=self._to_datetime(data.get('due_date')),
            tags=self._serialize_tags(data.get('tags')),
        )
        return task.to_dict()

    def update_task(self, task_id, payload, actor_id=None, actor_role=None):
        task = self._get_or_404(task_id)
        self._ensure_owner(task, actor_id, actor_role)
        payload = self._normalize_due_date(payload)
        data = validate_schema(TaskUpdateSchema(), payload)

        if 'user_id' in data:
            self._ensure_owner_change(data['user_id'], actor_id, actor_role)
            self._ensure_user(data['user_id'])
        if 'category_id' in data:
            self._ensure_category(data['category_id'])

        for field in ('title', 'description', 'status', 'priority', 'user_id', 'category_id'):
            if field in data:
                setattr(task, field, data[field])
        if 'due_date' in data:
            task.due_date = self._to_datetime(data['due_date'])
        if 'tags' in data:
            task.tags = self._serialize_tags(data['tags'])
        task.updated_at = utcnow()

        self.tasks.save()
        return task.to_dict()

    def delete_task(self, task_id, actor_id=None, actor_role=None):
        task = self._get_or_404(task_id)
        self._ensure_owner(task, actor_id, actor_role)
        self.tasks.delete(task)

    # --- auxiliares ----------------------------------------------------
    @staticmethod
    def _is_admin(actor_role):
        return actor_role == 'admin'

    def _resolve_owner(self, requested_user_id, actor_id, actor_role):
        """Deriva o dono do token; admin pode criar em nome de terceiro."""
        if self._is_admin(actor_role):
            return requested_user_id if requested_user_id is not None else actor_id
        if requested_user_id is not None and requested_user_id != actor_id:
            raise ForbiddenError('Não é permitido criar tarefa para outro usuário')
        return actor_id

    def _ensure_owner(self, task, actor_id, actor_role):
        if self._is_admin(actor_role):
            return
        if task.user_id != actor_id:
            raise ForbiddenError('Acesso negado à tarefa')

    def _ensure_owner_change(self, new_user_id, actor_id, actor_role):
        """Impede que não-admin transfira a tarefa para terceiro."""
        if self._is_admin(actor_role):
            return
        if new_user_id != actor_id:
            raise ForbiddenError('Não é permitido transferir a tarefa para outro usuário')

    def _get_or_404(self, task_id):
        task = self.tasks.get_by_id(task_id)
        if not task:
            raise NotFoundError('Task não encontrada')
        return task

    def _ensure_user(self, user_id):
        if user_id and not self.users.get_by_id(user_id):
            raise NotFoundError('Usuário não encontrado')

    def _ensure_category(self, category_id):
        if category_id and not self.categories.get_by_id(category_id):
            raise NotFoundError('Categoria não encontrada')

    @staticmethod
    def _with_relations(task):
        data = task.to_dict()
        data['overdue'] = task.is_overdue()
        data['user_name'] = task.user.name if task.user else None
        data['category_name'] = task.category.name if task.category else None
        return data

    @staticmethod
    def _to_datetime(value):
        if value is None or value == '':
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, date):
            return datetime.combine(value, datetime.min.time())
        return datetime.strptime(str(value), '%Y-%m-%d')

    @staticmethod
    def _serialize_tags(tags):
        if tags is None:
            return None
        if isinstance(tags, list):
            return ','.join(str(tag) for tag in tags)
        return tags

    @staticmethod
    def _normalize_due_date(payload):
        payload = dict(payload)
        if 'due_date' in payload and not payload['due_date']:
            payload['due_date'] = None
        return payload

    @staticmethod
    def _optional_int(value, message):
        if value in (None, ''):
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            raise ValidationError(message)
