from database import db
from models.task import Task
from models.user import User
from models.category import Category
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import or_
from utils.helpers import parse_date, VALID_STATUSES, MAX_TITLE_LENGTH, MIN_TITLE_LENGTH, DEFAULT_PRIORITY


class TaskController:

    @staticmethod
    def get_all(page=None, per_page=20):
        query = Task.query.options(
            joinedload(Task.user),
            joinedload(Task.category)
        )

        if page is not None:
            pagination = query.paginate(page=page, per_page=per_page, error_out=False)
            items = pagination.items
            meta = {
                'total': pagination.total,
                'page': pagination.page,
                'per_page': pagination.per_page,
                'pages': pagination.pages,
            }
        else:
            items = query.all()
            meta = None

        result = []
        for t in items:
            data = t.to_dict()
            data['overdue'] = t.is_overdue()
            data['user_name'] = t.user.name if t.user else None
            data['category_name'] = t.category.name if t.category else None
            result.append(data)

        if meta:
            return {'items': result, **meta}, 200
        return result, 200

    @staticmethod
    def get_by_id(task_id):
        task = Task.query.get(task_id)
        if not task:
            return {'error': 'Task não encontrada'}, 404
        data = task.to_dict()
        data['overdue'] = task.is_overdue()
        return data, 200

    @staticmethod
    def create(data):
        title = (data.get('title') or '').strip()
        if not title:
            return {'error': 'Título é obrigatório'}, 400
        if len(title) < MIN_TITLE_LENGTH:
            return {'error': f'Título deve ter no mínimo {MIN_TITLE_LENGTH} caracteres'}, 400
        if len(title) > MAX_TITLE_LENGTH:
            return {'error': f'Título deve ter no máximo {MAX_TITLE_LENGTH} caracteres'}, 400

        status = data.get('status', 'pending')
        if status not in VALID_STATUSES:
            return {'error': 'Status inválido'}, 400

        priority = data.get('priority', DEFAULT_PRIORITY)
        if not isinstance(priority, int) or priority < 1 or priority > 5:
            return {'error': 'Prioridade deve ser entre 1 e 5'}, 400

        user_id = data.get('user_id')
        if user_id and not User.query.get(user_id):
            return {'error': 'Usuário não encontrado'}, 404

        category_id = data.get('category_id')
        if category_id and not Category.query.get(category_id):
            return {'error': 'Categoria não encontrada'}, 404

        task = Task(
            title=title,
            description=data.get('description', ''),
            status=status,
            priority=priority,
            user_id=user_id,
            category_id=category_id,
        )

        due_date_str = data.get('due_date')
        if due_date_str:
            parsed = parse_date(due_date_str)
            if not parsed:
                return {'error': 'Formato de data inválido. Use YYYY-MM-DD'}, 400
            task.due_date = parsed

        tags = data.get('tags')
        if tags:
            task.tags = ','.join(tags) if isinstance(tags, list) else tags

        try:
            db.session.add(task)
            db.session.commit()
            return task.to_dict(), 201
        except SQLAlchemyError:
            db.session.rollback()
            raise

    @staticmethod
    def update(task_id, data):
        task = Task.query.get(task_id)
        if not task:
            return {'error': 'Task não encontrada'}, 404

        if 'title' in data:
            title = (data['title'] or '').strip()
            if len(title) < MIN_TITLE_LENGTH:
                return {'error': 'Título muito curto'}, 400
            if len(title) > MAX_TITLE_LENGTH:
                return {'error': 'Título muito longo'}, 400
            task.title = title

        if 'description' in data:
            task.description = data['description']

        if 'status' in data:
            if data['status'] not in VALID_STATUSES:
                return {'error': 'Status inválido'}, 400
            task.status = data['status']

        if 'priority' in data:
            if not isinstance(data['priority'], int) or data['priority'] < 1 or data['priority'] > 5:
                return {'error': 'Prioridade deve ser entre 1 e 5'}, 400
            task.priority = data['priority']

        if 'user_id' in data:
            if data['user_id'] and not User.query.get(data['user_id']):
                return {'error': 'Usuário não encontrado'}, 404
            task.user_id = data['user_id']

        if 'category_id' in data:
            if data['category_id'] and not Category.query.get(data['category_id']):
                return {'error': 'Categoria não encontrada'}, 404
            task.category_id = data['category_id']

        if 'due_date' in data:
            if data['due_date']:
                parsed = parse_date(data['due_date'])
                if not parsed:
                    return {'error': 'Formato de data inválido'}, 400
                task.due_date = parsed
            else:
                task.due_date = None

        if 'tags' in data:
            tags = data['tags']
            task.tags = ','.join(tags) if isinstance(tags, list) else tags

        from datetime import datetime
        task.updated_at = datetime.utcnow()

        try:
            db.session.commit()
            return task.to_dict(), 200
        except SQLAlchemyError:
            db.session.rollback()
            raise

    @staticmethod
    def delete(task_id):
        task = Task.query.get(task_id)
        if not task:
            return {'error': 'Task não encontrada'}, 404

        try:
            db.session.delete(task)
            db.session.commit()
            return {'message': 'Task deletada com sucesso'}, 200
        except SQLAlchemyError:
            db.session.rollback()
            raise

    @staticmethod
    def search(q='', status='', priority='', user_id=''):
        query = Task.query

        if q:
            query = query.filter(
                or_(
                    Task.title.like(f'%{q}%'),
                    Task.description.like(f'%{q}%')
                )
            )
        if status:
            query = query.filter(Task.status == status)
        if priority:
            query = query.filter(Task.priority == int(priority))
        if user_id:
            query = query.filter(Task.user_id == int(user_id))

        return [t.to_dict() for t in query.all()], 200

    @staticmethod
    def get_stats():
        total = Task.query.count()
        pending = Task.query.filter_by(status='pending').count()
        in_progress = Task.query.filter_by(status='in_progress').count()
        done = Task.query.filter_by(status='done').count()
        cancelled = Task.query.filter_by(status='cancelled').count()
        overdue_count = sum(1 for t in Task.query.all() if t.is_overdue())

        return {
            'total': total,
            'pending': pending,
            'in_progress': in_progress,
            'done': done,
            'cancelled': cancelled,
            'overdue': overdue_count,
            'completion_rate': round((done / total) * 100, 2) if total > 0 else 0,
        }, 200
