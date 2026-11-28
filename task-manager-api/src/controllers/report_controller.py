"""Report use cases (aggregations are pushed to the database with GROUP BY)."""
from datetime import timedelta

from src.controllers.errors import NotFoundError
from src.controllers.metrics import completion_rate
from src.models.constants import (
    HIGH_PRIORITY_THRESHOLD,
    PRIORITY_LABELS,
    RECENT_ACTIVITY_DAYS,
    STATUS_DONE,
    VALID_STATUSES,
)
from src.models.database import utcnow


class ReportController:
    def __init__(self, tasks, users, categories, clock=utcnow):
        self.tasks = tasks
        self.users = users
        self.categories = categories
        self.clock = clock

    def summary(self):
        now = self.clock()
        since = now - timedelta(days=RECENT_ACTIVITY_DAYS)
        by_status = self.tasks.count_by_status()
        by_priority = self.tasks.count_by_priority()
        by_user_status = self.tasks.count_by_user_and_status()
        overdue_tasks = self.tasks.list_overdue(now)

        productivity = []
        for user in self.users.list_all():
            total = sum(n for (user_id, _status), n in by_user_status.items() if user_id == user.id)
            completed = by_user_status.get((user.id, STATUS_DONE), 0)
            productivity.append({
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
            "tasks_by_status": {status: by_status.get(status, 0) for status in VALID_STATUSES},
            "tasks_by_priority": {label: by_priority.get(level, 0) for level, label in PRIORITY_LABELS.items()},
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
                "tasks_completed_last_7_days": self.tasks.count_completed_since(since),
            },
            "user_productivity": productivity,
        }

    def user_report(self, user_id):
        user = self.users.get(user_id)
        if user is None:
            raise NotFoundError("Usuário não encontrado")
        by_status = self.tasks.count_by_status(user_id=user_id)
        total = sum(by_status.values())
        done = by_status.get(STATUS_DONE, 0)
        statistics = {status: by_status.get(status, 0) for status in VALID_STATUSES}
        statistics.update(
            total_tasks=total,
            overdue=self.tasks.count_overdue(self.clock(), user_id=user_id),
            high_priority=self.tasks.count_high_priority(user_id, HIGH_PRIORITY_THRESHOLD),
            completion_rate=completion_rate(done, total),
        )
        return {"user": {"id": user.id, "name": user.name, "email": user.email}, "statistics": statistics}
