"""Model de Tarefa — entidade, invariantes e acesso a dados do agregado.

`is_overdue()` já existia no legado e nunca era chamado: a mesma regra estava reescrita em
seis blocos `if/else` dentro das rotas. Aqui ela é o único lugar que define "atrasada", e
`to_dict()` a usa.
"""
from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import joinedload

from src.domain.constants import (
    DEFAULT_PRIORITY,
    HIGH_PRIORITY_THRESHOLD,
    STATUS_DONE,
    STATUS_PENDING,
    TERMINAL_STATUSES,
)
from src.extensions import db
from src.utils.datetime_utils import now_utc


class Task(db.Model):
    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default=STATUS_PENDING)
    priority = db.Column(db.Integer, default=DEFAULT_PRIORITY)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=now_utc)
    updated_at = db.Column(db.DateTime, default=now_utc, onupdate=now_utc)
    due_date = db.Column(db.DateTime, nullable=True)
    tags = db.Column(db.String(500), nullable=True)

    # `cascade` no lado do usuário evita a deleção manual em laço que o legado fazia.
    user = db.relationship("User", backref=db.backref("tasks", cascade="all, delete-orphan"))
    category = db.relationship("Category", backref="tasks")

    # --- invariantes / regras do agregado ---

    def is_overdue(self):
        """Única definição de "tarefa atrasada" no projeto."""
        if not self.due_date:
            return False
        return self.due_date < now_utc() and self.status not in TERMINAL_STATUSES

    @property
    def tag_list(self):
        return self.tags.split(",") if self.tags else []

    def set_tags(self, tags):
        if tags is None:
            self.tags = None
        elif isinstance(tags, (list, tuple)):
            self.tags = ",".join(str(tag) for tag in tags)
        else:
            self.tags = str(tags)

    # --- serialização ---

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "user_id": self.user_id,
            "category_id": self.category_id,
            "created_at": str(self.created_at),
            "updated_at": str(self.updated_at),
            "due_date": str(self.due_date) if self.due_date else None,
            "tags": self.tag_list,
        }

    def to_dict_with_overdue(self):
        return {**self.to_dict(), "overdue": self.is_overdue()}

    def to_dict_with_relations(self):
        """Inclui os nomes de usuário e categoria já carregados (sem N+1)."""
        return {
            **self.to_dict_with_overdue(),
            "user_name": self.user.name if self.user else None,
            "category_name": self.category.name if self.category else None,
        }

    def to_summary_dict(self):
        """Forma reduzida usada em `GET /users/<id>/tasks`."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "created_at": str(self.created_at),
            "due_date": str(self.due_date) if self.due_date else None,
            "overdue": self.is_overdue(),
        }

    # --- acesso a dados ---

    @staticmethod
    def get(task_id):
        return db.session.get(Task, task_id)

    @staticmethod
    def list_with_relations():
        """Carrega usuário e categoria junto: uma query em vez de 1 + 2N."""
        return list(
            db.session.scalars(
                select(Task)
                .options(joinedload(Task.user), joinedload(Task.category))
                .order_by(Task.id)
            ).unique()
        )

    @staticmethod
    def list_by_user(user_id):
        return list(
            db.session.scalars(
                select(Task).where(Task.user_id == user_id).order_by(Task.id)
            )
        )

    @staticmethod
    def search(termo=None, status=None, priority=None, user_id=None):
        statement = select(Task)
        if termo:
            padrao = f"%{termo}%"
            statement = statement.where(
                or_(Task.title.like(padrao), Task.description.like(padrao))
            )
        if status:
            statement = statement.where(Task.status == status)
        if priority is not None:
            statement = statement.where(Task.priority == priority)
        if user_id is not None:
            statement = statement.where(Task.user_id == user_id)
        return list(db.session.scalars(statement.order_by(Task.id)))

    @staticmethod
    def count():
        return db.session.scalar(select(func.count(Task.id))) or 0

    @staticmethod
    def count_by_status():
        """Contagem por status em uma query (o legado fazia um COUNT por status)."""
        rows = db.session.execute(
            select(Task.status, func.count(Task.id)).group_by(Task.status)
        ).all()
        return {status: total for status, total in rows}

    @staticmethod
    def count_by_priority():
        rows = db.session.execute(
            select(Task.priority, func.count(Task.id)).group_by(Task.priority)
        ).all()
        return {priority: total for priority, total in rows}

    @staticmethod
    def overdue_tasks():
        """Tarefas atrasadas resolvidas no banco, não em laço Python."""
        agora = now_utc()
        return list(
            db.session.scalars(
                select(Task)
                .where(Task.due_date.isnot(None))
                .where(Task.due_date < agora)
                .where(Task.status.notin_(TERMINAL_STATUSES))
                .order_by(Task.id)
            )
        )

    @staticmethod
    def count_created_since(momento):
        return (
            db.session.scalar(
                select(func.count(Task.id)).where(Task.created_at >= momento)
            )
            or 0
        )

    @staticmethod
    def count_done_since(momento):
        return (
            db.session.scalar(
                select(func.count(Task.id))
                .where(Task.status == STATUS_DONE)
                .where(Task.updated_at >= momento)
            )
            or 0
        )

    @staticmethod
    def productivity_by_user():
        """Total e concluídas por usuário em uma query, em vez de uma por usuário."""
        from src.models.user import User

        rows = db.session.execute(
            select(
                User.id,
                User.name,
                func.count(Task.id),
                func.coalesce(
                    func.sum(case((Task.status == STATUS_DONE, 1), else_=0)), 0
                ),
            )
            .outerjoin(Task, Task.user_id == User.id)
            .group_by(User.id)
            .order_by(User.id)
        ).all()
        return [
            {
                "user_id": user_id,
                "user_name": user_name,
                "total_tasks": total or 0,
                "completed_tasks": int(concluidas or 0),
            }
            for user_id, user_name, total, concluidas in rows
        ]

    @staticmethod
    def statistics_for_user(user_id):
        """Estatísticas de um usuário: contagens por status, atraso e alta prioridade."""
        por_status = dict(
            db.session.execute(
                select(Task.status, func.count(Task.id))
                .where(Task.user_id == user_id)
                .group_by(Task.status)
            ).all()
        )
        total = sum(por_status.values())
        agora = now_utc()
        atrasadas = (
            db.session.scalar(
                select(func.count(Task.id))
                .where(Task.user_id == user_id)
                .where(Task.due_date.isnot(None))
                .where(Task.due_date < agora)
                .where(Task.status.notin_(TERMINAL_STATUSES))
            )
            or 0
        )
        alta_prioridade = (
            db.session.scalar(
                select(func.count(Task.id))
                .where(Task.user_id == user_id)
                .where(Task.priority <= HIGH_PRIORITY_THRESHOLD)
            )
            or 0
        )
        return {
            "por_status": por_status,
            "total": total,
            "atrasadas": atrasadas,
            "alta_prioridade": alta_prioridade,
        }
