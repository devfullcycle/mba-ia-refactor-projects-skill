"""Category entity and its repository."""
from sqlalchemy import func, select

from .database import db, utcnow
from .task_model import Task

DEFAULT_COLOR = "#000000"


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(300), nullable=True)
    color = db.Column(db.String(7), default=DEFAULT_COLOR)
    created_at = db.Column(db.DateTime, default=utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "color": self.color,
            "created_at": str(self.created_at),
        }


class CategoryRepository:
    def __init__(self, session):
        self.session = session

    def get(self, category_id):
        return self.session.get(Category, category_id)

    def count(self):
        return self.session.scalar(select(func.count(Category.id)))

    def list_with_task_counts(self):
        stmt = (
            select(Category, func.count(Task.id))
            .outerjoin(Task, Task.category_id == Category.id)
            .group_by(Category.id)
            .order_by(Category.id)
        )
        return self.session.execute(stmt).all()

    def add(self, category):
        self.session.add(category)

    def delete(self, category):
        self.session.delete(category)

    def commit(self):
        self.session.commit()
