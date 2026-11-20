"""Response serializers: turn entities returned by controllers into the public JSON shapes."""


def present_task(task):
    data = task.to_dict()
    data["overdue"] = task.is_overdue()
    return data


def present_task_with_relations(task):
    data = present_task(task)
    data["user_name"] = task.user.name if task.user else None
    data["category_name"] = task.category.name if task.category else None
    return data


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


def present_user_with_count(user, task_count):
    data = user.to_dict()
    data["task_count"] = task_count
    return data


def present_category_with_count(category, task_count):
    data = category.to_dict()
    data["task_count"] = task_count
    return data
