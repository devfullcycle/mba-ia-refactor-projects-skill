from database import db
from datetime import datetime
from config import settings


class Task(db.Model):
    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default="pending")
    priority = db.Column(db.Integer, default=settings.DEFAULT_PRIORITY)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
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

    def serializable(self):
        """Payload HTTP com flags derivadas (overdue)."""
        data = self.to_dict()
        data["overdue"] = self.is_overdue()
        return data

    def is_overdue(self):
        valid = _is_active_status(self.status)
        return self.due_date is not None and self.due_date < datetime.utcnow() and valid

    def days_overdue(self):
        if self.is_overdue():
            return (datetime.utcnow() - self.due_date).days
        return 0


def _is_active_status(status):
    return status not in ("done", "cancelled")


def validate_status(status):
    return status in settings.VALID_STATUSES


def validate_priority(priority):
    return 1 <= priority <= 5