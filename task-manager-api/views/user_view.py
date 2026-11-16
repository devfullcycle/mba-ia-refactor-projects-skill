"""Serializers de User. O hash de senha nunca é exposto."""
from views import task_view


def render(user):
    return {
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'role': user.role,
        'active': user.active,
        'created_at': str(user.created_at),
    }


def render_list_item(user, task_count):
    data = render(user)
    data['task_count'] = task_count
    return data


def render_detail(user, tasks):
    data = render(user)
    data['tasks'] = [task_view.render(t) for t in tasks]
    return data
