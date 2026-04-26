from database import db
from models.category import Category
from models.task import Task


class CategoryController:

    @staticmethod
    def get_all():
        categories = Category.query.all()
        return [
            {
                **cat.to_dict(),
                'task_count': Task.query.filter_by(category_id=cat.id).count(),
            }
            for cat in categories
        ], 200

    @staticmethod
    def create(data):
        if not data:
            return {'error': 'Dados inválidos'}, 400

        name = data.get('name')
        if not name:
            return {'error': 'Nome é obrigatório'}, 400

        category = Category()
        category.name = name
        category.description = data.get('description', '')
        category.color = data.get('color', '#000000')

        db.session.add(category)
        db.session.commit()
        return category.to_dict(), 201

    @staticmethod
    def update(category_id, data):
        category = db.session.get(Category, category_id)
        if not category:
            return {'error': 'Categoria não encontrada'}, 404

        if 'name' in data:
            category.name = data['name']
        if 'description' in data:
            category.description = data['description']
        if 'color' in data:
            category.color = data['color']

        db.session.commit()
        return category.to_dict(), 200

    @staticmethod
    def delete(category_id):
        category = db.session.get(Category, category_id)
        if not category:
            return {'error': 'Categoria não encontrada'}, 404

        db.session.delete(category)
        db.session.commit()
        return {'message': 'Categoria deletada'}, 200
