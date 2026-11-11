from datetime import timedelta

from sqlalchemy import case, func, or_
from sqlalchemy.orm import joinedload

from src.config.database import db
from src.utils.dates import format_datetime, utc_now

STATUS_PENDING = "pending"
STATUS_IN_PROGRESS = "in_progress"
STATUS_DONE = "done"
STATUS_CANCELLED = "cancelled"
VALID_STATUSES = (STATUS_PENDING, STATUS_IN_PROGRESS, STATUS_DONE, STATUS_CANCELLED)
# Tasks nesses status nunca ficam atrasadas.
CLOSED_STATUSES = (STATUS_DONE, STATUS_CANCELLED)

PRIORITY_MIN = 1
PRIORITY_MAX = 5
DEFAULT_PRIORITY = 3
# Prioridades 1 (critical) e 2 (high) contam como "alta prioridade" nos relatórios.
HIGH_PRIORITY_MAX = 2
PRIORITY_LABELS = {1: "critical", 2: "high", 3: "medium", 4: "low", 5: "minimal"}

TITLE_MIN_LENGTH = 3
TITLE_MAX_LENGTH = 200
TAGS_MAX_LENGTH = 500


class Task(db.Model):
    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(TITLE_MAX_LENGTH), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default=STATUS_PENDING)
    priority = db.Column(db.Integer, default=DEFAULT_PRIORITY)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)
    due_date = db.Column(db.DateTime, nullable=True)
    tags = db.Column(db.String(TAGS_MAX_LENGTH), nullable=True)

    user = db.relationship("User", backref=db.backref("tasks", cascade="all, delete-orphan"))
    category = db.relationship("Category", backref="tasks")

    def is_overdue(self, now=None):
        now = now or utc_now()
        return bool(self.due_date and self.due_date < now and self.status not in CLOSED_STATUSES)

    def tag_list(self):
        return self.tags.split(",") if self.tags else []

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "user_id": self.user_id,
            "category_id": self.category_id,
            "created_at": format_datetime(self.created_at),
            "updated_at": format_datetime(self.updated_at),
            "due_date": format_datetime(self.due_date),
            "tags": self.tag_list(),
        }

    def to_dict_with_overdue(self):
        data = self.to_dict()
        data["overdue"] = self.is_overdue()
        return data

    def to_list_item(self):
        """Formato de GET /tasks: inclui atraso e nomes de usuário/categoria."""
        data = self.to_dict_with_overdue()
        data["user_name"] = self.user.name if self.user else None
        data["category_name"] = self.category.name if self.category else None
        return data

    def to_user_task_item(self):
        """Formato reduzido de GET /users/<id>/tasks."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "created_at": format_datetime(self.created_at),
            "due_date": format_datetime(self.due_date),
            "overdue": self.is_overdue(),
        }


def _overdue_filter(now):
    return Task.due_date.isnot(None), Task.due_date < now, Task.status.notin_(CLOSED_STATUSES)


def find_by_id(task_id):
    return db.session.get(Task, task_id)


def base_query():
    return Task.query.order_by(Task.id)


def list_with_relations():
    # joinedload elimina as 2 queries extras por task (usuário e categoria).
    return base_query().options(joinedload(Task.user), joinedload(Task.category))


def search(text=None, status=None, priority=None, user_id=None):
    query = base_query()
    if text:
        pattern = f"%{text}%"
        query = query.filter(or_(Task.title.like(pattern), Task.description.like(pattern)))
    if status:
        query = query.filter(Task.status == status)
    if priority is not None:
        query = query.filter(Task.priority == priority)
    if user_id is not None:
        query = query.filter(Task.user_id == user_id)
    return query


def by_user(user_id):
    return base_query().filter(Task.user_id == user_id)


def count_by_status():
    rows = db.session.query(Task.status, func.count(Task.id)).group_by(Task.status).all()
    counts = {status: 0 for status in VALID_STATUSES}
    counts.update({status: total for status, total in rows if status in counts})
    return counts


def count_by_priority():
    rows = db.session.query(Task.priority, func.count(Task.id)).group_by(Task.priority).all()
    counts = {priority: 0 for priority in PRIORITY_LABELS}
    counts.update({priority: total for priority, total in rows if priority in counts})
    return counts


def count():
    return db.session.query(func.count(Task.id)).scalar()


def count_overdue(now):
    return db.session.query(func.count(Task.id)).filter(*_overdue_filter(now)).scalar()


def list_overdue(now):
    return base_query().filter(*_overdue_filter(now)).all()


def recent_activity(days, now):
    since = now - timedelta(days=days)
    created = db.session.query(func.count(Task.id)).filter(Task.created_at >= since).scalar()
    completed = (
        db.session.query(func.count(Task.id))
        .filter(Task.status == STATUS_DONE, Task.updated_at >= since)
        .scalar()
    )
    return created, completed


def productivity_by_user():
    """(user, total, concluídas) para todos os usuários em uma única query agregada."""
    from src.models.user import User

    done = func.coalesce(func.sum(case((Task.status == STATUS_DONE, 1), else_=0)), 0)
    return (
        db.session.query(User, func.count(Task.id), done)
        .outerjoin(Task, Task.user_id == User.id)
        .group_by(User.id)
        .order_by(User.id)
        .all()
    )


def user_statistics(user_id, now):
    """Estatísticas de um usuário calculadas no banco (uma query)."""
    def count_when(*conditions):
        return func.coalesce(func.sum(case((db.and_(*conditions), 1), else_=0)), 0)

    row = (
        db.session.query(
            func.count(Task.id),
            count_when(Task.status == STATUS_DONE),
            count_when(Task.status == STATUS_PENDING),
            count_when(Task.status == STATUS_IN_PROGRESS),
            count_when(Task.status == STATUS_CANCELLED),
            count_when(*_overdue_filter(now)),
            count_when(Task.priority <= HIGH_PRIORITY_MAX),
        )
        .filter(Task.user_id == user_id)
        .one()
    )
    keys = ("total_tasks", "done", "pending", "in_progress", "cancelled", "overdue", "high_priority")
    return dict(zip(keys, (int(value) for value in row)))


def create(**fields):
    task = Task(**fields)
    db.session.add(task)
    db.session.commit()
    return task


def save():
    db.session.commit()


def delete(task):
    db.session.delete(task)
    db.session.commit()
