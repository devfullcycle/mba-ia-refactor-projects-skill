from sqlalchemy.orm import joinedload

from src.models.database import db, utcnow

STATUS_PENDING = "pending"
STATUS_IN_PROGRESS = "in_progress"
STATUS_DONE = "done"
STATUS_CANCELLED = "cancelled"
TASK_STATUSES = (STATUS_PENDING, STATUS_IN_PROGRESS, STATUS_DONE, STATUS_CANCELLED)
CLOSED_STATUSES = (STATUS_DONE, STATUS_CANCELLED)

PRIORITY_MIN = 1
PRIORITY_MAX = 5
DEFAULT_PRIORITY = 3
HIGH_PRIORITY_THRESHOLD = 2  # priority <= 2 counts as high priority
PRIORITY_LABELS = {1: "critical", 2: "high", 3: "medium", 4: "low", 5: "minimal"}

TITLE_MIN_LENGTH = 3
TITLE_MAX_LENGTH = 200
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
            "tags": self.tags.split(TAG_SEPARATOR) if self.tags else [],
        }

    def is_overdue(self, now=None):
        """Single source of the 'overdue' rule: past due date and still open."""
        now = now or utcnow()
        return bool(self.due_date and self.due_date < now and self.status not in CLOSED_STATUSES)


class TaskRepository:
    def __init__(self, database):
        self.db = database

    def get(self, task_id):
        return self.db.session.get(Task, task_id)

    def list_all(self):
        return self.db.session.execute(self.db.select(Task).order_by(Task.id)).scalars().all()

    def list_with_relations(self):
        query = self.db.select(Task).options(joinedload(Task.user), joinedload(Task.category)).order_by(Task.id)
        return self.db.session.execute(query).scalars().all()

    def list_by_user(self, user_id):
        query = self.db.select(Task).where(Task.user_id == user_id).order_by(Task.id)
        return self.db.session.execute(query).scalars().all()

    def search(self, text=None, status=None, priority=None, user_id=None):
        query = self.db.select(Task)
        if text:
            pattern = f"%{text}%"  # bound parameter, not SQL concatenation
            query = query.where(self.db.or_(Task.title.like(pattern), Task.description.like(pattern)))
        if status:
            query = query.where(Task.status == status)
        if priority is not None:
            query = query.where(Task.priority == priority)
        if user_id is not None:
            query = query.where(Task.user_id == user_id)
        return self.db.session.execute(query.order_by(Task.id)).scalars().all()

    def count(self):
        return self.db.session.execute(self.db.select(self.db.func.count(Task.id))).scalar_one()

    def count_by_status(self):
        rows = self.db.session.execute(
            self.db.select(Task.status, self.db.func.count(Task.id)).group_by(Task.status)
        ).all()
        counts = dict.fromkeys(TASK_STATUSES, 0)
        counts.update({status: total for status, total in rows})
        return counts

    def count_by_priority(self):
        rows = self.db.session.execute(
            self.db.select(Task.priority, self.db.func.count(Task.id)).group_by(Task.priority)
        ).all()
        counts = dict.fromkeys(PRIORITY_LABELS, 0)
        counts.update({priority: total for priority, total in rows})
        return counts

    def count_by_user(self):
        """{user_id: (total, done)} in a single grouped query."""
        done = self.db.func.sum(self.db.case((Task.status == STATUS_DONE, 1), else_=0))
        rows = self.db.session.execute(
            self.db.select(Task.user_id, self.db.func.count(Task.id), done).group_by(Task.user_id)
        ).all()
        return {user_id: (total, int(done_count or 0)) for user_id, total, done_count in rows}

    def count_by_category(self):
        rows = self.db.session.execute(
            self.db.select(Task.category_id, self.db.func.count(Task.id)).group_by(Task.category_id)
        ).all()
        return dict(rows)

    def count_created_since(self, moment):
        query = self.db.select(self.db.func.count(Task.id)).where(Task.created_at >= moment)
        return self.db.session.execute(query).scalar_one()

    def count_done_since(self, moment):
        query = self.db.select(self.db.func.count(Task.id)).where(
            Task.status == STATUS_DONE, Task.updated_at >= moment
        )
        return self.db.session.execute(query).scalar_one()

    def clear_category(self, category_id):
        self.db.session.execute(
            self.db.update(Task).where(Task.category_id == category_id).values(category_id=None)
        )

    def delete_by_user(self, user_id):
        self.db.session.execute(self.db.delete(Task).where(Task.user_id == user_id))

    def add(self, task):
        self.db.session.add(task)

    def delete(self, task):
        self.db.session.delete(task)

    def commit(self):
        self.db.session.commit()
