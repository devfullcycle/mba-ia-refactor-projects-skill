"""Relatórios: agregações de tasks e produtividade por usuário."""
from datetime import timedelta

from config.constants import (
    HIGH_PRIORITY_MAX,
    PRIORITY_LABELS,
    RECENT_ACTIVITY_DAYS,
    STATUS_CANCELLED,
    STATUS_DONE,
    STATUS_IN_PROGRESS,
    STATUS_PENDING,
)
from controllers.common import get_or_404
from models.category import Category
from models.task import Task
from models.user import User
from utils.helpers import calculate_percentage, utc_now


def summary_report():
    now = utc_now()
    since = now - timedelta(days=RECENT_ACTIVITY_DAYS)

    by_status = Task.count_by_status()
    by_priority = Task.count_by_priority()
    overdue_tasks = Task.list_overdue(now)
    totals_by_user = Task.totals_by_user()

    user_stats = []
    for user in User.list_all():
        total, completed = totals_by_user.get(user.id, (0, 0))
        user_stats.append({
            'user_id': user.id,
            'user_name': user.name,
            'total_tasks': total,
            'completed_tasks': completed,
            'completion_rate': calculate_percentage(completed, total),
        })

    return {
        'generated_at': str(now),
        'overview': {
            'total_tasks': Task.count_all(),
            'total_users': User.count_all(),
            'total_categories': Category.count_all(),
        },
        'tasks_by_status': {
            STATUS_PENDING: by_status.get(STATUS_PENDING, 0),
            STATUS_IN_PROGRESS: by_status.get(STATUS_IN_PROGRESS, 0),
            STATUS_DONE: by_status.get(STATUS_DONE, 0),
            STATUS_CANCELLED: by_status.get(STATUS_CANCELLED, 0),
        },
        'tasks_by_priority': {
            label: by_priority.get(priority, 0) for priority, label in PRIORITY_LABELS.items()
        },
        'overdue': {
            'count': len(overdue_tasks),
            'tasks': [
                {
                    'id': task.id,
                    'title': task.title,
                    'due_date': str(task.due_date),
                    'days_overdue': (now - task.due_date).days,
                }
                for task in overdue_tasks
            ],
        },
        'recent_activity': {
            'tasks_created_last_7_days': Task.count_created_since(since),
            'tasks_completed_last_7_days': Task.count_done_updated_since(since),
        },
        'user_productivity': user_stats,
    }


def user_report(user_id):
    user = get_or_404(User, user_id, 'Usuário não encontrado')
    tasks = Task.find_by_user(user.id)
    now = utc_now()

    total = len(tasks)
    done = sum(1 for t in tasks if t.status == STATUS_DONE)

    return {
        'user': {'id': user.id, 'name': user.name, 'email': user.email},
        'statistics': {
            'total_tasks': total,
            'done': done,
            'pending': sum(1 for t in tasks if t.status == STATUS_PENDING),
            'in_progress': sum(1 for t in tasks if t.status == STATUS_IN_PROGRESS),
            'cancelled': sum(1 for t in tasks if t.status == STATUS_CANCELLED),
            'overdue': sum(1 for t in tasks if t.is_overdue(now)),
            'high_priority': sum(
                1 for t in tasks if t.priority is not None and t.priority <= HIGH_PRIORITY_MAX
            ),
            'completion_rate': calculate_percentage(done, total),
        },
    }
