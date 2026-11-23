from datetime import timedelta

from src.controllers.errors import NotFoundError
from src.controllers.metrics import completion_rate
from src.models.database import utcnow
from src.models.task_model import (
    HIGH_PRIORITY_THRESHOLD, PRIORITY_LABELS, STATUS_CANCELLED, STATUS_DONE, STATUS_IN_PROGRESS,
    STATUS_PENDING,
)

RECENT_ACTIVITY_DAYS = 7


class ReportController:
    def __init__(self, tasks, users, categories):
        self.tasks = tasks
        self.users = users
        self.categories = categories

    def summary(self):
        now = utcnow()
        since = now - timedelta(days=RECENT_ACTIVITY_DAYS)
        overdue_tasks = [task for task in self.tasks.list_all() if task.is_overdue(now)]
        by_priority = self.tasks.count_by_priority()
        per_user = self.tasks.count_by_user()

        user_productivity = []
        for user in self.users.list_all():
            total, completed = per_user.get(user.id, (0, 0))
            user_productivity.append({
                "user_id": user.id,
                "user_name": user.name,
                "total_tasks": total,
                "completed_tasks": completed,
                "completion_rate": completion_rate(completed, total),
            })

        return {
            "generated_at": str(now),
            "overview": {
                "total_tasks": self.tasks.count(),
                "total_users": self.users.count(),
                "total_categories": self.categories.count(),
            },
            "tasks_by_status": self.tasks.count_by_status(),
            "tasks_by_priority": {label: by_priority[level] for level, label in PRIORITY_LABELS.items()},
            "overdue": {
                "count": len(overdue_tasks),
                "tasks": [
                    {
                        "id": task.id,
                        "title": task.title,
                        "due_date": str(task.due_date),
                        "days_overdue": (now - task.due_date).days,
                    }
                    for task in overdue_tasks
                ],
            },
            "recent_activity": {
                "tasks_created_last_7_days": self.tasks.count_created_since(since),
                "tasks_completed_last_7_days": self.tasks.count_done_since(since),
            },
            "user_productivity": user_productivity,
        }

    def user_report(self, user_id):
        user = self.users.get(user_id)
        if user is None:
            raise NotFoundError("Usuário não encontrado")

        tasks = self.tasks.list_by_user(user_id)
        now = utcnow()

        def count_status(status):
            return sum(1 for task in tasks if task.status == status)

        done = count_status(STATUS_DONE)
        return {
            "user": {"id": user.id, "name": user.name, "email": user.email},
            "statistics": {
                "total_tasks": len(tasks),
                "done": done,
                "pending": count_status(STATUS_PENDING),
                "in_progress": count_status(STATUS_IN_PROGRESS),
                "cancelled": count_status(STATUS_CANCELLED),
                "overdue": sum(1 for task in tasks if task.is_overdue(now)),
                "high_priority": sum(1 for task in tasks if task.priority <= HIGH_PRIORITY_THRESHOLD),
                "completion_rate": completion_rate(done, len(tasks)),
            },
        }
