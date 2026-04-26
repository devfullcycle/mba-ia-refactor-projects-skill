from database import db
from models.task import Task
from models.user import User
from models.category import Category
from utils.helpers import VALID_STATUSES, MIN_TITLE_LENGTH, MAX_TITLE_LENGTH, DEFAULT_PRIORITY
from datetime import datetime, timezone


class TaskController:

    @staticmethod
    def get_all():
        tasks = Task.query.options(db.joinedload(Task.user), db.joinedload(Task.category)).all()
        result = []
        for task in tasks:
            data = task.to_dict()
            data['overdue'] = task.is_overdue()
            data['user_name'] = task.user.name if task.user else None
            data['category_name'] = task.category.name if task.category else None
            result.append(data)
        return result, 200

    @staticmethod
    def get_by_id(task_id):
        task = db.session.get(Task, task_id)
        if not task:
            return {'error': 'Task não encontrada'}, 404
        data = task.to_dict()
        data['overdue'] = task.is_overdue()
        return data, 200

    @staticmethod
    def create(data):
        if not data:
            return {'error': 'Dados inválidos'}, 400

        title = data.get('title')
        if not title:
            return {'error': 'Título é obrigatório'}, 400
        title = title.strip()
        if len(title) < MIN_TITLE_LENGTH:
            return {'error': 'Título muito curto'}, 400
        if len(title) > MAX_TITLE_LENGTH:
            return {'error': 'Título muito longo'}, 400

        status = data.get('status', 'pending')
        if status not in VALID_STATUSES:
            return {'error': 'Status inválido'}, 400

        priority = data.get('priority', DEFAULT_PRIORITY)
        try:
            priority = int(priority)
        except (TypeError, ValueError):
            return {'error': 'Prioridade inválida'}, 400
        if priority < 1 or priority > 5:
            return {'error': 'Prioridade deve ser entre 1 e 5'}, 400

        user_id = data.get('user_id')
        if user_id:
            if not db.session.get(User, user_id):
                return {'error': 'Usuário não encontrado'}, 404

        category_id = data.get('category_id')
        if category_id:
            if not db.session.get(Category, category_id):
                return {'error': 'Categoria não encontrada'}, 404

        task = Task()
        task.title = title
        task.description = data.get('description', '')
        task.status = status
        task.priority = priority
        task.user_id = user_id
        task.category_id = category_id

        due_date = data.get('due_date')
        if due_date:
            try:
                task.due_date = datetime.strptime(due_date, '%Y-%m-%d').replace(tzinfo=timezone.utc)
            except (ValueError, TypeError):
                return {'error': 'Formato de data inválido. Use YYYY-MM-DD'}, 400

        tags = data.get('tags')
        if tags:
            task.tags = ','.join(tags) if isinstance(tags, list) else tags

        db.session.add(task)
        db.session.commit()
        return task.to_dict(), 201

    @staticmethod
    def update(task_id, data):
        if not data:
            return {'error': 'Dados inválidos'}, 400

        task = db.session.get(Task, task_id)
        if not task:
            return {'error': 'Task não encontrada'}, 404

        if 'title' in data:
            title = data['title'].strip() if data['title'] else ''
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
            try:
                p = int(data['priority'])
            except (TypeError, ValueError):
                return {'error': 'Prioridade inválida'}, 400
            if p < 1 or p > 5:
                return {'error': 'Prioridade deve ser entre 1 e 5'}, 400
            task.priority = p

        if 'user_id' in data:
            if data['user_id']:
                if not db.session.get(User, data['user_id']):
                    return {'error': 'Usuário não encontrado'}, 404
            task.user_id = data['user_id']

        if 'category_id' in data:
            if data['category_id']:
                if not db.session.get(Category, data['category_id']):
                    return {'error': 'Categoria não encontrada'}, 404
            task.category_id = data['category_id']

        if 'due_date' in data:
            if data['due_date']:
                try:
                    task.due_date = datetime.strptime(data['due_date'], '%Y-%m-%d').replace(tzinfo=timezone.utc)
                except (ValueError, TypeError):
                    return {'error': 'Formato de data inválido'}, 400
            else:
                task.due_date = None

        if 'tags' in data:
            tags = data['tags']
            task.tags = ','.join(tags) if isinstance(tags, list) else tags

        task.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        return task.to_dict(), 200

    @staticmethod
    def delete(task_id):
        task = db.session.get(Task, task_id)
        if not task:
            return {'error': 'Task não encontrada'}, 404

        db.session.delete(task)
        db.session.commit()
        return {'message': 'Task deletada com sucesso'}, 200

    @staticmethod
    def search(query='', status='', priority='', user_id=''):
        tasks = Task.query

        if query:
            search_term = f'%{query}%'
            tasks = tasks.filter(
                db.or_(
                    Task.title.like(search_term),
                    Task.description.like(search_term),
                )
            )

        if status:
            tasks = tasks.filter(Task.status == status)

        if priority:
            try:
                tasks = tasks.filter(Task.priority == int(priority))
            except (TypeError, ValueError):
                pass

        if user_id:
            try:
                tasks = tasks.filter(Task.user_id == int(user_id))
            except (TypeError, ValueError):
                pass

        results = tasks.all()
        return [task.to_dict() for task in results], 200

    @staticmethod
    def stats():
        total = Task.query.count()
        if total == 0:
            return {
                'total': 0, 'pending': 0, 'in_progress': 0,
                'done': 0, 'cancelled': 0, 'overdue': 0,
                'completion_rate': 0,
            }, 200

        pending = Task.query.filter_by(status='pending').count()
        in_progress = Task.query.filter_by(status='in_progress').count()
        done = Task.query.filter_by(status='done').count()
        cancelled = Task.query.filter_by(status='cancelled').count()
        overdue = sum(1 for t in Task.query.filter(
            Task.due_date.isnot(None),
            Task.status.notin_(['done', 'cancelled']),
        ).all() if t.is_overdue())

        return {
            'total': total,
            'pending': pending,
            'in_progress': in_progress,
            'done': done,
            'cancelled': cancelled,
            'overdue': overdue,
            'completion_rate': round((done / total) * 100, 2),
        }, 200
