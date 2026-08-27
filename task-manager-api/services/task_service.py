from database import db
from models.task import Task
from models.user import User
from models.category import Category
from datetime import datetime, timezone
from services.notification_service import NotificationService

class TaskService:
    @staticmethod
    def get_tasks(filters):
        query = Task.query
        if filters.get('status'):
            query = query.filter_by(status=filters['status'])
        if filters.get('priority'):
            query = query.filter_by(priority=int(filters['priority']))
        if filters.get('user_id'):
            query = query.filter_by(user_id=int(filters['user_id']))
        if filters.get('category_id'):
            query = query.filter_by(category_id=int(filters['category_id']))
        return query.all()

    @staticmethod
    def get_task(task_id):
        return Task.query.get(task_id)

    @staticmethod
    def create_task(data):
        title = data.get('title')
        if not title:
            raise ValueError('Título é obrigatório')
        
        task = Task()
        task.title = title
        task.description = data.get('description', '')
        
        status = data.get('status', 'pending')
        if not task.validate_status(status):
            raise ValueError('Status inválido')
        task.status = status
        
        priority = data.get('priority', 3)
        if not task.validate_priority(priority):
            raise ValueError('Prioridade inválida')
        task.priority = priority
        
        user_id = data.get('user_id')
        user = None
        if user_id:
            user = User.query.get(user_id)
            if not user:
                raise ValueError('Usuário associado não existe')
            task.user_id = user_id
            
        category_id = data.get('category_id')
        if category_id:
            category = Category.query.get(category_id)
            if not category:
                raise ValueError('Categoria associada não existe')
            task.category_id = category_id
            
        due_date_str = data.get('due_date')
        if due_date_str:
            try:
                task.due_date = datetime.fromisoformat(due_date_str.replace('Z', '+00:00'))
            except:
                raise ValueError('Formato de data inválido')
        
        tags = data.get('tags', [])
        if isinstance(tags, list):
            task.tags = ','.join(tags)
            
        db.session.add(task)
        db.session.commit()
        
        if user:
            try:
                ns = NotificationService()
                ns.notify_task_assigned(user, task)
            except Exception as e:
                print(f"Erro notificação: {str(e)}")
                
        return task

    @staticmethod
    def update_task(task_id, data):
        task = Task.query.get(task_id)
        if not task:
            return None
            
        if 'title' in data:
            task.title = data['title']
        if 'description' in data:
            task.description = data['description']
        if 'status' in data:
            if not task.validate_status(data['status']):
                raise ValueError('Status inválido')
            task.status = data['status']
        if 'priority' in data:
            if not task.validate_priority(data['priority']):
                raise ValueError('Prioridade inválida')
            task.priority = data['priority']
        if 'user_id' in data:
            if data['user_id']:
                if not User.query.get(data['user_id']):
                    raise ValueError('Usuário não existe')
                task.user_id = data['user_id']
            else:
                task.user_id = None
        if 'category_id' in data:
            if data['category_id']:
                if not Category.query.get(data['category_id']):
                    raise ValueError('Categoria não existe')
                task.category_id = data['category_id']
            else:
                task.category_id = None
        if 'due_date' in data:
            if data['due_date']:
                try:
                    task.due_date = datetime.fromisoformat(data['due_date'].replace('Z', '+00:00'))
                except:
                    raise ValueError('Formato de data inválido')
            else:
                task.due_date = None
        if 'tags' in data:
            if isinstance(data['tags'], list):
                task.tags = ','.join(data['tags'])
                
        task.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        return task

    @staticmethod
    def delete_task(task_id):
        task = Task.query.get(task_id)
        if not task:
            return False
        db.session.delete(task)
        db.session.commit()
        return True
