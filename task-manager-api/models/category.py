from sqlalchemy import func

from database import db
from utils.clock import utcnow

DEFAULT_COLOR = "#000000"
COLOR_LENGTH = 7


def is_valid_color(color):
    return isinstance(color, str) and len(color) == COLOR_LENGTH and color.startswith("#")


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(300), nullable=True)
    color = db.Column(db.String(COLOR_LENGTH), default=DEFAULT_COLOR)
    created_at = db.Column(db.DateTime, default=utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "color": self.color,
            "created_at": str(self.created_at),
        }

    @staticmethod
    def get(category_id):
        return db.session.get(Category, category_id)

    @staticmethod
    def all():
        return db.session.execute(db.select(Category).order_by(Category.id)).scalars().all()

    @staticmethod
    def count():
        return db.session.scalar(db.select(func.count(Category.id)))
