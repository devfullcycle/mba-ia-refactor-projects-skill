from collections import defaultdict
from datetime import datetime, timedelta
from database import db
from models.task import Task
from models.user import User
from models.category import Category


class ReportController:

    @staticmethod
    def summary():
        total_tasks = Task.query.count()
        total_users = User.query.count()
        total_categories = Category.query.count()

        # Aggregate status counts in one query instead of N separate count() calls
        status_rows = db.session.query(Task.status, db.func.count(Task.id)).group_by(Task.status).all()
        status_counts = {status: count for status, count in status_rows}

        priority_rows = db.session.query(Task.priority, db.func.count(Task.id)).group_by(Task.priority).all()
        priority_counts = {priority: count for priority, count in priority_rows}

        all_tasks = Task.query.all()
        overdue_list = [
            {
                'id': t.id,
                'title': t.title,
                'due_date': str(t.due_date),
                'days_overdue': (datetime.utcnow() - t.due_date).days,
            }
            for t in all_tasks if t.is_overdue()
        ]

        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recent_tasks = Task.query.filter(Task.created_at >= seven_days_ago).count()
        recent_done = Task.query.filter(
            Task.status == 'done',
            Task.updated_at >= seven_days_ago
        ).count()

        # Fix N+1: fetch (user_id, status) for all tasks in one query
        task_rows = db.session.query(Task.user_id, Task.status).all()
        user_task_stats = defaultdict(lambda: {'total': 0, 'done': 0})
        for user_id, status in task_rows:
            if user_id is not None:
                user_task_stats[user_id]['total'] += 1
                if status == 'done':
                    user_task_stats[user_id]['done'] += 1

        user_productivity = []
        for u in User.query.all():
            stats = user_task_stats[u.id]
            total = stats['total']
            done = stats['done']
            user_productivity.append({
                'user_id': u.id,
                'user_name': u.name,
                'total_tasks': total,
                'completed_tasks': done,
                'completion_rate': round((done / total) * 100, 2) if total > 0 else 0,
            })

        return {
            'generated_at': str(datetime.utcnow()),
            'overview': {
                'total_tasks': total_tasks,
                'total_users': total_users,
                'total_categories': total_categories,
            },
            'tasks_by_status': {
                'pending': status_counts.get('pending', 0),
                'in_progress': status_counts.get('in_progress', 0),
                'done': status_counts.get('done', 0),
                'cancelled': status_counts.get('cancelled', 0),
            },
            'tasks_by_priority': {
                'critical': priority_counts.get(1, 0),
                'high': priority_counts.get(2, 0),
                'medium': priority_counts.get(3, 0),
                'low': priority_counts.get(4, 0),
                'minimal': priority_counts.get(5, 0),
            },
            'overdue': {
                'count': len(overdue_list),
                'tasks': overdue_list,
            },
            'recent_activity': {
                'tasks_created_last_7_days': recent_tasks,
                'tasks_completed_last_7_days': recent_done,
            },
            'user_productivity': user_productivity,
        }, 200

    @staticmethod
    def user_report(user_id):
        user = User.query.get(user_id)
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
            'user': {'id': user.id, 'name': user.name, 'email': user.email},
            'statistics': {
                'total_tasks': total,
                'done': done,
                'pending': pending,
                'in_progress': in_progress,
                'cancelled': cancelled,
                'overdue': overdue,
                'high_priority': high_priority,
                'completion_rate': round((done / total) * 100, 2) if total > 0 else 0,
            },
        }, 200
