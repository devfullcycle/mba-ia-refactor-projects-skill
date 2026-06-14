from database import db
from models.category import Category
from models.task import Task
from sqlalchemy.exc import SQLAlchemyError


class CategoryController:

    @staticmethod
    def get_all():
        categories = Category.query.all()
        result = []
        for c in categories:
            data = c.to_dict()
            data['task_count'] = Task.query.filter_by(category_id=c.id).count()
            result.append(data)
        return result, 200

    @staticmethod
    def create(data):
        if not data:
            return {'error': 'Dados inválidos'}, 400
        name = data.get('name')
        if not name:
            return {'error': 'Nome é obrigatório'}, 400

        category = Category(
            name=name,
            description=data.get('description', ''),
            color=data.get('color', '#000000'),
        )
        try:
            db.session.add(category)
            db.session.commit()
            return category.to_dict(), 201
        except SQLAlchemyError:
            db.session.rollback()
            raise

    @staticmethod
    def update(cat_id, data):
        if not data:
            return {'error': 'Dados inválidos'}, 400
        cat = Category.query.get(cat_id)
        if not cat:
            return {'error': 'Categoria não encontrada'}, 404

        if 'name' in data:
            cat.name = data['name']
        if 'description' in data:
            cat.description = data['description']
        if 'color' in data:
            cat.color = data['color']

        try:
            db.session.commit()
            return cat.to_dict(), 200
        except SQLAlchemyError:
            db.session.rollback()
            raise

    @staticmethod
    def delete(cat_id):
        cat = Category.query.get(cat_id)
        if not cat:
            return {'error': 'Categoria não encontrada'}, 404

        try:
            db.session.delete(cat)
            db.session.commit()
            return {'message': 'Categoria deletada'}, 200
        except SQLAlchemyError:
            db.session.rollback()
            raise
