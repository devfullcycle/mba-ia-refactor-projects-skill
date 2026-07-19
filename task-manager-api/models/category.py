from database import db
from utils.constants import DEFAULT_COLOR
from utils.datetime_utils import now_utc


class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(300), nullable=True)
    color = db.Column(db.String(7), default=DEFAULT_COLOR)
    created_at = db.Column(db.DateTime, default=now_utc)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'color': self.color,
            'created_at': str(self.created_at),
        }

    # ------- acesso a dados -------
    @classmethod
    def get(cls, category_id):
        return db.session.get(cls, category_id)

    @classmethod
    def all(cls):
        return cls.query.all()

    @classmethod
    def count(cls):
        return cls.query.count()

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()
