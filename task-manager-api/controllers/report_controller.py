"""Relatórios de produtividade."""
from datetime import timedelta

from models.category import Category
from models.task import (HIGH_PRIORITY_THRESHOLD, PRIORITY_LABELS, STATUS_CANCELLED, STATUS_DONE,
                         STATUS_IN_PROGRESS, STATUS_PENDING, Task, completion_rate)
from models.user import User
from utils.clock import utcnow
from utils.errors import NotFoundError

RECENT_ACTIVITY_DAYS = 7
_STATUSES = (STATUS_PENDING, STATUS_IN_PROGRESS, STATUS_DONE, STATUS_CANCELLED)


class ReportController:
    def summary(self):
        now = utcnow()
        since = now - timedelta(days=RECENT_ACTIVITY_DAYS)
        by_status = Task.count_by(Task.status)
        by_priority = Task.count_by(Task.priority)
        overdue = Task.overdue(now)
        task_totals = Task.totals_by_user()

        user_stats = []
        for user in User.all():
            total, completed = task_totals.get(user.id, (0, 0))
            user_stats.append({
                "user_id": user.id,
                "user_name": user.name,
                "total_tasks": total,
                "completed_tasks": completed,
                "completion_rate": completion_rate(completed, total),
            })

        return {
            "generated_at": str(now),
            "overview": {
                "total_tasks": Task.count(),
                "total_users": User.count(),
                "total_categories": Category.count(),
            },
            "tasks_by_status": {status: by_status.get(status, 0) for status in _STATUSES},
            "tasks_by_priority": {label: by_priority.get(level, 0) for level, label in PRIORITY_LABELS.items()},
            "overdue": {
                "count": len(overdue),
                "tasks": [
                    {"id": t.id, "title": t.title, "due_date": str(t.due_date), "days_overdue": t.days_overdue(now)}
                    for t in overdue
                ],
            },
            "recent_activity": {
                "tasks_created_last_7_days": Task.count_created_since(since),
                "tasks_completed_last_7_days": Task.count_done_since(since),
            },
            "user_productivity": user_stats,
        }

    def user_report(self, user_id):
        user = User.get(user_id)
        if not user:
            raise NotFoundError("Usuário não encontrado")

        tasks = Task.by_user(user_id)
        now = utcnow()
        counts = {status: sum(1 for t in tasks if t.status == status) for status in _STATUSES}
        total = len(tasks)
        return {
            "user": user.to_summary(),
            "statistics": {
                "total_tasks": total,
                "done": counts[STATUS_DONE],
                "pending": counts[STATUS_PENDING],
                "in_progress": counts[STATUS_IN_PROGRESS],
                "cancelled": counts[STATUS_CANCELLED],
                "overdue": sum(1 for t in tasks if t.is_overdue(now)),
                "high_priority": sum(1 for t in tasks if t.priority <= HIGH_PRIORITY_THRESHOLD),
                "completion_rate": completion_rate(counts[STATUS_DONE], total),
            },
        }
