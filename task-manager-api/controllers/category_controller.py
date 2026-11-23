import logging
from sqlalchemy import func
from database import db
from models.category import Category
from models.task import Task

logger = logging.getLogger(__name__)

class CategoryController:

    @staticmethod
    def get_all_categories():
        """Recupera categorias e quantidade de tarefas com query agregada única (sem N+1)."""
        results = (
            db.session.query(Category, func.count(Task.id).label('task_count'))
            .outerjoin(Task, Task.category_id == Category.id)
            .group_by(Category.id)
            .all()
        )
        output = []
        for cat, task_count in results:
            cat_data = cat.to_dict()
            cat_data['task_count'] = task_count
            output.append(cat_data)
        return output, 200

    @staticmethod
    def create_category(data: dict):
        if not data:
            return {'error': 'Dados inválidos'}, 400

        name = data.get('name')
        if not name:
            return {'error': 'Nome é obrigatório'}, 400

        category = Category()
        category.name = str(name).strip()
        category.description = data.get('description', '')
        category.color = data.get('color', '#000000')

        try:
            db.session.add(category)
            db.session.commit()
            logger.info(f"Categoria criada: ID {category.id} - '{category.name}'")
            return category.to_dict(), 201
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao criar categoria: {str(e)}", exc_info=True)
            return {'error': 'Erro ao criar categoria'}, 500

    @staticmethod
    def update_category(cat_id: int, data: dict):
        cat = db.session.get(Category, cat_id)
        if not cat:
            return {'error': 'Categoria não encontrada'}, 404

        if not data:
            return {'error': 'Dados inválidos'}, 400

        if 'name' in data:
            cat.name = str(data['name']).strip()
        if 'description' in data:
            cat.description = data['description']
        if 'color' in data:
            cat.color = data['color']

        try:
            db.session.commit()
            logger.info(f"Categoria atualizada: ID {cat_id}")
            return cat.to_dict(), 200
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao atualizar categoria {cat_id}: {str(e)}", exc_info=True)
            return {'error': 'Erro ao atualizar'}, 500

    @staticmethod
    def delete_category(cat_id: int):
        cat = db.session.get(Category, cat_id)
        if not cat:
            return {'error': 'Categoria não encontrada'}, 404

        try:
            # Validação e desvinculação prévia dos registros dependentes (tasks)
            dependent_tasks = Task.query.filter_by(category_id=cat_id).all()
            if dependent_tasks:
                logger.info(f"Desvinculando {len(dependent_tasks)} tarefa(s) da categoria ID {cat_id}")
                for task in dependent_tasks:
                    task.category_id = None

            db.session.delete(cat)
            db.session.commit()
            logger.info(f"Categoria deletada: ID {cat_id}")
            return {'message': 'Categoria deletada'}, 200
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao deletar categoria {cat_id}: {str(e)}", exc_info=True)
            return {'error': 'Erro ao deletar'}, 500
