from database import db
from datetime import datetime, timezone

class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default='pending')
    priority = db.Column(db.Integer, default=3)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id', ondelete='SET NULL'), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    due_date = db.Column(db.DateTime, nullable=True)
    tags = db.Column(db.String(500), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'user_id': self.user_id,
            'category_id': self.category_id,
            'created_at': str(self.created_at),
            'updated_at': str(self.updated_at),
            'due_date': str(self.due_date) if self.due_date else None,
            'tags': self.tags.split(',') if self.tags else []
        }

    @staticmethod
    def is_valid_status(status: str) -> bool:
        return status in ['pending', 'in_progress', 'done', 'cancelled']

    @staticmethod
    def is_valid_priority(priority: int) -> bool:
        return isinstance(priority, int) and 1 <= priority <= 5

    def is_overdue(self) -> bool:
        """Determina se a tarefa está vencida utilizando Guard Clauses lineares."""
        if not self.due_date:
            return False
        now = datetime.now(timezone.utc)
        due = self.due_date
        if due.tzinfo is None:
            now = now.replace(tzinfo=None)
        return due < now and self.status not in ('done', 'cancelled')
