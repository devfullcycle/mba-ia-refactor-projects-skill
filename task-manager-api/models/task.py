from sqlalchemy import case, func
from sqlalchemy.orm import joinedload

from config.constants import CLOSED_STATUSES, DEFAULT_PRIORITY, STATUS_DONE, STATUS_PENDING
from database import db
from models.base import CrudMixin
from utils.helpers import utc_now


class Task(CrudMixin, db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default=STATUS_PENDING)
    priority = db.Column(db.Integer, default=DEFAULT_PRIORITY)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)
    due_date = db.Column(db.DateTime, nullable=True)
    tags = db.Column(db.String(500), nullable=True)

    # Apagar o usuário apaga suas tasks (comportamento original de DELETE /users/<id>).
    user = db.relationship('User', backref=db.backref('tasks', cascade='all'))
    category = db.relationship('Category', backref='tasks')

    # ------------------------------------------------------------------ regras
    def is_overdue(self, now=None):
        """Atrasada: tem prazo vencido e ainda não foi concluída/cancelada."""
        if not self.due_date:
            return False
        now = now or utc_now()
        return self.due_date < now and self.status not in CLOSED_STATUSES

    # ------------------------------------------------------------ serialização
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

    def to_brief_dict(self):
        """Visão resumida usada em GET /users/<id>/tasks."""
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

    # ---------------------------------------------------------- acesso a dados
    @classmethod
    def list_with_relations(cls):
        """Todas as tasks com usuário e categoria carregados em uma consulta (sem N+1)."""
        return (
            cls.query
            .options(joinedload(cls.user), joinedload(cls.category))
            .order_by(cls.id)
            .all()
        )

    @classmethod
    def find_by_user(cls, user_id):
        return cls.query.filter_by(user_id=user_id).order_by(cls.id).all()

    @classmethod
    def search(cls, text=None, status=None, priority=None, user_id=None):
        query = cls.query
        if text:
            pattern = f'%{text}%'  # valor vai como parâmetro vinculado, nunca no SQL
            query = query.filter(db.or_(cls.title.like(pattern), cls.description.like(pattern)))
        if status:
            query = query.filter(cls.status == status)
        if priority is not None:
            query = query.filter(cls.priority == priority)
        if user_id is not None:
            query = query.filter(cls.user_id == user_id)
        return query.order_by(cls.id).all()

    @classmethod
    def count_all(cls):
        return cls.query.count()

    @classmethod
    def count_by_status(cls):
        rows = db.session.query(cls.status, func.count(cls.id)).group_by(cls.status).all()
        return dict(rows)

    @classmethod
    def count_by_priority(cls):
        rows = db.session.query(cls.priority, func.count(cls.id)).group_by(cls.priority).all()
        return dict(rows)

    @classmethod
    def count_created_since(cls, moment):
        return cls.query.filter(cls.created_at >= moment).count()

    @classmethod
    def count_done_updated_since(cls, moment):
        return cls.query.filter(cls.status == STATUS_DONE, cls.updated_at >= moment).count()

    @classmethod
    def _overdue_query(cls, now):
        """Mesma regra de `is_overdue`, aplicada no banco."""
        return cls.query.filter(
            cls.due_date.isnot(None), cls.due_date < now, cls.status.notin_(CLOSED_STATUSES)
        )

    @classmethod
    def list_overdue(cls, now=None):
        return cls._overdue_query(now or utc_now()).order_by(cls.id).all()

    @classmethod
    def count_overdue(cls, now=None):
        return cls._overdue_query(now or utc_now()).count()

    @classmethod
    def totals_by_user(cls):
        """{user_id: (total, concluídas)} em uma única consulta agregada."""
        done = func.sum(case((cls.status == STATUS_DONE, 1), else_=0))
        rows = (
            db.session.query(cls.user_id, func.count(cls.id), done)
            .filter(cls.user_id.isnot(None))
            .group_by(cls.user_id)
            .all()
        )
        return {user_id: (total, int(completed or 0)) for user_id, total, completed in rows}

    @classmethod
    def totals_by_category(cls):
        """{category_id: total} em uma única consulta agregada."""
        rows = (
            db.session.query(cls.category_id, func.count(cls.id))
            .filter(cls.category_id.isnot(None))
            .group_by(cls.category_id)
            .all()
        )
        return dict(rows)
