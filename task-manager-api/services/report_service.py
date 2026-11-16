from collections import Counter
from datetime import timedelta

from sqlalchemy import func, select

from database import db
from models.category import Category
from models.task import Task
from models.user import User
from services import user_service
from utils.clock import utc_now
from utils.constants import HIGH_PRIORITY_MAX, PRIORITY_LABELS, RECENT_DAYS, TASK_STATUSES
from utils.stats import percentage


def _count(model, *conditions):
    return db.session.scalar(select(func.count()).select_from(model).where(*conditions))


def _group_counts(column):
    return dict(db.session.execute(select(column, func.count()).group_by(column)).all())


def summary():
    now = utc_now()
    by_status = _group_counts(Task.status)
    by_priority = _group_counts(Task.priority)

    overdue_tasks = db.session.scalars(
        select(Task).where(Task.overdue_clause(now)).order_by(Task.id)).all()

    since = now - timedelta(days=RECENT_DAYS)
    recent_tasks = _count(Task, Task.created_at >= since)
    recent_done = _count(Task, Task.status == 'done', Task.updated_at >= since)

    per_user = Counter()
    per_user_done = Counter()
    for user_id, status, count in db.session.execute(
            select(Task.user_id, Task.status, func.count())
            .where(Task.user_id.isnot(None))
            .group_by(Task.user_id, Task.status)):
        per_user[user_id] += count
        if status == 'done':
            per_user_done[user_id] += count

    users = db.session.scalars(select(User).order_by(User.id)).all()

    return {
        'generated_at': str(now),
        'overview': {
            'total_tasks': _count(Task),
            'total_users': _count(User),
            'total_categories': _count(Category),
        },
        'tasks_by_status': {s: by_status.get(s, 0) for s in TASK_STATUSES},
        'tasks_by_priority': {
            label: by_priority.get(priority, 0) for priority, label in PRIORITY_LABELS.items()
        },
        'overdue': {
            'count': len(overdue_tasks),
            'tasks': [
                {
                    'id': t.id,
                    'title': t.title,
                    'due_date': str(t.due_date),
                    'days_overdue': (now - t.due_date).days,
                }
                for t in overdue_tasks
            ],
        },
        'recent_activity': {
            'tasks_created_last_7_days': recent_tasks,
            'tasks_completed_last_7_days': recent_done,
        },
        'user_productivity': [
            {
                'user_id': u.id,
                'user_name': u.name,
                'total_tasks': per_user[u.id],
                'completed_tasks': per_user_done[u.id],
                'completion_rate': percentage(per_user_done[u.id], per_user[u.id]),
            }
            for u in users
        ],
    }


def user_report(user_id):
    user = user_service.get(user_id)
    tasks = user_service.tasks_of(user_id)
    now = utc_now()

    total = len(tasks)
    status_counts = Counter(t.status for t in tasks)
    done = status_counts['done']

    return {
        'user': {'id': user.id, 'name': user.name, 'email': user.email},
        'statistics': {
            'total_tasks': total,
            'done': done,
            'pending': status_counts['pending'],
            'in_progress': status_counts['in_progress'],
            'cancelled': status_counts['cancelled'],
            'overdue': sum(1 for t in tasks if t.is_overdue(now)),
            'high_priority': sum(1 for t in tasks if t.priority <= HIGH_PRIORITY_MAX),
            'completion_rate': percentage(done, total),
        },
    }
