from src.models import category as category_model
from src.utils import validators
from src.utils.errors import NotFoundError


def _get_or_404(category_id):
    category = category_model.find_by_id(category_id)
    if category is None:
        raise NotFoundError("Categoria não encontrada")
    return category


def _validate_name(value):
    name = validators.required_string(value, "Nome é obrigatório")
    return validators.string_length(
        name, 1, category_model.NAME_MAX_LENGTH, "Nome é obrigatório", "Nome muito longo"
    )


def _validate_description(value):
    description = validators.optional_string(value, "Descrição") or ""
    return validators.string_length(
        description, 0, category_model.DESCRIPTION_MAX_LENGTH, "", "Descrição muito longa"
    )


def list_categories():
    result = []
    for category, task_count in category_model.list_with_task_count():
        data = category.to_dict()
        data["task_count"] = task_count
        result.append(data)
    return result


def create_category(data):
    data = validators.require_json_object(data)
    category = category_model.create(
        name=_validate_name(data.get("name")),
        description=_validate_description(data.get("description", "")),
        color=validators.color(data.get("color", category_model.DEFAULT_COLOR)),
    )
    return category.to_dict()


def update_category(category_id, data):
    category = _get_or_404(category_id)
    data = validators.require_json_object(data)

    if "name" in data:
        category.name = _validate_name(data["name"])
    if "description" in data:
        category.description = _validate_description(data["description"])
    if "color" in data:
        category.color = validators.color(data["color"])

    category_model.save()
    return category.to_dict()


def delete_category(category_id):
    category_model.delete(_get_or_404(category_id))
    return {"message": "Categoria deletada"}
