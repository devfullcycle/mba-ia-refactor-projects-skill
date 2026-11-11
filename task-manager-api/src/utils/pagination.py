from dataclasses import dataclass

from flask import current_app

from src.utils.errors import ValidationError
from src.utils.validators import query_int


@dataclass(frozen=True)
class Page:
    page: int
    per_page: int

    @property
    def offset(self):
        return (self.page - 1) * self.per_page


def parse_page(args):
    """Paginação opcional: sem ?page/?per_page a listagem completa é mantida (contrato legado)."""
    if "page" not in args and "per_page" not in args:
        return None

    page = query_int(args.get("page", 1), "page")
    per_page = query_int(args.get("per_page", current_app.config["DEFAULT_PER_PAGE"]), "per_page")
    if page < 1 or per_page < 1:
        raise ValidationError("page e per_page devem ser maiores que zero")
    return Page(page=page, per_page=min(per_page, current_app.config["MAX_PER_PAGE"]))


def apply_page(query, page):
    if page is None:
        return query
    return query.limit(page.per_page).offset(page.offset)


def pagination_headers(total, page):
    if page is None:
        return {}
    return {"X-Total-Count": str(total), "X-Page": str(page.page), "X-Per-Page": str(page.per_page)}
