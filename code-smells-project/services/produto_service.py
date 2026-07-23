from core.constants import CATEGORIAS_VALIDAS
from core.errors import ValidationError
from schemas.produto_schema import ProdutoSchema
from models import produto_model


def _validate(data):
    errors = ProdutoSchema().validate(data or {})
    if errors:
        raise ValidationError(str(errors))
    if data["categoria"] not in CATEGORIAS_VALIDAS:
        raise ValidationError(
            "Categoria invalida. Validas: " + str(CATEGORIAS_VALIDAS)
        )


def list_products():
    return produto_model.list_all()


def get_product(produto_id):
    produto = produto_model.get_by_id(produto_id)
    if not produto:
        from core.errors import NotFoundError
        raise NotFoundError("Produto nao encontrado")
    return produto


def create_product(data):
    _validate(data)
    novo_id = produto_model.create(
        data["nome"],
        data.get("descricao", ""),
        data["preco"],
        data["estoque"],
        data.get("categoria", "geral"),
    )
    return novo_id


def update_product(produto_id, data):
    _validate(data)
    if not produto_model.get_by_id(produto_id):
        from core.errors import NotFoundError
        raise NotFoundError("Produto nao encontrado")
    produto_model.update(
        produto_id,
        data["nome"],
        data.get("descricao", ""),
        data["preco"],
        data["estoque"],
        data.get("categoria", "geral"),
    )


def delete_product(produto_id):
    if not produto_model.get_by_id(produto_id):
        from core.errors import NotFoundError
        raise NotFoundError("Produto nao encontrado")
    produto_model.delete(produto_id)


def search_products(termo=None, categoria=None, preco_min=None, preco_max=None):
    return produto_model.search(termo, categoria, preco_min, preco_max)
