from sqlalchemy import func

from src.config.database import db
from src.utils.dates import format_datetime, utc_now

DEFAULT_COLOR = "#000000"
NAME_MAX_LENGTH = 100
DESCRIPTION_MAX_LENGTH = 300


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(NAME_MAX_LENGTH), nullable=False)
    description = db.Column(db.String(DESCRIPTION_MAX_LENGTH), nullable=True)
    color = db.Column(db.String(7), default=DEFAULT_COLOR)
    created_at = db.Column(db.DateTime, default=utc_now)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "color": self.color,
            "created_at": format_datetime(self.created_at),
        }


def find_by_id(category_id):
    return db.session.get(Category, category_id)


def list_with_task_count():
    """Categorias + total de tasks em uma única query (antes: 1 COUNT por categoria)."""
    from src.models.task import Task

    return (
        db.session.query(Category, func.count(Task.id))
        .outerjoin(Task, Task.category_id == Category.id)
        .group_by(Category.id)
        .order_by(Category.id)
        .all()
    )


def count():
    return db.session.query(func.count(Category.id)).scalar()


def create(**fields):
    category = Category(**fields)
    db.session.add(category)
    db.session.commit()
    return category


def save():
    db.session.commit()


def delete(category):
    """Desvincula as tasks e remove a categoria na mesma transação (sem FKs órfãs)."""
    from src.models.task import Task

    Task.query.filter_by(category_id=category.id).update({Task.category_id: None})
    db.session.delete(category)
    db.session.commit()
