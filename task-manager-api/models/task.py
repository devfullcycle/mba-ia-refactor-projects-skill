from sqlalchemy import case, func
from sqlalchemy.orm import joinedload

from database import db
from utils.clock import to_str, utcnow

STATUS_PENDING = "pending"
STATUS_IN_PROGRESS = "in_progress"
STATUS_DONE = "done"
STATUS_CANCELLED = "cancelled"
VALID_STATUSES = (STATUS_PENDING, STATUS_IN_PROGRESS, STATUS_DONE, STATUS_CANCELLED)
CLOSED_STATUSES = frozenset({STATUS_DONE, STATUS_CANCELLED})

PRIORITY_MIN = 1
PRIORITY_MAX = 5
DEFAULT_PRIORITY = 3
HIGH_PRIORITY_THRESHOLD = 2  # prioridades 1 e 2 são consideradas altas
PRIORITY_LABELS = {1: "critical", 2: "high", 3: "medium", 4: "low", 5: "minimal"}

TITLE_MIN_LENGTH = 3
TITLE_MAX_LENGTH = 200
TAG_SEPARATOR = ","


class Task(db.Model):
    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(TITLE_MAX_LENGTH), nullable=False)
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

    # ---- regras de domínio -------------------------------------------------
    def is_overdue(self, now=None):
        now = now or utcnow()
        return bool(self.due_date and self.due_date < now and self.status not in CLOSED_STATUSES)

    def days_overdue(self, now=None):
        return ((now or utcnow()) - self.due_date).days

    def set_tags(self, tags):
        self.tags = TAG_SEPARATOR.join(tags) if isinstance(tags, list) else tags

    def tag_list(self):
        return self.tags.split(TAG_SEPARATOR) if self.tags else []

    # ---- serialização --------------------------------------------------------
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
            "due_date": to_str(self.due_date),
            "tags": self.tag_list(),
        }

    def to_detail_dict(self, now=None):
        return {**self.to_dict(), "overdue": self.is_overdue(now)}

    def to_list_item(self, now=None):
        data = self.to_detail_dict(now)
        data["user_name"] = self.user.name if self.user else None
        data["category_name"] = self.category.name if self.category else None
        return data

    def to_user_task_dict(self, now=None):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "created_at": str(self.created_at),
            "due_date": to_str(self.due_date),
            "overdue": self.is_overdue(now),
        }

    # ---- consultas -----------------------------------------------------------
    @staticmethod
    def get(task_id):
        return db.session.get(Task, task_id)

    @staticmethod
    def list_with_relations():
        stmt = db.select(Task).options(joinedload(Task.user), joinedload(Task.category)).order_by(Task.id)
        return db.session.execute(stmt).scalars().all()

    @staticmethod
    def by_user(user_id):
        return db.session.execute(db.select(Task).where(Task.user_id == user_id).order_by(Task.id)).scalars().all()

    @staticmethod
    def search(text=None, status=None, priority=None, user_id=None):
        stmt = db.select(Task)
        if text:
            pattern = f"%{text}%"
            stmt = stmt.where(db.or_(Task.title.like(pattern), Task.description.like(pattern)))
        if status:
            stmt = stmt.where(Task.status == status)
        if priority is not None:
            stmt = stmt.where(Task.priority == priority)
        if user_id is not None:
            stmt = stmt.where(Task.user_id == user_id)
        return db.session.execute(stmt.order_by(Task.id)).scalars().all()

    @staticmethod
    def count():
        return db.session.scalar(db.select(func.count(Task.id)))

    @staticmethod
    def count_by(column):
        rows = db.session.execute(db.select(column, func.count(Task.id)).group_by(column)).all()
        return {key: total for key, total in rows}

    @staticmethod
    def overdue(now=None):
        now = now or utcnow()
        stmt = db.select(Task).where(
            Task.due_date.is_not(None),
            Task.due_date < now,
            Task.status.not_in(CLOSED_STATUSES),
        ).order_by(Task.id)
        return db.session.execute(stmt).scalars().all()

    @staticmethod
    def count_created_since(since):
        return db.session.scalar(db.select(func.count(Task.id)).where(Task.created_at >= since))

    @staticmethod
    def count_done_since(since):
        return db.session.scalar(
            db.select(func.count(Task.id)).where(Task.status == STATUS_DONE, Task.updated_at >= since)
        )

    @staticmethod
    def totals_by_user():
        """{user_id: (total, concluídas)} em uma única query."""
        stmt = db.select(
            Task.user_id,
            func.count(Task.id),
            func.sum(case((Task.status == STATUS_DONE, 1), else_=0)),
        ).group_by(Task.user_id)
        return {user_id: (total, done or 0) for user_id, total, done in db.session.execute(stmt).all()}

    @staticmethod
    def detach_category(category_id):
        db.session.execute(db.update(Task).where(Task.category_id == category_id).values(category_id=None))

    @staticmethod
    def delete_by_user(user_id):
        db.session.execute(db.delete(Task).where(Task.user_id == user_id))


def completion_rate(done, total):
    return round((done / total) * 100, 2) if total > 0 else 0
