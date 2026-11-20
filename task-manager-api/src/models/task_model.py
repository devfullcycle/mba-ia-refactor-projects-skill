"""Task entity and its repository."""
from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.orm import joinedload

from .database import db, utcnow

STATUS_PENDING = "pending"
STATUS_IN_PROGRESS = "in_progress"
STATUS_DONE = "done"
STATUS_CANCELLED = "cancelled"
TASK_STATUSES = (STATUS_PENDING, STATUS_IN_PROGRESS, STATUS_DONE, STATUS_CANCELLED)
CLOSED_STATUSES = (STATUS_DONE, STATUS_CANCELLED)

PRIORITY_MIN = 1
PRIORITY_MAX = 5
DEFAULT_PRIORITY = 3
PRIORITY_LABELS = {1: "critical", 2: "high", 3: "medium", 4: "low", 5: "minimal"}
TAG_SEPARATOR = ","


class Task(db.Model):
    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default=STATUS_PENDING)
    priority = db.Column(db.Integer, default=DEFAULT_PRIORITY)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)
    due_date = db.Column(db.DateTime, nullable=True)
    tags = db.Column(db.String(500), nullable=True)

    user = db.relationship("User", backref="tasks")
    category = db.relationship("Category", backref="tasks")

    @property
    def tag_list(self):
        return self.tags.split(TAG_SEPARATOR) if self.tags else []

    def is_overdue(self, now=None):
        now = now or utcnow()
        return bool(self.due_date and self.due_date < now and self.status not in CLOSED_STATUSES)

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


def _overdue_clause(now):
    return (Task.due_date.is_not(None), Task.due_date < now, Task.status.not_in(CLOSED_STATUSES))


class TaskRepository:
    def __init__(self, session):
        self.session = session

    def get(self, task_id):
        return self.session.get(Task, task_id)

    def list_with_relations(self):
        stmt = select(Task).options(joinedload(Task.user), joinedload(Task.category)).order_by(Task.id)
        return self.session.scalars(stmt).all()

    def list_by_user(self, user_id):
        return self.session.scalars(select(Task).where(Task.user_id == user_id).order_by(Task.id)).all()

    def search(self, text=None, status=None, priority=None, user_id=None):
        stmt = select(Task)
        if text:
            pattern = f"%{text}%"  # bound parameter, not SQL concatenation
            stmt = stmt.where(or_(Task.title.like(pattern), Task.description.like(pattern)))
        if status:
            stmt = stmt.where(Task.status == status)
        if priority is not None:
            stmt = stmt.where(Task.priority == priority)
        if user_id is not None:
            stmt = stmt.where(Task.user_id == user_id)
        return self.session.scalars(stmt.order_by(Task.id)).all()

    def count(self):
        return self.session.scalar(select(func.count(Task.id)))

    def count_by_status(self):
        rows = self.session.execute(select(Task.status, func.count(Task.id)).group_by(Task.status)).all()
        return dict(rows)

    def count_by_priority(self):
        rows = self.session.execute(select(Task.priority, func.count(Task.id)).group_by(Task.priority)).all()
        return dict(rows)

    def list_overdue(self, now):
        return self.session.scalars(select(Task).where(*_overdue_clause(now)).order_by(Task.id)).all()

    def count_overdue(self, now):
        return self.session.scalar(select(func.count(Task.id)).where(*_overdue_clause(now)))

    def count_created_since(self, since):
        return self.session.scalar(select(func.count(Task.id)).where(Task.created_at >= since))

    def count_completed_since(self, since):
        stmt = select(func.count(Task.id)).where(Task.status == STATUS_DONE, Task.updated_at >= since)
        return self.session.scalar(stmt)

    def add(self, task):
        self.session.add(task)

    def delete(self, task):
        self.session.delete(task)

    def delete_by_user(self, user_id):
        self.session.execute(delete(Task).where(Task.user_id == user_id))

    def detach_category(self, category_id):
        self.session.execute(update(Task).where(Task.category_id == category_id).values(category_id=None))

    def commit(self):
        self.session.commit()
