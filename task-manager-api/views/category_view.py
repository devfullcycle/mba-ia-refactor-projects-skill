def render(category):
    return {
        'id': category.id,
        'name': category.name,
        'description': category.description,
        'color': category.color,
        'created_at': str(category.created_at),
    }


def render_list_item(category, task_count):
    data = render(category)
    data['task_count'] = task_count
    return data
