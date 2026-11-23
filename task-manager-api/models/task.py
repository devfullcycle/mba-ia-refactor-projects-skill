from sqlalchemy import and_, func, or_, select

from database import db
from utils.clock import utc_now
from utils.constants import DEFAULT_PRIORITY, DEFAULT_STATUS, FINISHED_STATUSES


class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default=DEFAULT_STATUS)
    priority = db.Column(db.Integer, default=DEFAULT_PRIORITY)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)
    due_date = db.Column(db.DateTime, nullable=True)
    tags = db.Column(db.String(500), nullable=True)

    user = db.relationship('User', back_populates='tasks')
    category = db.relationship('Category', back_populates='tasks')

    def is_overdue(self, now=None):
        """Atrasada: tem prazo vencido e ainda não foi concluída/cancelada."""
        if not self.due_date or self.status in FINISHED_STATUSES:
            return False
        return self.due_date < (now or utc_now())

    @classmethod
    def overdue_clause(cls, now=None):
        """Mesma regra de is_overdue(), como expressão SQL (evita carregar tudo em memória)."""
        return and_(
            cls.due_date.is_not(None),
            cls.due_date < (now or utc_now()),
            or_(cls.status.is_(None), cls.status.not_in(FINISHED_STATUSES)),
        )

    @classmethod
    def counts_by(cls, column):
        """{valor da FK: nº de tasks} numa única agregação (ignora tasks sem a FK)."""
        return dict(db.session.execute(
            select(column, func.count()).where(column.is_not(None)).group_by(column)
        ).all())
