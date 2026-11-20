"""Reporting use cases (aggregations are done in the repositories with GROUP BY)."""
from datetime import timedelta

from ..models.database import utcnow
from ..models.task_model import (
    PRIORITY_LABELS,
    STATUS_CANCELLED,
    STATUS_DONE,
    STATUS_IN_PROGRESS,
    STATUS_PENDING,
    TASK_STATUSES,
)
from .errors import NotFoundError
from .metrics import completion_rate

RECENT_ACTIVITY_DAYS = 7
HIGH_PRIORITY_THRESHOLD = 2  # priorities 1 (critical) and 2 (high)


class ReportController:
    def __init__(self, tasks, users, categories):
        self.tasks = tasks
        self.users = users
        self.categories = categories

    def summary(self):
        now = utcnow()
        since = now - timedelta(days=RECENT_ACTIVITY_DAYS)
        by_status = self.tasks.count_by_status()
        by_priority = self.tasks.count_by_priority()
        overdue = self.tasks.list_overdue(now)
        return {
            "generated_at": str(now),
            "overview": {
                "total_tasks": self.tasks.count(),
                "total_users": self.users.count(),
                "total_categories": self.categories.count(),
            },
            "tasks_by_status": {status: by_status.get(status, 0) for status in TASK_STATUSES},
            "tasks_by_priority": {label: by_priority.get(level, 0) for level, label in PRIORITY_LABELS.items()},
            "overdue": {
                "count": len(overdue),
                "tasks": [self._overdue_entry(task, now) for task in overdue],
            },
            "recent_activity": {
                "tasks_created_last_7_days": self.tasks.count_created_since(since),
                "tasks_completed_last_7_days": self.tasks.count_completed_since(since),
            },
            "user_productivity": [
                {
                    "user_id": user.id,
                    "user_name": user.name,
                    "total_tasks": total,
                    "completed_tasks": completed,
                    "completion_rate": completion_rate(completed, total),
                }
                for user, total, completed in self.users.productivity()
            ],
        }

    def user_report(self, user_id):
        user = self.users.get(user_id)
        if user is None:
            raise NotFoundError("Usuário não encontrado")
        tasks = self.tasks.list_by_user(user_id)
        now = utcnow()
        statuses = [task.status for task in tasks]
        done = statuses.count(STATUS_DONE)
        return {
            "user": {"id": user.id, "name": user.name, "email": user.email},
            "statistics": {
                "total_tasks": len(tasks),
                "done": done,
                "pending": statuses.count(STATUS_PENDING),
                "in_progress": statuses.count(STATUS_IN_PROGRESS),
                "cancelled": statuses.count(STATUS_CANCELLED),
                "overdue": sum(1 for task in tasks if task.is_overdue(now)),
                "high_priority": sum(1 for task in tasks if task.priority <= HIGH_PRIORITY_THRESHOLD),
                "completion_rate": completion_rate(done, len(tasks)),
            },
        }

    @staticmethod
    def _overdue_entry(task, now):
        return {
            "id": task.id,
            "title": task.title,
            "due_date": str(task.due_date),
            "days_overdue": (now - task.due_date).days,
        }
