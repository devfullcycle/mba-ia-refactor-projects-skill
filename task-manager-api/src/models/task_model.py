"""Task entity and repository (all task queries live here)."""
from sqlalchemy.orm import joinedload

from src.models.constants import CLOSED_STATUSES, DEFAULT_PRIORITY, STATUS_DONE, STATUS_PENDING
from src.models.database import BaseRepository, db, utcnow


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
            "tags": self.tags.split(",") if self.tags else [],
        }

    # The overdue rule — the Python and SQL forms below are its only definitions.
    def is_overdue(self, now=None):
        now = now or utcnow()
        return bool(self.due_date and self.due_date < now and self.status not in CLOSED_STATUSES)

    @classmethod
    def overdue_clause(cls, now):
        return db.and_(cls.due_date.is_not(None), cls.due_date < now, cls.status.not_in(CLOSED_STATUSES))


class TaskRepository(BaseRepository):
    model = Task

    def _scalars(self, statement):
        return self.session.execute(statement.order_by(Task.id)).scalars().all()

    def list_all(self):
        return self._scalars(db.select(Task))

    def list_with_relations(self):
        statement = db.select(Task).options(joinedload(Task.user), joinedload(Task.category))
        return self.session.execute(statement.order_by(Task.id)).unique().scalars().all()

    def list_by_user(self, user_id):
        return self._scalars(db.select(Task).where(Task.user_id == user_id))

    def list_overdue(self, now):
        return self._scalars(db.select(Task).where(Task.overdue_clause(now)))

    def search(self, text=None, status=None, priority=None, user_id=None):
        statement = db.select(Task)
        if text:
            pattern = f"%{text}%"  # bound parameter, not SQL interpolation
            statement = statement.where(db.or_(Task.title.like(pattern), Task.description.like(pattern)))
        if status:
            statement = statement.where(Task.status == status)
        if priority is not None:
            statement = statement.where(Task.priority == priority)
        if user_id is not None:
            statement = statement.where(Task.user_id == user_id)
        return self._scalars(statement)

    def delete_by_user(self, user_id):
        self.session.execute(db.delete(Task).where(Task.user_id == user_id))

    def count(self, *conditions):
        statement = db.select(db.func.count(Task.id))
        if conditions:
            statement = statement.where(*conditions)
        return self.session.execute(statement).scalar_one()

    def count_overdue(self, now, user_id=None):
        conditions = [Task.overdue_clause(now)]
        if user_id is not None:
            conditions.append(Task.user_id == user_id)
        return self.count(*conditions)

    def count_created_since(self, since):
        return self.count(Task.created_at >= since)

    def count_completed_since(self, since):
        return self.count(Task.status == STATUS_DONE, Task.updated_at >= since)

    def _grouped_counts(self, *columns, where=None):
        statement = db.select(*columns, db.func.count(Task.id)).group_by(*columns)
        if where is not None:
            statement = statement.where(where)
        rows = self.session.execute(statement).all()
        if len(columns) == 1:
            return {row[0]: row[1] for row in rows}
        return {tuple(row[:-1]): row[-1] for row in rows}

    def count_by_status(self, user_id=None):
        return self._grouped_counts(Task.status, where=(Task.user_id == user_id) if user_id is not None else None)

    def count_by_priority(self):
        return self._grouped_counts(Task.priority)

    def count_by_user(self):
        return self._grouped_counts(Task.user_id)

    def count_by_category(self):
        return self._grouped_counts(Task.category_id)

    def count_by_user_and_status(self):
        return self._grouped_counts(Task.user_id, Task.status)

    def count_high_priority(self, user_id, threshold):
        return self.count(Task.user_id == user_id, Task.priority <= threshold)
