"""Serializers de Task: definem a forma JSON de cada resposta."""


def _date(value):
    return str(value) if value else None


def render(task):
    return {
        'id': task.id,
        'title': task.title,
        'description': task.description,
        'status': task.status,
        'priority': task.priority,
        'user_id': task.user_id,
        'category_id': task.category_id,
        'created_at': str(task.created_at),
        'updated_at': str(task.updated_at),
        'due_date': _date(task.due_date),
        'tags': task.tags.split(',') if task.tags else [],
    }


def render_detail(task):
    data = render(task)
    data['overdue'] = task.is_overdue()
    return data


def render_list_item(task):
    data = render_detail(task)
    data['user_name'] = task.user.name if task.user else None
    data['category_name'] = task.category.name if task.category else None
    return data


def render_summary(task):
    """Formato reduzido usado em /users/<id>/tasks."""
    return {
        'id': task.id,
        'title': task.title,
        'description': task.description,
        'status': task.status,
        'priority': task.priority,
        'created_at': str(task.created_at),
        'due_date': _date(task.due_date),
        'overdue': task.is_overdue(),
    }
