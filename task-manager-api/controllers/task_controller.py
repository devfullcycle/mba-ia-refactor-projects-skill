import logging
from datetime import datetime, timezone
from sqlalchemy.orm import joinedload
from database import db
from models.task import Task
from models.user import User
from models.category import Category
from utils.helpers import parse_date

logger = logging.getLogger(__name__)

class TaskController:

    @staticmethod
    def get_all_tasks():
        """Recupera todas as tarefas usando joinedload para eliminar o problema de N+1 queries."""
        tasks = Task.query.options(joinedload(Task.user), joinedload(Task.category)).all()
        result = []
        for t in tasks:
            task_data = t.to_dict()
            task_data['overdue'] = t.is_overdue()
            task_data['user_name'] = t.user.name if t.user else None
            task_data['category_name'] = t.category.name if t.category else None
            result.append(task_data)
        return result, 200

    @staticmethod
    def get_task_by_id(task_id: int):
        task = Task.query.options(joinedload(Task.user), joinedload(Task.category)).filter(Task.id == task_id).first()
        if not task:
            return {'error': 'Task não encontrada'}, 404
        data = task.to_dict()
        data['overdue'] = task.is_overdue()
        return data, 200

    @staticmethod
    def create_task(data: dict):
        if not data:
            return {'error': 'Dados inválidos'}, 400

        title = data.get('title')
        if not title:
            return {'error': 'Título é obrigatório'}, 400

        title = str(title).strip()
        if len(title) < 3:
            return {'error': 'Título muito curto'}, 400
        if len(title) > 200:
            return {'error': 'Título muito longo'}, 400

        status = data.get('status', 'pending')
        if not Task.is_valid_status(status):
            return {'error': 'Status inválido'}, 400

        priority = data.get('priority', 3)
        try:
            priority = int(priority)
            if not Task.is_valid_priority(priority):
                return {'error': 'Prioridade deve ser entre 1 e 5'}, 400
        except (ValueError, TypeError):
            return {'error': 'Prioridade deve ser entre 1 e 5'}, 400

        user_id = data.get('user_id')
        if user_id:
            user = db.session.get(User, user_id)
            if not user:
                return {'error': 'Usuário não encontrado'}, 404

        category_id = data.get('category_id')
        if category_id:
            cat = db.session.get(Category, category_id)
            if not cat:
                return {'error': 'Categoria não encontrada'}, 404

        task = Task()
        task.title = title
        task.description = data.get('description', '')
        task.status = status
        task.priority = priority
        task.user_id = user_id
        task.category_id = category_id

        due_date_str = data.get('due_date')
        if due_date_str:
            parsed = parse_date(due_date_str)
            if not parsed:
                return {'error': 'Formato de data inválido. Use YYYY-MM-DD'}, 400
            task.due_date = parsed

        tags = data.get('tags')
        if tags:
            task.tags = ','.join(tags) if isinstance(tags, list) else str(tags)

        try:
            db.session.add(task)
            db.session.commit()
            logger.info(f"Task criada com sucesso: ID {task.id} - '{task.title}'")
            return task.to_dict(), 201
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao persistir task: {str(e)}", exc_info=True)
            return {'error': 'Erro ao criar task'}, 500

    @staticmethod
    def update_task(task_id: int, data: dict):
        task = db.session.get(Task, task_id)
        if not task:
            return {'error': 'Task não encontrada'}, 404

        if not data:
            return {'error': 'Dados inválidos'}, 400

        if 'title' in data:
            title = str(data['title']).strip()
            if len(title) < 3:
                return {'error': 'Título muito curto'}, 400
            if len(title) > 200:
                return {'error': 'Título muito longo'}, 400
            task.title = title

        if 'description' in data:
            task.description = data['description']

        if 'status' in data:
            if not Task.is_valid_status(data['status']):
                return {'error': 'Status inválido'}, 400
            task.status = data['status']

        if 'priority' in data:
            try:
                p = int(data['priority'])
                if not Task.is_valid_priority(p):
                    return {'error': 'Prioridade deve ser entre 1 e 5'}, 400
                task.priority = p
            except (ValueError, TypeError):
                return {'error': 'Prioridade deve ser entre 1 e 5'}, 400

        if 'user_id' in data:
            user_id = data['user_id']
            if user_id:
                user = db.session.get(User, user_id)
                if not user:
                    return {'error': 'Usuário não encontrado'}, 404
            task.user_id = user_id

        if 'category_id' in data:
            category_id = data['category_id']
            if category_id:
                cat = db.session.get(Category, category_id)
                if not cat:
                    return {'error': 'Categoria não encontrada'}, 404
            task.category_id = category_id

        if 'due_date' in data:
            due_val = data['due_date']
            if due_val:
                parsed = parse_date(due_val)
                if not parsed:
                    return {'error': 'Formato de data inválido'}, 400
                task.due_date = parsed
            else:
                task.due_date = None

        if 'tags' in data:
            tags = data['tags']
            task.tags = ','.join(tags) if isinstance(tags, list) else (str(tags) if tags else None)

        task.updated_at = datetime.now(timezone.utc)

        try:
            db.session.commit()
            logger.info(f"Task atualizada com sucesso: ID {task.id}")
            return task.to_dict(), 200
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao atualizar task {task_id}: {str(e)}", exc_info=True)
            return {'error': 'Erro ao atualizar'}, 500

    @staticmethod
    def delete_task(task_id: int):
        task = db.session.get(Task, task_id)
        if not task:
            return {'error': 'Task não encontrada'}, 404

        try:
            db.session.delete(task)
            db.session.commit()
            logger.info(f"Task deletada com sucesso: ID {task_id}")
            return {'message': 'Task deletada com sucesso'}, 200
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao deletar task {task_id}: {str(e)}", exc_info=True)
            return {'error': 'Erro ao deletar'}, 500

    @staticmethod
    def search_tasks(query: str = '', status: str = '', priority: str = '', user_id: str = ''):
        tasks_query = Task.query

        if query:
            tasks_query = tasks_query.filter(
                db.or_(
                    Task.title.like(f'%{query}%'),
                    Task.description.like(f'%{query}%')
                )
            )

        if status:
            tasks_query = tasks_query.filter(Task.status == status)

        if priority:
            try:
                tasks_query = tasks_query.filter(Task.priority == int(priority))
            except ValueError:
                pass

        if user_id:
            try:
                tasks_query = tasks_query.filter(Task.user_id == int(user_id))
            except ValueError:
                pass

        results = tasks_query.all()
        return [t.to_dict() for t in results], 200

    @staticmethod
    def get_task_stats():
        total = Task.query.count()
        pending = Task.query.filter_by(status='pending').count()
        in_progress = Task.query.filter_by(status='in_progress').count()
        done = Task.query.filter_by(status='done').count()
        cancelled = Task.query.filter_by(status='cancelled').count()

        all_tasks = Task.query.all()
        overdue_count = sum(1 for t in all_tasks if t.is_overdue())

        stats = {
            'total': total,
            'pending': pending,
            'in_progress': in_progress,
            'done': done,
            'cancelled': cancelled,
            'overdue': overdue_count,
            'completion_rate': round((done / total) * 100, 2) if total > 0 else 0
        }
        return stats, 200
