"""Category entity and repository."""
from src.models.constants import DEFAULT_COLOR
from src.models.database import BaseRepository, db, utcnow


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


class CategoryRepository(BaseRepository):
    model = Category

    def list_all(self):
        return self.session.execute(db.select(Category).order_by(Category.id)).scalars().all()

    def count(self):
        return self.session.execute(db.select(db.func.count(Category.id))).scalar_one()
