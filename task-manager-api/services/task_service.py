from sqlalchemy.orm import joinedload

from database import db
from models.task import Task
from utils.helpers import now_utc


class TaskService:
    """Regra de negócio e consultas de tasks (antes espalhadas nas rotas)."""

    def list(self):
        # joinedload evita o N+1 (user/category carregados numa query).
        tasks = Task.query.options(
            joinedload(Task.user), joinedload(Task.category)
        ).all()
        result = []
        for t in tasks:
            data = t.to_dict()
            data['user_name'] = t.user.name if t.user else None
            data['category_name'] = t.category.name if t.category else None
            result.append(data)
        return result

    def get(self, task_id):
        return db.session.get(Task, task_id)

    def search(self, query=None, status=None, priority=None, user_id=None):
        q = Task.query
        if query:
            q = q.filter(db.or_(
                Task.title.like(f'%{query}%'),
                Task.description.like(f'%{query}%'),
            ))
        if status:
            q = q.filter(Task.status == status)
        if priority:
            q = q.filter(Task.priority == int(priority))
        if user_id:
            q = q.filter(Task.user_id == int(user_id))
        return [t.to_dict() for t in q.all()]

    def create(self, data):
        task = Task()
        task.title = data['title']
        task.description = data.get('description', '')
        task.status = data.get('status', 'pending')
        task.priority = data.get('priority', 3)
        task.user_id = data.get('user_id')
        task.category_id = data.get('category_id')
        if data.get('due_date_parsed') is not None:
            task.due_date = data['due_date_parsed']
        if data.get('tags') is not None:
            task.tags = data['tags']
        db.session.add(task)
        db.session.commit()
        return task

    def update(self, task, data):
        for field in ('title', 'description', 'status', 'priority', 'user_id', 'category_id'):
            if field in data:
                setattr(task, field, data[field])
        if 'due_date_parsed' in data:
            task.due_date = data['due_date_parsed']
        if 'tags' in data:
            task.tags = data['tags']
        task.updated_at = now_utc()
        db.session.commit()
        return task

    def delete(self, task):
        db.session.delete(task)
        db.session.commit()

    def stats(self):
        counts = {s: Task.query.filter_by(status=s).count()
                  for s in ('pending', 'in_progress', 'done', 'cancelled')}
        total = Task.query.count()
        overdue = sum(1 for t in Task.query.all() if t.is_overdue())
        return {
            'total': total,
            'pending': counts['pending'],
            'in_progress': counts['in_progress'],
            'done': counts['done'],
            'cancelled': counts['cancelled'],
            'overdue': overdue,
            'completion_rate': round((counts['done'] / total) * 100, 2) if total > 0 else 0,
        }
