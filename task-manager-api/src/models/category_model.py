from src.models.database import db, utcnow

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
    def __init__(self, database):
        self.db = database

    def get(self, category_id):
        return self.db.session.get(Category, category_id)

    def list_all(self):
        return self.db.session.execute(self.db.select(Category).order_by(Category.id)).scalars().all()

    def count(self):
        return self.db.session.execute(self.db.select(self.db.func.count(Category.id))).scalar_one()

    def add(self, category):
        self.db.session.add(category)

    def delete(self, category):
        self.db.session.delete(category)

    def commit(self):
        self.db.session.commit()
