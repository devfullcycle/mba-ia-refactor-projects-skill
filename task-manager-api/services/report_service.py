from datetime import datetime, timezone, timedelta
from sqlalchemy import func, select
from database import db
from models.task import Task
from models.user import User
from models.category import Category
from utils.helpers import calculate_percentage


def _now():
    # SQLite stores naive datetimes; use naive UTC now so all comparisons stay consistent
    # (avoids the deprecated datetime.utcnow() while remaining tz-safe at the storage layer).
    return datetime.now(timezone.utc).replace(tzinfo=None)


def summary():
    now = _now()
    session = db.session

    total_tasks = session.scalar(select(func.count(Task.id)))
    total_users = session.scalar(select(func.count(User.id)))
    total_categories = session.scalar(select(func.count(Category.id)))

    by_status = {
        r.status: r.n
        for r in session.execute(
            select(Task.status, func.count(Task.id).label("n")).group_by(Task.status)
        ).all()
    }
    by_priority = {
        r.priority: r.n
        for r in session.execute(
            select(Task.priority, func.count(Task.id).label("n")).group_by(
                Task.priority
            )
        ).all()
    }

    active = ("pending", "in_progress")
    overdue_rows = (
        session.execute(
            select(Task).where(
                Task.due_date.is_not(None),
                Task.due_date < now,
                Task.status.in_(active),
            )
        )
        .scalars()
        .all()
    )
    overdue_list = [
        {
            "id": t.id,
            "title": t.title,
            "due_date": str(t.due_date),
            "days_overdue": (now - t.due_date).days,
        }
        for t in overdue_rows
    ]

    seven_days_ago = now - timedelta(days=7)
    recent_tasks = session.scalar(
        select(func.count(Task.id)).where(Task.created_at >= seven_days_ago)
    )
    recent_done = session.scalar(
        select(func.count(Task.id)).where(
            Task.status == "done", Task.updated_at >= seven_days_ago
        )
    )

    productivity = session.execute(
        select(
            User.id.label("uid"),
            User.name.label("uname"),
            func.count(Task.id).label("total"),
            func.count(Task.id).filter(Task.status == "done").label("completed"),
        )
        .outerjoin(Task, Task.user_id == User.id)
        .group_by(User.id, User.name)
    ).all()
    user_stats = [
        {
            "user_id": row.uid,
            "user_name": row.uname,
            "total_tasks": row.total,
            "completed_tasks": int(row.completed or 0),
            "completion_rate": calculate_percentage(int(row.completed or 0), row.total),
        }
        for row in productivity
    ]

    return {
        "generated_at": str(now),
        "overview": {
            "total_tasks": total_tasks,
            "total_users": total_users,
            "total_categories": total_categories,
        },
        "tasks_by_status": {
            "pending": by_status.get("pending", 0),
            "in_progress": by_status.get("in_progress", 0),
            "done": by_status.get("done", 0),
            "cancelled": by_status.get("cancelled", 0),
        },
        "tasks_by_priority": {
            "critical": by_priority.get(1, 0),
            "high": by_priority.get(2, 0),
            "medium": by_priority.get(3, 0),
            "low": by_priority.get(4, 0),
            "minimal": by_priority.get(5, 0),
        },
        "overdue": {"count": len(overdue_list), "tasks": overdue_list},
        "recent_activity": {
            "tasks_created_last_7_days": recent_tasks,
            "tasks_completed_last_7_days": recent_done,
        },
        "user_productivity": user_stats,
    }


def user_report(user_id):
    from core.errors import NotFoundError

    user = db.session.get(User, user_id)
    if not user:
        raise NotFoundError("Usuario nao encontrado")

    rows = (
        db.session.execute(select(Task).where(Task.user_id == user_id))
        .scalars()
        .all()
    )

    total = len(rows)
    counts = {"done": 0, "pending": 0, "in_progress": 0, "cancelled": 0}
    high_priority = 0
    overdue = 0
    for t in rows:
        if t.status in counts:
            counts[t.status] += 1
        if t.priority <= 2:
            high_priority += 1
        if t.is_overdue():
            overdue += 1

    return {
        "user": {"id": user.id, "name": user.name, "email": user.email},
        "statistics": {
            "total_tasks": total,
            "done": counts["done"],
            "pending": counts["pending"],
            "in_progress": counts["in_progress"],
            "cancelled": counts["cancelled"],
            "overdue": overdue,
            "high_priority": high_priority,
            "completion_rate": calculate_percentage(counts["done"], total),
        },
    }
