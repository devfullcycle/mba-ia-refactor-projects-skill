from database import db
from utils.constants import CLOSED_STATUSES
from utils.datetime_utils import now_utc


class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default='pending')
    priority = db.Column(db.Integer, default=3)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=now_utc)
    updated_at = db.Column(db.DateTime, default=now_utc, onupdate=now_utc)
    due_date = db.Column(db.DateTime, nullable=True)
    tags = db.Column(db.String(500), nullable=True)

    user = db.relationship('User', backref='tasks')
    category = db.relationship('Category', backref='tasks')

    # ------- regra de domínio (fonte única de "overdue") -------
    def is_overdue(self):
        if not self.due_date:
            return False
        if self.status in CLOSED_STATUSES:
            return False
        return self.due_date < now_utc()

    # ------- serialização (variantes preservam os contratos originais) -------
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
            'tags': self.tags.split(',') if self.tags else [],
        }

    def to_dict_with_overdue(self):
        data = self.to_dict()
        data['overdue'] = self.is_overdue()
        return data

    def to_dict_full(self):
        data = self.to_dict_with_overdue()
        data['user_name'] = self.user.name if self.user else None
        data['category_name'] = self.category.name if self.category else None
        return data

    def to_summary_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'created_at': str(self.created_at),
            'due_date': str(self.due_date) if self.due_date else None,
            'overdue': self.is_overdue(),
        }

    def touch(self):
        self.updated_at = now_utc()

    # ------- acesso a dados -------
    @classmethod
    def get(cls, task_id):
        return db.session.get(cls, task_id)

    @classmethod
    def all(cls):
        return cls.query.all()

    @classmethod
    def count(cls):
        return cls.query.count()

    @classmethod
    def count_by_status(cls, status):
        return cls.query.filter_by(status=status).count()

    @classmethod
    def count_by_priority(cls, priority):
        return cls.query.filter_by(priority=priority).count()

    @classmethod
    def count_by_category(cls, category_id):
        return cls.query.filter_by(category_id=category_id).count()

    @classmethod
    def for_category(cls, category_id):
        return cls.query.filter_by(category_id=category_id).all()

    @classmethod
    def for_user(cls, user_id):
        return cls.query.filter_by(user_id=user_id).all()

    @classmethod
    def created_since(cls, since):
        return cls.query.filter(cls.created_at >= since).count()

    @classmethod
    def completed_since(cls, since):
        return cls.query.filter(cls.status == 'done', cls.updated_at >= since).count()

    @classmethod
    def search(cls, query=None, status=None, priority=None, user_id=None):
        q = cls.query
        if query:
            q = q.filter(db.or_(
                cls.title.like(f'%{query}%'),
                cls.description.like(f'%{query}%'),
            ))
        if status:
            q = q.filter(cls.status == status)
        if priority:
            q = q.filter(cls.priority == int(priority))
        if user_id:
            q = q.filter(cls.user_id == int(user_id))
        return q.all()

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()
