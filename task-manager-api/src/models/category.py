"""Model de Categoria — entidade e acesso a dados do agregado."""
from sqlalchemy import func, select

from src.domain.constants import DEFAULT_COLOR
from src.extensions import db
from src.utils.datetime_utils import now_utc


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(300), nullable=True)
    color = db.Column(db.String(7), default=DEFAULT_COLOR)
    created_at = db.Column(db.DateTime, default=now_utc)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "color": self.color,
            "created_at": str(self.created_at),
        }

    # --- acesso a dados ---

    @staticmethod
    def get(category_id):
        return db.session.get(Category, category_id)

    @staticmethod
    def list_with_task_counts():
        """Categorias com contagem de tarefas em uma query (o legado fazia um COUNT por
        categoria dentro do laço)."""
        from src.models.task import Task

        rows = db.session.execute(
            select(Category, func.count(Task.id))
            .outerjoin(Task, Task.category_id == Category.id)
            .group_by(Category.id)
            .order_by(Category.id)
        ).all()
        return [(category, total) for category, total in rows]

    @staticmethod
    def count():
        return db.session.scalar(select(func.count(Category.id))) or 0
