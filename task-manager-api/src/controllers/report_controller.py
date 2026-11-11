from src.controllers.task_controller import completion_rate
from src.controllers.user_controller import get_or_404 as get_user_or_404
from src.models import category as category_model
from src.models import task as task_model
from src.models import user as user_model
from src.utils.dates import format_datetime, utc_now
from src.utils.errors import ForbiddenError

RECENT_ACTIVITY_DAYS = 7


def summary_report():
    now = utc_now()

    by_status = task_model.count_by_status()
    by_priority = task_model.count_by_priority()
    overdue_tasks = task_model.list_overdue(now)
    created_recently, completed_recently = task_model.recent_activity(RECENT_ACTIVITY_DAYS, now)

    user_productivity = [
        {
            "user_id": user.id,
            "user_name": user.name,
            "total_tasks": total,
            "completed_tasks": int(completed),
            "completion_rate": completion_rate(int(completed), total),
        }
        for user, total, completed in task_model.productivity_by_user()
    ]

    return {
        "generated_at": str(now),
        "overview": {
            "total_tasks": task_model.count(),
            "total_users": user_model.count(),
            "total_categories": category_model.count(),
        },
        "tasks_by_status": {status: by_status[status] for status in task_model.VALID_STATUSES},
        "tasks_by_priority": {label: by_priority[priority] for priority, label in task_model.PRIORITY_LABELS.items()},
        "overdue": {
            "count": len(overdue_tasks),
            "tasks": [
                {
                    "id": task.id,
                    "title": task.title,
                    "due_date": format_datetime(task.due_date),
                    "days_overdue": (now - task.due_date).days,
                }
                for task in overdue_tasks
            ],
        },
        "recent_activity": {
            f"tasks_created_last_{RECENT_ACTIVITY_DAYS}_days": created_recently,
            f"tasks_completed_last_{RECENT_ACTIVITY_DAYS}_days": completed_recently,
        },
        "user_productivity": user_productivity,
    }


def user_report(user_id, actor):
    if not actor.is_staff() and actor.id != user_id:
        raise ForbiddenError("Você só pode consultar o próprio relatório")

    user = get_user_or_404(user_id)
    statistics = task_model.user_statistics(user_id, utc_now())
    statistics["completion_rate"] = completion_rate(statistics["done"], statistics["total_tasks"])

    return {
        "user": {"id": user.id, "name": user.name, "email": user.email},
        "statistics": statistics,
    }
