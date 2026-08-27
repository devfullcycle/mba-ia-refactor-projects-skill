from flask import request, jsonify
from database import db
from models.category import Category
from models.task import Task

def get_categories():
    try:
        categories = Category.query.all()
        result = []
        for c in categories:
            cat_data = c.to_dict()
            cat_data['task_count'] = Task.query.filter_by(category_id=c.id).count()
            result.append(cat_data)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def create_category():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Dados inválidos'}), 400

        name = data.get('name')
        if not name:
            return jsonify({'error': 'Nome é obrigatório'}), 400

        category = Category()
        category.name = name
        category.description = data.get('description', '')
        category.color = data.get('color', '#000000')

        db.session.add(category)
        db.session.commit()
        return jsonify(category.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao criar categoria: {str(e)}'}), 500

def update_category(cat_id):
    try:
        cat = Category.query.get(cat_id)
        if not cat:
            return jsonify({'error': 'Categoria não encontrada'}), 404

        data = request.get_json()
        if not data:
            return jsonify({'error': 'Dados inválidos'}), 400

        if 'name' in data:
            cat.name = data['name']
        if 'description' in data:
            cat.description = data['description']
        if 'color' in data:
            cat.color = data['color']

        db.session.commit()
        return jsonify(cat.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao atualizar: {str(e)}'}), 500

def delete_category(cat_id):
    try:
        cat = Category.query.get(cat_id)
        if not cat:
            return jsonify({'error': 'Categoria não encontrada'}), 404

        db.session.delete(cat)
        db.session.commit()
        return jsonify({'message': 'Categoria deletada com sucesso'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao deletar: {str(e)}'}), 500
