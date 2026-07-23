from __future__ import annotations

from datetime import timedelta

from errors import NotFoundError
from services.clock import utc_now


class ReportController:
    def __init__(self, tasks, users, categories, clock=utc_now):
        self.tasks = tasks
        self.users = users
        self.categories = categories
        self.clock = clock

    def summary(self):
        now = self.clock()
        status_counts = self.tasks.counts_by_status()
        priority_counts = self.tasks.counts_by_priority()
        overdue_tasks = self.tasks.list_overdue(now)
        recent = self.tasks.recent_activity(now - timedelta(days=7))
        productivity = self.tasks.productivity_by_user()

        for item in productivity:
            total = item["total_tasks"]
            item["completion_rate"] = (
                round((item["completed_tasks"] / total) * 100, 2) if total else 0
            )

        return {
            "generated_at": now,
            "overview": {
                "total_tasks": self.tasks.count(),
                "total_users": self.users.count(),
                "total_categories": self.categories.count(),
            },
            "tasks_by_status": {
                status: status_counts.get(status, 0)
                for status in ("pending", "in_progress", "done", "cancelled")
            },
            "tasks_by_priority": {
                "critical": priority_counts.get(1, 0),
                "high": priority_counts.get(2, 0),
                "medium": priority_counts.get(3, 0),
                "low": priority_counts.get(4, 0),
                "minimal": priority_counts.get(5, 0),
            },
            "overdue": {
                "count": len(overdue_tasks),
                "tasks": [
                    {
                        "id": task.id,
                        "title": task.title,
                        "due_date": task.due_date,
                        "days_overdue": (now - task.due_date).days,
                    }
                    for task in overdue_tasks
                ],
            },
            "recent_activity": {
                "tasks_created_last_7_days": recent["created"],
                "tasks_completed_last_7_days": recent["completed"],
            },
            "user_productivity": productivity,
        }

    def user(self, user_id):
        user = self.users.get(user_id)
        if user is None:
            raise NotFoundError("Usuário não encontrado")
        statistics = self.tasks.user_statistics(user_id, self.clock())
        total = statistics["total_tasks"]
        statistics["completion_rate"] = (
            round((statistics["done"] / total) * 100, 2) if total else 0
        )
        return user, statistics
