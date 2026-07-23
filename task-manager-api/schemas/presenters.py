"""Presenters públicos por allowlist, sem dependência de Flask ou SQLAlchemy."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
from typing import Any


_MISSING = object()


def _value(source: Any, name: str, default: Any = None) -> Any:
    if isinstance(source, Mapping):
        return source.get(name, default)
    return getattr(source, name, default)


def _timestamp(value: Any) -> str:
    return str(value)


def _optional_timestamp(value: Any) -> str | None:
    return str(value) if value is not None else None


def _task_tags(value: Any) -> list[Any]:
    if not value:
        return []
    if isinstance(value, str):
        return value.split(",")
    return list(value)


def _overdue(task: Any, now: datetime | None = None) -> bool:
    explicit = _value(task, "overdue", _MISSING)
    if explicit is not _MISSING:
        return bool(explicit)
    due_date = _value(task, "due_date")
    if not due_date or _value(task, "status") in ("done", "cancelled"):
        return False
    if isinstance(due_date, str):
        try:
            due_date = datetime.fromisoformat(due_date)
        except ValueError:
            return False
    current = now or datetime.now(UTC).replace(tzinfo=None)
    if due_date.tzinfo is not None and current.tzinfo is None:
        current = current.replace(tzinfo=UTC)
    elif due_date.tzinfo is None and current.tzinfo is not None:
        current = current.replace(tzinfo=None)
    return due_date < current


def present_task(
    task: Any,
    *,
    include_overdue: bool = False,
    include_relations: bool = False,
    now: datetime | None = None,
    user_name: Any = _MISSING,
    category_name: Any = _MISSING,
) -> dict[str, Any]:
    data = {
        "id": _value(task, "id"),
        "title": _value(task, "title"),
        "description": _value(task, "description"),
        "status": _value(task, "status"),
        "priority": _value(task, "priority"),
        "user_id": _value(task, "user_id"),
        "category_id": _value(task, "category_id"),
        "created_at": _timestamp(_value(task, "created_at")),
        "updated_at": _timestamp(_value(task, "updated_at")),
        "due_date": _optional_timestamp(_value(task, "due_date")),
        "tags": _task_tags(_value(task, "tags")),
    }
    if include_overdue:
        data["overdue"] = _overdue(task, now)
    if include_relations:
        if user_name is _MISSING:
            user_name = _value(task, "user_name", _MISSING)
        if user_name is _MISSING:
            user = _value(task, "user")
            user_name = _value(user, "name") if user is not None else None
        if category_name is _MISSING:
            category_name = _value(task, "category_name", _MISSING)
        if category_name is _MISSING:
            category = _value(task, "category")
            category_name = _value(category, "name") if category is not None else None
        data["user_name"] = user_name
        data["category_name"] = category_name
    return data


def present_tasks(tasks: Iterable[Any], **options: Any) -> list[dict[str, Any]]:
    return [present_task(task, **options) for task in tasks]


def present_task_overdue(task: Any, *, now: datetime | None = None) -> dict[str, Any]:
    return present_task(task, include_overdue=True, now=now)


def present_task_with_relations(
    task: Any, *, now: datetime | None = None
) -> dict[str, Any]:
    return present_task(task, include_overdue=True, include_relations=True, now=now)


def present_user(user: Any) -> dict[str, Any]:
    """DTO público: credenciais nunca são lidas nem copiadas."""

    return {
        "id": _value(user, "id"),
        "name": _value(user, "name"),
        "email": _value(user, "email"),
        "role": _value(user, "role"),
        "active": _value(user, "active"),
        "created_at": _timestamp(_value(user, "created_at")),
    }


present_public_user = present_user


def present_user_list_item(user: Any, *, task_count: Any = _MISSING) -> dict[str, Any]:
    data = present_user(user)
    if task_count is _MISSING:
        task_count = _value(user, "task_count", _MISSING)
    if task_count is _MISSING:
        tasks = _value(user, "tasks", ())
        task_count = len(tasks)
    data["task_count"] = task_count
    return data


def present_users(users: Iterable[Any]) -> list[dict[str, Any]]:
    return [present_user_list_item(user) for user in users]


def present_user_detail(
    user: Any, *, tasks: Iterable[Any] | None = None
) -> dict[str, Any]:
    data = present_user(user)
    task_values = _value(user, "tasks", ()) if tasks is None else tasks
    data["tasks"] = present_tasks(task_values)
    return data


def present_user_task(
    task: Any, *, now: datetime | None = None
) -> dict[str, Any]:
    return {
        "id": _value(task, "id"),
        "title": _value(task, "title"),
        "description": _value(task, "description"),
        "status": _value(task, "status"),
        "priority": _value(task, "priority"),
        "created_at": _timestamp(_value(task, "created_at")),
        "due_date": _optional_timestamp(_value(task, "due_date")),
        "overdue": _overdue(task, now),
    }


def present_user_tasks(
    tasks: Iterable[Any], *, now: datetime | None = None
) -> list[dict[str, Any]]:
    return [present_user_task(task, now=now) for task in tasks]


def present_category(
    category: Any, *, include_task_count: bool = False, task_count: Any = _MISSING
) -> dict[str, Any]:
    data = {
        "id": _value(category, "id"),
        "name": _value(category, "name"),
        "description": _value(category, "description"),
        "color": _value(category, "color"),
        "created_at": _timestamp(_value(category, "created_at")),
    }
    if include_task_count:
        if task_count is _MISSING:
            task_count = _value(category, "task_count", _MISSING)
        if task_count is _MISSING:
            task_count = len(_value(category, "tasks", ()))
        data["task_count"] = task_count
    return data


def present_categories(
    categories: Iterable[Any], *, include_task_count: bool = False
) -> list[dict[str, Any]]:
    return [
        present_category(category, include_task_count=include_task_count)
        for category in categories
    ]


def present_task_stats(stats: Any) -> dict[str, Any]:
    return {
        field: _value(stats, field, 0)
        for field in (
            "total",
            "pending",
            "in_progress",
            "done",
            "cancelled",
            "overdue",
            "completion_rate",
        )
    }


def present_overdue_report_task(task: Any) -> dict[str, Any]:
    return {
        "id": _value(task, "id"),
        "title": _value(task, "title"),
        "due_date": _optional_timestamp(_value(task, "due_date")),
        "days_overdue": _value(task, "days_overdue"),
    }


def present_user_productivity(item: Any) -> dict[str, Any]:
    return {
        field: _value(item, field)
        for field in (
            "user_id",
            "user_name",
            "total_tasks",
            "completed_tasks",
            "completion_rate",
        )
    }


def present_summary_report(report: Any) -> dict[str, Any]:
    overview = _value(report, "overview", {})
    statuses = _value(report, "tasks_by_status", {})
    priorities = _value(report, "tasks_by_priority", {})
    overdue = _value(report, "overdue", {})
    recent = _value(report, "recent_activity", {})
    return {
        "generated_at": _timestamp(_value(report, "generated_at")),
        "overview": {
            field: _value(overview, field, 0)
            for field in ("total_tasks", "total_users", "total_categories")
        },
        "tasks_by_status": {
            field: _value(statuses, field, 0)
            for field in ("pending", "in_progress", "done", "cancelled")
        },
        "tasks_by_priority": {
            field: _value(priorities, field, 0)
            for field in ("critical", "high", "medium", "low", "minimal")
        },
        "overdue": {
            "count": _value(overdue, "count", 0),
            "tasks": [
                present_overdue_report_task(task)
                for task in _value(overdue, "tasks", ())
            ],
        },
        "recent_activity": {
            field: _value(recent, field, 0)
            for field in (
                "tasks_created_last_7_days",
                "tasks_completed_last_7_days",
            )
        },
        "user_productivity": [
            present_user_productivity(item)
            for item in _value(report, "user_productivity", ())
        ],
    }


def present_user_report(user: Any, statistics: Any | None = None) -> dict[str, Any]:
    if statistics is None and _value(user, "statistics", _MISSING) is not _MISSING:
        statistics = _value(user, "statistics")
        user = _value(user, "user")
    return {
        "user": {
            "id": _value(user, "id"),
            "name": _value(user, "name"),
            "email": _value(user, "email"),
        },
        "statistics": {
            field: _value(statistics, field, 0)
            for field in (
                "total_tasks",
                "done",
                "pending",
                "in_progress",
                "cancelled",
                "overdue",
                "high_priority",
                "completion_rate",
            )
        },
    }


def present_login(user: Any, token: str) -> dict[str, Any]:
    return {
        "message": "Login realizado com sucesso",
        "user": present_user(user),
        "token": token,
    }


def present_message(message: str) -> dict[str, str]:
    return {"message": message}


def present_error(message: str) -> dict[str, str]:
    return {"error": message}


def present_health(status: str, timestamp: Any) -> dict[str, str]:
    return {"status": status, "timestamp": _timestamp(timestamp)}


def present_index(message: str, version: str) -> dict[str, str]:
    return {"message": message, "version": version}
