"""Response shapes. Every task/user representation derives from the model's to_dict()."""
USER_TASK_FIELDS = ("id", "title", "description", "status", "priority", "created_at", "due_date")


def task_detail(task, now=None):
    data = task.to_dict()
    data["overdue"] = task.is_overdue(now)
    return data


def task_list_item(task, now=None):
    data = task_detail(task, now)
    data["user_name"] = task.user.name if task.user else None
    data["category_name"] = task.category.name if task.category else None
    return data


def task_list(tasks):
    return [task_list_item(task) for task in tasks]


def user_task_list(tasks):
    result = []
    for task in tasks:
        data = {field: value for field, value in task.to_dict().items() if field in USER_TASK_FIELDS}
        data["overdue"] = task.is_overdue()
        result.append(data)
    return result


def user_summary(user, task_count):
    data = user.to_dict()
    data["task_count"] = task_count
    return data


def user_detail(user, tasks):
    data = user.to_dict()
    data["tasks"] = [task.to_dict() for task in tasks]
    return data


def category_summary(category, task_count):
    data = category.to_dict()
    data["task_count"] = task_count
    return data


def login_response(user, token):
    return {"message": "Login realizado com sucesso", "user": user.to_dict(), "token": token}
