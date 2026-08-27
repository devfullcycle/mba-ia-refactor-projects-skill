from database import db
from datetime import datetime, timezone
import json

class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default='pending')
    priority = db.Column(db.Integer, default=3)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    
    # Fix Deprecated: datetime.utcnow -> timezone-aware datetime.now(timezone.utc)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    due_date = db.Column(db.DateTime, nullable=True)
    tags = db.Column(db.String(500), nullable=True)

    user = db.relationship('User', backref='tasks')
    category = db.relationship('Category', backref='tasks')

    def to_dict(self):
        data = {}
        data['id'] = self.id
        data['title'] = self.title
        data['description'] = self.description
        data['status'] = self.status
        data['priority'] = self.priority
        data['user_id'] = self.user_id
        data['category_id'] = self.category_id
        data['created_at'] = str(self.created_at)
        data['updated_at'] = str(self.updated_at)
        data['due_date'] = str(self.due_date) if self.due_date else None
        data['tags'] = self.tags.split(',') if self.tags else []
        data['overdue'] = self.is_overdue()
        return data

    def validate_status(self, new_status):
        valid = ['pending', 'in_progress', 'done', 'cancelled']
        if new_status in valid:
            return True
        else:
            return False

    def validate_priority(self, p):
        if p >= 1 and p <= 5:
            return True
        return False

    def is_overdue(self):
        if self.due_date:
            due_naive = self.due_date.replace(tzinfo=None) if self.due_date.tzinfo else self.due_date
            now_naive = datetime.now(timezone.utc).replace(tzinfo=None)
            if due_naive < now_naive:
                if self.status != 'done' and self.status != 'cancelled':
                    return True
        return False
