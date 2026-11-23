"""Serializers dos relatórios (forma JSON de /reports/*)."""
from utils.constants import (
    PRIORITY_LABELS, STATUS_CANCELLED, STATUS_DONE, STATUS_IN_PROGRESS, STATUS_PENDING, TASK_STATUSES,
)
from utils.stats import percentage


def _overdue_item(task, now):
    return {
        'id': task.id,
        'title': task.title,
        'due_date': str(task.due_date),
        'days_overdue': (now - task.due_date).days,
    }


def _productivity(user, total, done):
    return {
        'user_id': user.id,
        'user_name': user.name,
        'total_tasks': total,
        'completed_tasks': done,
        'completion_rate': percentage(done, total),
    }


def render_summary(data):
    now = data['now']
    by_status, by_priority = data['by_status'], data['by_priority']
    return {
        'generated_at': str(now),
        'overview': {
            'total_tasks': data['totals']['tasks'],
            'total_users': data['totals']['users'],
            'total_categories': data['totals']['categories'],
        },
        'tasks_by_status': {s: by_status.get(s, 0) for s in TASK_STATUSES},
        'tasks_by_priority': {
            label: by_priority.get(priority, 0) for priority, label in PRIORITY_LABELS.items()
        },
        'overdue': {
            'count': len(data['overdue_tasks']),
            'tasks': [_overdue_item(t, now) for t in data['overdue_tasks']],
        },
        'recent_activity': {
            'tasks_created_last_7_days': data['recent_created'],
            'tasks_completed_last_7_days': data['recent_done'],
        },
        'user_productivity': [
            _productivity(u, data['per_user'][u.id], data['per_user_done'][u.id]) for u in data['users']
        ],
    }


def render_user_report(data):
    user, by_status, total = data['user'], data['by_status'], data['total']
    return {
        'user': {'id': user.id, 'name': user.name, 'email': user.email},
        'statistics': {
            'total_tasks': total,
            'done': by_status[STATUS_DONE],
            'pending': by_status[STATUS_PENDING],
            'in_progress': by_status[STATUS_IN_PROGRESS],
            'cancelled': by_status[STATUS_CANCELLED],
            'overdue': data['overdue'],
            'high_priority': data['high_priority'],
            'completion_rate': percentage(by_status[STATUS_DONE], total),
        },
    }
