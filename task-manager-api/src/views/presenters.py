"""Response serializers — keep the exact keys of the original API."""


def present_task(task):
    return task.to_dict()


def present_task_detail(task):
    return {**task.to_dict(), "overdue": task.is_overdue()}


def present_task_with_relations(task):
    return {
        **present_task_detail(task),
        "user_name": task.user.name if task.user else None,
        "category_name": task.category.name if task.category else None,
    }


def present_user_task(task):
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "status": task.status,
        "priority": task.priority,
        "created_at": str(task.created_at),
        "due_date": str(task.due_date) if task.due_date else None,
        "overdue": task.is_overdue(),
    }


def present_user(user):
    return user.to_dict()


def present_user_summary(user, task_count):
    return {**user.to_dict(), "task_count": task_count}


def present_user_detail(user, tasks):
    return {**user.to_dict(), "tasks": [present_task(task) for task in tasks]}


def present_category(category, task_count=None):
    data = category.to_dict()
    if task_count is not None:
        data["task_count"] = task_count
    return data
