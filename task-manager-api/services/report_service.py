"""Regras de agregação de relatórios (fora das rotas).

Carrega os conjuntos uma vez e agrega em memória, evitando o N+1 da versão
original (que disparava uma query de tasks por usuário)."""
from datetime import timedelta

from models.task import Task
from models.user import User
from models.category import Category
from utils.datetime_utils import now_utc
from utils.constants import CLOSED_STATUSES


def _completion_rate(done, total):
    return round((done / total) * 100, 2) if total > 0 else 0


def build_summary():
    now = now_utc()
    all_tasks = Task.all()
    users = User.all()

    status_counts = {'pending': 0, 'in_progress': 0, 'done': 0, 'cancelled': 0}
    priority_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    overdue_list = []
    seven_days_ago = now - timedelta(days=7)
    recent_created = 0
    recent_done = 0
    tasks_by_user = {}

    for task in all_tasks:
        if task.status in status_counts:
            status_counts[task.status] += 1
        if task.priority in priority_counts:
            priority_counts[task.priority] += 1

        if task.is_overdue():
            overdue_list.append({
                'id': task.id,
                'title': task.title,
                'due_date': str(task.due_date),
                'days_overdue': (now - task.due_date).days,
            })

        if task.created_at and task.created_at >= seven_days_ago:
            recent_created += 1
        if task.status == 'done' and task.updated_at and task.updated_at >= seven_days_ago:
            recent_done += 1

        tasks_by_user.setdefault(task.user_id, []).append(task)

    user_stats = []
    for user in users:
        user_tasks = tasks_by_user.get(user.id, [])
        total = len(user_tasks)
        completed = sum(1 for t in user_tasks if t.status == 'done')
        user_stats.append({
            'user_id': user.id,
            'user_name': user.name,
            'total_tasks': total,
            'completed_tasks': completed,
            'completion_rate': _completion_rate(completed, total),
        })

    return {
        'generated_at': str(now),
        'overview': {
            'total_tasks': len(all_tasks),
            'total_users': len(users),
            'total_categories': Category.count(),
        },
        'tasks_by_status': {
            'pending': status_counts['pending'],
            'in_progress': status_counts['in_progress'],
            'done': status_counts['done'],
            'cancelled': status_counts['cancelled'],
        },
        'tasks_by_priority': {
            'critical': priority_counts[1],
            'high': priority_counts[2],
            'medium': priority_counts[3],
            'low': priority_counts[4],
            'minimal': priority_counts[5],
        },
        'overdue': {
            'count': len(overdue_list),
            'tasks': overdue_list,
        },
        'recent_activity': {
            'tasks_created_last_7_days': recent_created,
            'tasks_completed_last_7_days': recent_done,
        },
        'user_productivity': user_stats,
    }


def build_user_report(user):
    tasks = Task.for_user(user.id)

    counts = {'done': 0, 'pending': 0, 'in_progress': 0, 'cancelled': 0}
    overdue = 0
    high_priority = 0

    for task in tasks:
        if task.status in counts:
            counts[task.status] += 1
        if task.priority <= 2:
            high_priority += 1
        if task.is_overdue():
            overdue += 1

    total = len(tasks)
    return {
        'user': {
            'id': user.id,
            'name': user.name,
            'email': user.email,
        },
        'statistics': {
            'total_tasks': total,
            'done': counts['done'],
            'pending': counts['pending'],
            'in_progress': counts['in_progress'],
            'cancelled': counts['cancelled'],
            'overdue': overdue,
            'high_priority': high_priority,
            'completion_rate': _completion_rate(counts['done'], total),
        },
    }


def task_stats():
    all_tasks = Task.all()
    total = len(all_tasks)
    counts = {'pending': 0, 'in_progress': 0, 'done': 0, 'cancelled': 0}
    overdue = 0
    for task in all_tasks:
        if task.status in counts:
            counts[task.status] += 1
        if task.is_overdue():
            overdue += 1
    return {
        'total': total,
        'pending': counts['pending'],
        'in_progress': counts['in_progress'],
        'done': counts['done'],
        'cancelled': counts['cancelled'],
        'overdue': overdue,
        'completion_rate': _completion_rate(counts['done'], total),
    }
