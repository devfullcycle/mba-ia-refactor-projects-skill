from database import db
from models.task import Task
from models.user import User
from models.category import Category
from utils.helpers import calculate_percentage
from datetime import datetime, timezone, timedelta


class ReportController:

    @staticmethod
    def summary():
        total_tasks = Task.query.count()
        total_users = User.query.count()
        total_categories = Category.query.count()

        pending = Task.query.filter_by(status='pending').count()
        in_progress = Task.query.filter_by(status='in_progress').count()
        done = Task.query.filter_by(status='done').count()
        cancelled = Task.query.filter_by(status='cancelled').count()

        priorities = {}
        for p in range(1, 6):
            priorities[p] = Task.query.filter_by(priority=p).count()

        overdue_tasks = Task.query.filter(
            Task.due_date.isnot(None),
            Task.status.notin_(['done', 'cancelled']),
        ).all()
        overdue_list = [
            {
                'id': t.id,
                'title': t.title,
                'due_date': str(t.due_date),
                'days_overdue': (datetime.now(timezone.utc) - t.due_date.replace(tzinfo=timezone.utc)).days if t.due_date.tzinfo is None else (datetime.now(timezone.utc) - t.due_date).days,
            }
            for t in overdue_tasks if t.is_overdue()
        ]

        seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
        recent_tasks = Task.query.filter(Task.created_at >= seven_days_ago).count()
        recent_done = Task.query.filter(
            Task.status == 'done',
            Task.updated_at >= seven_days_ago,
        ).count()

        users = User.query.all()
        user_stats = []
        for user in users:
            user_tasks = Task.query.filter_by(user_id=user.id).all()
            total = len(user_tasks)
            completed = sum(1 for t in user_tasks if t.status == 'done')
            user_stats.append({
                'user_id': user.id,
                'user_name': user.name,
                'total_tasks': total,
                'completed_tasks': completed,
                'completion_rate': calculate_percentage(completed, total),
            })

        return {
            'generated_at': str(datetime.now(timezone.utc)),
            'overview': {
                'total_tasks': total_tasks,
                'total_users': total_users,
                'total_categories': total_categories,
            },
            'tasks_by_status': {
                'pending': pending,
                'in_progress': in_progress,
                'done': done,
                'cancelled': cancelled,
            },
            'tasks_by_priority': {
                'critical': priorities[1],
                'high': priorities[2],
                'medium': priorities[3],
                'low': priorities[4],
                'minimal': priorities[5],
            },
            'overdue': {
                'count': len(overdue_list),
                'tasks': overdue_list,
            },
            'recent_activity': {
                'tasks_created_last_7_days': recent_tasks,
                'tasks_completed_last_7_days': recent_done,
            },
            'user_productivity': user_stats,
        }, 200

    @staticmethod
    def user_report(user_id):
        user = db.session.get(User, user_id)
        if not user:
            return {'error': 'Usuário não encontrado'}, 404

        tasks = Task.query.filter_by(user_id=user_id).all()
        total = len(tasks)
        done = sum(1 for t in tasks if t.status == 'done')
        pending = sum(1 for t in tasks if t.status == 'pending')
        in_progress = sum(1 for t in tasks if t.status == 'in_progress')
        cancelled = sum(1 for t in tasks if t.status == 'cancelled')
        overdue = sum(1 for t in tasks if t.is_overdue())
        high_priority = sum(1 for t in tasks if t.priority <= 2)

        return {
            'user': {
                'id': user.id,
                'name': user.name,
                'email': user.email,
            },
            'statistics': {
                'total_tasks': total,
                'done': done,
                'pending': pending,
                'in_progress': in_progress,
                'cancelled': cancelled,
                'overdue': overdue,
                'high_priority': high_priority,
                'completion_rate': calculate_percentage(done, total),
            },
        }, 200
