from datetime import timedelta

from sqlalchemy.orm import selectinload

from models.task import Task
from models.user import User
from models.category import Category
from utils.helpers import now_utc


class ReportService:
    """Monta os relatórios (antes calculados inline nas rotas)."""

    def summary(self):
        # Carrega todas as tasks de uma vez e agrega em memória (sem N+1).
        tasks = Task.query.options(selectinload(Task.user)).all()
        users = User.query.all()

        by_status = {s: 0 for s in ('pending', 'in_progress', 'done', 'cancelled')}
        by_priority = {p: 0 for p in range(1, 6)}
        overdue_list = []
        now = now_utc()
        seven_days_ago = now - timedelta(days=7)
        recent_created = 0
        recent_done = 0
        per_user = {u.id: {'user_id': u.id, 'user_name': u.name, 'total_tasks': 0, 'completed_tasks': 0}
                    for u in users}

        for t in tasks:
            by_status[t.status] = by_status.get(t.status, 0) + 1
            by_priority[t.priority] = by_priority.get(t.priority, 0) + 1
            if t.is_overdue():
                overdue_list.append({
                    'id': t.id,
                    'title': t.title,
                    'due_date': str(t.due_date),
                    'days_overdue': (now - t.due_date).days,
                })
            if t.created_at and t.created_at >= seven_days_ago:
                recent_created += 1
            if t.status == 'done' and t.updated_at and t.updated_at >= seven_days_ago:
                recent_done += 1
            if t.user_id in per_user:
                per_user[t.user_id]['total_tasks'] += 1
                if t.status == 'done':
                    per_user[t.user_id]['completed_tasks'] += 1

        user_stats = []
        for stats in per_user.values():
            total = stats['total_tasks']
            stats['completion_rate'] = round((stats['completed_tasks'] / total) * 100, 2) if total > 0 else 0
            user_stats.append(stats)

        return {
            'generated_at': str(now),
            'overview': {
                'total_tasks': len(tasks),
                'total_users': len(users),
                'total_categories': Category.query.count(),
            },
            'tasks_by_status': {
                'pending': by_status.get('pending', 0),
                'in_progress': by_status.get('in_progress', 0),
                'done': by_status.get('done', 0),
                'cancelled': by_status.get('cancelled', 0),
            },
            'tasks_by_priority': {
                'critical': by_priority.get(1, 0),
                'high': by_priority.get(2, 0),
                'medium': by_priority.get(3, 0),
                'low': by_priority.get(4, 0),
                'minimal': by_priority.get(5, 0),
            },
            'overdue': {'count': len(overdue_list), 'tasks': overdue_list},
            'recent_activity': {
                'tasks_created_last_7_days': recent_created,
                'tasks_completed_last_7_days': recent_done,
            },
            'user_productivity': user_stats,
        }

    def user_report(self, user):
        tasks = Task.query.filter_by(user_id=user.id).all()
        counters = {'done': 0, 'pending': 0, 'in_progress': 0, 'cancelled': 0}
        overdue = 0
        high_priority = 0
        for t in tasks:
            if t.status in counters:
                counters[t.status] += 1
            if t.priority <= 2:
                high_priority += 1
            if t.is_overdue():
                overdue += 1
        total = len(tasks)
        return {
            'user': {'id': user.id, 'name': user.name, 'email': user.email},
            'statistics': {
                'total_tasks': total,
                'done': counters['done'],
                'pending': counters['pending'],
                'in_progress': counters['in_progress'],
                'cancelled': counters['cancelled'],
                'overdue': overdue,
                'high_priority': high_priority,
                'completion_rate': round((counters['done'] / total) * 100, 2) if total > 0 else 0,
            },
        }
