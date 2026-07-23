from sqlalchemy import select, func
from flask import request
from database import db
from models.category import Category
from models.task import Task
from core.errors import NotFoundError, ValidationError
from utils.helpers import is_valid_color


def list_categories():
    categories = db.session.execute(select(Category)).scalars().all()
    result = []
    for c in categories:
        data = c.to_dict()
        data["task_count"] = (
            db.session.scalar(
                select(func.count(Task.id)).where(Task.category_id == c.id)
            )
            or 0
        )
        result.append(data)
    return result, 200


def create_category():
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    if not name:
        raise ValidationError("Nome e obrigatorio")
    color = data.get("color", "#000000")
    if not is_valid_color(color):
        raise ValidationError("Cor invalida (use #RRGGBB)")

    category = Category(name=name, description=data.get("description", ""), color=color)
    db.session.add(category)
    db.session.commit()
    return category.to_dict(), 201


def update_category(cat_id):
    cat = db.session.get(Category, cat_id)
    if not cat:
        raise NotFoundError("Categoria nao encontrada")
    data = request.get_json() or {}
    if "name" in data:
        cat.name = data["name"]
    if "description" in data:
        cat.description = data["description"]
    if "color" in data:
        if not is_valid_color(data["color"]):
            raise ValidationError("Cor invalida (use #RRGGBB)")
        cat.color = data["color"]
    db.session.commit()
    return cat.to_dict(), 200


def delete_category(cat_id):
    cat = db.session.get(Category, cat_id)
    if not cat:
        raise NotFoundError("Categoria nao encontrada")
    db.session.delete(cat)
    db.session.commit()
    return {"message": "Categoria deletada"}, 200
